"""The question battery and its scorer.

Each question carries the prompt an agent sees, the shape of the expected answer, and a
function pulling the correct answer out of the generator's ground truth. Prompts are
byte-identical across arms; only the arm's preamble differs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

ANSWER_RE = re.compile(r"^\s*ANSWER:\s*(.*)$", re.MULTILINE | re.IGNORECASE)


@dataclass(frozen=True)
class Question:
    id: str
    shape: str
    prompt: str
    kind: str  # "set" | "number" | "mapping" | "name"
    truth: Callable[[dict], object]


def _fmt_set(what: str) -> str:
    return (
        f"Finish your reply with a single final line in exactly this form, listing every "
        f"{what} separated by commas (order does not matter):\nANSWER: name-1, name-2, name-3"
    )


_FMT_NUMBER = (
    "Finish your reply with a single final line in exactly this form:\nANSWER: <number>"
)
_FMT_NAME = (
    "Finish your reply with a single final line in exactly this form:\nANSWER: <concept-name>"
)
_FMT_MAPPING = (
    "Finish your reply with a single final line in exactly this form, one pair per "
    "category, separated by commas:\nANSWER: category-a=12, category-b=34"
)


QUESTIONS: list[Question] = [
    Question(
        id="q1",
        shape="type rollup",
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
        prompt=(
            "List the names of every `Service` concept owned by the team `{team}` whose `tier` "
            "is 1 and whose `status` is anything other than `ga`. A concept's name is its "
            "filename without the `.md` extension.\n\n" + _fmt_set("name")
        ),
        kind="set",
        truth=lambda t: set(t["q3"]["answer"]),
    ),
    Question(
        id="q4",
        shape="cross-reference",
        prompt=(
            "Every `Runbook` concept names the service it covers in its `service` field. List "
            "the names of all `Runbook` concepts whose service is a `Service` concept with "
            "`tier` 1 and `status` `deprecated`. A concept's name is its filename without the "
            "`.md` extension.\n\n" + _fmt_set("runbook name")
        ),
        kind="set",
        truth=lambda t: set(t["q4"]),
    ),
    Question(
        id="q5",
        shape="list membership",
        prompt=(
            "Each `Incident` concept lists the services it affected in its `services` field. "
            "List the names of every `Incident` concept whose `services` includes "
            "`{service}`. A concept's name is its filename without the `.md` extension.\n\n"
            + _fmt_set("incident name")
        ),
        kind="set",
        truth=lambda t: set(t["q5"]["answer"]),
    ),
    Question(
        id="q6",
        shape="extremum",
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
        shape="body needle",
        prompt=(
            "Exactly one concept's body text contains the phrase "
            '"the circuit breaker tripped during a partial region drain". Which concept is it? '
            "A concept's name is its filename without the `.md` extension.\n\n" + _FMT_NAME
        ),
        kind="name",
        truth=lambda t: t["q7"]["answer"],
    ),
    Question(
        id="q8",
        shape="multi-hop",
        prompt=(
            "A service counts as sev1-affected when at least one `Incident` concept with "
            "`severity` `sev1` lists it in its `services` field. List the names of every "
            "`Runbook` concept whose `status` is `stale`, whose `service` is a `Service` "
            "concept with `tier` 1, and whose service is sev1-affected. A concept's name is "
            "its filename without the `.md` extension.\n\n" + _fmt_set("runbook name")
        ),
        kind="set",
        truth=lambda t: set(t["q8"]["answer"]),
    ),
]

BY_ID = {q.id: q for q in QUESTIONS}


def render(question: Question, truth: dict) -> str:
    """Fill the corpus-specific placeholders a question needs."""
    return question.prompt.format(
        team=truth["q3"]["team"],
        service=truth["q5"]["service"],
    )


# --- scoring ------------------------------------------------------------------


def extract_answer(text: str) -> str | None:
    matches = ANSWER_RE.findall(text or "")
    return matches[-1].strip() if matches else None


def _norm_token(token: str) -> str:
    return token.strip().strip("`'\"").lower()


def _parse_set(raw: str) -> set[str]:
    return {_norm_token(p) for p in re.split(r"[,\s]+", raw) if _norm_token(p)}


def _parse_mapping(raw: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for pair in raw.split(","):
        if "=" not in pair:
            continue
        key, _, value = pair.partition("=")
        digits = re.sub(r"[^0-9-]", "", value)
        if digits:
            out[_norm_token(key)] = int(digits)
    return out


def score(question: Question, raw_answer: str | None, truth: dict) -> tuple[bool, object]:
    """Binary correctness plus the parsed answer, for inspection of wrong runs."""
    if raw_answer is None:
        return False, None
    expected = question.truth(truth)
    if question.kind == "set":
        got = _parse_set(raw_answer)
        return got == {e.lower() for e in expected}, sorted(got)
    if question.kind == "mapping":
        got = _parse_mapping(raw_answer)
        return got == expected, got
    if question.kind == "name":
        got = _norm_token(raw_answer)
        return got == expected.lower(), got
    if question.kind == "number":
        digits = re.sub(r"[^0-9-]", "", raw_answer)
        got = int(digits) if digits else None
        return got == expected, got
    raise ValueError(f"unknown kind {question.kind}")
