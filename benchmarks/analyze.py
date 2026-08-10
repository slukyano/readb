"""Aggregate benchmark runs into the tables the write-up publishes.

Medians, never means: the distributions are long-tailed and one runaway run would carry a
mean. Arm-level comparisons are **paired by question** — per-question median per arm, then
the ratio, then the median ratio across questions — with a percentile bootstrap interval
resampled over questions, because the dominant variance here is between question shapes,
not between repeats of one question.

    python benchmarks/analyze.py --results benchmarks/results/run.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

BASELINE = "baseline"
METRICS = [
    ("cost_billed_usd", "cost, as billed (USD)", 4),
    ("cost_cache_neutral_usd", "cost, cache-neutral (USD)", 4),
    ("new_tokens_ingested", "new tokens ingested", 0),
    ("wall_s", "wall clock (s)", 1),
    ("output_tokens", "output tokens", 0),
    ("num_turns", "turns", 1),
    ("cumulative_prompt_tokens", "cumulative prompt tokens", 0),
]
BOOTSTRAP = 10_000


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def faulted(rec: dict) -> bool:
    return bool(rec.get("harness_error")) or bool(rec.get("is_error"))


def invalid(rec: dict) -> str | None:
    """Runs whose numbers must not be used, and why."""
    if rec.get("retracted"):
        return rec["retracted"]
    if faulted(rec):
        return rec.get("harness_error") or f"api error {rec.get('api_error_status')}"
    if rec.get("leak_baseline_readb"):
        return "readb leaked into the baseline arm"
    if rec.get("permission_denials"):
        return "permission denied mid-run"
    return None


def med(values: list[float]) -> float:
    return statistics.median(values) if values else float("nan")


def fmt(value: float, digits: int) -> str:
    if value != value:
        return "—"
    return f"{value:,.{digits}f}" if digits else f"{value:,.0f}"


def bootstrap_ci(ratios: list[float], seed: int = 24) -> tuple[float, float]:
    """Percentile bootstrap over questions. Labelled as such — this is not a p-value."""
    if len(ratios) < 3:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    draws = sorted(statistics.median(rng.choices(ratios, k=len(ratios))) for _ in range(BOOTSTRAP))
    return draws[int(0.025 * BOOTSTRAP)], draws[int(0.975 * BOOTSTRAP)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument(
        "--baseline-from",
        type=Path,
        help=(
            "pull the baseline arm from another results file, for a batch that re-measures one "
            "arm alone. Without it such a batch has nothing to pair against and every ratio "
            "prints as '—', which invites hand-computation — how four wrong cells reached a "
            "published table once already."
        ),
    )
    ap.add_argument("--floor", type=Path, help="floor runs, to report floor-subtracted ratios")
    args = ap.parse_args()

    records = load(args.results)
    if args.baseline_from:
        records += [r for r in load(args.baseline_from) if r["arm"] == BASELINE]
    dropped = [(r, why) for r in records if (why := invalid(r))]
    clean = [r for r in records if not invalid(r)]
    arms = sorted({r["arm"] for r in records}, key=lambda a: (a != BASELINE, a))
    questions = sorted({r["question"] for r in records})
    shape_of = {r["question"]: (r["shape"], r["favours"]) for r in records}

    print("# Benchmark results\n")
    print(f"{len(records)} runs recorded, {len(dropped)} excluded as invalid, {len(clean)} used.\n")

    by_arm = defaultdict(list)
    for r in clean:
        by_arm[r["arm"]].append(r)

    print("## Per arm, all questions pooled\n")
    print("| arm | n | exact | partial credit | " + " | ".join(m[1] for m in METRICS) + " |")
    print("|" + "---|" * (len(METRICS) + 4))
    for arm in arms:
        rows = by_arm[arm]
        if not rows:
            continue
        exact = sum(1 for r in rows if r["correct"]) / len(rows)
        partial = statistics.mean(r.get("partial_credit") or 0 for r in rows)
        cells = [fmt(med([r[k] for r in rows if r.get(k) is not None]), d) for k, _, d in METRICS]
        print(f"| {arm} | {len(rows)} | {exact:.0%} | {partial:.2f} | " + " | ".join(cells) + " |")

    print("\n## Ratio to baseline, paired by question (below 1.00 favours the arm)\n")
    print("| arm | " + " | ".join(f"{m[1]} [95% CI]" for m in METRICS) + " |")
    print("|" + "---|" * (len(METRICS) + 1))
    base = {
        (k, q): med(
            [
                r[k]
                for r in clean
                if r["arm"] == BASELINE and r["question"] == q and r.get(k) is not None
            ]
        )
        for k, _, _ in METRICS
        for q in questions
    }
    for arm in arms:
        if arm == BASELINE:
            continue
        cells = []
        for key, _, _ in METRICS:
            ratios = []
            for q in questions:
                values = [
                    r[key]
                    for r in clean
                    if r["arm"] == arm and r["question"] == q and r.get(key) is not None
                ]
                b = base.get((key, q))
                if values and b and b == b and b != 0:
                    ratios.append(med(values) / b)
            if ratios:
                lo, hi = bootstrap_ci(ratios)
                ci = f" [{lo:.2f}–{hi:.2f}]" if lo == lo else ""
                cells.append(f"{med(ratios):.2f}×{ci}")
            else:
                cells.append("—")
        print(f"| {arm} | " + " | ".join(cells) + " |")

    print("\n## By question shape\n")
    print(
        "| question | shape | favours | arm | n | exact | ingested | cost (neutral) "
        "| wall (s) | turns | readb calls |"
    )
    print("|" + "---|" * 11)
    for q in questions:
        shape, favours = shape_of[q]
        for arm in arms:
            rows = [r for r in clean if r["question"] == q and r["arm"] == arm]
            if not rows:
                continue
            exact = sum(1 for r in rows if r["correct"]) / len(rows)
            print(
                f"| {q} | {shape} | {favours} | {arm} | {len(rows)} | {exact:.0%} | "
                f"{fmt(med([r['new_tokens_ingested'] for r in rows]), 0)} | "
                f"{fmt(med([r['cost_cache_neutral_usd'] for r in rows]), 4)} | "
                f"{fmt(med([r['wall_s'] for r in rows]), 1)} | "
                f"{fmt(med([r['num_turns'] for r in rows if r.get('num_turns')]), 1)} | "
                f"{fmt(med([r['readb_invocations'] for r in rows]), 1)} |"
            )

    if args.floor:
        # Subtracting one floor per run treats the fixed overhead as belonging to neither arm.
        # It is a choice, not a correction: a ratio below 1 always moves further from 1 when a
        # constant is removed from both sides. Published beside the raw figure, never instead.
        floors = {r["arm"]: r for r in load(args.floor)}
        print("\n## Floor-subtracted cost ratios (one floor per run; see the caveat)\n")
        print("| arm | billed | cache-neutral |")
        print("|---|---|---|")
        for arm in arms:
            if arm == BASELINE or arm not in floors:
                continue
            cells = []
            for key in ("cost_billed_usd", "cost_cache_neutral_usd"):
                ratios = []
                for q in questions:
                    b = base.get((key, q))
                    v = med([r[key] for r in clean if r["arm"] == arm and r["question"] == q])
                    if b and v == v:
                        lo_b = b - floors[BASELINE][key]
                        lo_v = v - floors[arm][key]
                        if lo_b > 0:
                            ratios.append(lo_v / lo_b)
                cells.append(f"{med(ratios):.2f}×" if ratios else "—")
            print(f"| {arm} | " + " | ".join(cells) + " |")

    # The headline ratio is a median over questions, so it tracks the battery's shape mix.
    # Publishing it by declared shape is the honest sensitivity analysis.
    print("\n## Cost ratio to baseline, by the shape a question was declared to favour\n")
    favours = sorted({shape_of[q][1] for q in questions})
    print(
        "| arm | "
        + " | ".join(f"{f} (n={sum(1 for q in questions if shape_of[q][1] == f)})" for f in favours)
        + " |"
    )
    print("|" + "---|" * (len(favours) + 1))
    for arm in arms:
        if arm == BASELINE:
            continue
        cells = []
        for fav in favours:
            ratios = []
            for q in questions:
                if shape_of[q][1] != fav:
                    continue
                v = [r["cost_billed_usd"] for r in clean if r["arm"] == arm and r["question"] == q]
                b = base.get(("cost_billed_usd", q))
                if v and b:
                    ratios.append(med(v) / b)
            cells.append(f"{med(ratios):.2f}×" if ratios else "—")
        print(f"| {arm} | " + " | ".join(cells) + " |")

    print("\n## Integrity\n")
    print("| arm | runs | unsupported | skill fired | compacted | denials | readb never used |")
    print("|" + "---|" * 7)
    for arm in arms:
        rows = by_arm[arm]
        if not rows:
            continue
        expects_readb = arm != BASELINE
        print(
            f"| {arm} | {len(rows)} | {sum(1 for r in rows if not r.get('supported'))} | "
            f"{sum(1 for r in rows if r.get('skill_readb_used'))} | "
            f"{sum(1 for r in rows if r.get('compacted'))} | "
            f"{sum(1 for r in rows if r.get('permission_denials'))} | "
            f"{sum(1 for r in rows if expects_readb and not r.get('readb_used'))} |"
        )

    if dropped:
        print("\n## Excluded runs\n")
        for rec, why in dropped:
            print(f"- {rec['arm']} {rec['question']} r{rec['repeat']}: {why}")

    wrong = [r for r in clean if not r["correct"]]
    if wrong:
        print("\n## Every wrong answer\n")
        for r in sorted(wrong, key=lambda r: (r["question"], r["arm"])):
            print(
                f"- {r['question']} {r['arm']} r{r['repeat']}: answered `{r.get('parsed_answer')}` "
                f"(partial {r.get('partial_credit')})"
            )

    print(f"\nTotal reported spend: ${sum(r.get('cost_reported_usd') or 0 for r in records):.2f}")


if __name__ == "__main__":
    main()
