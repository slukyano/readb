"""The question battery, its answer protocol, and the scorer.

**v2: twenty-six questions across five pre-registered strata.** Eighteen run on the
platform knowledge base (`ops`, and its malformed and tidy variants), eight on the
task-tracker bundle (`backlog`).

Thirteen come from v1 unchanged in wording — including `q2`, the group-by readb *lost*,
and `q10b`, promoted out of the post-hoc probes into the battery proper. Only `q6`'s
answer template changed, because v1's template asked for a literal the model kept
transcribing (see `record` below); its question text is untouched.

Five are new on the ops corpora: a body-and-frontmatter hybrid neither half answers, an
output-heavy enumeration where a turn advantage should be diluted by the cost of writing
the answer out, a filter with no matches, a question resting on a field that does not
exist, and the malformed-file trap **with no warning in the prompt** — v1 warned the agent
in every arm, so it measured instruction-following rather than the hazard.

Eight are new on the backlog corpus, each modelled on a chore a person actually performs
against a task tracker. Two of them need a concept's *body*: which approach a task's design
names, and why a task was dropped. Both ask for a **checkable extraction**, never a
summary — free prose cannot be scored without an LLM judge, which would add a second model
as a noise source and a standing temptation to tune.

Strata partition the battery and are declared here, before any measured run:

| stratum | what it is | n |
| --- | --- | --- |
| `join` | the answer relates more than one record, or more than one source of fact | 8 |
| `scan` | one type, one pass — a rollup, a group-by, a plain filter | 4 |
| `retrieval` | finding one document among many by what it says | 3 |
| `hazard` | counting things a permissive loader skips | 3 |
| `backlog` | every question on the task-tracker bundle | 8 |

Everything in this file — the question text, the strata, the declared expert tool, and the
normalizer — is **pre-registered**: fixed before the first measured run, and not adjusted
after seeing results.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

ANSWER_RE = re.compile(r"^\s*ANSWER:\s*(.*)$", re.MULTILINE | re.IGNORECASE)

# The token that means "nothing matched". v1 had no convention for it, so an empty answer
# was indistinguishable from a missing one and no question could safely have an empty
# truth. Two of v2's questions do.
NONE_TOKEN = "none"


@dataclass(frozen=True)
class Question:
    id: str
    shape: str
    prompt: str
    kind: str  # set | number | mapping | mapping_str | name | record
    truth: Callable[[dict], object]
    favours: str  # sql | files | neutral — declared before the runs, not after
    stratum: str  # join | scan | retrieval | hazard | backlog
    expert_tool: str  # readb | shell | read — what a competent operator would reach for
    corpus: str = "ops"


# --- answer protocol ----------------------------------------------------------

_NONE_RULE = f"\n\nIf nothing matches, the answer is `{NONE_TOKEN}` — write "
_NONE_RULE += f"`ANSWER: {NONE_TOKEN}` and nothing else on that line."


def _fmt_set(what: str) -> str:
    return (
        f"Finish your reply with a single final line in exactly this form, listing every "
        f"{what} separated by commas (order does not matter):\nANSWER: name-1, name-2, name-3"
        + _NONE_RULE
    )


_FMT_NUMBER = "Finish your reply with a single final line in exactly this form:\nANSWER: <number>"
_FMT_NAME = (
    "Finish your reply with a single final line in exactly this form:\nANSWER: <concept-name>"
)
_FMT_MAPPING = (
    "Finish your reply with a single final line in exactly this form, one pair per "
    "category, separated by commas:\nANSWER: category-a=12, category-b=34"
)
# v1's Q6 asked for `ANSWER: team-name=<count>` and three runs answered the literal string
# `team-name`. The fix is not a looser scorer — it is a template whose keys are obviously
# keys and whose values are obviously placeholders.
_FMT_RECORD_TEAM = (
    "Finish your reply with a single final line in exactly this form, keeping the field "
    "names `team` and `count` literally as written:\nANSWER: team=<the team's name>, "
    "count=<the number>"
)
_FMT_RECORD_TASK = (
    "Finish your reply with a single final line in exactly this form, keeping the field "
    "names `status` and `priority` literally as written:\nANSWER: status=<the status>, "
    "priority=<the priority>"
)


def _fmt_mapping_str(key: str, value: str) -> str:
    return (
        f"Finish your reply with a single final line in exactly this form, one pair per "
        f"{key}, separated by commas:\nANSWER: {key}-a={value}-a, {key}-b={value}-b" + _NONE_RULE
    )


_NAME_RULE = "A concept's name is its filename without the `.md` extension."


# --- the ops battery — 18 questions -------------------------------------------

OPS_QUESTIONS: list[Question] = [
    Question(
        id="q1",
        shape="type rollup",
        favours="sql",
        stratum="scan",
        expert_tool="readb",
        prompt=(
            "How many concepts of each `type` are in the knowledge base? Count every concept "
            "of every type.\n\n" + _FMT_MAPPING
        ),
        kind="mapping",
        truth=lambda t: {k.lower(): v for k, v in t["q1"].items()},
    ),
    Question(
        id="q2",
        shape="group-by",
        favours="sql",
        stratum="scan",
        expert_tool="readb",
        prompt=(
            "Among concepts of type `Service`, how many are there in each `status`?\n\n"
            + _FMT_MAPPING
        ),
        kind="mapping",
        truth=lambda t: {k.lower(): v for k, v in t["q2"].items()},
    ),
    Question(
        id="q3",
        shape="filtered listing",
        favours="sql",
        stratum="join",
        expert_tool="readb",
        prompt=(
            "List the names of every `Service` concept owned by the team `{team}` whose `tier` "
            "is 1 and whose `status` is anything other than `ga`. "
            + _NAME_RULE
            + "\n\n"
            + _fmt_set("name")
        ),
        kind="set",
        truth=lambda t: set(t["q3"]["answer"]),
    ),
    Question(
        id="q4",
        shape="cross-reference",
        favours="sql",
        stratum="join",
        expert_tool="readb",
        prompt=(
            "Every `Runbook` concept names the service it covers in its `service` field. List "
            "the names of all `Runbook` concepts whose service is a `Service` concept with "
            "`tier` 1 and `status` `deprecated`. " + _NAME_RULE + "\n\n" + _fmt_set("runbook name")
        ),
        kind="set",
        truth=lambda t: set(t["q4"]),
    ),
    Question(
        id="q5",
        shape="list membership",
        favours="sql",
        stratum="join",
        expert_tool="readb",
        prompt=(
            "Each `Incident` concept lists the services it affected in its `services` field. "
            "List the names of every `Incident` concept whose `services` includes "
            "`{service}`. " + _NAME_RULE + "\n\n" + _fmt_set("incident name")
        ),
        kind="set",
        truth=lambda t: set(t["q5"]["answer"]),
    ),
    Question(
        id="q6",
        shape="extremum",
        favours="sql",
        stratum="join",
        expert_tool="readb",
        prompt=(
            "Which team owns the most `Service` concepts, and how many does it own?\n\n"
            + _FMT_RECORD_TEAM
        ),
        kind="record",
        truth=lambda t: {"team": t["q6"]["team"], "count": t["q6"]["count"]},
    ),
    Question(
        id="q7",
        shape="exact-phrase needle",
        favours="files",
        stratum="retrieval",
        expert_tool="shell",
        prompt=(
            "Exactly one concept's body text contains the phrase "
            '"the circuit breaker tripped during a partial region drain". Which concept is it? '
            + _NAME_RULE
            + "\n\n"
            + _FMT_NAME
        ),
        kind="name",
        truth=lambda t: t["q7"]["answer"],
    ),
    Question(
        id="q8",
        shape="multi-hop",
        favours="sql",
        stratum="join",
        expert_tool="readb",
        prompt=(
            "A service counts as sev1-affected when at least one `Incident` concept with "
            "`severity` `sev1` lists it in its `services` field. List the names of every "
            "`Runbook` concept whose `status` is `stale`, whose `service` is a `Service` "
            "concept with `tier` 1, and whose service is sev1-affected. "
            + _NAME_RULE
            + "\n\n"
            + _fmt_set("runbook name")
        ),
        kind="set",
        truth=lambda t: set(t["q8"]["answer"]),
    ),
    Question(
        id="q9",
        shape="single-file lookup",
        favours="files",
        stratum="retrieval",
        expert_tool="read",
        prompt=(
            "Which service does the runbook `{runbook}` cover? Give the value of its "
            "`service` field.\n\n" + _FMT_NAME
        ),
        kind="name",
        truth=lambda t: t["q9"]["answer"],
    ),
    Question(
        id="q10",
        shape="malformed-file honesty, warned",
        favours="files",
        stratum="hazard",
        expert_tool="shell",
        corpus="ops-malformed",
        prompt=(
            "Some files in this knowledge base have frontmatter that is not valid YAML. "
            "Counting every file under `corpus/` whose frontmatter block contains a "
            "`type: Service` line — including any file whose frontmatter fails to parse — "
            "how many are there?\n\n" + _FMT_NUMBER
        ),
        kind="number",
        truth=lambda t: t["q10"]["answer"],
    ),
    Question(
        id="q10b",
        shape="malformed count, tabular phrasing",
        favours="files",
        stratum="hazard",
        expert_tool="shell",
        corpus="ops-malformed",
        prompt=(
            "How many `Service` concepts does this knowledge base contain? Count every "
            "concept whose `type` is `Service`, including any whose frontmatter is "
            "malformed.\n\n" + _FMT_NUMBER
        ),
        kind="number",
        truth=lambda t: t["q10"]["answer"],
    ),
    Question(
        id="q11",
        shape="fuzzy retrieval",
        favours="files",
        stratum="retrieval",
        expert_tool="read",
        prompt=(
            "Four runbooks describe a failover procedure. Exactly one of them describes "
            "moving the write path onto a standby datastore by promoting it. Which runbook "
            "is that? " + _NAME_RULE + "\n\n" + _FMT_NAME
        ),
        kind="name",
        truth=lambda t: t["q11"]["answer"],
    ),
    Question(
        id="q12",
        shape="five-part session",
        favours="neutral",
        stratum="join",
        expert_tool="readb",
        prompt=(
            "Answer all five of the following about the knowledge base:\n"
            "a. How many `Service` concepts have `tier` 1?\n"
            "b. How many `Runbook` concepts have `status` `current`?\n"
            "c. How many `Incident` concepts have `severity` `sev1`?\n"
            "d. How many `Decision` concepts have `status` `accepted`?\n"
            "e. How many `Service` concepts are owned by the team `identity`?\n\n"
            "Finish your reply with a single final line in exactly this form:\n"
            "ANSWER: a=1, b=2, c=3, d=4, e=5"
        ),
        kind="mapping",
        truth=lambda t: dict(t["q12"]),
    ),
    # --- new in v2 ------------------------------------------------------------
    Question(
        id="q14",
        shape="body + frontmatter hybrid",
        favours="sql",
        stratum="join",
        expert_tool="readb",
        prompt=(
            "Every `Incident` concept's body contains a line beginning `Root cause:` naming "
            "one cause. List the names of every `Incident` whose `severity` field is `sev1` "
            "and whose root cause is `capacity`. " + _NAME_RULE + "\n\n" + _fmt_set("incident name")
        ),
        kind="set",
        truth=lambda t: set(t["q14"]["answer"]),
    ),
    Question(
        id="q15",
        shape="output-heavy enumeration",
        favours="neutral",
        stratum="scan",
        expert_tool="readb",
        prompt=(
            "List the names of every `Service` concept whose `tier` is 1. "
            + _NAME_RULE
            + "\n\n"
            + _fmt_set("name")
        ),
        kind="set",
        truth=lambda t: set(t["q15"]["answer"]),
    ),
    Question(
        id="q16",
        shape="zero result",
        favours="sql",
        stratum="join",
        expert_tool="readb",
        prompt=(
            "List the names of every `Service` concept owned by the team `{empty_team}` whose "
            "`tier` is {empty_tier} and whose `status` is `{empty_status}`. "
            + _NAME_RULE
            + "\n\n"
            + _fmt_set("name")
        ),
        kind="set",
        truth=lambda t: set(t["q16"]["answer"]),
    ),
    Question(
        id="q17",
        shape="false presupposition",
        favours="neutral",
        stratum="scan",
        expert_tool="readb",
        prompt=(
            "Every `Incident` concept records the team that resolved it in its `owner` field. "
            "List the names of every `Incident` concept whose `owner` is the team `{team}`. "
            + _NAME_RULE
            + "\n\n"
            + _fmt_set("incident name")
        ),
        kind="set",
        truth=lambda t: set(t["q17"]["answer"]),
    ),
    Question(
        id="q18",
        shape="malformed-file honesty, un-warned",
        favours="files",
        stratum="hazard",
        expert_tool="shell",
        corpus="ops-malformed",
        prompt=(
            "Which team owns the most `Service` concepts, and how many does it own?\n\n"
            + _FMT_RECORD_TEAM
        ),
        kind="record",
        truth=lambda t: {"team": t["q18"]["team"], "count": t["q18"]["count"]},
    ),
]


# --- the backlog battery — 8 questions ----------------------------------------

BACKLOG_QUESTIONS: list[Question] = [
    Question(
        id="b1",
        shape="ready-to-schedule",
        favours="sql",
        stratum="backlog",
        expert_tool="readb",
        corpus="backlog",
        prompt=(
            "A task is ready to schedule when its `status` is `Draft` and every task named in "
            "its `blocked_by` list has `status` `Done`. A task with no `blocked_by` is not "
            "blocked. List the names of every ready-to-schedule task whose `priority` is "
            "`high`. " + _NAME_RULE + "\n\n" + _fmt_set("task name")
        ),
        kind="set",
        truth=lambda t: set(t["b1"]["answer"]),
    ),
    Question(
        id="b2",
        shape="active sprint scope + design approach",
        favours="sql",
        stratum="backlog",
        expert_tool="readb",
        corpus="backlog",
        prompt=(
            "Exactly one `Sprint` concept has a `status` other than `Done`. Its `tasks` field "
            "lists the tasks in its scope. Each task's body has a `## Design` section; where a "
            "design exists it contains a line beginning `Approach:` naming one approach. For "
            "every task in that sprint's scope, give the approach its design names — or "
            f"`{NONE_TOKEN}` for a task whose design names none. "
            + _NAME_RULE
            + "\n\n"
            + _fmt_mapping_str("task", "approach")
        ),
        kind="mapping_str",
        truth=lambda t: dict(t["b2"]["answer"]),
    ),
    Question(
        id="b3",
        shape="delivered from a finished sprint",
        favours="sql",
        stratum="backlog",
        expert_tool="readb",
        corpus="backlog",
        prompt=(
            "The sprint `{finished_sprint}` lists the tasks in its scope in its `tasks` field. "
            "Which of those tasks were delivered — that is, have `status` `Done`? "
            + _NAME_RULE
            + "\n\n"
            + _fmt_set("task name")
        ),
        kind="set",
        truth=lambda t: set(t["b3"]["answer"]),
    ),
    Question(
        id="b4",
        shape="open work touching a feature",
        favours="sql",
        stratum="backlog",
        expert_tool="readb",
        corpus="backlog",
        prompt=(
            "A task is still open when its `status` is `Draft` or `Designed`. List the names "
            'of every still-open task whose body mentions "{feature}". '
            + _NAME_RULE
            + "\n\n"
            + _fmt_set("task name")
        ),
        kind="set",
        truth=lambda t: set(t["b4"]["answer"]),
    ),
    Question(
        id="b5",
        shape="single-task lookup",
        favours="files",
        stratum="backlog",
        expert_tool="read",
        corpus="backlog",
        prompt=(
            "What are the `status` and `priority` of the task `{task}`?\n\n" + _FMT_RECORD_TASK
        ),
        kind="record",
        truth=lambda t: dict(t["b5"]["answer"]),
    ),
    Question(
        id="b6",
        shape="dropped-task digest",
        favours="sql",
        stratum="backlog",
        expert_tool="readb",
        corpus="backlog",
        prompt=(
            "Every task with `status` `Dropped` has an `## Outcome` section whose first line "
            "begins `Dropped:` and names the reason. For every task with `status` `Dropped` "
            "whose `created` date falls in {drop_year}, give that reason. "
            + _NAME_RULE
            + "\n\n"
            + _fmt_mapping_str("task", "reason")
        ),
        kind="mapping_str",
        truth=lambda t: dict(t["b6"]["answer"]),
    ),
    Question(
        id="b7",
        shape="next free number",
        favours="sql",
        stratum="backlog",
        expert_tool="readb",
        corpus="backlog",
        prompt=(
            "Every task's name begins with a three-digit number. What is the lowest number "
            "above every number already used — that is, the next free task number?\n\n"
            + _FMT_NUMBER
        ),
        kind="number",
        truth=lambda t: t["b7"]["answer"],
    ),
    Question(
        id="b8",
        shape="tag rollup",
        favours="sql",
        stratum="backlog",
        expert_tool="readb",
        corpus="backlog",
        prompt=(
            "Each `Task` concept carries a `tags` list. Across every task, how many tasks "
            "carry each tag?\n\n" + _FMT_MAPPING
        ),
        kind="mapping",
        truth=lambda t: {k.lower(): v for k, v in t["b8"]["answer"].items()},
    ),
]


QUESTIONS: list[Question] = OPS_QUESTIONS + BACKLOG_QUESTIONS
ALL_QUESTIONS = QUESTIONS
BY_ID = {q.id: q for q in ALL_QUESTIONS}

# There is no `q13`. `q10b` keeps the name it had as v1's post-hoc probe — renaming it
# would break the link to the batch it came from — and it occupies the thirteenth slot in
# the ops battery, so the five questions new in v2 start at `q14`.

STRATA = ("join", "scan", "retrieval", "hazard", "backlog")


def render(question: Question, truth: dict) -> str:
    """Fill the corpus-specific placeholders a question needs."""
    return question.prompt.format(**placeholders(truth))


def placeholders(truth: dict) -> dict:
    """Real names out of a corpus's ground truth, so every prompt names something that exists.

    Both corpus families pass through here; a key absent from one family's truth simply
    never appears in that family's prompts.
    """
    values: dict[str, object] = {}
    if "q3" in truth:
        values.update(
            team=truth["q3"]["team"],
            service=truth["q5"]["service"],
            runbook=truth["q9"]["runbook"],
            empty_team=truth["q16"]["team"],
            empty_tier=truth["q16"]["tier"],
            empty_status=truth["q16"]["status"],
        )
    if "b3" in truth:
        values.update(
            finished_sprint=truth["b3"]["sprint"],
            feature=truth["b4"]["phrase"],
            task=truth["b5"]["task"],
            drop_year=truth["b6"]["year"],
        )
    return values


# --- scoring (pre-registered; do not tune after seeing results) ----------------


def extract_answer(text: str) -> str | None:
    """The last `ANSWER:` line's content, or None when there is none to read.

    A bare `ANSWER:` with nothing after it counts as **no answer**. Without that, an empty
    capture parses as the empty set and scores exactly correct on the two questions whose
    truth is empty — so a run that simply trailed off would be recorded as right, and as
    having produced a parseable answer.
    """
    matches = ANSWER_RE.findall(text or "")
    if not matches:
        return None
    last = matches[-1].strip()
    return last or None


# Bullets and quotes an agent may wrap a name in, and the sentence punctuation it may end
# one with. Stripped so that formatting is never scored as a wrong answer — arms format
# differently by construction, and the normalizer must not pick a winner.
_TRIM = "`'\"*.,;:!?()[]"


def _norm_token(token: str) -> str:
    """Canonicalise one answer token.

    Arms name things differently by construction — readb emits a bare `__name`, a shell
    pipeline emits `services/svc-0042.md`, a reading agent may emit a title — so the
    normalizer strips list bullets, directories, the `.md` suffix, surrounding punctuation
    and case.
    """
    token = token.strip()
    while token[:2] in ("- ", "* ", "+ "):
        token = token[2:].strip()
    token = token.strip(_TRIM).strip()
    token = token.rsplit("/", 1)[-1]
    if token.endswith(".md"):
        token = token[:-3]
    return token.strip(_TRIM).strip().lower()


def _is_none(raw: str) -> bool:
    """The empty answer, spelled the one way every prompt asks for."""
    return _norm_token(raw) == NONE_TOKEN


def _parse_set(raw: str) -> set[str]:
    if _is_none(raw):
        return set()
    return {t for t in (_norm_token(p) for p in re.split(r"[,\n;]+", raw)) if t}


def _as_int(text: str) -> int | None:
    """Digits out of a free-text value, or None. A lone `-` is not a number.

    Text after the last `=` wins. The hazard questions ask an agent to add unparseable
    files to a parsed count, and writing the sum out — `600 + 12 = 612` — is the natural
    thing to do; taking the first integer would score the pre-trap number and penalise
    exactly the arm that did the accounting.
    """
    if "=" in text:
        text = text.rsplit("=", 1)[1]
    match = re.search(r"-?\d+", text)
    return int(match.group()) if match else None


def _parse_pairs(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in re.split(r"[,\n;]+", raw):
        if "=" not in pair:
            continue
        key, _, value = pair.partition("=")
        out[_norm_token(key)] = value.strip()
    return out


def _parse_mapping(raw: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, value in _parse_pairs(raw).items():
        number = _as_int(value)
        if number is not None:
            out[key] = number
    return out


def f1(got: set[str], expected: set[str]) -> float:
    if not got and not expected:
        return 1.0
    if not got or not expected:
        return 0.0
    hits = len(got & expected)
    if not hits:
        return 0.0
    precision, recall = hits / len(got), hits / len(expected)
    return 2 * precision * recall / (precision + recall)


def _score_record(raw: str, expected: dict) -> tuple[bool, float, object]:
    """A fixed set of literal keys, each with its own value type.

    Numbers are compared as numbers and strings as normalized tokens, so `count=31` and
    `count=31 services` agree while `team=platform` and `team=identity` do not.
    """
    got = _parse_pairs(raw)
    agreed = 0
    for key, want in expected.items():
        value = got.get(key)
        if value is None:
            continue
        if isinstance(want, int):
            agreed += _as_int(value) == want
        else:
            agreed += _norm_token(value) == str(want).lower()
    exact = agreed == len(expected) and set(got) == set(expected)
    return exact, agreed / len(expected) if expected else 0.0, got


def _score_mapping_str(raw: str, expected: dict) -> tuple[bool, float, object]:
    """Keys named by the corpus, values scored by token containment.

    Containment rather than equality because the value is an extraction from prose: an
    agent that answers `worker-queue (a background queue)` found the same token as one
    that answers `worker-queue`. The key set must still match exactly — naming a task that
    is not in scope is a different answer, not a verbose one.
    """
    if not expected:
        # Symmetric with the set kind: an empty answer must be *stated*, not implied by a
        # line that happens to carry no `=`.
        return (_is_none(raw), 1.0 if _is_none(raw) else 0.0, {})
    got = _parse_pairs(raw)
    agreed = sum(
        1
        for key, want in expected.items()
        if key in got and str(want).lower() in _norm_token(got[key])
    )
    exact = agreed == len(expected) and set(got) == set(expected)
    return exact, agreed / len(expected) if expected else 0.0, got


def score(question: Question, raw_answer: str | None, truth: dict) -> tuple[bool, float, object]:
    """Exactness, F1, and the parsed answer — the last so wrong runs can be inspected."""
    if raw_answer is None:
        return False, 0.0, None
    expected = question.truth(truth)
    if question.kind == "set":
        want = {str(e).lower() for e in expected}
        if not want:
            # An empty answer must be *stated*. Letting a line that parsed to no tokens
            # satisfy an empty truth would score a run that trailed off as exactly correct
            # on the two questions whose answer is nothing.
            stated = _is_none(raw_answer)
            return stated, 1.0 if stated else 0.0, []
        got = _parse_set(raw_answer)
        return got == want, f1(got, want), sorted(got)
    if question.kind == "mapping":
        got = _parse_mapping(raw_answer)
        exact = got == expected
        agreed = sum(1 for k, v in expected.items() if got.get(k) == v)
        return exact, agreed / len(expected) if expected else 0.0, got
    if question.kind == "mapping_str":
        return _score_mapping_str(raw_answer, expected)
    if question.kind == "record":
        return _score_record(raw_answer, expected)
    if question.kind == "name":
        want = str(expected).lower()
        got = _norm_token(raw_answer)
        # `inc-0042 (the incident)` named the same concept as `inc-0042`. The first token
        # is tried only when the whole line does not match, so this can turn a right answer
        # written loosely into a pass and can never turn a wrong name into one.
        if got != want and " " in got:
            got = _norm_token(got.split()[0])
        exact = got == want
        return exact, 1.0 if exact else 0.0, got
    if question.kind == "number":
        got = _as_int(raw_answer)
        exact = got == expected
        return exact, 1.0 if exact else 0.0, got
    raise ValueError(f"unknown kind {question.kind}")
