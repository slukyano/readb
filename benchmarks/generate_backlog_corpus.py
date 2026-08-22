"""Generate a task-tracker-shaped OKF bundle plus its ground truth.

The second corpus family. v1 measured one bundle shape — a wide, flat, four-type reference
knowledge base — and every question it asked was answerable from frontmatter alone. That
left two things unmeasured: a bundle whose concepts point at each other and change state,
and a question that needs a concept's *body* alongside its frontmatter.

The domain is a generic engineering backlog for **Lumenstore**, an invented self-hosted
photo-library server. Nothing here is drawn from any real project's backlog, and the
product does not exist; it is one plausible OKF domain among many, chosen because task
trackers are the commonest place a directory of frontmatter documents actually arises.

    python benchmarks/generate_backlog_corpus.py --out /tmp/backlog \
        --truth /tmp/truth_backlog.json --tasks 170 --sprints 22 --seed 24

Ground truth is computed from the generated records in plain Python and then re-derived
from the written files by an independent PyYAML read-back — never by querying readb,
which would make the benchmark's correctness check circular.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generate_corpus import _frontmatter  # noqa: E402

STATUSES = ["Draft", "Designed", "Done", "Dropped"]
# Weighted so the archive is the larger half, as a backlog of any age is.
STATUS_WEIGHTS = [0.32, 0.14, 0.44, 0.10]
PRIORITIES = ["low", "medium", "high"]
TAG_POOL = [
    "ingest",
    "thumbnails",
    "search",
    "storage",
    "sync",
    "ui",
    "api",
    "metadata",
    "performance",
    "packaging",
]

# The `## Design` section of every Designed/Done task names one of these. Q b2 asks which,
# so the answer is an extraction from the body, checkable without a judge.
APPROACHES = [
    "sqlite",
    "worker-queue",
    "filesystem-cache",
    "content-hash",
    "thumbnail-pyramid",
    "sidecar-index",
]
# The `## Outcome` section of every Dropped task names one of these.
DROP_REASONS = [
    "duplicate",
    "obsolete",
    "out-of-scope",
    "upstream-fixed",
    "too-costly",
]

# Q b4 asks which tasks mentioning one feature are still open. The phrase is planted in
# bodies across every status, so the frontmatter filter and the body search are both
# needed and neither alone answers it.
FEATURE_PHRASE = "face grouping"

VERBS = ["Add", "Fix", "Speed up", "Rework", "Harden", "Document", "Simplify", "Extend"]
OBJECTS = [
    "the import scanner",
    "album ordering",
    "the thumbnail cache",
    "EXIF extraction",
    "the duplicate detector",
    "library sync",
    "the media server handshake",
    "the tag editor",
    "sidecar writes",
    "the search index",
    "album sharing links",
    "the storage migration",
    "RAW decoding",
    "the mobile upload path",
    "backup verification",
]

PROBLEM_SENTENCES = [
    "Importing a large library stalls once the scanner reaches directories with mixed media.",
    "Thumbnails are regenerated on every start, which makes the first page load unusable.",
    "The index falls behind whenever two clients write metadata at the same time.",
    "Sidecar files are rewritten in full, so a single tag edit rewrites megabytes.",
    "Album ordering is derived at request time and does not survive a restart.",
    "Duplicate detection compares file sizes only, so re-encoded copies slip through.",
    "The sync protocol retries from the beginning after any interruption.",
    "Search results are ordered by insertion, which buries the obvious match.",
    "RAW files are decoded twice, once for the preview and once for the histogram.",
    "Backups report success before the manifest has been flushed.",
]

DESIGN_SENTENCES = [
    "State is kept out of the request path so a restart cannot lose it.",
    "The work is idempotent, so a partial run can simply be repeated.",
    "Nothing is written until the whole batch verifies.",
    "The change is additive; existing libraries keep working untouched.",
    "One writer owns the index, and readers never block on it.",
    "Failure is reported per item rather than per batch.",
]

OUTCOME_SENTENCES = [
    "Measured on a library of two hundred thousand items before and after.",
    "The regression suite gained a case for the interrupted path.",
    "No change to the on-disk format was needed.",
    "The slow path is now bounded by disk rather than by CPU.",
]

INDEX = """---
title: Lumenstore backlog
---

# Lumenstore backlog

Work items for Lumenstore, a self-hosted photo-library server.

- `tasks/` — items still open
- `archive/` — items closed, delivered or dropped
- `sprints/` — one record per batch of work
"""


@dataclass
class Doc:
    name: str
    subdir: str
    frontmatter: dict
    body: str


def _date(rng: random.Random, lo: int = 2024, hi: int = 2026) -> str:
    return f"{rng.randint(lo, hi):04d}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _numbers(count: int, rng: random.Random) -> list[int]:
    """Sparse task numbers.

    Real backlogs have holes — items renumbered, merged, or never written. The gaps are
    the point: counting the files gives one answer and the next free number gives another,
    so Q b7 cannot be answered by `ls | wc -l`.
    """
    numbers: list[int] = []
    current = 0
    for _ in range(count):
        current += rng.choice([1, 1, 1, 2, 2, 3, 5])
        numbers.append(current)
    return numbers


def generate(tasks: int, sprints: int, seed: int) -> tuple[list[Doc], dict]:
    rng = random.Random(seed)
    docs: list[Doc] = []

    records: list[dict] = []
    for number in _numbers(tasks, rng):
        title = f"{rng.choice(VERBS)} {rng.choice(OBJECTS)}"
        status = rng.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        records.append(
            {
                "number": number,
                "name": f"{number:03d}-{_slug(title)}",
                "title": title,
                "status": status,
                "priority": rng.choices(PRIORITIES, weights=[0.3, 0.5, 0.2], k=1)[0],
                "tags": sorted(rng.sample(TAG_POOL, rng.randint(1, 3))),
                "created": _date(rng),
                "approach": rng.choice(APPROACHES) if status != "Draft" else None,
                "reason": rng.choice(DROP_REASONS) if status == "Dropped" else None,
                "feature": rng.random() < 0.12,
                "blocked_by": [],
            }
        )

    # Blockers point backwards only, so the graph cannot contain a cycle and "unblocked"
    # is decidable by looking at each blocker's own status.
    by_name = {r["name"]: r for r in records}
    for index, record in enumerate(records):
        if record["status"] != "Draft" or index == 0 or rng.random() > 0.30:
            continue
        pool = [r["name"] for r in records[:index]]
        record["blocked_by"] = sorted(rng.sample(pool, min(len(pool), rng.randint(1, 2))))

    for record in records:
        frontmatter = {
            "type": "Task",
            "title": record["title"],
            "description": f"{record['title']} — {rng.choice(PROBLEM_SENTENCES)}",
            "status": record["status"],
            "priority": record["priority"],
            "tags": record["tags"],
            "created": record["created"],
        }
        if record["blocked_by"]:
            frontmatter["blocked_by"] = record["blocked_by"]
        docs.append(
            Doc(
                name=record["name"],
                subdir="tasks" if record["status"] in ("Draft", "Designed") else "archive",
                frontmatter=frontmatter,
                body=_task_body(record, rng),
            )
        )

    # --- sprints --------------------------------------------------------------
    sprint_records: list[dict] = []
    pool = [r["name"] for r in records]
    for i in range(sprints):
        # Exactly one sprint is unfinished: an active sprint is a singleton in any real
        # tracker, and Q b2 asks for "the" active one.
        status = "Implementing" if i == sprints - 1 else "Done"
        scope = sorted(rng.sample(pool, rng.randint(2, 5)))
        if status != "Done":
            # The active sprint carries at least one task with no design yet, so Q b2's
            # answer exercises the battery's `none` convention rather than avoiding it.
            drafts = [r["name"] for r in records if r["status"] == "Draft"]
            if drafts and not any(by_name[n]["status"] == "Draft" for n in scope):
                scope = sorted(set(scope) | {rng.choice(drafts)})
        sprint_records.append(
            {
                "name": f"sprint-{i + 1:03d}",
                "status": status,
                "branch": f"sprint/{i + 1:03d}",
                "tasks": scope,
                "created": _date(rng),
            }
        )
    for record in sprint_records:
        docs.append(
            Doc(
                name=record["name"],
                subdir="sprints",
                frontmatter={
                    "type": "Sprint",
                    "title": f"Sprint {record['name'].split('-')[1]}",
                    "status": record["status"],
                    "branch": record["branch"],
                    "tasks": record["tasks"],
                    "created": record["created"],
                },
                body=(
                    "## Scope\n\n"
                    + " ".join(rng.sample(DESIGN_SENTENCES, 2))
                    + "\n\n## Notes\n\n"
                    + rng.choice(OUTCOME_SENTENCES)
                    + "\n"
                ),
            )
        )

    return docs, ground_truth(records, sprint_records, by_name)


def _task_body(record: dict, rng: random.Random) -> str:
    parts = ["## Problem", "", rng.choice(PROBLEM_SENTENCES)]
    if record["feature"]:
        parts.append(f"The work overlaps {FEATURE_PHRASE}, which shares the same metadata path.")
    parts += ["", "## Design", ""]
    if record["approach"]:
        parts.append(f"Approach: {record['approach']}.")
        parts.append(rng.choice(DESIGN_SENTENCES))
    else:
        parts.append("Not designed yet.")
    if record["status"] in ("Done", "Dropped"):
        parts += ["", "## Outcome", ""]
        if record["reason"]:
            parts.append(f"Dropped: {record['reason']}.")
        else:
            parts.append("Delivered. " + rng.choice(OUTCOME_SENTENCES))
    return "\n".join(parts) + "\n"


def ground_truth(records: list[dict], sprints: list[dict], by_name: dict) -> dict:
    """Every answer, computed from the records themselves."""
    status_of = {r["name"]: r["status"] for r in records}

    # b1 — Draft, high priority, and every blocker Done. A dangling blocker counts as
    # blocking. Narrowed by priority on purpose: the unfiltered set runs to dozens of
    # names, which measures an agent's willingness to type a long list more than its
    # ability to resolve a dependency.
    b1 = sorted(
        r["name"]
        for r in records
        if r["status"] == "Draft"
        and r["priority"] == "high"
        and all(status_of.get(dep) == "Done" for dep in r["blocked_by"])
    )

    active = next(s for s in sprints if s["status"] != "Done")
    # b2 — the active sprint's scope, each task mapped to the approach its design names.
    # A task still in Draft has no design, which the `none` convention expresses.
    b2 = {
        name: (by_name[name]["approach"] or "none") for name in active["tasks"] if name in by_name
    }

    # b3 — a finished sprint, and which of its tasks actually shipped. Chosen as the last
    # Done sprint whose scope contains both delivered and undelivered work: a sprint where
    # everything shipped makes the question a restatement of its own task list.
    finished = None
    for sprint in reversed([s for s in sprints if s["status"] == "Done"]):
        delivered = [n for n in sprint["tasks"] if status_of.get(n) == "Done"]
        if delivered and len(delivered) < len(sprint["tasks"]):
            finished = (sprint, sorted(delivered))
            break
    if finished is None:
        raise ValueError("no finished sprint mixes delivered and undelivered tasks")

    # b4 — the feature phrase lives in the body; "still open" lives in the frontmatter.
    b4 = sorted(r["name"] for r in records if r["feature"] and r["status"] in ("Draft", "Designed"))

    # b5 — one task looked up by name. Deliberately a shape a whole-bundle load loses on.
    lookup = records[len(records) // 3]

    # b6 — the dropped tasks of one year and the reason each outcome names. Scoped by
    # year for the same reason b1 is scoped by priority.
    dropped_records = [r for r in records if r["status"] == "Dropped"]
    drop_year = sorted(
        {r["created"][:4] for r in dropped_records},
        key=lambda y: (-sum(1 for r in dropped_records if r["created"][:4] == y), y),
    )[0]
    b6 = {r["name"]: r["reason"] for r in dropped_records if r["created"][:4] == drop_year}

    # b7 — the next free number. `len(records)` is a different number, because the
    # sequence has gaps.
    b7 = max(r["number"] for r in records) + 1

    tags: dict[str, int] = {}
    for record in records:
        for tag in record["tags"]:
            tags[tag] = tags.get(tag, 0) + 1

    return {
        "counts": {
            "Task": len(records),
            "Sprint": len(sprints),
            "open": sum(1 for r in records if r["status"] in ("Draft", "Designed")),
            # Recorded so the harness can check the coached shell recipe against a known
            # number rather than merely against a zero exit code.
            "Draft": sum(1 for r in records if r["status"] == "Draft"),
        },
        "b1": {"answer": b1},
        "b2": {"sprint": active["name"], "branch": active["branch"], "answer": b2},
        "b3": {"sprint": finished[0]["name"], "answer": finished[1]},
        "b4": {"phrase": FEATURE_PHRASE, "answer": b4},
        "b5": {
            "task": lookup["name"],
            "answer": {"status": lookup["status"], "priority": lookup["priority"]},
        },
        "b6": {"year": drop_year, "answer": b6},
        "b7": {"answer": b7, "file_count": len(records)},
        "b8": {"answer": tags},
    }


def write(
    out_dir: Path,
    truth_path: Path,
    docs: list[Doc],
    truth: dict,
    seed: int = 24,
    messy: bool = True,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.md").write_text(INDEX)
    for doc in docs:
        sub = out_dir / doc.subdir
        sub.mkdir(exist_ok=True)
        style = random.Random(f"{seed}:style:{doc.name}") if messy else None
        (sub / f"{doc.name}.md").write_text(_frontmatter(doc.frontmatter, style) + "\n" + doc.body)

    names = [d.name for d in docs]
    if len(set(names)) != len(names):
        raise AssertionError("concept names must be unique across the bundle")
    _cross_check(out_dir, truth)

    truth["_meta"] = {
        "seed": seed,
        "tasks": truth["counts"]["Task"],
        "sprints": truth["counts"]["Sprint"],
        "messy": messy,
        "feature_phrase": FEATURE_PHRASE,
        "product": "Lumenstore (invented for this corpus)",
    }
    truth_path.parent.mkdir(parents=True, exist_ok=True)
    truth_path.write_text(json.dumps(truth, indent=2, sort_keys=True) + "\n")


def _read_back(out_dir: Path) -> tuple[list[dict], list[dict]]:
    """Re-parse the written bundle with PyYAML, independently of how it was produced."""
    import yaml

    tasks, sprints = [], []
    for path in sorted(out_dir.rglob("*.md")):
        if path.name == "index.md":
            continue
        text = path.read_text()
        _, _, rest = text.partition("---\n")
        block, _, body = rest.partition("\n---")
        data = yaml.safe_load(block)
        if not isinstance(data, dict):
            raise AssertionError(f"{path} did not parse as a mapping")
        data["__name"] = path.stem
        data["__body"] = body
        (tasks if data.get("type") == "Task" else sprints).append(data)
    return tasks, sprints


def _cross_check(out_dir: Path, truth: dict) -> None:
    """Recompute every published answer by reading the files back off disk.

    Ground truth above comes from the generation parameters; this comes from the bytes.
    A generator bug would otherwise be scored as an agent's error.
    """
    try:
        tasks, sprints = _read_back(out_dir)
    except ImportError:  # the cross-check is a safety net, not a hard dependency
        print("warning: PyYAML unavailable, skipping the independent cross-check")
        return

    status_of = {t["__name"]: t.get("status") for t in tasks}
    checks: dict[str, tuple] = {}

    checks["b1"] = (
        sorted(
            t["__name"]
            for t in tasks
            if t.get("status") == "Draft"
            and t.get("priority") == "high"
            and all(status_of.get(d) == "Done" for d in (t.get("blocked_by") or []))
        ),
        truth["b1"]["answer"],
    )

    active = [s for s in sprints if s.get("status") != "Done"]
    if len(active) != 1:
        raise AssertionError(f"exactly one sprint must be unfinished, found {len(active)}")
    approach = re.compile(r"^Approach: ([a-z-]+)\.", re.MULTILINE)
    body_of = {t["__name"]: t["__body"] for t in tasks}
    checks["b2"] = (
        {
            name: (m.group(1) if (m := approach.search(body_of.get(name, ""))) else "none")
            for name in active[0]["tasks"]
        },
        truth["b2"]["answer"],
    )

    finished = next(s for s in sprints if s["__name"] == truth["b3"]["sprint"])
    checks["b3"] = (
        sorted(n for n in finished["tasks"] if status_of.get(n) == "Done"),
        truth["b3"]["answer"],
    )

    checks["b4"] = (
        sorted(
            t["__name"]
            for t in tasks
            if FEATURE_PHRASE in t["__body"] and t.get("status") in ("Draft", "Designed")
        ),
        truth["b4"]["answer"],
    )

    lookup = next(t for t in tasks if t["__name"] == truth["b5"]["task"])
    checks["b5"] = (
        {"status": lookup.get("status"), "priority": lookup.get("priority")},
        truth["b5"]["answer"],
    )

    dropped = re.compile(r"^Dropped: ([a-z-]+)\.", re.MULTILINE)
    checks["b6"] = (
        {
            t["__name"]: m.group(1)
            for t in tasks
            if t.get("status") == "Dropped"
            and str(t.get("created"))[:4] == truth["b6"]["year"]
            and (m := dropped.search(t["__body"]))
        },
        truth["b6"]["answer"],
    )

    checks["b7"] = (
        max(int(t["__name"].split("-")[0]) for t in tasks) + 1,
        truth["b7"]["answer"],
    )

    tags: dict[str, int] = {}
    for task in tasks:
        for tag in task.get("tags") or []:
            tags[tag] = tags.get(tag, 0) + 1
    checks["b8"] = (tags, truth["b8"]["answer"])

    for question, (derived, declared) in checks.items():
        if derived != declared:
            raise AssertionError(f"cross-check disagrees on {question}: {derived} != {declared}")

    if len(tasks) == truth["b7"]["answer"] - 1:
        raise AssertionError(
            "the task numbers have no gaps, so counting the files answers b7 by accident"
        )

    index = (out_dir / "index.md").read_text()
    if "type:" in index:
        raise AssertionError("a typed index would make the rollup questions test OKF trivia")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--truth", required=True, type=Path)
    ap.add_argument("--tasks", type=int, default=170)
    ap.add_argument("--sprints", type=int, default=22)
    ap.add_argument("--seed", type=int, default=24)
    ap.add_argument("--tidy", dest="messy", action="store_false")
    ap.set_defaults(messy=True)
    args = ap.parse_args()

    docs, truth = generate(args.tasks, args.sprints, args.seed)
    write(args.out, args.truth, docs, truth, seed=args.seed, messy=args.messy)
    print(f"{len(docs)} concepts -> {args.out} ({'messy' if args.messy else 'tidy'})")
    print(json.dumps(truth["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
