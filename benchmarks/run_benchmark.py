"""Run the A/B/C benchmark: one agent, one battery, three arms.

Every run is a headless Claude Code invocation in a fresh working directory holding its
own copy of the corpus. Arms differ only in what the runtime makes available; the
question text is byte-identical across arms.

    python benchmarks/run_benchmark.py --corpus /tmp/corpus600 \
        --truth /tmp/corpus600_ground_truth.json --readb-bin /tmp/benchvenv/bin/readb \
        --results benchmarks/results/run.jsonl --repeats 3

Results are appended as JSONL and the run is resumable: a (arm, question, repeat) cell
already present in the results file is skipped.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from battery import QUESTIONS, extract_answer, render, score  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# A deliberately minimal PATH: the user's own ~/.local/bin carries a globally installed
# readb, which would leak the treatment into the baseline arm.
BASE_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"

PREAMBLE_BASELINE = (
    "You are working in a directory that contains a knowledge base. Standard shell tools "
    "are available to you.\n\n"
)

PREAMBLE_READB = (
    "You are working in a directory that contains a knowledge base. Standard shell tools "
    "are available to you, and so is `readb`, a command that runs read-only SQL over a "
    "directory of markdown files with YAML frontmatter: `readb query \"<sql>\" --bundle "
    "corpus` runs a query, and `readb schema --bundle corpus` lists the tables and "
    "columns it exposes.\n\n"
)

TASK_INTRO = (
    "The directory `corpus/` holds a knowledge base: markdown files with YAML "
    "frontmatter, one concept per file, organised into subdirectories by kind.\n\n"
)


@dataclass(frozen=True)
class Arm:
    name: str
    preamble: str
    readb_on_path: bool
    extra_args: tuple[str, ...]


# `--setting-sources ""` strips user, project and local settings — no personal CLAUDE.md,
# skill, plugin, hook or MCP server reaches any arm; only Claude Code's own built-in skills
# remain, identically in all three. `--plugin-dir` then adds exactly one skill (`readb`) to
# arm C, which is the single variable that arm exists to test. `--safe-mode` cannot be used
# here: it suppresses `--plugin-dir`, and arm C would silently collapse onto arm A.
ISOLATION = ("--setting-sources", "")

ARMS = {
    "baseline": Arm("baseline", PREAMBLE_BASELINE, readb_on_path=False, extra_args=ISOLATION),
    "readb-bare": Arm("readb-bare", PREAMBLE_READB, readb_on_path=True, extra_args=ISOLATION),
    "readb-skill": Arm(
        "readb-skill",
        PREAMBLE_BASELINE,
        readb_on_path=True,
        extra_args=(*ISOLATION, "--plugin-dir", str(REPO_ROOT)),
    ),
}


def build_prompt(arm: Arm, question, truth: dict) -> str:
    return arm.preamble + TASK_INTRO + render(question, truth)


def run_one(
    arm: Arm,
    question,
    repeat: int,
    corpus: Path,
    truth: dict,
    readb_bin: Path,
    workroot: Path,
    model: str,
    effort: str,
    budget: float,
    timeout: int,
) -> dict:
    workdir = workroot / f"{arm.name}-{question.id}-r{repeat}"
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    # A per-run copy: a shared corpus could be mutated by one run and read by the next,
    # and a symlink would hide the tree from tools that do not follow links.
    shutil.copytree(corpus, workdir / "corpus")

    env = {
        "HOME": os.environ["HOME"],
        "USER": os.environ.get("USER", ""),
        "TERM": "dumb",
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "PATH": f"{readb_bin.parent}:{BASE_PATH}" if arm.readb_on_path else BASE_PATH,
    }
    for passthrough in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "SHELL", "TMPDIR"):
        if passthrough in os.environ:
            env[passthrough] = os.environ[passthrough]

    prompt = build_prompt(arm, question, truth)
    cmd = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--effort",
        effort,
        "--output-format",
        "json",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--permission-mode",
        "bypassPermissions",
        "--disallowedTools",
        "WebSearch",
        "WebFetch",
        "--max-budget-usd",
        str(budget),
        *arm.extra_args,
    ]

    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=workdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - started
        payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
        harness_error = None if payload else f"no json (rc={proc.returncode}): {proc.stderr[:400]}"
    except subprocess.TimeoutExpired:
        elapsed = time.time() - started
        payload = {}
        harness_error = f"timeout after {timeout}s"
    except json.JSONDecodeError as exc:
        elapsed = time.time() - started
        payload = {}
        harness_error = f"unparseable json: {exc}"

    result_text = payload.get("result", "")
    raw_answer = extract_answer(result_text)
    correct, parsed = score(question, raw_answer, truth) if payload else (False, None)

    usage = payload.get("usage", {}) or {}
    model_usage = payload.get("modelUsage", {}) or {}
    main = model_usage.get(model, {})

    record = {
        "arm": arm.name,
        "question": question.id,
        "shape": question.shape,
        "repeat": repeat,
        "model": model,
        "effort": effort,
        "correct": correct,
        "parsed_answer": parsed,
        "raw_answer": raw_answer,
        "wall_s": round(elapsed, 3),
        "agent_duration_ms": payload.get("duration_ms"),
        "num_turns": payload.get("num_turns"),
        "cost_usd": payload.get("total_cost_usd"),
        "main_model_cost_usd": main.get("costUSD"),
        "input_tokens": usage.get("input_tokens"),
        "cache_creation_tokens": usage.get("cache_creation_input_tokens"),
        "cache_read_tokens": usage.get("cache_read_input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "main_input_tokens": main.get("inputTokens"),
        "main_cache_creation_tokens": main.get("cacheCreationInputTokens"),
        "main_cache_read_tokens": main.get("cacheReadInputTokens"),
        "main_output_tokens": main.get("outputTokens"),
        "is_error": payload.get("is_error"),
        "api_error_status": payload.get("api_error_status"),
        "stop_reason": payload.get("stop_reason"),
        "permission_denials": payload.get("permission_denials"),
        "harness_error": harness_error,
        "session_id": payload.get("session_id"),
        "result_text": result_text[-4000:],
    }
    shutil.rmtree(workdir, ignore_errors=True)
    return record


def done_cells(results: Path) -> set[tuple[str, str, int]]:
    if not results.exists():
        return set()
    seen = set()
    for line in results.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        seen.add((rec["arm"], rec["question"], rec["repeat"]))
    return seen


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--truth", required=True, type=Path)
    ap.add_argument("--readb-bin", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--workroot", type=Path, default=Path("/tmp/readb-bench-work"))
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--budget", type=float, default=1.5)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--questions", default=",".join(q.id for q in QUESTIONS))
    args = ap.parse_args()

    truth = json.loads(args.truth.read_text())
    arms = [ARMS[a] for a in args.arms.split(",")]
    questions = [q for q in QUESTIONS if q.id in args.questions.split(",")]
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.workroot.mkdir(parents=True, exist_ok=True)

    already = done_cells(args.results)

    # Interleave: arms round-robin inside each repeat, and the question order rotates per
    # repeat, so no arm systematically inherits a warm prompt cache or a quiet machine.
    plan: list[tuple[Arm, object, int]] = []
    for repeat in range(1, args.repeats + 1):
        rotated = questions[(repeat - 1) % len(questions) :] + questions[: (repeat - 1) % len(questions)]
        for question in rotated:
            for arm in arms:
                if (arm.name, question.id, repeat) not in already:
                    plan.append((arm, question, repeat))

    print(f"{len(plan)} runs to go ({len(already)} already recorded)", flush=True)
    spent = 0.0
    for i, (arm, question, repeat) in enumerate(plan, 1):
        record = run_one(
            arm,
            question,
            repeat,
            args.corpus,
            truth,
            args.readb_bin,
            args.workroot,
            args.model,
            args.effort,
            args.budget,
            args.timeout,
        )
        spent += record.get("cost_usd") or 0.0
        with args.results.open("a") as fh:
            fh.write(json.dumps(record) + "\n")
        print(
            f"[{i}/{len(plan)}] {arm.name:12s} {question.id} r{repeat} "
            f"correct={record['correct']!s:5s} {record['wall_s']:6.1f}s "
            f"${record.get('cost_usd') or 0:.3f} turns={record.get('num_turns')} "
            f"(running ${spent:.2f})"
            + (f" ERROR: {record['harness_error']}" if record["harness_error"] else ""),
            flush=True,
        )


if __name__ == "__main__":
    main()
