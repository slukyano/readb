"""The question battery, its answer protocol, and the scorer.

Twelve questions. Seven are frontmatter aggregation, where a SQL layer is expected to
win. Five exist because a battery with no losing shape is not a measurement: a single-file
lookup (where loading a whole bundle is pure overhead), a fuzzy retrieval no exact match
can resolve, an exact-phrase needle grep answers in one call, a count that includes files
readb's permissive load silently skips, and a five-part session that pays readb's
per-invocation reload repeatedly.

The normalizer below is **pre-registered**: it is fixed before the first measured run and
must not be adjusted after seeing results.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

ANSWER_RE = re.compile(r"^\s*ANSWER:\s*(.*)$", re.MULTILINE | re.IGNORECASE)


@dataclass(frozen=True)
class Question:
    id: str
    shape: str
    prompt: str
    kind: str  # "set" | "number" | "mapping" | "name"
    truth: Callable[[dict], object]
    favours: str  # "sql" | "files" | "neutral" — declared before the runs, not after
    corpus: str = "clean"


def _fmt_set(what: str) -> str:
    return (
        f"Finish your reply with a single final line in exactly this form, listing every "
        f"{what} separated by commas (order does not matter):\nANSWER: name-1, name-2, name-3"
    )


_FMT_NUMBER = "Finish your reply with a single final line in exactly this form:\nANSWER: <number>"
_FMT_NAME = (
    "Finish your reply with a single final line in exactly this form:\nANSWER: <concept-name>"
)
_FMT_MAPPING = (
    "Finish your reply with a single final line in exactly this form, one pair per "
    "category, separated by commas:\nANSWER: category-a=12, category-b=34"
)
_NAME_RULE = "A concept's name is its filename without the `.md` extension."


QUESTIONS: list[Question] = [
    Question(
        id="q1",
        shape="type rollup",
        favours="sql",
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
        prompt=(
            "Which team owns the most `Service` concepts, and how many does it own?\n\n"
            "Finish your reply with a single final line in exactly this form:\n"
            "ANSWER: team-name=<count>"
        ),
        kind="mapping",
        truth=lambda t: {t["q6"]["team"].lower(): t["q6"]["count"]},
    ),
    Question(
        id="q7",
        shape="exact-phrase needle",
        favours="files",
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
        prompt=(
            "Which service does the runbook `{runbook}` cover? Give the value of its "
            "`service` field.\n\n" + _FMT_NAME
        ),
        kind="name",
        truth=lambda t: t["q9"]["answer"],
    ),
    Question(
        id="q10",
        shape="malformed-file honesty",
        favours="files",
        corpus="malformed",
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
        id="q11",
        shape="fuzzy retrieval",
        favours="files",
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
]

BY_ID = {q.id: q for q in QUESTIONS}


def render(question: Question, truth: dict) -> str:
    """Fill the corpus-specific placeholders a question needs."""
    return question.prompt.format(
        team=truth["q3"]["team"],
        service=truth["q5"]["service"],
        runbook=truth["q9"]["runbook"],
    )


# --- scoring (pre-registered; do not tune after seeing results) ----------------


def extract_answer(text: str) -> str | None:
    matches = ANSWER_RE.findall(text or "")
    return matches[-1].strip() if matches else None


def _norm_token(token: str) -> str:
    """Canonicalise one answer token.

    Arms name things differently by construction — readb emits a bare `__name`, a shell
    pipeline emits `services/svc-0042.md`, a reading agent may emit a title — so the
    normalizer strips directories, the `.md` suffix, surrounding punctuation and case.
    """
    token = token.strip().strip("`'\"*")
    token = token.rsplit("/", 1)[-1]
    if token.endswith(".md"):
        token = token[:-3]
    return token.strip().lower()


def _parse_set(raw: str) -> set[str]:
    return {t for t in (_norm_token(p) for p in re.split(r"[,\n;]+", raw)) if t}


def _parse_mapping(raw: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for pair in re.split(r"[,\n;]+", raw):
        if "=" not in pair:
            continue
        key, _, value = pair.partition("=")
        digits = re.sub(r"[^0-9-]", "", value)
        if digits:
            out[_norm_token(key)] = int(digits)
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


def score(question: Question, raw_answer: str | None, truth: dict) -> tuple[bool, float, object]:
    """Exactness, F1, and the parsed answer — the last so wrong runs can be inspected."""
    if raw_answer is None:
        return False, 0.0, None
    expected = question.truth(truth)
    if question.kind == "set":
        got = _parse_set(raw_answer)
        want = {str(e).lower() for e in expected}
        return got == want, f1(got, want), sorted(got)
    if question.kind == "mapping":
        got = _parse_mapping(raw_answer)
        exact = got == expected
        agreed = sum(1 for k, v in expected.items() if got.get(k) == v)
        return exact, agreed / len(expected) if expected else 0.0, got
    if question.kind == "name":
        got = _norm_token(raw_answer)
        exact = got == str(expected).lower()
        return exact, 1.0 if exact else 0.0, got
    if question.kind == "number":
        digits = re.sub(r"[^0-9-]", "", raw_answer)
        got = int(digits) if digits else None
        exact = got == expected
        return exact, 1.0 if exact else 0.0, got
    raise ValueError(f"unknown kind {question.kind}")
