"""Tests for the benchmark harness itself.

The scorer decides what gets published, and the cost model turns token counts into a
number a reader will quote. Both are worth pinning. Run with `uv run pytest benchmarks`;
the package's own suite does not collect this directory, and the sdist does not ship it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from battery import BY_ID, extract_answer, f1, score  # noqa: E402
from generate_corpus import generate, write  # noqa: E402
from run_benchmark import costs, integrity  # noqa: E402

# --- the scorer ---------------------------------------------------------------


def test_extract_answer_takes_the_last_marker():
    text = "ANSWER: wrong\nsome more reasoning\nANSWER: right"
    assert extract_answer(text) == "right"


def test_extract_answer_absent():
    assert extract_answer("no marker here") is None


@pytest.mark.parametrize(
    "raw",
    [
        "svc-0001, svc-0002",
        "SVC-0001, SVC-0002",
        "services/svc-0001.md, services/svc-0002.md",
        "`svc-0002`, `svc-0001`",
        "svc-0002\nsvc-0001",
    ],
)
def test_set_normalizer_is_arm_neutral(raw):
    """Arms name things differently by construction; the normalizer must not pick a winner."""
    question = BY_ID["q3"]
    truth = {"q3": {"team": "x", "answer": ["svc-0001", "svc-0002"]}}
    exact, partial, _ = score(question, raw, truth)
    assert exact and partial == 1.0


def test_set_scoring_is_binary_but_reports_f1():
    question = BY_ID["q3"]
    truth = {"q3": {"team": "x", "answer": ["a", "b", "c", "d"]}}
    exact, partial, _ = score(question, "a, b, c", truth)
    assert not exact
    assert partial == pytest.approx(2 * (1.0 * 0.75) / 1.75)


def test_f1_edges():
    assert f1(set(), set()) == 1.0
    assert f1({"a"}, set()) == 0.0
    assert f1(set(), {"a"}) == 0.0


def test_mapping_requires_every_key():
    question = BY_ID["q1"]
    truth = {"q1": {"Service": 2, "Runbook": 3}}
    assert score(question, "service=2, runbook=3", truth)[0]
    # An extra category is a different answer, not a rounding error.
    assert not score(question, "service=2, runbook=3, index=1", truth)[0]


def test_number_scoring_ignores_surrounding_prose():
    question = BY_ID["q10"]
    truth = {"q10": {"answer": 192}}
    assert score(question, "192 files", truth)[0]
    assert not score(question, "180", truth)[0]


def test_missing_answer_scores_zero():
    question = BY_ID["q7"]
    assert score(question, None, {"q7": {"answer": "inc-0001"}}) == (False, 0.0, None)


# --- the cost model -----------------------------------------------------------


def test_cost_model_reproduces_a_known_billing():
    """Pinned against a real result payload: the price table must stay right."""
    usage = {
        "input_tokens": 2,
        "output_tokens": 4,
        "cache_read_input_tokens": 21692,
        "cache_creation": {"ephemeral_1h_input_tokens": 4843, "ephemeral_5m_input_tokens": 0},
    }
    out = costs(usage)
    assert out["cost_billed_usd"] == pytest.approx(0.0356316, rel=1e-4)
    assert out["new_tokens_ingested"] == 4845
    assert out["cumulative_prompt_tokens"] == 26537
    # Cache-neutral prices every input token as fresh, so it must exceed the billed figure.
    assert out["cost_cache_neutral_usd"] > out["cost_billed_usd"]


def test_cost_model_falls_back_to_the_flat_cache_creation_field():
    """An untyped cache-creation count is priced at the cheaper TTL, never the dearer one."""
    out = costs({"input_tokens": 10, "output_tokens": 0, "cache_creation_input_tokens": 100})
    assert out["new_tokens_ingested"] == 110
    expected = (10 * 3.00 + 100 * 3.75) / 1e6
    assert out["cost_billed_usd"] == pytest.approx(expected)


# --- integrity checks ---------------------------------------------------------


class _Arm:
    def __init__(self, readb_on_path):
        self.readb_on_path = readb_on_path


def test_leak_check_only_fires_for_readb_free_arms():
    tools = [{"name": "Bash", "input": {"command": "grep -c foo corpus/*.md"}}]
    assert integrity(_Arm(False), tools, {}, "nothing here")["leak_baseline_readb"] is False
    assert integrity(_Arm(False), tools, {}, "ran readb query")["leak_baseline_readb"] is True
    assert integrity(_Arm(True), tools, {}, "ran readb query")["leak_baseline_readb"] is False


def test_compaction_is_not_triggered_by_the_slash_command_list():
    """The bug this replaced flagged all 144 runs by matching a command name."""
    init = json.dumps({"commands": ["autocompact", "clear", "compact", "config"]})
    assert integrity(_Arm(True), [], {}, init)["compacted"] is False
    assert integrity(_Arm(True), [], {}, '{"subtype":"compact_boundary"}')["compacted"] is True


def test_readb_invocations_counted_from_bash_only():
    tools = [
        {"name": "Bash", "input": {"command": "readb query 'SELECT 1' --bundle corpus"}},
        {"name": "Bash", "input": {"command": "readb schema --bundle corpus"}},
        {"name": "Read", "input": {"file_path": "readb-notes.md"}},
    ]
    checks = integrity(_Arm(True), tools, {}, "")
    assert checks["readb_invocations"] == 2
    assert checks["supported"] is True


def test_an_answer_with_no_tool_call_is_unsupported():
    assert integrity(_Arm(True), [], {}, "")["supported"] is False


# --- the corpus ---------------------------------------------------------------


def test_ground_truth_survives_the_independent_cross_check(tmp_path):
    """`write` recomputes every headline answer by reading the files back with PyYAML."""
    concepts, truth = generate(120, seed=7)
    write(tmp_path / "kb", tmp_path / "truth.json", concepts, truth, malformed=5, seed=7)
    written = json.loads((tmp_path / "truth.json").read_text())
    assert written["q10"]["answer"] == written["counts"]["Service"] + 5
    assert not (tmp_path / "kb" / "ground_truth.json").exists(), (
        "answers must not sit in the bundle"
    )


def test_the_needle_appears_exactly_once(tmp_path):
    concepts, truth = generate(120, seed=7)
    write(tmp_path / "kb", tmp_path / "truth.json", concepts, truth)
    needle = json.loads((tmp_path / "truth.json").read_text())["q7"]
    hits = [p for p in (tmp_path / "kb").rglob("*.md") if needle["phrase"] in p.read_text()]
    assert [p.stem for p in hits] == [needle["answer"]]


def test_the_index_leaks_no_answer(tmp_path):
    concepts, truth = generate(120, seed=7)
    write(tmp_path / "kb", tmp_path / "truth.json", concepts, truth)
    index = (tmp_path / "kb" / "index.md").read_text()
    assert "type:" not in index, "a typed index makes the rollup question test OKF trivia"
    assert "180" not in index


# --- the analyzer -------------------------------------------------------------
# This is the code that turns records into published numbers. The exclusion predicate in
# particular decides whether a retracted batch reaches a table.

import analyze  # noqa: E402


def _rec(arm, question, cost, **extra):
    rec = {
        "arm": arm,
        "question": question,
        "repeat": 1,
        "shape": "s",
        "favours": "sql",
        "correct": True,
        "partial_credit": 1.0,
        "cost_billed_usd": cost,
        "cost_cache_neutral_usd": cost * 3,
        "new_tokens_ingested": 1000,
        "wall_s": 1.0,
        "output_tokens": 100,
        "num_turns": 2,
        "cumulative_prompt_tokens": 10_000,
    }
    rec.update(extra)
    return rec


def test_retracted_records_are_excluded():
    assert analyze.invalid(_rec("a", "q1", 1.0, retracted="environment defect")) == (
        "environment defect"
    )
    assert analyze.invalid(_rec("a", "q1", 1.0)) is None


def test_other_exclusion_reasons():
    assert analyze.invalid(_rec("a", "q1", 1.0, harness_error="timeout")) == "timeout"
    assert "leaked" in analyze.invalid(_rec("a", "q1", 1.0, leak_baseline_readb=True))
    assert "permission" in analyze.invalid(_rec("a", "q1", 1.0, permission_denials=["Bash"]))
    assert analyze.invalid(_rec("a", "q1", 1.0, is_error=True)) is not None


def test_paired_ratio_is_a_median_over_questions_not_over_runs():
    """One question dominated by an outlier must not carry the arm-level ratio."""
    rows = [
        _rec("baseline", "q1", 1.0),
        _rec("arm", "q1", 0.5),
        _rec("baseline", "q2", 1.0),
        _rec("arm", "q2", 0.5),
        _rec("baseline", "q3", 1.0),
        _rec("arm", "q3", 100.0),
    ]
    ratios = []
    for q in ("q1", "q2", "q3"):
        b = analyze.med(
            [r["cost_billed_usd"] for r in rows if r["arm"] == "baseline" and r["question"] == q]
        )
        v = analyze.med(
            [r["cost_billed_usd"] for r in rows if r["arm"] == "arm" and r["question"] == q]
        )
        ratios.append(v / b)
    assert analyze.med(ratios) == 0.5


def test_bootstrap_interval_brackets_the_median_and_is_seed_stable():
    ratios = [0.5, 0.6, 0.7, 0.8, 0.9]
    lo, hi = analyze.bootstrap_ci(ratios)
    assert lo <= 0.7 <= hi
    assert analyze.bootstrap_ci(ratios) == (lo, hi)


def test_bootstrap_declines_to_invent_an_interval_from_two_points():
    lo, hi = analyze.bootstrap_ci([0.5, 0.6])
    assert lo != lo and hi != hi  # NaN


def test_median_of_nothing_is_nan_not_a_crash():
    assert analyze.med([]) != analyze.med([])
    assert analyze.fmt(float("nan"), 2) == "—"
