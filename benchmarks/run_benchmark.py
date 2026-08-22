"""Run the A/B/C benchmark: one agent, one battery, three arms.

Every run is a headless Claude Code invocation in a fresh working directory holding
nothing but its own copy of the corpus. Arms differ only in what the runtime makes
available; the question text is identical across arms and only the preamble differs.

    python benchmarks/run_benchmark.py --corpus-clean /tmp/kb_clean \
        --corpus-malformed /tmp/kb_malformed --truth-clean /tmp/truth_clean.json \
        --truth-malformed /tmp/truth_malformed.json \
        --readb-bin /tmp/benchvenv/bin/readb \
        --results benchmarks/results/run.jsonl --repeats 3

Full stream transcripts are kept per run: without them the integrity checks below —
did readb leak into the baseline, did the skill actually load, did the agent answer
without doing any work — cannot be made at all.

Results are appended as JSONL and the run is resumable: a (arm, question, repeat) cell
already present in the results file is skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from battery import ALL_QUESTIONS, QUESTIONS, extract_answer, render, score  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# A deliberately minimal PATH: the machine may carry a globally installed readb (and uv,
# which could fetch one), either of which would leak the treatment into the baseline arm.
# The runtime binary is therefore resolved from the parent environment and invoked by
# absolute path rather than found on the child's PATH.
BASE_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
CLAUDE_BIN = shutil.which("claude") or "claude"

# USD per million tokens, per model. Committed with the results so the published cost can
# be recomputed in six months, when the live price list will have moved on.
#
# Two notes on the basis, both of which the write-up must carry:
#
# - v1 priced Sonnet at $3/$15. That was the announced post-introductory rate; the
#   introductory $2/$10 has since become the standard price, so v2's absolute dollar
#   figures are NOT comparable to v1's. Every published ratio is a contrast between two
#   arms on the same model, where a uniform scale cancels, so no ratio changes.
# - Cache rates are the published multipliers on each model's base input rate: 1.25x for a
#   5-minute write, 2x for a 1-hour write, 0.1x for a read.
PRICES = {
    "claude-sonnet-5": {
        "input": 2.00,
        "output": 10.00,
        "cache_read": 0.20,
        "cache_write_5m": 2.50,
        "cache_write_1h": 4.00,
    },
    "claude-haiku-4-5": {
        "input": 1.00,
        "output": 5.00,
        "cache_read": 0.10,
        "cache_write_5m": 1.25,
        "cache_write_1h": 2.00,
    },
}


def prices_for(model: str) -> dict:
    """The price table for a model, or a loud failure.

    Falling back to another model's prices would publish a cost figure that is wrong by a
    factor of two or three with nothing in the output to show it.
    """
    try:
        return PRICES[model]
    except KeyError:
        raise SystemExit(
            f"no price table for model {model!r} — add one to PRICES before running it, "
            f"since a benchmark that cannot price a run cannot report its cost"
        ) from None


PREAMBLE_BASELINE = "You are working in a directory that holds a knowledge base.\n\n"

PREAMBLE_READB = (
    "You are working in a directory that holds a knowledge base. Also installed is "
    "`readb`, a command that runs read-only SQL over a directory of markdown files with "
    'YAML frontmatter: `readb query "<sql>" --bundle corpus` runs a query, and '
    "`readb schema --bundle corpus` lists the tables and columns it exposes.\n\n"
)

# The honest competitor to readb is not an uncoached agent — it is a shell pipeline. Without
# this arm, arm B minus arm A measures "given a worked recipe" against "given none", and
# would be read as "readb against file tools".
#
# The coached recipe is data, not prose, so the exact commands an arm is shown can be
# executed against a real corpus before any measured run. Coaching a command the arm cannot
# run is what retracted 36 runs once already — and `yq '.tier' <file>` is such a command: it
# prints the value and then fails, because it reads the markdown body as a second YAML
# document. `--front-matter=extract` is the form that works.
#
# v2's corpora are written in mixed styles, so a naive `rg '^status: ga'` silently misses
# every file that quoted the value. The coached patterns therefore tolerate quoting and
# spacing, and the preflight checks one of them against ground truth rather than merely
# checking that it exits zero: a recipe that runs and under-counts is a straw man, and a
# straw man in the competitor arm is worth more to readb's numbers than any real effect.
_COUNT_VALUES = '| sed -E "s/.*:[[:space:]]*//; s/^[\'\\"]|[\'\\"]$//g" | sort | uniq -c'

OPS_RECIPE = (
    (
        "lists the files carrying a given frontmatter field, quoted or not",
        'rg -l "^tier:[[:space:]]*1" corpus/services',
    ),
    (
        "counts one field's values across a directory",
        'rg -N "^status:" corpus/services ' + _COUNT_VALUES,
    ),
    (
        "reads one field out of a single file's frontmatter",
        "yq --front-matter=extract '.tier' corpus/services/{service}.md",
    ),
)

BACKLOG_RECIPE = (
    (
        "lists the files carrying a given frontmatter field, quoted or not",
        'rg -l "^status:[[:space:]]*[\'\\"]?Draft" corpus/tasks',
    ),
    (
        "counts one field's values across a directory",
        'rg -N "^priority:" corpus/tasks corpus/archive ' + _COUNT_VALUES,
    ),
    (
        "reads one field out of a single file's frontmatter",
        "yq --front-matter=extract '.status' corpus/tasks/{task}.md",
    ),
)

# One recipe per corpus *family*: coaching an arm with paths that do not exist in the
# bundle in front of it is the same defect as coaching a command it cannot run.
RECIPES = {
    "ops": OPS_RECIPE,
    "ops-malformed": OPS_RECIPE,
    "ops-tidy": OPS_RECIPE,
    "backlog": BACKLOG_RECIPE,
}


def recipe_placeholders(truth: dict) -> dict:
    """Real names from the corpus, so a coached command is runnable as shown."""
    values = {}
    if "q3" in truth:
        values["service"] = truth["q3"]["answer"][0]
    if "b1" in truth:
        values["task"] = truth["b1"]["answer"][0]
    return values


def shell_preamble(recipe: tuple[tuple[str, str], ...], placeholders: dict) -> str:
    examples = ", ".join(
        f"`{command.format(**placeholders)}` {gloss}" for gloss, command in recipe[:-1]
    )
    gloss, command = recipe[-1]
    return (
        "You are working in a directory that holds a knowledge base. For example, "
        f"{examples}, and `{command.format(**placeholders)}` {gloss}.\n\n"
    )


# Tool availability belongs in the SHARED intro, not in an arm's preamble: every arm has
# the same tools on PATH, so every arm must be told so in the same words. Otherwise the
# experiment measures which tools an arm was told about rather than which it had.
TASK_INTRO = (
    "The directory `corpus/` holds a knowledge base: markdown files with YAML "
    "frontmatter, one concept per file, organised into subdirectories by kind. "
    "`corpus/index.md` is a listing of the knowledge base, not a concept.\n\n"
    "Alongside the standard shell you have `rg` (ripgrep), `jq`, `yq` (a YAML "
    "processor), `python3`, `perl` and `sqlite3`.\n\n"
)

# `--setting-sources ""` strips user, project and local settings — no personal CLAUDE.md,
# skill, plugin, hook or MCP server reaches any arm; only Claude Code's own built-in skills
# remain, identically in all three. `--plugin-dir` then adds exactly one skill (`readb`) to
# arm C, which is the single variable that arm exists to test. `--safe-mode` cannot be used
# here: it suppresses `--plugin-dir`, and arm C would silently collapse onto arm A with no
# visible sign in the output.
ISOLATION = ("--setting-sources", "")


@dataclass(frozen=True)
class Arm:
    name: str
    preamble: str
    readb_on_path: bool
    extra_args: tuple[str, ...]
    expects_skill: bool
    uv_on_path: bool = False


# A PATH entry is built by symlinking named binaries into a directory, rather than adding
# a whole package manager's bin — that would hand one arm several hundred tools the arms it
# is compared against do not have.
def shim(workroot: Path, label: str, names: tuple[str, ...]) -> str:
    path = workroot / f".{label}-shim"
    path.mkdir(parents=True, exist_ok=True)
    for name in names:
        source, link = shutil.which(name), path / name
        if source and not link.exists():
            link.symlink_to(source)
    return str(path)


# Given to EVERY arm, identically. The first battery ran with only `/usr/bin` on PATH, so no
# arm had ripgrep or a YAML processor and every arm was reduced to grep and awk — which
# handicapped the file-reading arms specifically, since structured search returns parsed,
# truncated output instead of piping raw text into the context. readb's competitor should be
# the best tooling a shell can offer, not the worst.
SHARED_TOOLS = ("rg", "jq", "yq", "python3", "perl", "sqlite3")

# `uv` is the exception: it goes to the skill arm alone, and now as insurance rather than as a
# requirement. The skill's leading example used to be `uvx readb …`, so that arm could not
# execute its own documentation without it; the example now invokes the bare binary, so `uv` is
# unnecessary — but leaving it removes a way for the arm to fail on something other than what is
# being measured, and the arm already has readb, so `uv` grants it nothing. Handing `uvx` to a
# readb-free arm would let it fetch readb, which is the leak the PATH control exists to prevent.
UV_TOOLS = ("uv", "uvx")


# --- the nudge -----------------------------------------------------------------
# FROZEN. Written once, before the first measured run, and not edited afterwards.
#
# Routing guidance is a fifth ARM rather than an edit to `readb-bare`, for two reasons.
# Folding it into the base arm would silently redefine what v1 measured, so the two
# batteries would stop being comparable. And editing prompt text until the agent picks the
# tool the experimenter prefers is tuning the benchmark until it flatters the tool — the
# un-nudged arm is always run and always reported, and the nudge's worth is the contrast
# between them, declared in advance.
#
# RETRACTION RULE: if this sentence changes after any measured run, every `readb-nudged`
# record produced before the change is flagged `retracted` and re-measured. If the nudge
# proves valuable, that is an argument for changing the shipped skill — a separate task,
# measured separately, never a change to this experiment.
NUDGE = (
    "When a question is about many documents at once — counting them, filtering them, "
    "grouping them, or relating one kind of document to another — a single `readb query` "
    "is usually cheaper than reading or searching the files.\n\n"
)

ARMS = {
    "baseline": Arm("baseline", PREAMBLE_BASELINE, False, ISOLATION, False),
    "shell-coached": Arm("shell-coached", "", False, ISOLATION, False),
    "readb-bare": Arm("readb-bare", PREAMBLE_READB, True, ISOLATION, False),
    "readb-nudged": Arm("readb-nudged", PREAMBLE_READB + NUDGE, True, ISOLATION, False),
    "readb-skill": Arm(
        "readb-skill",
        PREAMBLE_BASELINE,
        True,
        (*ISOLATION, "--plugin-dir", str(REPO_ROOT)),
        True,
        uv_on_path=True,
    ),
}

# A trivial prompt run through the identical harness, to measure the fixed overhead that
# both arms pay before any work happens. Without it, every ratio is diluted toward 1 by an
# unknown constant.
FLOOR_PROMPT = "Reply with exactly this line and nothing else:\nANSWER: ok"


# Transcripts and manifests are committed verbatim, and a run's own paths travel inside
# them — home directory, scratch directory, and the account name embedded in both. The
# repository is public-bound, so those are redacted on the way out rather than left for a
# later sweep to catch.
REDACTIONS = [
    (os.environ.get("TMPDIR", "").rstrip("/") or "\0", "<TMP>"),
    (str(Path.home()), "<HOME>"),
    (os.environ.get("USER") or "\0", "<USER>"),
]


def scrub(text: str) -> str:
    for needle, placeholder in REDACTIONS:
        if needle and needle != "\0":
            text = text.replace(needle, placeholder)
    return text


# --- transcript analysis ------------------------------------------------------


def parse_stream(lines: list[str]) -> tuple[dict, list[dict], list[dict]]:
    """Split a stream-json transcript into its final result, its tool calls, and their results.

    v1 read only the calls. The results are where the retry rate lives — a failed command
    and its recovery are invisible in the call list, which is why v1 could report a clean
    sheet on a batch that was in fact paying for exit-127 recoveries.
    """
    result: dict = {}
    tools: list[dict] = []
    results: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            result = event
        message = event.get("message") or {}
        for block in message.get("content", []) or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                tools.append(
                    {
                        "id": block.get("id"),
                        "name": block.get("name"),
                        "input": block.get("input") or {},
                    }
                )
            elif block.get("type") == "tool_result":
                results.append(
                    {
                        "id": block.get("tool_use_id"),
                        "is_error": bool(block.get("is_error")),
                        "text": _result_text(block.get("content")),
                    }
                )
    return result, tools, results


def _result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    return ""


# Binaries that count as *searching* the corpus rather than reading one file of it. Fixed
# before the runs: tool choice is reported as a result, never used to adjust a prompt.
SEARCH_BINARIES = (
    "rg",
    "grep",
    "awk",
    "sed",
    "yq",
    "jq",
    "python3",
    "perl",
    "sqlite3",
    "find",
    "ls",
    "wc",
    "head",
    "tail",
)
_SEARCH_RE = re.compile(r"\b(" + "|".join(SEARCH_BINARIES) + r")\b")


def classify_tool_choice(tools: list[dict]) -> str:
    """One label for what the agent actually reached for.

    `readb` wins outright — an agent that ran it chose it, however else it also poked
    around. Otherwise the label goes to whichever of searching and reading it did more of,
    with ties going to searching, since a search is the cheaper habit and calling a tie a
    read would flatter the file-reading arms.
    """
    if not tools:
        return "none"
    commands = [str(t["input"].get("command", "")) for t in tools if t["name"] == "Bash"]
    if any("readb" in command for command in commands):
        return "readb"
    search = sum(1 for command in commands if _SEARCH_RE.search(command))
    search += sum(1 for t in tools if t["name"] in ("Grep", "Glob"))
    reads = sum(1 for t in tools if t["name"] == "Read")
    if not search and not reads:
        return "other"
    return "shell" if search >= reads else "read"


# readb prints one of these per file it skips. A run that saw one and still answered as if
# nothing had been skipped is a different finding from a run that never saw the warning:
# the first says the warning did not work, the second says the hazard is silent.
SKIP_WARNING_MARKERS = ("malformed YAML frontmatter", "skipping ")


def integrity(
    arm: Arm,
    tools: list[dict],
    result: dict,
    transcript: str,
    tool_results: list[dict] | None = None,
) -> dict:
    """Facts about a run that decide whether its numbers may be used at all."""
    tool_results = tool_results or []
    by_id = {t.get("id"): t for t in tools}
    commands = " ".join(str(t["input"].get("command", "")) for t in tools if t["name"] == "Bash")
    readb_used = "readb" in commands
    skill_used = any(t["name"] in ("Skill", "SlashCommand") for t in tools)
    skill_readb = any(
        t["name"] in ("Skill", "SlashCommand") and "readb" in json.dumps(t["input"]).lower()
        for t in tools
    )

    def command_of(entry: dict) -> str:
        call = by_id.get(entry.get("id")) or {}
        return str((call.get("input") or {}).get("command", ""))

    failed = [entry for entry in tool_results if entry["is_error"]]
    return {
        # The retry rate the model comparison needs. A failed command and the turn spent
        # recovering from it are what separate a weaker model from a stronger one here.
        "failed_tool_results": len(failed),
        "failed_readb_calls": sum(1 for entry in failed if "readb" in command_of(entry)),
        # Trap diagnostics: an un-warned wrong answer and a warning that went unread are
        # different failures, and only the transcript can tell them apart.
        "saw_skip_warning": any(
            marker in entry["text"] for entry in tool_results for marker in SKIP_WARNING_MARKERS
        ),
        "tool_choice": classify_tool_choice(tools),
        "tool_calls": len(tools),
        "tool_names": sorted({t["name"] for t in tools if t.get("name")}),
        "readb_invocations": commands.count("readb"),
        "readb_used": readb_used,
        "skill_used": skill_used,
        "skill_readb_used": skill_readb,
        "supported": len(tools) > 0,
        # The baseline must never touch readb: if it did, the arm is contaminated.
        "leak_baseline_readb": (not arm.readb_on_path) and ("readb" in transcript.lower()),
        # Look for an actual compaction event, not the word: the init event lists every
        # built-in slash command, `compact` among them, so a substring match on the raw
        # stream flags every run ever recorded.
        "compacted": any(
            marker in transcript
            for marker in ('"compact_boundary"', '"isCompactSummary":true', '"subtype":"compact')
        ),
        "permission_denials": result.get("permission_denials") or [],
    }


def costs(usage: dict, prices: dict) -> dict:
    """Two costs: as billed, and cache-invariant.

    As-billed depends on the machine's cache state and on prices that move. The
    cache-invariant figure prices every input token as fresh, which is what makes two
    arms comparable and what a reader can recompute from the token counts alone.
    """
    inp = usage.get("input_tokens") or 0
    out = usage.get("output_tokens") or 0
    read = usage.get("cache_read_input_tokens") or 0
    creation = usage.get("cache_creation") or {}
    w1h = creation.get("ephemeral_1h_input_tokens") or 0
    w5m = creation.get("ephemeral_5m_input_tokens") or 0
    if not (w1h or w5m):
        # The flat field carries no TTL. Price it at the cheaper rate: guessing the dearer one
        # would inflate a published cost on any runtime that omits the breakdown.
        w5m = usage.get("cache_creation_input_tokens") or 0

    billed = (
        inp * prices["input"]
        + out * prices["output"]
        + read * prices["cache_read"]
        + w1h * prices["cache_write_1h"]
        + w5m * prices["cache_write_5m"]
    ) / 1e6
    neutral = ((inp + read + w1h + w5m) * prices["input"] + out * prices["output"]) / 1e6
    return {
        "cost_billed_usd": round(billed, 6),
        "cost_cache_neutral_usd": round(neutral, 6),
        "new_tokens_ingested": inp + w1h + w5m,
        "cumulative_prompt_tokens": inp + read + w1h + w5m,
        "output_tokens": out,
        "cache_read_tokens": read,
    }


# --- one run ------------------------------------------------------------------


def run_one(
    arm: Arm, question, repeat: int, cfg, truth: dict, corpus: Path, model: str, corpus_name: str
) -> dict:
    # The working directory name must not contain the tool's name: the cwd is echoed
    # into the system prompt, and "readb" sitting there would prime the baseline arm.
    workdir = cfg.workroot / f"kb-{uuid.uuid4().hex[:12]}"
    workdir.mkdir(parents=True)
    shutil.copytree(corpus, workdir / "corpus")

    env = {
        "HOME": os.environ["HOME"],
        "USER": os.environ.get("USER", ""),
        "TERM": "dumb",
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "PATH": ":".join(
            ([str(cfg.readb_bin.parent)] if arm.readb_on_path else [])
            + ([cfg.uv_shim] if arm.uv_on_path else [])
            + [cfg.tools_shim, BASE_PATH]
        ),
    }
    for key in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "SHELL"):
        if key in os.environ:
            env[key] = os.environ[key]

    # An empty preamble means the arm's treatment is the worked recipe, rendered from the
    # executable command list against this corpus's own names.
    preamble = arm.preamble or shell_preamble(RECIPES[corpus_name], recipe_placeholders(truth))
    prompt = FLOOR_PROMPT if cfg.floor else preamble + TASK_INTRO + render(question, truth)
    cmd = [
        CLAUDE_BIN,
        "-p",
        prompt,
        "--model",
        model,
        "--effort",
        cfg.effort,
        "--output-format",
        "stream-json",
        "--verbose",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--permission-mode",
        "bypassPermissions",
        "--disallowedTools",
        "WebSearch",
        "WebFetch",
        "Task",
        "--autocompact",
        str(cfg.autocompact),
        "--max-budget-usd",
        str(cfg.budget),
        *arm.extra_args,
    ]

    started = time.time()
    stdout, harness_error = "", None
    try:
        proc = subprocess.run(
            cmd, cwd=workdir, env=env, capture_output=True, text=True, timeout=cfg.timeout
        )
        stdout = proc.stdout
        if not stdout.strip():
            harness_error = f"no output (rc={proc.returncode}): {proc.stderr[:400]}"
    except subprocess.TimeoutExpired as exc:
        stdout = (
            (exc.stdout or b"").decode(errors="replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")
        )
        harness_error = f"timeout after {cfg.timeout}s"
    elapsed = time.time() - started

    lines = stdout.splitlines()
    result, tools, tool_results = parse_stream(lines)

    # Namespaced by batch: a re-measurement of one arm must not overwrite the evidence for
    # the batch it replaces. The first arm-C batch lost its transcripts this way.
    slug = model.replace("claude-", "").replace("-", "")
    transcript_path = (
        cfg.transcripts / cfg.results.stem / f"{slug}-{arm.name}-{question.id}-r{repeat}.jsonl"
    )
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    # Never overwrite: a transcript is the only evidence its run happened, and a batch that
    # reused a cell once silently destroyed 68 of them.
    suffix = 1
    while transcript_path.exists():
        suffix += 1
        transcript_path = transcript_path.with_name(
            f"{slug}-{arm.name}-{question.id}-r{repeat}.{suffix}.jsonl"
        )
    transcript_path.write_text(scrub(stdout))

    result_text = result.get("result", "")
    raw_answer = extract_answer(result_text)
    correct, partial, parsed = score(question, raw_answer, truth)
    usage = result.get("usage", {}) or {}
    checks = integrity(arm, tools, result, stdout, tool_results)

    # An answer produced without a single tool call was not derived from the corpus.
    if not checks["supported"]:
        correct, partial = False, 0.0

    record = {
        "arm": arm.name,
        "question": question.id,
        "shape": question.shape,
        "favours": question.favours,
        "repeat": repeat,
        # The corpus actually used, and the one the question declares. They differ only in
        # the messy/tidy sweep, where the same question runs against both renderings.
        "corpus": corpus_name,
        "corpus_declared": question.corpus,
        "model": model,
        # modelUsage also carries the runtime's small side-calls on another model; the
        # dated id worth recording is the one that did the work.
        "model_dated": max(
            (result.get("modelUsage") or {}).items(),
            key=lambda kv: kv[1].get("outputTokens", 0),
            default=(None, None),
        )[0],
        "effort": cfg.effort,
        "started_utc": datetime.fromtimestamp(started, UTC).isoformat(),
        "correct": correct,
        # Format compliance, reported apart from accuracy: a model that found the right
        # answer and wrote it in the wrong shape has a formatting problem, not a knowledge
        # one, and folding the two together would quietly deflate a weaker model's score.
        "answer_parsed": raw_answer is not None,
        "expert_tool": question.expert_tool,
        "stratum": question.stratum,
        "tool_match": None,  # filled below, once the transcript has been classified
        "partial_credit": round(partial, 4),
        "parsed_answer": parsed,
        "raw_answer": raw_answer,
        "wall_s": round(elapsed, 3),
        "agent_duration_ms": result.get("duration_ms"),
        "api_duration_ms": result.get("duration_api_ms"),
        "num_turns": result.get("num_turns"),
        "cost_reported_usd": result.get("total_cost_usd"),
        **costs(usage, prices_for(model)),
        "usage_raw": usage,
        "is_error": result.get("is_error"),
        "api_error_status": result.get("api_error_status"),
        "stop_reason": result.get("stop_reason"),
        "harness_error": harness_error,
        "session_id": result.get("session_id"),
        "transcript": str(transcript_path.relative_to(cfg.transcripts)),
        "result_text": result_text[-3000:],
        **checks,
    }
    record["tool_match"] = record["tool_choice"] == question.expert_tool
    shutil.rmtree(workdir, ignore_errors=True)
    return record


def assert_workroot_is_neutral(workroot: Path) -> None:
    """The working root must not contain the tool's name, anywhere in its absolute path.

    The agent's cwd is echoed into its system prompt, so a single `readb` in the path primes
    every readb-free arm with the word it is supposed not to know — and the leak check then
    flags every one of their runs. This was a comment in this file for a whole version, and
    a comment does not stop a run: a session scratchpad named after the repository ate the
    first twelve runs of the v2 matrix before it was caught.
    """
    resolved = str(workroot.resolve()).lower()
    if "readb" in resolved:
        raise SystemExit(
            f"refusing to run: the working root {resolved} contains the tool's name, which "
            f"is echoed into every arm's system prompt through its cwd. Pass a --workroot "
            f"outside any path carrying it (the default, /tmp/kbbench, is one)."
        )


def preflight(cfg, corpora: dict, truths: dict) -> dict:
    """Verify the arms are what they claim before spending money on a matrix.

    Arm C exists to measure a skill; if the plugin does not load, every number it
    produces is a measurement of arm A wearing arm C's label.
    """
    probe = "List the names of every skill available to you, comma separated. If none, reply NONE."
    seen = {}
    for name in ("baseline", "readb-skill"):
        arm = ARMS[name]
        out = subprocess.run(
            [
                CLAUDE_BIN,
                "-p",
                probe,
                "--model",
                cfg.models.split(",")[0],
                "--output-format",
                "json",
                "--no-session-persistence",
                "--strict-mcp-config",
                *arm.extra_args,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        text = json.loads(out.stdout).get("result", "") if out.stdout.strip() else ""
        seen[name] = "readb" in text.lower()
    if seen.get("baseline"):
        raise SystemExit("preflight failed: the baseline arm can see a readb skill")
    if not seen.get("readb-skill"):
        raise SystemExit("preflight failed: arm readb-skill did not load the readb skill")

    # Skill visibility was never the thing that broke. What broke was an arm that could not
    # run the command its own documentation leads with, so probe each arm's constructed PATH
    # for every binary that arm is supposed to reach.
    for name, arm in ARMS.items():
        if name not in cfg.arms.split(","):
            continue
        path = ":".join(
            ([str(cfg.readb_bin.parent)] if arm.readb_on_path else [])
            + ([cfg.uv_shim] if arm.uv_on_path else [])
            + [cfg.tools_shim, BASE_PATH]
        )
        wanted = ([("readb", ["readb", "--version"])] if arm.readb_on_path else []) + (
            [("uv", ["uvx", "--version"])] if arm.uv_on_path else []
        )
        for binary, argv in wanted:
            probe = subprocess.run(
                argv, env={"PATH": path, "HOME": os.environ["HOME"]}, capture_output=True
            )
            if probe.returncode != 0:
                raise SystemExit(
                    f"preflight failed: arm {name} cannot execute {binary} on its PATH "
                    f"({path}) — this is the defect that retracted 36 runs once already"
                )
        seen[f"{name}:binaries"] = [b for b, _ in wanted] or ["none required"]

    if "shell-coached" in cfg.arms.split(","):
        seen["recipes"] = recipe_preflight(cfg, corpora, truths)
    return seen


def recipe_preflight(cfg, corpora: dict, truths: dict) -> dict:
    """Run every coached command against the corpus the arm will actually see.

    Two failures are checked, not one. A command that cannot run is the defect that
    retracted 36 runs. A command that runs and quietly returns *less* than the truth is
    worse: it makes the competitor arm a straw man, and a straw man in the competitor arm
    is worth more to readb's published ratio than any real effect could be.
    """
    env = {"PATH": f"{cfg.tools_shim}:{BASE_PATH}", "HOME": os.environ["HOME"]}
    checked = {}
    for name, directory in corpora.items():
        recipe = RECIPES.get(name)
        if recipe is None:
            raise SystemExit(f"preflight failed: no coached recipe for corpus {name!r}")
        # The arm sees the bundle mounted at `corpus/`, so the commands are run from a
        # parent directory holding exactly that name.
        stage = Path(cfg.workroot) / f".recipe-{name}"
        shutil.rmtree(stage, ignore_errors=True)
        stage.mkdir(parents=True)
        (stage / "corpus").symlink_to(directory.resolve(), target_is_directory=True)
        placeholders = recipe_placeholders(truths[name])
        for _, template in recipe:
            command = template.format(**placeholders)
            done = subprocess.run(
                command, shell=True, cwd=stage, env=env, capture_output=True, text=True
            )
            if done.returncode != 0 or not done.stdout.strip():
                raise SystemExit(
                    f"preflight failed: coached command for {name!r} produced nothing — "
                    f"{command}\n{done.stderr[:400]}"
                )
        # The listing command is the one whose answer is known, so it is the one checked.
        expected = _recipe_expectation(name, truths[name])
        if expected is not None:
            command = recipe[0][1].format(**placeholders)
            done = subprocess.run(
                command, shell=True, cwd=stage, env=env, capture_output=True, text=True
            )
            found = len([line for line in done.stdout.splitlines() if line.strip()])
            if found != expected:
                raise SystemExit(
                    f"preflight failed: the coached listing for {name!r} finds {found} "
                    f"files where the ground truth has {expected} — the recipe under-matches "
                    f"this corpus, which would make the competitor arm a straw man\n{command}"
                )
            checked[name] = f"{found} files, matches ground truth"
        else:
            checked[name] = "runs, no ground truth to check against"
        shutil.rmtree(stage, ignore_errors=True)
    return checked


def _recipe_expectation(name: str, truth: dict) -> int | None:
    """How many files the first coached command must find, where that is knowable."""
    if name in ("ops", "ops-tidy") and "q15" in truth:
        return len(truth["q15"]["answer"])  # every tier-1 service
    if name == "backlog" and "counts" in truth:
        return truth["counts"]["Draft"]  # every Draft task lives in `tasks/`
    return None


def sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def git_sha() -> str:
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    return out.stdout.strip() or "unknown"


def done_cells(results: Path) -> set[tuple[str, str, str, int]]:
    if not results.exists():
        return set()
    return {
        (rec["arm"], rec["question"], rec.get("model", ""), rec["repeat"])
        for rec in (json.loads(line) for line in results.read_text().splitlines() if line.strip())
        if not rec.get("retracted")
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--corpus",
        action="append",
        required=True,
        metavar="NAME=DIR,TRUTH",
        help=(
            "register one corpus, repeatable. v1 hard-coded two; v2 has four, and a "
            "registry keeps adding a fifth from touching the harness."
        ),
    )
    ap.add_argument(
        "--corpus-map",
        action="append",
        default=[],
        dest="corpus_map_specs",
        metavar="FROM=TO",
        help=(
            "redirect every question declaring corpus FROM to corpus TO. This is how the "
            "messy/tidy sweep runs the same pre-registered questions against both "
            "renderings without a second copy of the battery."
        ),
    )
    ap.add_argument("--readb-bin", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path)
    # The working root must sit outside any path containing the tool's name: the agent's
    # cwd is echoed into its system prompt, and a directory named after readb primes the
    # baseline arm with the very word the arm is supposed not to know.
    ap.add_argument("--workroot", type=Path, default=Path("/tmp/kbbench"))
    ap.add_argument("--transcripts", type=Path)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument(
        "--models",
        default="claude-sonnet-5",
        help="comma-separated; model is a factor in the matrix, recorded per run",
    )
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--autocompact", type=int, default=1000000)
    ap.add_argument(
        "--budget", type=float, default=3.0, help="per-run runaway guard, not a live constraint"
    )
    ap.add_argument("--total-budget", type=float, default=80.0)
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument(
        "--questions",
        default=",".join(q.id for q in QUESTIONS),
        help="default is the pre-registered battery; post-hoc probes must be named explicitly",
    )
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument(
        "--floor",
        action="store_true",
        help="replace every question with a trivial prompt, to measure fixed harness overhead",
    )
    cfg = ap.parse_args()

    cfg.transcripts = cfg.transcripts or cfg.results.parent / "transcripts"
    cfg.transcripts.mkdir(parents=True, exist_ok=True)
    cfg.results.parent.mkdir(parents=True, exist_ok=True)
    cfg.workroot.mkdir(parents=True, exist_ok=True)
    # Checked before the shims are built, and outside `preflight`, so `--skip-preflight`
    # cannot skip past the one failure that silently invalidates a whole batch.
    assert_workroot_is_neutral(cfg.workroot)
    cfg.tools_shim = shim(cfg.workroot, "tools", SHARED_TOOLS)
    cfg.uv_shim = shim(cfg.workroot, "uv", UV_TOOLS)

    corpora, truths = {}, {}
    for spec in cfg.corpus:
        name, _, rest = spec.partition("=")
        directory, _, truth_path = rest.partition(",")
        if not (name and directory and truth_path):
            raise SystemExit(f"--corpus wants NAME=DIR,TRUTH, got {spec!r}")
        corpora[name] = Path(directory)
        truths[name] = json.loads(Path(truth_path).read_text())

    cfg.corpus_map = {}
    for spec in cfg.corpus_map_specs:
        source, _, target = spec.partition("=")
        if not (source and target):
            raise SystemExit(f"--corpus-map wants FROM=TO, got {spec!r}")
        cfg.corpus_map[source] = target

    questions_wanted = [q for q in ALL_QUESTIONS if q.id in cfg.questions.split(",")]
    for question in questions_wanted:
        resolved = cfg.corpus_map.get(question.corpus, question.corpus)
        if resolved not in corpora:
            raise SystemExit(
                f"question {question.id} needs corpus {resolved!r}, which no --corpus registered"
            )

    if not cfg.skip_preflight:
        print("preflight: checking arm isolation...", flush=True)
        print(f"preflight ok: {preflight(cfg, corpora, truths)}", flush=True)

    manifest = {
        "started_utc": datetime.now(UTC).isoformat(),
        "git_sha": git_sha(),
        "claude_version": subprocess.run(
            [CLAUDE_BIN, "--version"], capture_output=True, text=True
        ).stdout.strip(),
        "readb_version": subprocess.run(
            [str(cfg.readb_bin), "--version"], capture_output=True, text=True
        ).stdout.strip(),
        "readb_bin": str(cfg.readb_bin),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "models": cfg.models,
        "effort": cfg.effort,
        "autocompact": cfg.autocompact,
        "per_run_budget_usd": cfg.budget,
        "prices_usd_per_mtok": {m: PRICES[m] for m in cfg.models.split(",")},
        "repeats": cfg.repeats,
        "arms": cfg.arms,
        "questions": cfg.questions,
        "corpus_dirs": {k: str(v) for k, v in corpora.items()},
        "corpus_map": cfg.corpus_map,
        "corpus_generation": {k: truths[k].get("_meta") for k in truths},
        "corpus_sha256": {k: sha256_tree(v) for k, v in corpora.items()},
        "corpus_concepts": {k: sum(1 for _ in v.rglob("*.md")) - 1 for k, v in corpora.items()},
        # Frozen before the first measured run; a change after one retracts the arm.
        "nudge": NUDGE,
        "strata": {q.id: q.stratum for q in questions_wanted},
        "expert_tools": {q.id: q.expert_tool for q in questions_wanted},
        # The variable that invalidated the first arm-C batch: the shipped skill's leading
        # example is `uvx readb`, and the arm had no uv.
        "arm_paths": {
            name: ":".join(
                ([str(cfg.readb_bin.parent)] if arm.readb_on_path else [])
                + ([cfg.uv_shim] if arm.uv_on_path else [])
                + [cfg.tools_shim, BASE_PATH]
            )
            for name, arm in ARMS.items()
            if name in cfg.arms.split(",")
        },
        "floor_mode": cfg.floor,
    }
    # One manifest per batch, named after its results file: a shared filename means the
    # last batch silently overwrites the record of every earlier one.
    (cfg.results.parent / f"manifest-{cfg.results.stem}.json").write_text(
        scrub(json.dumps(manifest, indent=2)) + "\n"
    )
    print(json.dumps(manifest, indent=2), flush=True)

    arms = [ARMS[a] for a in cfg.arms.split(",")]
    questions = questions_wanted
    already = done_cells(cfg.results)

    # Interleave: arms round-robin inside each repeat and the question order rotates per
    # repeat, so no arm systematically inherits a warm cache or a quiet machine.
    plan = []
    models = cfg.models.split(",")
    for repeat in range(1, cfg.repeats + 1):
        offset = (repeat - 1) % len(questions)
        for question in questions[offset:] + questions[:offset]:
            for model in models:
                for arm in arms:
                    if (arm.name, question.id, model, repeat) not in already:
                        plan.append((arm, question, repeat, model))

    print(f"{len(plan)} runs to go ({len(already)} already recorded)", flush=True)
    spent = 0.0
    for i, (arm, question, repeat, model) in enumerate(plan, 1):
        corpus_name = cfg.corpus_map.get(question.corpus, question.corpus)
        record = run_one(
            arm,
            question,
            repeat,
            cfg,
            truths[corpus_name],
            corpora[corpus_name],
            model,
            corpus_name,
        )
        spent += record.get("cost_reported_usd") or 0.0
        with cfg.results.open("a") as fh:
            fh.write(json.dumps(record) + "\n")

        flags = []
        if record["harness_error"]:
            flags.append(f"ERROR {record['harness_error']}")
        if record["leak_baseline_readb"]:
            flags.append("LEAK")
        if record["permission_denials"]:
            flags.append("DENIED")
        if not record["supported"]:
            flags.append("UNSUPPORTED")
        if arm.expects_skill and not record["skill_readb_used"]:
            flags.append("skill-not-fired")
        print(
            f"[{i}/{len(plan)}] {record['model'].replace('claude-', ''):12s} "
            f"{arm.name:12s} {question.id:5s} r{repeat} "
            f"ok={record['correct']!s:5s} f1={record['partial_credit']:.2f} "
            f"{record['wall_s']:6.1f}s ingested={record['new_tokens_ingested']:>7,} "
            f"turns={record.get('num_turns')} readb={record['readb_invocations']} "
            f"${record.get('cost_reported_usd') or 0:.3f} (run ${spent:.2f}) " + " ".join(flags),
            flush=True,
        )
        if spent > cfg.total_budget:
            print(f"stopping: total budget ${cfg.total_budget} exceeded", flush=True)
            break


if __name__ == "__main__":
    main()
