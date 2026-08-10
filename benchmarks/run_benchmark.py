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
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from battery import QUESTIONS, extract_answer, render, score  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# A deliberately minimal PATH: the machine may carry a globally installed readb (and uv,
# which could fetch one), either of which would leak the treatment into the baseline arm.
# The runtime binary is therefore resolved from the parent environment and invoked by
# absolute path rather than found on the child's PATH.
BASE_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
CLAUDE_BIN = shutil.which("claude") or "claude"

# USD per million tokens. Committed with the results so the published cost can be
# recomputed in six months, when the live price list will have moved on.
PRICES = {
    "input": 3.00,
    "output": 15.00,
    "cache_read": 0.30,
    "cache_write_5m": 3.75,
    "cache_write_1h": 6.00,
}

PREAMBLE_BASELINE = (
    "You are working in a directory that holds a knowledge base. The standard shell "
    "tools are available to you — you can read files, list directories, and search "
    "their contents with grep.\n\n"
)

PREAMBLE_READB = (
    "You are working in a directory that holds a knowledge base. The standard shell "
    "tools are available to you — you can read files, list directories, and search "
    "their contents with grep. So is `readb`, a command that runs read-only SQL over a "
    'directory of markdown files with YAML frontmatter: `readb query "<sql>" --bundle '
    "corpus` runs a query, and `readb schema --bundle corpus` lists the tables and "
    "columns it exposes.\n\n"
)

# The honest competitor to readb is not an uncoached agent — it is a shell pipeline. Without
# this arm, arm B minus arm A measures "given a worked recipe" against "given none", and
# would be read as "readb against file tools".
PREAMBLE_SHELL = (
    "You are working in a directory that holds a knowledge base. The standard shell "
    "tools are available to you — you can read files, list directories, and search "
    "their contents with grep. For example, `grep -l '^tier: 1' corpus/services/*.md` "
    "lists the files carrying a given frontmatter field, `grep -h '^status:' "
    "corpus/services/*.md | sort | uniq -c` counts one field's values across a "
    "directory, and `awk '/^---$/{n++; next} n==1' <file>` prints a single file's "
    "frontmatter block.\n\n"
)

TASK_INTRO = (
    "The directory `corpus/` holds a knowledge base: markdown files with YAML "
    "frontmatter, one concept per file, organised into subdirectories by kind. "
    "`corpus/index.md` is a listing of the knowledge base, not a concept.\n\n"
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


ARMS = {
    "baseline": Arm("baseline", PREAMBLE_BASELINE, False, ISOLATION, False),
    "shell-coached": Arm("shell-coached", PREAMBLE_SHELL, False, ISOLATION, False),
    "readb-bare": Arm("readb-bare", PREAMBLE_READB, True, ISOLATION, False),
    "readb-skill": Arm(
        "readb-skill",
        PREAMBLE_BASELINE,
        True,
        (*ISOLATION, "--plugin-dir", str(REPO_ROOT)),
        True,
    ),
}


# --- transcript analysis ------------------------------------------------------


def parse_stream(lines: list[str]) -> tuple[dict, list[dict]]:
    """Split a stream-json transcript into its final result and its tool calls."""
    result: dict = {}
    tools: list[dict] = []
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
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tools.append({"name": block.get("name"), "input": block.get("input") or {}})
    return result, tools


def integrity(arm: Arm, tools: list[dict], result: dict, transcript: str) -> dict:
    """Facts about a run that decide whether its numbers may be used at all."""
    commands = " ".join(str(t["input"].get("command", "")) for t in tools if t["name"] == "Bash")
    readb_used = "readb" in commands
    skill_used = any(t["name"] in ("Skill", "SlashCommand") for t in tools)
    skill_readb = any(
        t["name"] in ("Skill", "SlashCommand") and "readb" in json.dumps(t["input"]).lower()
        for t in tools
    )
    return {
        "tool_calls": len(tools),
        "tool_names": sorted({t["name"] for t in tools if t.get("name")}),
        "readb_invocations": commands.count("readb"),
        "readb_used": readb_used,
        "skill_used": skill_used,
        "skill_readb_used": skill_readb,
        "supported": len(tools) > 0,
        # The baseline must never touch readb: if it did, the arm is contaminated.
        "leak_baseline_readb": (not arm.readb_on_path) and ("readb" in transcript.lower()),
        "compacted": '"compact' in transcript or "context low" in transcript.lower(),
        "permission_denials": result.get("permission_denials") or [],
    }


def costs(usage: dict) -> dict:
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
        w1h = usage.get("cache_creation_input_tokens") or 0

    billed = (
        inp * PRICES["input"]
        + out * PRICES["output"]
        + read * PRICES["cache_read"]
        + w1h * PRICES["cache_write_1h"]
        + w5m * PRICES["cache_write_5m"]
    ) / 1e6
    neutral = ((inp + read + w1h + w5m) * PRICES["input"] + out * PRICES["output"]) / 1e6
    return {
        "cost_billed_usd": round(billed, 6),
        "cost_cache_neutral_usd": round(neutral, 6),
        "new_tokens_ingested": inp + w1h + w5m,
        "cumulative_prompt_tokens": inp + read + w1h + w5m,
        "output_tokens": out,
        "cache_read_tokens": read,
    }


# --- one run ------------------------------------------------------------------


def run_one(arm: Arm, question, repeat: int, cfg, truth: dict, corpus: Path) -> dict:
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
        "PATH": f"{cfg.readb_bin.parent}:{BASE_PATH}" if arm.readb_on_path else BASE_PATH,
    }
    for key in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "SHELL"):
        if key in os.environ:
            env[key] = os.environ[key]

    prompt = arm.preamble + TASK_INTRO + render(question, truth)
    cmd = [
        CLAUDE_BIN,
        "-p",
        prompt,
        "--model",
        cfg.model,
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
    result, tools = parse_stream(lines)

    transcript_path = cfg.transcripts / f"{arm.name}-{question.id}-r{repeat}.jsonl"
    transcript_path.write_text(stdout)

    result_text = result.get("result", "")
    raw_answer = extract_answer(result_text)
    correct, partial, parsed = score(question, raw_answer, truth)
    usage = result.get("usage", {}) or {}
    checks = integrity(arm, tools, result, stdout)

    # An answer produced without a single tool call was not derived from the corpus.
    if not checks["supported"]:
        correct, partial = False, 0.0

    record = {
        "arm": arm.name,
        "question": question.id,
        "shape": question.shape,
        "favours": question.favours,
        "repeat": repeat,
        "corpus": question.corpus,
        "model": cfg.model,
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
        "partial_credit": round(partial, 4),
        "parsed_answer": parsed,
        "raw_answer": raw_answer,
        "wall_s": round(elapsed, 3),
        "agent_duration_ms": result.get("duration_ms"),
        "api_duration_ms": result.get("duration_api_ms"),
        "num_turns": result.get("num_turns"),
        "cost_reported_usd": result.get("total_cost_usd"),
        **costs(usage),
        "usage_raw": usage,
        "is_error": result.get("is_error"),
        "api_error_status": result.get("api_error_status"),
        "stop_reason": result.get("stop_reason"),
        "harness_error": harness_error,
        "session_id": result.get("session_id"),
        "transcript": str(transcript_path.name),
        "result_text": result_text[-3000:],
        **checks,
    }
    shutil.rmtree(workdir, ignore_errors=True)
    return record


def preflight(cfg) -> dict:
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
                cfg.model,
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
    return seen


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


def done_cells(results: Path) -> set[tuple[str, str, int]]:
    if not results.exists():
        return set()
    return {
        (rec["arm"], rec["question"], rec["repeat"])
        for rec in (json.loads(line) for line in results.read_text().splitlines() if line.strip())
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus-clean", required=True, type=Path)
    ap.add_argument("--corpus-malformed", required=True, type=Path)
    ap.add_argument("--truth-clean", required=True, type=Path)
    ap.add_argument("--truth-malformed", required=True, type=Path)
    ap.add_argument("--readb-bin", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path)
    # The working root must sit outside any path containing the tool's name: the agent's
    # cwd is echoed into its system prompt, and a directory named after readb primes the
    # baseline arm with the very word the arm is supposed not to know.
    ap.add_argument("--workroot", type=Path, default=Path("/tmp/kbbench"))
    ap.add_argument("--transcripts", type=Path)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--autocompact", type=int, default=1000000)
    ap.add_argument(
        "--budget", type=float, default=3.0, help="per-run runaway guard, not a live constraint"
    )
    ap.add_argument("--total-budget", type=float, default=80.0)
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--questions", default=",".join(q.id for q in QUESTIONS))
    ap.add_argument("--skip-preflight", action="store_true")
    cfg = ap.parse_args()

    cfg.transcripts = cfg.transcripts or cfg.results.parent / "transcripts"
    cfg.transcripts.mkdir(parents=True, exist_ok=True)
    cfg.results.parent.mkdir(parents=True, exist_ok=True)
    cfg.workroot.mkdir(parents=True, exist_ok=True)

    truths = {
        "clean": json.loads(cfg.truth_clean.read_text()),
        "malformed": json.loads(cfg.truth_malformed.read_text()),
    }
    corpora = {"clean": cfg.corpus_clean, "malformed": cfg.corpus_malformed}

    if not cfg.skip_preflight:
        print("preflight: checking arm isolation...", flush=True)
        print(f"preflight ok: {preflight(cfg)}", flush=True)

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
        "model": cfg.model,
        "effort": cfg.effort,
        "autocompact": cfg.autocompact,
        "per_run_budget_usd": cfg.budget,
        "prices_usd_per_mtok": PRICES,
        "repeats": cfg.repeats,
        "corpus_sha256": {k: sha256_tree(v) for k, v in corpora.items()},
        "corpus_concepts": {k: sum(1 for _ in v.rglob("*.md")) - 1 for k, v in corpora.items()},
    }
    (cfg.results.parent / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)

    arms = [ARMS[a] for a in cfg.arms.split(",")]
    questions = [q for q in QUESTIONS if q.id in cfg.questions.split(",")]
    already = done_cells(cfg.results)

    # Interleave: arms round-robin inside each repeat and the question order rotates per
    # repeat, so no arm systematically inherits a warm cache or a quiet machine.
    plan = []
    for repeat in range(1, cfg.repeats + 1):
        offset = (repeat - 1) % len(questions)
        for question in questions[offset:] + questions[:offset]:
            for arm in arms:
                if (arm.name, question.id, repeat) not in already:
                    plan.append((arm, question, repeat))

    print(f"{len(plan)} runs to go ({len(already)} already recorded)", flush=True)
    spent = 0.0
    for i, (arm, question, repeat) in enumerate(plan, 1):
        record = run_one(
            arm, question, repeat, cfg, truths[question.corpus], corpora[question.corpus]
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
            f"[{i}/{len(plan)}] {arm.name:12s} {question.id:4s} r{repeat} "
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
