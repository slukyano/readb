"""Tests for the benchmark harness itself.

The scorer decides what gets published, the cost model turns token counts into a number a
reader will quote, and the corpus generators decide what "correct" means. All three are
worth pinning. Run with `uv run pytest benchmarks`; the package's own suite does not
collect this directory, and the sdist does not ship it.
"""

from __future__ import annotations

import json
import pathlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import analyze  # noqa: E402
from battery import (  # noqa: E402
    BY_ID,
    OPS_QUESTIONS,
    QUESTIONS,
    STRATA,
    extract_answer,
    f1,
    placeholders,
    render,
    score,
)
from generate_corpus import generate, rig_malformed_teams, write  # noqa: E402
from run_benchmark import (  # noqa: E402
    classify_tool_choice,
    costs,
    integrity,
    parse_stream,
    prices_for,
)

SONNET = prices_for("claude-sonnet-5")

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


# --- v2's new scoring ---------------------------------------------------------


def test_the_none_convention_means_an_empty_set():
    """Two v2 questions have an empty truth; v1 had no way to express one."""
    question = BY_ID["q16"]
    truth = {"q16": {"team": "x", "tier": 1, "status": "y", "answer": []}}
    for raw in ("none", "None", "`none`"):
        exact, partial, parsed = score(question, raw, truth)
        assert exact and partial == 1.0 and parsed == []
    # An agent that invents a name has not answered `none`.
    assert not score(question, "svc-0001", truth)[0]


def test_none_is_not_a_free_pass_when_something_does_match():
    question = BY_ID["q3"]
    truth = {"q3": {"team": "x", "answer": ["svc-0001"]}}
    assert not score(question, "none", truth)[0]


def test_record_scoring_survives_the_defect_that_broke_v1_q6():
    """v1's template asked for `team-name=<count>` and three runs answered `team-name`."""
    question = BY_ID["q6"]
    truth = {"q6": {"team": "platform", "count": 31}}
    assert score(question, "team=platform, count=31", truth)[0]
    # Prose around a value is not a wrong answer; a wrong value is.
    assert score(question, "team=platform, count=31 services", truth)[0]
    assert not score(question, "team=identity, count=31", truth)[0]
    # The literal template, transcribed rather than filled in, must fail.
    exact, partial, _ = score(question, "team=<the team's name>, count=<the number>", truth)
    assert not exact and partial == 0.0


def test_record_scoring_needs_every_field():
    question = BY_ID["q6"]
    truth = {"q6": {"team": "platform", "count": 31}}
    exact, partial, _ = score(question, "team=platform", truth)
    assert not exact and partial == 0.5


def test_mapping_str_scores_by_containment_but_demands_the_right_keys():
    question = BY_ID["b2"]
    truth = {"b2": {"answer": {"001-a": "sqlite", "002-b": "worker-queue"}}}
    assert score(question, "001-a=sqlite, 002-b=worker-queue", truth)[0]
    # The value is an extraction from prose, so a verbose one found the same token.
    assert score(question, "001-a=sqlite, 002-b=worker-queue (a background queue)", truth)[0]
    # A task that is not in scope is a different answer, not a verbose one.
    assert not score(question, "001-a=sqlite, 002-b=worker-queue, 003-c=none", truth)[0]
    assert not score(question, "001-a=sqlite", truth)[0]


def test_mapping_str_accepts_none_only_for_an_empty_truth():
    question = BY_ID["b6"]
    assert score(question, "none", {"b6": {"answer": {}}})[0]
    assert not score(question, "none", {"b6": {"answer": {"001-a": "obsolete"}}})[0]


# --- the battery's own shape --------------------------------------------------


def test_the_battery_is_the_pre_registered_twenty_six():
    assert len(QUESTIONS) == 26
    assert len({q.id for q in QUESTIONS}) == 26


def test_strata_partition_the_battery_in_the_declared_sizes():
    counts = {s: sum(1 for q in QUESTIONS if q.stratum == s) for s in STRATA}
    assert counts == {"join": 8, "scan": 4, "retrieval": 3, "hazard": 3, "backlog": 8}
    assert all(q.stratum in STRATA for q in QUESTIONS)


def test_every_question_declares_a_tool_an_expert_would_reach_for():
    # Recorded so tool choice can be reported as a matrix. It is never a reason to edit a
    # prompt, which is why it lives on the question rather than in the harness.
    assert all(q.expert_tool in ("readb", "shell", "read") for q in QUESTIONS)
    # The hazard questions count files a permissive loader skips, which readb cannot do.
    assert all(q.expert_tool == "shell" for q in QUESTIONS if q.stratum == "hazard")


def test_thirteen_ops_questions_carry_v1_wording(tmp_path):
    carried = {f"q{n}" for n in range(1, 13)} | {"q10b"}
    assert carried <= {q.id for q in OPS_QUESTIONS}
    assert len(OPS_QUESTIONS) == 18


def test_every_prompt_renders_against_its_corpus_truth(tmp_path):
    """A `{placeholder}` reaching an agent is a question about a concept that does not exist."""
    import generate_backlog_corpus as backlog

    concepts, ops_truth = generate(300, seed=7)
    write(tmp_path / "ops", tmp_path / "ops.json", concepts, ops_truth, malformed=12, seed=7)
    ops_truth = json.loads((tmp_path / "ops.json").read_text())

    docs, backlog_truth = backlog.generate(120, 8, seed=7)
    backlog.write(tmp_path / "bl", tmp_path / "bl.json", docs, backlog_truth, seed=7)
    backlog_truth = json.loads((tmp_path / "bl.json").read_text())

    for question in QUESTIONS:
        truth = backlog_truth if question.corpus == "backlog" else ops_truth
        rendered = render(question, truth)
        assert "{" not in rendered and "}" not in rendered, question.id


def test_placeholders_of_one_corpus_do_not_leak_into_the_other():
    ops = {
        "q3": {"team": "t"},
        "q5": {"service": "s"},
        "q9": {"runbook": "r"},
        "q16": {"team": "t", "tier": 1, "status": "ga"},
    }
    filled = placeholders(ops)
    assert "team" in filled
    assert "finished_sprint" not in filled, "a backlog placeholder must not appear for ops truth"
    assert "team" not in placeholders(
        {"b3": {"sprint": "s"}, "b4": {"phrase": "p"}, "b5": {"task": "t"}, "b6": {"year": "2025"}}
    )


# --- the cost model -----------------------------------------------------------


def test_cost_model_reproduces_a_known_billing():
    """Pinned against a real result payload, repriced at Sonnet 5's current rates."""
    usage = {
        "input_tokens": 2,
        "output_tokens": 4,
        "cache_read_input_tokens": 21692,
        "cache_creation": {"ephemeral_1h_input_tokens": 4843, "ephemeral_5m_input_tokens": 0},
    }
    out = costs(usage, SONNET)
    expected = (2 * 2.00 + 4 * 10.00 + 21692 * 0.20 + 4843 * 4.00) / 1e6
    # `costs` rounds to six decimals, which is a hundredth of a cent.
    assert out["cost_billed_usd"] == pytest.approx(expected, abs=1e-6)
    assert out["new_tokens_ingested"] == 4845
    assert out["cumulative_prompt_tokens"] == 26537
    # Cache-neutral prices every input token as fresh, so it must exceed the billed figure.
    assert out["cost_cache_neutral_usd"] > out["cost_billed_usd"]


def test_cost_model_falls_back_to_the_flat_cache_creation_field():
    """An untyped cache-creation count is priced at the cheaper TTL, never the dearer one."""
    out = costs(
        {"input_tokens": 10, "output_tokens": 0, "cache_creation_input_tokens": 100}, SONNET
    )
    assert out["new_tokens_ingested"] == 110
    assert out["cost_billed_usd"] == pytest.approx((10 * 2.00 + 100 * 2.50) / 1e6)


def test_each_model_is_priced_on_its_own_table():
    """One table for both models would misprice a whole block by a factor of two."""
    usage = {"input_tokens": 1000, "output_tokens": 1000}
    sonnet = costs(usage, prices_for("claude-sonnet-5"))["cost_billed_usd"]
    haiku = costs(usage, prices_for("claude-haiku-4-5"))["cost_billed_usd"]
    assert sonnet == pytest.approx(2 * haiku)


def test_an_unpriced_model_stops_the_run_instead_of_guessing():
    with pytest.raises(SystemExit, match="no price table"):
        prices_for("claude-not-a-model")


def test_cache_rates_are_the_published_multipliers():
    for model in ("claude-sonnet-5", "claude-haiku-4-5"):
        prices = prices_for(model)
        base = prices["input"]
        assert prices["cache_write_5m"] == pytest.approx(1.25 * base)
        assert prices["cache_write_1h"] == pytest.approx(2.0 * base)
        assert prices["cache_read"] == pytest.approx(0.1 * base)


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


def test_failed_calls_are_attributed_to_the_command_that_failed():
    """The retry rate the model comparison needs; v1 read only the calls, never the results."""
    tools = [
        {"id": "a", "name": "Bash", "input": {"command": "readb query 'SELECT nope'"}},
        {"id": "b", "name": "Bash", "input": {"command": "rg -l foo corpus"}},
        {"id": "c", "name": "Bash", "input": {"command": "readb schema --bundle corpus"}},
    ]
    results = [
        {"id": "a", "is_error": True, "text": "Parser Error"},
        {"id": "b", "is_error": True, "text": "no matches"},
        {"id": "c", "is_error": False, "text": "Tables"},
    ]
    checks = integrity(_Arm(True), tools, {}, "", results)
    assert checks["failed_tool_results"] == 2
    assert checks["failed_readb_calls"] == 1


def test_the_skip_warning_is_seen_only_when_it_reaches_the_transcript():
    tools = [{"id": "a", "name": "Bash", "input": {"command": "readb query 'SELECT 1'"}}]
    quiet = [{"id": "a", "is_error": False, "text": "180"}]
    warned = [
        {"id": "a", "is_error": False, "text": "skipping services/x.md: malformed YAML frontmatter"}
    ]
    assert integrity(_Arm(True), tools, {}, "", quiet)["saw_skip_warning"] is False
    assert integrity(_Arm(True), tools, {}, "", warned)["saw_skip_warning"] is True


def test_parse_stream_collects_results_alongside_calls():
    lines = [
        json.dumps(
            {"message": {"content": [{"type": "tool_use", "id": "a", "name": "Bash", "input": {}}]}}
        ),
        json.dumps(
            {
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "a",
                            "is_error": True,
                            "content": [{"type": "text", "text": "boom"}],
                        }
                    ]
                }
            }
        ),
        json.dumps({"type": "result", "result": "ANSWER: 1"}),
    ]
    result, tools, results = parse_stream(lines)
    assert result["result"] == "ANSWER: 1"
    assert [t["id"] for t in tools] == ["a"]
    assert results == [{"id": "a", "is_error": True, "text": "boom"}]


# --- tool-choice classification -----------------------------------------------


def test_tool_choice_gives_readb_the_run_outright():
    tools = [
        {"name": "Read", "input": {"file_path": "a.md"}},
        {"name": "Read", "input": {"file_path": "b.md"}},
        {"name": "Bash", "input": {"command": "readb query 'SELECT 1'"}},
    ]
    assert classify_tool_choice(tools) == "readb"


def test_tool_choice_separates_searching_from_reading():
    assert classify_tool_choice([{"name": "Bash", "input": {"command": "rg -l x corpus"}}]) == (
        "shell"
    )
    assert classify_tool_choice([{"name": "Read", "input": {"file_path": "a.md"}}]) == "read"
    assert classify_tool_choice([{"name": "Grep", "input": {"pattern": "x"}}]) == "shell"
    # A tie goes to searching: calling it a read would flatter the file-reading arms.
    tools = [{"name": "Grep", "input": {}}, {"name": "Read", "input": {}}]
    assert classify_tool_choice(tools) == "shell"


def test_tool_choice_of_a_run_that_used_nothing():
    assert classify_tool_choice([]) == "none"
    assert classify_tool_choice([{"name": "TodoWrite", "input": {}}]) == "other"


# --- the arms -----------------------------------------------------------------


def test_shim_grants_exactly_what_it_is_asked_for(tmp_path):
    """A shim must not become a back door onto a whole package manager's bin."""
    from run_benchmark import SHARED_TOOLS, UV_TOOLS, shim

    uv = pathlib.Path(shim(tmp_path, "uv", UV_TOOLS))
    assert uv.parent == tmp_path
    assert {p.name for p in uv.iterdir()} <= set(UV_TOOLS)

    tools = pathlib.Path(shim(tmp_path, "tools", SHARED_TOOLS))
    assert {p.name for p in tools.iterdir()} <= set(SHARED_TOOLS)
    # The readb-free arms must never be able to fetch readb through a package manager.
    assert not (set(SHARED_TOOLS) & set(UV_TOOLS))


def test_every_arm_is_told_about_the_tools_every_arm_has():
    """Availability without awareness would measure what an arm was told, not what it had."""
    from run_benchmark import ARMS, SHARED_TOOLS, TASK_INTRO

    for tool in ("rg", "jq", "yq"):
        assert tool in TASK_INTRO, f"{tool} is on every PATH but named to no arm"
    for name, arm in ARMS.items():
        if name == "shell-coached":
            continue  # its whole treatment is a worked recipe using them
        for tool in SHARED_TOOLS:
            assert tool not in arm.preamble, f"{name} preamble names {tool}"


def test_only_the_skill_arm_carries_uv():
    """Every other arm's preamble shows the bare binary, so none needs uvx."""
    from run_benchmark import ARMS

    assert ARMS["readb-skill"].uv_on_path is True
    assert not any(a.uv_on_path for name, a in ARMS.items() if name != "readb-skill")


def test_the_nudge_is_an_arm_and_never_an_edit_to_the_base_arm():
    """Folding routing guidance into `readb-bare` would silently redefine what v1 measured."""
    from run_benchmark import ARMS, NUDGE, PREAMBLE_READB

    assert NUDGE not in ARMS["readb-bare"].preamble
    assert ARMS["readb-bare"].preamble == PREAMBLE_READB
    assert ARMS["readb-nudged"].preamble == PREAMBLE_READB + NUDGE
    # The nudge routes; it must not answer. Naming a table or a column would leak the schema
    # to one arm and turn the contrast into a hint.
    for leak in ("SELECT", "FROM", "service", "task", "GROUP BY"):
        assert leak not in NUDGE, f"the nudge names {leak!r}, which is coaching, not routing"


def test_every_corpus_has_a_coached_recipe():
    from battery import QUESTIONS as ALL
    from run_benchmark import RECIPES

    for question in ALL:
        assert question.corpus in RECIPES, question.id
    assert "ops-tidy" in RECIPES, "the sweep redirects onto it, so it needs one too"


@pytest.mark.parametrize("corpus", ["ops", "backlog"])
def test_every_coached_command_actually_runs_and_finds_what_is_there(tmp_path, corpus):
    """A recipe that runs and under-counts makes the competitor arm a straw man.

    v1's corpus was rendered in one style, so `rg '^tier: 1'` found everything. v2's is
    written in mixed styles, and a naive pattern silently misses every quoted value — which
    would hand readb a win it did not earn.
    """
    import os
    import shutil as _shutil
    import subprocess

    import generate_backlog_corpus as backlog
    from run_benchmark import BASE_PATH, RECIPES, SHARED_TOOLS, recipe_placeholders, shim

    if [t for t in ("rg", "yq") if not _shutil.which(t)]:
        pytest.skip("the recipe needs rg and yq")

    root = tmp_path / "stage"
    root.mkdir()
    if corpus == "ops":
        concepts, truth = generate(300, seed=7)
        write(root / "corpus", tmp_path / "truth.json", concepts, truth, seed=7, messy=True)
        expected = len(json.loads((tmp_path / "truth.json").read_text())["q15"]["answer"])
    else:
        docs, truth = backlog.generate(120, 8, seed=7)
        backlog.write(root / "corpus", tmp_path / "truth.json", docs, truth, seed=7, messy=True)
        expected = json.loads((tmp_path / "truth.json").read_text())["counts"]["Draft"]
    truth = json.loads((tmp_path / "truth.json").read_text())

    env = {
        "PATH": f"{shim(tmp_path, 'tools', SHARED_TOOLS)}:{BASE_PATH}",
        "HOME": os.environ["HOME"],
    }
    values = recipe_placeholders(truth)
    for _, template in RECIPES[corpus]:
        command = template.format(**values)
        done = subprocess.run(
            command, shell=True, cwd=root, env=env, capture_output=True, text=True
        )
        assert done.returncode == 0, f"coached command failed: {command}\n{done.stderr}"
        assert done.stdout.strip(), f"coached command produced nothing: {command}"

    listing = RECIPES[corpus][0][1].format(**values)
    done = subprocess.run(listing, shell=True, cwd=root, env=env, capture_output=True, text=True)
    found = len([line for line in done.stdout.splitlines() if line.strip()])
    assert found == expected, f"the coached listing found {found} of {expected}: {listing}"


# --- the ops corpus -----------------------------------------------------------


def test_ground_truth_survives_the_independent_cross_check(tmp_path):
    """`write` recomputes every headline answer by reading the files back with PyYAML."""
    concepts, truth = generate(300, seed=7)
    write(tmp_path / "kb", tmp_path / "truth.json", concepts, truth, malformed=12, seed=7)
    written = json.loads((tmp_path / "truth.json").read_text())
    assert written["q10"]["answer"] == written["counts"]["Service"] + 12
    assert not (tmp_path / "kb" / "ground_truth.json").exists(), (
        "answers must not sit in the bundle"
    )


def test_the_needle_appears_exactly_once(tmp_path):
    concepts, truth = generate(300, seed=7)
    write(tmp_path / "kb", tmp_path / "truth.json", concepts, truth)
    needle = json.loads((tmp_path / "truth.json").read_text())["q7"]
    hits = [p for p in (tmp_path / "kb").rglob("*.md") if needle["phrase"] in p.read_text()]
    assert [p.stem for p in hits] == [needle["answer"]]


def test_the_index_leaks_no_answer(tmp_path):
    concepts, truth = generate(300, seed=7)
    write(tmp_path / "kb", tmp_path / "truth.json", concepts, truth)
    index = (tmp_path / "kb" / "index.md").read_text()
    assert "type:" not in index, "a typed index makes the rollup question test OKF trivia"


def test_messiness_changes_the_bytes_and_not_the_meaning(tmp_path):
    """The whole basis of the messy/tidy sweep: one corpus, two renderings, one truth."""
    import yaml

    concepts, truth_messy = generate(300, seed=7)
    write(tmp_path / "messy", tmp_path / "m.json", concepts, truth_messy, seed=7, messy=True)
    concepts, truth_tidy = generate(300, seed=7)
    write(tmp_path / "tidy", tmp_path / "t.json", concepts, truth_tidy, seed=7, messy=False)

    messy = json.loads((tmp_path / "m.json").read_text())
    tidy = json.loads((tmp_path / "t.json").read_text())
    messy.pop("_meta"), tidy.pop("_meta")
    assert messy == tidy, "the two renderings must not have different answers"

    differing = 0
    for path in sorted((tmp_path / "messy").rglob("*.md")):
        other = tmp_path / "tidy" / path.relative_to(tmp_path / "messy")
        if path.read_text() != other.read_text():
            differing += 1
        left = yaml.safe_load(path.read_text().split("---\n")[1])
        right = yaml.safe_load(other.read_text().split("---\n")[1])
        # An unknown extra key is allowed; a changed value is not.
        for key, value in right.items():
            assert left[key] == value, f"{path.name}: messiness changed {key}"
    assert differing > 100, "messiness that changes almost no file is not messiness"


def test_the_type_line_keeps_its_canonical_rendering(tmp_path):
    """Q10, carried from v1 verbatim, asks for files containing a `type: Service` line."""
    import re

    concepts, truth = generate(300, seed=7)
    write(tmp_path / "kb", tmp_path / "truth.json", concepts, truth, seed=7, messy=True)
    for path in (tmp_path / "kb").rglob("*.md"):
        if path.name == "index.md":
            continue
        assert re.search(r"^type: \S", path.read_text(), re.MULTILINE), path.name


def test_the_malformed_files_flip_which_team_owns_the_most(tmp_path):
    """Without a flip, the un-warned trap traps nobody: skipping the files still answers right."""
    concepts, truth = generate(300, seed=7)
    write(tmp_path / "kb", tmp_path / "truth.json", concepts, truth, malformed=12, seed=7)
    written = json.loads((tmp_path / "truth.json").read_text())
    assert written["q18"]["team"] != written["q18"]["naive_team"]
    assert written["q18"]["count"] > written["q18"]["naive_count"]


def test_a_flip_that_cannot_be_rigged_is_an_error_not_a_silent_pass():
    services = [{"team": "a"} for _ in range(50)] + [{"team": "b"}]
    with pytest.raises(ValueError, match="cannot flip"):
        rig_malformed_teams(3, services)


def test_the_zero_result_question_is_empty_by_combination_not_by_typo(tmp_path):
    concepts, truth = generate(300, seed=7)
    write(tmp_path / "kb", tmp_path / "truth.json", concepts, truth, seed=7)
    empty = json.loads((tmp_path / "truth.json").read_text())["q16"]
    services = [c.record for c in concepts if c.subdir == "services"]
    assert empty["answer"] == []
    assert any(s["team"] == empty["team"] for s in services)
    assert any(s["tier"] == empty["tier"] for s in services)
    assert any(s["status"] == empty["status"] for s in services)


# --- the backlog corpus -------------------------------------------------------


def test_backlog_ground_truth_survives_its_read_back(tmp_path):
    import generate_backlog_corpus as backlog

    docs, truth = backlog.generate(120, 8, seed=7)
    backlog.write(tmp_path / "bl", tmp_path / "truth.json", docs, truth, seed=7)
    written = json.loads((tmp_path / "truth.json").read_text())
    assert written["counts"]["Task"] == 120
    assert written["b2"]["answer"], "the active sprint must have a scope"


def test_the_task_numbers_have_gaps(tmp_path):
    """Counting the files and asking for the next free number must give different answers."""
    import generate_backlog_corpus as backlog

    docs, truth = backlog.generate(120, 8, seed=7)
    backlog.write(tmp_path / "bl", tmp_path / "truth.json", docs, truth, seed=7)
    written = json.loads((tmp_path / "truth.json").read_text())
    assert written["b7"]["answer"] > written["b7"]["file_count"] + 1


def test_the_active_sprint_carries_a_task_with_no_design(tmp_path):
    """So Q b2's answer exercises the `none` convention rather than avoiding it."""
    import generate_backlog_corpus as backlog

    docs, truth = backlog.generate(120, 8, seed=7)
    backlog.write(tmp_path / "bl", tmp_path / "truth.json", docs, truth, seed=7)
    written = json.loads((tmp_path / "truth.json").read_text())
    assert "none" in written["b2"]["answer"].values()


def test_the_backlog_corpus_names_an_invented_product(tmp_path):
    """A public write-up must not be able to read as commentary on a real project."""
    import generate_backlog_corpus as backlog

    docs, truth = backlog.generate(120, 8, seed=7)
    backlog.write(tmp_path / "bl", tmp_path / "truth.json", docs, truth, seed=7)
    written = json.loads((tmp_path / "truth.json").read_text())
    assert "invented" in written["_meta"]["product"]
    # And nothing of readb's own process may appear in it.
    for path in (tmp_path / "bl").rglob("*.md"):
        text = path.read_text().lower()
        for term in ("readb", "okf", "maintainer"):
            assert term not in text, f"{path.name} mentions {term!r}"


# --- the analyzer -------------------------------------------------------------


def _rec(arm, question, cost, **extra):
    rec = {
        "arm": arm,
        "question": question,
        "repeat": 1,
        "shape": "s",
        "favours": "sql",
        "stratum": "join",
        "expert_tool": "readb",
        "model": "claude-sonnet-5",
        "correct": True,
        "partial_credit": 1.0,
        "cost_billed_usd": cost,
        "cost_cache_neutral_usd": cost * 3,
        "new_tokens_ingested": 1000,
        "wall_s": 1.0,
        "output_tokens": 100,
        "num_turns": 2,
        "cumulative_prompt_tokens": 10_000,
        "readb_invocations": 0,
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
    base = analyze.question_medians(rows, "baseline", None, "cost_billed_usd")
    arm = analyze.question_medians(rows, "arm", None, "cost_billed_usd")
    assert analyze.med([arm[q] / base[q] for q in sorted(base)]) == 0.5


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


# --- the pre-registered test --------------------------------------------------


def test_wilcoxon_matches_the_textbook_exact_values():
    # Five differences, all positive: only the all-plus and all-minus assignments are as
    # extreme, so the two-sided exact p is 2/32.
    assert analyze.wilcoxon([1, 2, 3, 4, 5])["p"] == pytest.approx(0.0625)
    # One negative at rank 2 gives W+ = 13, W- = 2; the textbook two-sided p is 0.1875.
    assert analyze.wilcoxon([1, -2, 3, 4, 5])["p"] == pytest.approx(0.1875)


def test_wilcoxon_drops_zero_differences_and_declines_below_five_pairs():
    assert analyze.wilcoxon([0, 0, 1, 2, 3]) is None  # three non-zero pairs
    result = analyze.wilcoxon([0, 1, 2, 3, 4, 5])
    assert result["n"] == 5


def test_wilcoxon_handles_ties_in_the_absolute_difference():
    result = analyze.wilcoxon([0.1, 0.1, 0.1, -0.1, 0.1, 0.1])
    assert result["n"] == 6
    assert 0 < result["p"] < 1


def test_average_ranks():
    assert analyze._average_ranks([1, 1, 2, 3, 3, 3]) == [1.5, 1.5, 3.0, 5.0, 5.0, 5.0]


def test_holm_adjustment_is_monotone_and_correct():
    assert analyze.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert analyze.holm([0.5, 0.5, 0.5]) == pytest.approx([1.0, 1.0, 1.0])


def test_the_three_endpoints_are_the_pre_registered_ones():
    assert [e["id"] for e in analyze.ENDPOINTS] == ["E1", "E2", "E3"]
    for endpoint in analyze.ENDPOINTS:
        assert endpoint["against"] == "shell-coached", "the honest competitor, never the baseline"
        assert endpoint["arm"] == "readb-bare", "never the nudged arm — that contrast is its own"
    assert [e["measure"] for e in analyze.ENDPOINTS] == ["cost", "cost", "exact"]
    assert analyze.ENDPOINTS[2]["model"] == "claude-haiku-4-5"


def test_an_endpoint_reports_the_ratio_and_a_p_value():
    rows = []
    for i in range(8):
        rows.append(_rec("shell-coached", f"q{i}", 1.0))
        rows.append(_rec("readb-bare", f"q{i}", 0.6))
    result = analyze.run_endpoint(analyze.ENDPOINTS[0], rows, {f"q{i}": "join" for i in range(8)})
    assert result["questions"] == 8
    assert result["effect"] == "0.60x"
    assert result["test"]["p"] == pytest.approx(2 / 2**8)


def test_a_workroot_named_after_the_tool_is_refused(tmp_path):
    """The agent's cwd reaches its system prompt, so the path itself can contaminate an arm."""
    from run_benchmark import assert_workroot_is_neutral

    assert_workroot_is_neutral(tmp_path / "kbbench")
    with pytest.raises(SystemExit, match="contains the tool's name"):
        assert_workroot_is_neutral(tmp_path / "personal-readb" / "scratch")


def test_resume_keys_on_the_corpus_so_a_sweep_is_not_half_skipped(tmp_path):
    """The same question against a different rendering is a different cell."""
    from run_benchmark import done_cells

    results = tmp_path / "r.jsonl"
    results.write_text(
        json.dumps(
            {
                "arm": "readb-bare",
                "question": "q2",
                "model": "claude-sonnet-5",
                "corpus": "ops",
                "repeat": 1,
            }
        )
        + "\n"
    )
    cells = done_cells(results)
    assert ("readb-bare", "q2", "claude-sonnet-5", "ops", 1) in cells
    assert ("readb-bare", "q2", "claude-sonnet-5", "ops-tidy", 1) not in cells


def test_the_floor_is_the_median_of_its_repeats(tmp_path, capsys):
    """v1's floor was a single run, so taking the last record was harmless. v2's is three."""
    results = tmp_path / "r.jsonl"
    floor = tmp_path / "f.jsonl"
    rows = []
    for question in ("q1", "q2", "q3", "q4", "q5"):
        rows.append(_rec("baseline", question, 1.0))
        rows.append(_rec("readb-bare", question, 0.6))
    results.write_text("".join(json.dumps(r) + "\n" for r in rows))
    # A wild last repeat must not become the floor.
    floor.write_text(
        "".join(
            json.dumps(_rec(arm, "q1", cost)) + "\n"
            for arm in ("baseline", "readb-bare")
            for cost in (0.1, 0.1, 9.9)
        )
    )
    sys.argv = [
        "analyze",
        "--results",
        str(results),
        "--floor",
        str(floor),
        "--skip-endpoints",
    ]
    analyze.main()
    out = capsys.readouterr().out
    assert "Overhead-subtracted" in out
    # median floor 0.1: (0.6-0.1)/(1.0-0.1) = 0.56. The last-record floor of 9.9 would have
    # made both sides negative and printed a dash instead.
    assert "0.56x" in out
