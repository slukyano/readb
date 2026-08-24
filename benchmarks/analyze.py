"""Aggregate benchmark runs into the tables the write-up publishes.

Medians, never means: the distributions are long-tailed and one runaway run would carry a
mean. Arm-level comparisons are **paired by question** — per-question median per arm, then
the ratio, then the median ratio across questions — with a percentile bootstrap interval
resampled over questions, because the dominant variance here is between question shapes,
not between repeats of one question.

**v2 does not chase a pooled number.** Pooling across all 26 questions produces a figure
set by the battery's composition, and a power computation on v1's raw data says why:
separating 0.90x from 1.00x on the pooled coached contrast has 22% power at 12 questions,
51% at 36, and 63% at 48. Three endpoints are declared instead, before any run, and
Holm-corrected together (`ENDPOINTS` below). Everything else this file prints is
descriptive, the pooled coached ratio explicitly so.

    python benchmarks/analyze.py --results benchmarks/results/v2.jsonl
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

DEFAULT_BASELINE = "baseline"
# The headline metrics. Wall clock, output tokens and cache-neutral cost left the headline
# after v1: none of them ever disagreed with billed cost in direction, and two headline
# bases doubled the length of every sentence about the result.
METRICS = [
    ("cost_billed_usd", "cost, as billed (USD)", 4),
    ("new_tokens_ingested", "new tokens ingested", 0),
    ("num_turns", "turns", 1),
    ("cumulative_prompt_tokens", "cumulative prompt tokens", 0),
]
APPENDIX_METRICS = [
    ("cost_cache_neutral_usd", "cost, cache-neutral (USD)", 4),
    ("wall_s", "wall clock (s)", 1),
    ("output_tokens", "output tokens", 0),
]
BASELINE = DEFAULT_BASELINE
BOOTSTRAP = 10_000

# --- the pre-registered endpoints ---------------------------------------------
# Fixed before the first measured run. Each names a contrast, a model, a stratum, and the
# statistic; the three p-values are corrected together by Holm.
ENDPOINTS = [
    {
        "id": "E1",
        "what": "billed cost, backlog stratum",
        "arm": "readb-cached",
        "against": "readb-bare",
        "model": "claude-sonnet-5",
        "strata": ("backlog",),
        "measure": "cost",
        "why": (
            "the cache's own contrast: two arms with identical preambles, differing only in "
            "whether the bundle is a registry with a warm cache. Parity is the predicted "
            "outcome, recorded as such in the pre-registration"
        ),
    },
    {
        "id": "E3",
        "what": "billed cost, join stratum",
        "arm": "readb-cached",
        "against": "shell-coached",
        "model": "claude-sonnet-5",
        "strata": ("join",),
        "measure": "cost",
        "why": "readb at its best against the honest competitor, carried forward from v2's E1",
    },
]

# E2 is a proportion rather than a paired contrast over questions, so it is computed apart from
# these two and reported beside them.
SKILL_INVOCATION_V2 = (37, 78)  # v2: the skill arm loaded the skill on 37 of 78 runs


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


# --- the exact test -----------------------------------------------------------
# Pre-registered, and pure stdlib on purpose: a benchmark whose published p-value cannot be
# recomputed without installing a scientific stack is one nobody will recompute.

EXACT_MAX = 18  # above this, 2**n sign assignments stop being enumerable
PERMUTATIONS = 200_000


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        shared = (position + end) / 2 + 1
        for index in order[position : end + 1]:
            ranks[index] = shared
        position = end + 1
    return ranks


def wilcoxon(diffs: list[float], seed: int = 24) -> dict | None:
    """Two-sided Wilcoxon signed-rank test by exact sign-flip enumeration.

    Zero differences are dropped, which is the standard handling. Ties in |difference| get
    average ranks; the null distribution is then the sign-flip permutation distribution of
    the signed-rank sum, which stays exact in the presence of those ties. Above `EXACT_MAX`
    non-zero pairs the enumeration is replaced by a seeded Monte Carlo over the same null,
    and the result says so.
    """
    kept = [d for d in diffs if d != 0]
    n = len(kept)
    if n < 5:
        return None
    ranks = _average_ranks([abs(d) for d in kept])
    observed = sum(rank if d > 0 else -rank for d, rank in zip(kept, ranks, strict=True))
    target = abs(observed)

    if n <= EXACT_MAX:
        hits = sum(
            1
            for signs in itertools.product((1, -1), repeat=n)
            if abs(sum(s * r for s, r in zip(signs, ranks, strict=True))) >= target - 1e-9
        )
        p = hits / (2**n)
        method = f"exact ({2**n} sign assignments)"
    else:
        rng = random.Random(seed)
        hits = sum(
            1
            for _ in range(PERMUTATIONS)
            if abs(sum(r if rng.random() < 0.5 else -r for r in ranks)) >= target - 1e-9
        )
        p = (hits + 1) / (PERMUTATIONS + 1)
        method = f"Monte Carlo ({PERMUTATIONS:,} sign flips, seed {seed})"
    return {"n": n, "statistic": observed, "p": p, "method": method}


def holm(pvalues: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, kept monotone."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for step, index in enumerate(order):
        value = min(1.0, (len(pvalues) - step) * pvalues[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted


# --- helpers over the record set ----------------------------------------------


def question_medians(rows: list[dict], arm: str, model: str | None, key: str) -> dict[str, float]:
    grouped = defaultdict(list)
    for r in rows:
        if r["arm"] != arm or (model and r.get("model") != model):
            continue
        if r.get(key) is not None:
            grouped[r["question"]].append(r[key])
    return {q: med(values) for q, values in grouped.items()}


def question_exactness(rows: list[dict], arm: str, model: str | None) -> dict[str, float]:
    grouped = defaultdict(list)
    for r in rows:
        if r["arm"] != arm or (model and r.get("model") != model):
            continue
        grouped[r["question"]].append(1.0 if r["correct"] else 0.0)
    return {q: statistics.mean(values) for q, values in grouped.items()}


def run_endpoint(endpoint: dict, clean: list[dict], strata_of: dict) -> dict:
    rows = [r for r in clean if r.get("model") == endpoint["model"]]
    if endpoint["strata"]:
        rows = [r for r in rows if strata_of.get(r["question"]) in endpoint["strata"]]

    if endpoint["measure"] == "cost":
        arm = question_medians(rows, endpoint["arm"], None, "cost_billed_usd")
        against = question_medians(rows, endpoint["against"], None, "cost_billed_usd")
        shared = sorted(set(arm) & set(against))
        diffs, ratios = [], []
        for q in shared:
            if arm[q] > 0 and against[q] > 0:
                diffs.append(math.log(arm[q] / against[q]))
                ratios.append(arm[q] / against[q])
        effect = f"{med(ratios):.2f}x" if ratios else "—"
        lo, hi = bootstrap_ci(ratios)
        interval = f"[{lo:.2f}–{hi:.2f}]" if lo == lo else ""
    else:
        arm = question_exactness(rows, endpoint["arm"], None)
        against = question_exactness(rows, endpoint["against"], None)
        shared = sorted(set(arm) & set(against))
        diffs = [arm[q] - against[q] for q in shared]
        if shared:
            effect = (
                f"{statistics.mean(arm[q] for q in shared):.0%} vs "
                f"{statistics.mean(against[q] for q in shared):.0%}"
            )
        else:
            effect = "—"
        interval = ""

    test = wilcoxon(diffs)
    # The pairs actually compared, not the questions both arms happened to answer: a
    # question whose median cost is missing or non-positive is dropped inside the loop, and
    # reporting `len(shared)` would over-state what the test saw.
    return {**endpoint, "questions": len(diffs), "effect": effect, "ci": interval, "test": test}


# --- the report ---------------------------------------------------------------


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
    ap.add_argument(
        "--baseline-arm",
        default=DEFAULT_BASELINE,
        help="the arm every descriptive ratio is taken against (default: baseline). The "
        "pre-registered endpoints have their own comparator and ignore this.",
    )
    ap.add_argument(
        "--corpus",
        help="keep only runs against this corpus, for a results file that spans several",
    )
    ap.add_argument(
        "--sweep-only",
        action="store_true",
        help="print only the messy/tidy comparison, for a batch that deliberately spans corpora",
    )
    ap.add_argument(
        "--skip-endpoints",
        action="store_true",
        help="omit the pre-registered endpoint tests, for a batch that is not the main matrix",
    )
    args = ap.parse_args()
    global BASELINE
    BASELINE = args.baseline_arm

    records = load(args.results)
    if args.baseline_from:
        records += [r for r in load(args.baseline_from) if r["arm"] == BASELINE]
    if args.corpus:
        records = [r for r in records if r.get("corpus") == args.corpus]

    # A question that appears under two corpora is the sweep, where every table other than
    # the sweep's own would silently pool a messy run with a tidy one for the same question
    # — and E1 (q3) and the scan stratum (q2, q15) are exactly the cells that would move.
    # The README says to analyse the sweep on its own; this makes the code say it too.
    spanning = sorted(
        q
        for q in {r["question"] for r in records}
        if len({r.get("corpus") for r in records if r["question"] == q}) > 1
    )
    if spanning and not (args.corpus or args.sweep_only):
        raise SystemExit(
            f"{len(spanning)} question(s) appear under more than one corpus "
            f"({', '.join(spanning)}). Pass --sweep-only for the messy/tidy table alone, or "
            f"--corpus NAME to pick one rendering; pooling them would put two renderings "
            f"in the same cell."
        )
    dropped = [(r, why) for r in records if (why := invalid(r))]
    clean = [r for r in records if not invalid(r)]
    arms = sorted({r["arm"] for r in records}, key=lambda a: (a != BASELINE, a))
    models = sorted({r.get("model") or "?" for r in records})
    questions = sorted({r["question"] for r in records})
    shape_of = {r["question"]: (r["shape"], r["favours"]) for r in records}
    strata_of = {r["question"]: r.get("stratum", "?") for r in records}
    expert_of = {r["question"]: r.get("expert_tool", "?") for r in records}
    strata = sorted({strata_of[q] for q in questions})

    print("# Benchmark results — v2\n")
    print(f"{len(records)} runs recorded, {len(dropped)} excluded as invalid, {len(clean)} used.")
    print(f"Models: {', '.join(models)}. Arms: {', '.join(arms)}. Questions: {len(questions)}.\n")

    # --- the endpoints, first, because everything after them is descriptive ----
    if not args.skip_endpoints and not args.sweep_only:
        print("## Pre-registered endpoints\n")
        results = [run_endpoint(e, clean, strata_of) for e in ENDPOINTS]
        raw = [r["test"]["p"] if r["test"] else 1.0 for r in results]
        adjusted = holm(raw)
        print("| id | contrast | model | questions | effect | p | Holm p | test |")
        print("|" + "---|" * 8)
        for result, p_adj in zip(results, adjusted, strict=True):
            test = result["test"]
            raw_p = f"{test['p']:.4f}" if test else "—"
            holm_p = f"{p_adj:.4f}" if test else "—"
            method = test["method"] if test else "too few pairs"
            print(
                f"| {result['id']} | {result['arm']} vs {result['against']}, {result['what']} "
                f"| {result['model'].replace('claude-', '')} | {result['questions']} "
                f"| {result['effect']} {result['ci']} | {raw_p} | {holm_p} | {method} |"
            )
        print()
        for result in results:
            print(f"- **{result['id']}** — {result['why']}.")
        print()

    by_arm_model = defaultdict(list)
    for r in clean:
        by_arm_model[(r.get("model"), r["arm"])].append(r)

    # --- per model ------------------------------------------------------------
    for model in [] if args.sweep_only else models:
        rows_for_model = [r for r in clean if (r.get("model") or "?") == model]
        if not rows_for_model:
            continue
        print(f"## {model}\n")
        print("### Per arm, all questions pooled\n")
        header = "| arm | n | exact | partial | answer parsed | " + " | ".join(
            m[1] for m in METRICS
        )
        print(header + " |")
        print("|" + "---|" * (len(METRICS) + 5))
        for arm in arms:
            rows = by_arm_model.get((model, arm)) or []
            if not rows:
                continue
            exact = sum(1 for r in rows if r["correct"]) / len(rows)
            partial = statistics.mean(r.get("partial_credit") or 0 for r in rows)
            parsed = sum(1 for r in rows if r.get("answer_parsed")) / len(rows)
            cells = [
                fmt(med([r[k] for r in rows if r.get(k) is not None]), d) for k, _, d in METRICS
            ]
            print(
                f"| {arm} | {len(rows)} | {exact:.0%} | {partial:.2f} | {parsed:.0%} | "
                + " | ".join(cells)
                + " |"
            )

        print(f"\n### Ratio to `{BASELINE}`, paired by question (below 1.00 favours the arm)\n")
        print("| arm | " + " | ".join(f"{m[1]} [95% CI]" for m in METRICS) + " |")
        print("|" + "---|" * (len(METRICS) + 1))
        for arm in arms:
            if arm == BASELINE:
                continue
            cells = []
            for key, _, _ in METRICS:
                arm_med = question_medians(rows_for_model, arm, model, key)
                base_med = question_medians(rows_for_model, BASELINE, model, key)
                ratios = [
                    arm_med[q] / base_med[q]
                    for q in sorted(set(arm_med) & set(base_med))
                    if base_med[q] and base_med[q] == base_med[q]
                ]
                if ratios:
                    lo, hi = bootstrap_ci(ratios)
                    ci = f" [{lo:.2f}–{hi:.2f}]" if lo == lo else ""
                    cells.append(f"{med(ratios):.2f}x{ci}")
                else:
                    cells.append("—")
            print(f"| {arm} | " + " | ".join(cells) + " |")

        print(f"\n### Billed-cost ratio to `{BASELINE}` by stratum\n")
        counts = {s: sum(1 for q in questions if strata_of[q] == s) for s in strata}
        print("| arm | " + " | ".join(f"{s} (n={counts[s]})" for s in strata) + " |")
        print("|" + "---|" * (len(strata) + 1))
        for arm in arms:
            if arm == BASELINE:
                continue
            cells = []
            arm_med = question_medians(rows_for_model, arm, model, "cost_billed_usd")
            base_med = question_medians(rows_for_model, BASELINE, model, "cost_billed_usd")
            for stratum in strata:
                ratios = [
                    arm_med[q] / base_med[q]
                    for q in sorted(set(arm_med) & set(base_med))
                    if strata_of[q] == stratum and base_med[q]
                ]
                cells.append(f"{med(ratios):.2f}x" if ratios else "—")
            print(f"| {arm} | " + " | ".join(cells) + " |")

        print("\n### Tool choice — what the agent reached for, against what a question declares\n")
        print(
            "A result, never a reason to edit a prompt. `match` is the share of runs whose "
            "chosen tool equalled the question's declared expert tool.\n"
        )
        choices = ("readb", "shell", "read", "other", "none")
        print("| arm | " + " | ".join(choices) + " | match | failed calls | failed readb |")
        print("|" + "---|" * (len(choices) + 4))
        for arm in arms:
            rows = by_arm_model.get((model, arm)) or []
            if not rows:
                continue
            cells = [str(sum(1 for r in rows if r.get("tool_choice") == c)) for c in choices]
            match = sum(1 for r in rows if r.get("tool_match")) / len(rows)
            print(
                f"| {arm} | "
                + " | ".join(cells)
                + f" | {match:.0%} "
                + f"| {sum(r.get('failed_tool_results') or 0 for r in rows)} "
                + f"| {sum(r.get('failed_readb_calls') or 0 for r in rows)} |"
            )

        print()

    # --- the cache contrast ---------------------------------------------------
    for model in models:
        if {(model, "readb-bare"), (model, "readb-cached")} <= set(by_arm_model):
            bare_med = question_medians(rows, "readb-bare", model, "cost_billed_usd")
            cached_med = question_medians(rows, "readb-cached", model, "cost_billed_usd")
            shared = sorted(set(bare_med) & set(cached_med))
            ratios = [cached_med[q] / bare_med[q] for q in shared if bare_med[q]]
            wall_bare = question_medians(rows, "readb-bare", model, "wall_s")
            wall_cached = question_medians(rows, "readb-cached", model, "wall_s")
            wall_shared = sorted(set(wall_bare) & set(wall_cached))
            wall_ratios = [wall_cached[q] / wall_bare[q] for q in wall_shared if wall_bare[q]]
            print(f"\n### The cache — `readb-cached` against `readb-bare` ({model})\n")
            print("Identical preambles; the corpus is a registry with a primed cache.\n")
            print("| measure | ratio, cached/bare | questions |")
            print("| --- | --- | --- |")
            if ratios:
                print(f"| billed cost | {med(ratios):.2f}x | {len(ratios)} |")
            if wall_ratios:
                wall = f"{med(wall_ratios):.2f}x"
                print(f"| wall clock (declared secondary) | {wall} | {len(wall_ratios)} |")
            print()

    # --- hazard diagnostics ---------------------------------------------------
    hazard = (
        [] if args.sweep_only else [r for r in clean if strata_of.get(r["question"]) == "hazard"]
    )
    if hazard:
        print("## The malformed-file hazard\n")
        print(
            "`saw warning` counts runs where readb's skip warning reached the transcript. A "
            "wrong answer with the warning seen and a wrong answer without it are different "
            "findings: the first says the warning did not work, the second says the hazard is "
            "silent.\n"
        )
        print("| model | arm | question | n | exact | saw warning | tool |")
        print("|" + "---|" * 7)
        for model in models:
            for arm in arms:
                for q in sorted({r["question"] for r in hazard}):
                    rows = [
                        r
                        for r in hazard
                        if r["question"] == q and r["arm"] == arm and r.get("model") == model
                    ]
                    if not rows:
                        continue
                    exact = sum(1 for r in rows if r["correct"]) / len(rows)
                    warned = sum(1 for r in rows if r.get("saw_skip_warning"))
                    tools = "/".join(sorted({r.get("tool_choice") or "?" for r in rows}))
                    print(
                        f"| {model.replace('claude-', '')} | {arm} | {q} | {len(rows)} | "
                        f"{exact:.0%} | {warned}/{len(rows)} | {tools} |"
                    )
        print()

    # --- the messiness sweep --------------------------------------------------
    corpora = {r.get("corpus") for r in clean}
    if "ops" in corpora and "ops-tidy" in corpora:
        swept = sorted(
            {r["question"] for r in clean if r.get("corpus") == "ops-tidy"}
            & {r["question"] for r in clean if r.get("corpus") == "ops"}
        )
        if swept:
            print("## Messy against tidy — the same questions, two renderings\n")
            print("| model | arm | question | messy cost | tidy cost | messy/tidy | exact m/t |")
            print("|" + "---|" * 7)
            for model in models:
                for arm in arms:
                    for q in swept:
                        pair = {}
                        for corpus in ("ops", "ops-tidy"):
                            pair[corpus] = [
                                r
                                for r in clean
                                if r["question"] == q
                                and r["arm"] == arm
                                and r.get("model") == model
                                and r.get("corpus") == corpus
                            ]
                        if not (pair["ops"] and pair["ops-tidy"]):
                            continue
                        cost = {
                            c: med([r["cost_billed_usd"] for r in rows]) for c, rows in pair.items()
                        }
                        exact = {
                            c: sum(1 for r in rows if r["correct"]) / len(rows)
                            for c, rows in pair.items()
                        }
                        ratio = cost["ops"] / cost["ops-tidy"] if cost["ops-tidy"] else float("nan")
                        print(
                            f"| {model.replace('claude-', '')} | {arm} | {q} | "
                            f"{fmt(cost['ops'], 4)} | {fmt(cost['ops-tidy'], 4)} | "
                            f"{fmt(ratio, 2)}x | {exact['ops']:.0%}/{exact['ops-tidy']:.0%} |"
                        )
            print()

    # --- per question ---------------------------------------------------------
    if args.sweep_only:
        print(
            f"\nTotal reported spend: ${sum(r.get('cost_reported_usd') or 0 for r in records):.2f}"
        )
        return

    print("## By question\n")
    print(
        "| question | stratum | shape | expert | model | arm | n | exact | ingested "
        "| cost (billed) | turns | readb calls |"
    )
    print("|" + "---|" * 12)
    for q in questions:
        shape, _ = shape_of[q]
        for model in models:
            for arm in arms:
                rows = [
                    r
                    for r in clean
                    if r["question"] == q and r["arm"] == arm and (r.get("model") or "?") == model
                ]
                if not rows:
                    continue
                exact = sum(1 for r in rows if r["correct"]) / len(rows)
                print(
                    f"| {q} | {strata_of[q]} | {shape} | {expert_of[q]} "
                    f"| {model.replace('claude-', '')} | {arm} | {len(rows)} | {exact:.0%} | "
                    f"{fmt(med([r['new_tokens_ingested'] for r in rows]), 0)} | "
                    f"{fmt(med([r['cost_billed_usd'] for r in rows]), 4)} | "
                    f"{fmt(med([r['num_turns'] for r in rows if r.get('num_turns')]), 1)} | "
                    f"{fmt(med([r['readb_invocations'] for r in rows]), 1)} |"
                )

    # --- the floor ------------------------------------------------------------
    if args.floor:
        # Subtracting one floor per run treats the fixed overhead as belonging to neither arm.
        # It is a choice, not a correction: a ratio below 1 always moves further from 1 when a
        # constant is removed from both sides. Published beside the raw figure, never instead.
        # The median across a floor's repeats, not whichever record happened to be last.
        # v1's floor was n=1, so a dict comprehension was harmless; v2's is three per cell.
        floor_rows = defaultdict(list)
        for row in load(args.floor):
            if not invalid(row):
                floor_rows[(row.get("model"), row["arm"])].append(row)
        floors = {
            key: {
                metric: med([r[metric] for r in rows if r.get(metric) is not None])
                for metric in ("cost_billed_usd", "cumulative_prompt_tokens", "num_turns")
            }
            for key, rows in floor_rows.items()
        }
        print("\n## Overhead-subtracted cost ratios — a choice, not a correction\n")
        print(
            "The floor is a trivial prompt through the identical harness, so it measures the "
            "**runtime's** fixed cost under each arm's configuration — not that arm's own "
            "preamble, which is its treatment and is deliberately never subtracted. A ratio "
            "below 1.00 always moves further from 1.00 when a constant is removed from both "
            "sides, so which constant is removed is a choice; both rules are shown, neither "
            "as the authoritative one.\n"
        )
        print("| model | arm | one floor per run | one prompt prefix per turn |")
        print("|---|---|---|---|")
        for model in models:
            if (model, BASELINE) not in floors:
                continue
            rows_for_model = [r for r in clean if (r.get("model") or "?") == model]
            for arm in arms:
                if arm == BASELINE or (model, arm) not in floors:
                    continue
                arm_med = question_medians(rows_for_model, arm, model, "cost_billed_usd")
                base_med = question_medians(rows_for_model, BASELINE, model, "cost_billed_usd")
                ratios = []
                for q in sorted(set(arm_med) & set(base_med)):
                    lo_b = base_med[q] - floors[(model, BASELINE)]["cost_billed_usd"]
                    lo_v = arm_med[q] - floors[(model, arm)]["cost_billed_usd"]
                    if lo_b > 0 and lo_v > 0:
                        ratios.append(lo_v / lo_b)

                arm_tok = question_medians(rows_for_model, arm, model, "cumulative_prompt_tokens")
                base_tok = question_medians(
                    rows_for_model, BASELINE, model, "cumulative_prompt_tokens"
                )
                arm_turns = question_medians(rows_for_model, arm, model, "num_turns")
                base_turns = question_medians(rows_for_model, BASELINE, model, "num_turns")

                # One prompt *prefix*, not one whole floor run. A floor run takes a couple
                # of turns of its own, so its cumulative prompt tokens are already several
                # prefixes; multiplying that by the real run's turn count over-subtracts far
                # enough to drive both sides negative, which is why this column printed a
                # dash for every arm in v1.
                def prefix(key: tuple) -> float:
                    floor = floors[key]
                    return floor["cumulative_prompt_tokens"] / (floor["num_turns"] or 1)

                per_turn = []
                for q in sorted(set(arm_tok) & set(base_tok)):
                    b = base_tok[q] - base_turns.get(q, 0) * prefix((model, BASELINE))
                    v = arm_tok[q] - arm_turns.get(q, 0) * prefix((model, arm))
                    if b > 0 and v > 0:
                        per_turn.append(v / b)
                print(
                    f"| {model.replace('claude-', '')} | {arm} | "
                    f"{f'{med(ratios):.2f}x' if ratios else '—'} | "
                    f"{f'{med(per_turn):.2f}x' if per_turn else '—'} |"
                )

    print("\n## Integrity\n")
    print(
        "| model | arm | runs | no tool call | skill fired | compacted | denials "
        "| readb never used |"
    )
    print("|" + "---|" * 8)
    for model in models:
        for arm in arms:
            rows = by_arm_model.get((model, arm)) or []
            if not rows:
                continue
            expects_readb = arm.startswith("readb")
            print(
                f"| {model.replace('claude-', '')} | {arm} | {len(rows)} | "
                f"{sum(1 for r in rows if not r.get('supported'))} | "
                f"{sum(1 for r in rows if r.get('skill_readb_used'))} | "
                f"{sum(1 for r in rows if r.get('compacted'))} | "
                f"{sum(1 for r in rows if r.get('permission_denials'))} | "
                f"{sum(1 for r in rows if expects_readb and not r.get('readb_used'))} |"
            )

    print("\n## Appendix — the demoted metrics\n")
    print("| model | arm | " + " | ".join(m[1] for m in APPENDIX_METRICS) + " |")
    print("|" + "---|" * (len(APPENDIX_METRICS) + 2))
    for model in models:
        for arm in arms:
            rows = by_arm_model.get((model, arm)) or []
            if not rows:
                continue
            cells = [
                fmt(med([r[k] for r in rows if r.get(k) is not None]), d)
                for k, _, d in APPENDIX_METRICS
            ]
            print(f"| {model.replace('claude-', '')} | {arm} | " + " | ".join(cells) + " |")

    if dropped:
        print("\n## Excluded runs\n")
        for rec, why in dropped:
            print(f"- {rec['arm']} {rec['question']} r{rec['repeat']}: {why}")

    wrong = [r for r in clean if not r["correct"]]
    if wrong:
        print("\n## Every wrong answer\n")
        for r in sorted(wrong, key=lambda r: (r["question"], r.get("model") or "", r["arm"])):
            print(
                f"- {r['question']} {(r.get('model') or '').replace('claude-', '')} {r['arm']} "
                f"r{r['repeat']}: answered `{r.get('parsed_answer')}` "
                f"(partial {r.get('partial_credit')}, tool {r.get('tool_choice')})"
            )

    print(f"\nTotal reported spend: ${sum(r.get('cost_reported_usd') or 0 for r in records):.2f}")


if __name__ == "__main__":
    main()
