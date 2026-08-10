"""Generate a deterministic synthetic OKF bundle plus its ground truth.

The corpus is a neutral platform-engineering knowledge base: services, runbooks,
incidents and decisions. Ground truth is computed from the generated records in plain
Python — never by querying readb, which would make the benchmark's correctness check
circular.

    python benchmarks/generate_corpus.py --out /tmp/corpus --concepts 600 --seed 24
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

TEAMS = [
    "payments",
    "identity",
    "search",
    "billing",
    "platform",
    "media",
    "growth",
    "data",
]
LANGUAGES = ["python", "go", "rust", "typescript", "java"]
SERVICE_STATUSES = ["ga", "beta", "deprecated", "incubating"]
TIERS = [1, 2, 3]
RUNBOOK_STATUSES = ["current", "stale", "draft"]
SEVERITIES = ["sev1", "sev2", "sev3"]
INCIDENT_STATUSES = ["resolved", "monitoring", "open"]
DECISION_STATUSES = ["accepted", "proposed", "superseded"]
TAG_POOL = [
    "networking",
    "storage",
    "latency",
    "capacity",
    "security",
    "observability",
    "cost",
    "migration",
    "compliance",
    "release",
]

SERVICE_NOUNS = [
    "gateway",
    "ledger",
    "indexer",
    "scheduler",
    "router",
    "cache",
    "collector",
    "dispatcher",
    "resolver",
    "transcoder",
    "reconciler",
    "notifier",
    "aggregator",
    "validator",
    "shipper",
    "planner",
]
SERVICE_QUALIFIERS = [
    "edge",
    "core",
    "batch",
    "stream",
    "regional",
    "shadow",
    "legacy",
    "unified",
    "async",
    "inline",
]

# The Q7 needle. Generation asserts it occurs in exactly one concept body.
NEEDLE_PHRASE = "the circuit breaker tripped during a partial region drain"

BODY_SENTENCES = [
    "Traffic is admitted through the regional load balancer before any authorization check runs.",
    "Retries use exponential backoff with jitter, capped at four attempts per request.",
    "Capacity is provisioned for twice the observed weekday peak, reviewed each quarter.",
    "Requests carry a correlation identifier that is propagated to every downstream call.",
    "The write path is idempotent; duplicate submissions collapse on the natural key.",
    "Metrics are scraped every fifteen seconds and retained at full resolution for nine days.",
    "Schema changes are applied forward-only, with a compatibility window of two releases.",
    "Reads are served from a follower replica unless the request opts into strong consistency.",
    "Backpressure is signalled to callers as a retriable status rather than a queue build-up.",
    "Configuration is delivered at startup and refreshed on a signal, never polled in a loop.",
    "A partial failure leaves the batch marked incomplete so the next pass can resume it.",
    "Timeouts are budgeted per hop, and the remaining budget travels with the request.",
    "Secrets are mounted from the platform store and rotated without a restart.",
    "The rollout is staged by region, holding at ten percent until error rates settle.",
    "Dead-lettered messages are retained for seven days and replayed manually after triage.",
]


@dataclass
class Concept:
    name: str
    subdir: str
    frontmatter: dict
    body: str
    record: dict = field(default_factory=dict)


def _slug(rng: random.Random) -> str:
    return f"{rng.choice(SERVICE_QUALIFIERS)}-{rng.choice(SERVICE_NOUNS)}"


def _date(rng: random.Random, year_lo: int = 2023, year_hi: int = 2026) -> str:
    year = rng.randint(year_lo, year_hi)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _body(rng: random.Random, headings: list[str], needle: bool = False) -> str:
    parts: list[str] = []
    for heading in headings:
        parts.append(f"# {heading}")
        parts.append("")
        for _ in range(rng.randint(2, 4)):
            sentences = rng.sample(BODY_SENTENCES, rng.randint(2, 3))
            parts.append(" ".join(sentences))
            parts.append("")
    if needle:
        parts.append("# Postmortem note")
        parts.append("")
        parts.append(
            f"During the last exercise {NEEDLE_PHRASE}, and the fallback path absorbed "
            "the shifted load without a user-visible error."
        )
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def _yaml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return str(value)


def _frontmatter(fm: dict) -> str:
    lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"- {item}" for item in value)
        else:
            lines.append(f"{key}: {_yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def generate(concepts: int, seed: int) -> tuple[list[Concept], dict]:
    rng = random.Random(seed)

    n_services = max(1, round(concepts * 0.30))
    n_runbooks = max(1, round(concepts * 0.33))
    n_incidents = max(1, round(concepts * 0.27))
    n_decisions = max(1, concepts - n_services - n_runbooks - n_incidents)

    out: list[Concept] = []

    # --- Services -------------------------------------------------------------
    services: list[dict] = []
    for i in range(n_services):
        # The numeric prefix carries uniqueness; the slug is only there to make a name
        # readable, so slugs are allowed to repeat (there are fewer slugs than services).
        name = f"svc-{i + 1:04d}-{_slug(rng)}"
        record = {
            "name": name,
            "team": rng.choice(TEAMS),
            "tier": rng.choice(TIERS),
            "status": rng.choice(SERVICE_STATUSES),
            "language": rng.choice(LANGUAGES),
            "created": _date(rng),
        }
        services.append(record)

    # Dependencies reference other services; assigned after all names exist.
    names = [s["name"] for s in services]
    for record in services:
        others = [n for n in names if n != record["name"]]
        record["dependencies"] = sorted(rng.sample(others, rng.randint(0, min(4, len(others)))))
        fm = {
            "type": "Service",
            "title": record["name"].split("-", 2)[2].replace("-", " ").title() + " service",
            "team": record["team"],
            "tier": record["tier"],
            "status": record["status"],
            "language": record["language"],
            "created": record["created"],
        }
        if record["dependencies"]:
            fm["dependencies"] = record["dependencies"]
        out.append(
            Concept(
                name=record["name"],
                subdir="services",
                frontmatter=fm,
                body=_body(rng, ["Summary", "Interfaces", "Operations"]),
                record=record,
            )
        )

    # --- Runbooks -------------------------------------------------------------
    runbooks: list[dict] = []
    for i in range(n_runbooks):
        service = rng.choice(services)["name"]
        record = {
            "name": f"rb-{i + 1:04d}-{service.split('-', 2)[2]}",
            "service": service,
            "severity": rng.choice(SEVERITIES),
            "status": rng.choice(RUNBOOK_STATUSES),
            "tags": sorted(rng.sample(TAG_POOL, rng.randint(1, 3))),
            "last_reviewed": _date(rng, 2025, 2026),
        }
        runbooks.append(record)
        out.append(
            Concept(
                name=record["name"],
                subdir="runbooks",
                frontmatter={
                    "type": "Runbook",
                    "title": f"Runbook — {record['service']}",
                    "service": record["service"],
                    "severity": record["severity"],
                    "status": record["status"],
                    "tags": record["tags"],
                    "last_reviewed": record["last_reviewed"],
                },
                body=_body(rng, ["Symptoms", "Diagnosis", "Mitigation"]),
                record=record,
            )
        )

    # --- Incidents ------------------------------------------------------------
    needle_index = rng.randrange(n_incidents)
    incidents: list[dict] = []
    for i in range(n_incidents):
        affected = sorted(rng.sample(names, rng.randint(1, 4)))
        record = {
            "name": f"inc-{i + 1:04d}",
            "severity": rng.choice(SEVERITIES),
            "services": affected,
            "status": rng.choice(INCIDENT_STATUSES),
            "duration_minutes": rng.choice([15, 30, 45, 60, 90, 120, 180, 240, 360]),
            "date": _date(rng, 2025, 2026),
            "postmortem": rng.random() < 0.6,
        }
        incidents.append(record)
        out.append(
            Concept(
                name=record["name"],
                subdir="incidents",
                frontmatter={
                    "type": "Incident",
                    "title": f"Incident {record['name'].split('-')[1]} — {record['severity']}",
                    "severity": record["severity"],
                    "services": record["services"],
                    "status": record["status"],
                    "duration_minutes": record["duration_minutes"],
                    "date": record["date"],
                    "postmortem": record["postmortem"],
                },
                body=_body(rng, ["Impact", "Timeline"], needle=(i == needle_index)),
                record=record,
            )
        )

    # --- Decisions ------------------------------------------------------------
    decisions: list[dict] = []
    for i in range(n_decisions):
        record = {
            "name": f"dec-{i + 1:04d}",
            "team": rng.choice(TEAMS),
            "status": rng.choice(DECISION_STATUSES),
            "tags": sorted(rng.sample(TAG_POOL, rng.randint(1, 3))),
            "date": _date(rng, 2024, 2026),
        }
        decisions.append(record)
        out.append(
            Concept(
                name=record["name"],
                subdir="decisions",
                frontmatter={
                    "type": "Decision",
                    "title": f"Decision {record['name'].split('-')[1]}",
                    "team": record["team"],
                    "status": record["status"],
                    "tags": record["tags"],
                    "date": record["date"],
                },
                body=_body(rng, ["Context", "Decision", "Consequences"]),
                record=record,
            )
        )

    truth = ground_truth(services, runbooks, incidents, decisions)
    return out, truth


def ground_truth(
    services: list[dict],
    runbooks: list[dict],
    incidents: list[dict],
    decisions: list[dict],
) -> dict:
    """Every answer, computed from the records themselves."""
    by_team: dict[str, int] = {}
    for s in services:
        by_team[s["team"]] = by_team.get(s["team"], 0) + 1
    top_team = sorted(by_team.items(), key=lambda kv: (-kv[1], kv[0]))[0]

    service_by_name = {s["name"]: s for s in services}

    q2: dict[str, int] = {}
    for s in services:
        q2[s["status"]] = q2.get(s["status"], 0) + 1

    # Q3 targets the team owning the most services, so the answer set is never empty.
    q3_team = top_team[0]
    q3 = sorted(
        s["name"] for s in services if s["team"] == q3_team and s["tier"] == 1 and s["status"] != "ga"
    )

    q4 = sorted(
        r["name"]
        for r in runbooks
        if (svc := service_by_name.get(r["service"]))
        and svc["tier"] == 1
        and svc["status"] == "deprecated"
    )

    # Q5 targets the service that appears in the most incidents.
    appearances: dict[str, int] = {}
    for inc in incidents:
        for name in inc["services"]:
            appearances[name] = appearances.get(name, 0) + 1
    q5_service = sorted(appearances.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    q5 = sorted(inc["name"] for inc in incidents if q5_service in inc["services"])

    # Q8 is deliberately narrowed by three predicates: the un-narrowed "runbooks covering
    # any sev1-affected service" answer runs to ~90 names, which measures an agent's
    # willingness to type a long list more than its ability to find the answer.
    sev1_services = sorted({n for inc in incidents if inc["severity"] == "sev1" for n in inc["services"]})
    q8 = sorted(
        r["name"]
        for r in runbooks
        if r["status"] == "stale"
        and r["service"] in sev1_services
        and (svc := service_by_name.get(r["service"]))
        and svc["tier"] == 1
    )

    return {
        "counts": {
            "Service": len(services),
            "Runbook": len(runbooks),
            "Incident": len(incidents),
            "Decision": len(decisions),
        },
        "q1": {
            "Service": len(services),
            "Runbook": len(runbooks),
            "Incident": len(incidents),
            "Decision": len(decisions),
        },
        "q2": q2,
        "q3": {"team": q3_team, "answer": q3},
        "q4": q4,
        "q5": {"service": q5_service, "answer": q5},
        "q6": {"team": top_team[0], "count": top_team[1]},
        "q7": {"phrase": NEEDLE_PHRASE},  # concept name filled in by the writer
        "q8": {"sev1_services": sev1_services, "answer": q8},
    }


INDEX = """---
type: Index
title: Platform knowledge base
---

# Platform knowledge base

Services, their runbooks, the incidents that hit them, and the decisions behind them.

- `services/` — one concept per service
- `runbooks/` — operational runbooks, each tied to a service
- `incidents/` — incident records
- `decisions/` — architecture decisions
"""


def write(out_dir: Path, truth_path: Path, concepts: list[Concept], truth: dict) -> None:
    """Write the bundle to `out_dir` and the answers to `truth_path`.

    The ground truth is written OUTSIDE the bundle on purpose: an agent under test can
    read anything inside the corpus, and a file of answers sitting in it would be a
    leak, not a benchmark.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.md").write_text(INDEX)

    needle_holders = []
    for concept in concepts:
        sub = out_dir / concept.subdir
        sub.mkdir(exist_ok=True)
        text = _frontmatter(concept.frontmatter) + "\n" + concept.body
        (sub / f"{concept.name}.md").write_text(text)
        if NEEDLE_PHRASE in text:
            needle_holders.append(concept.name)

    if len(needle_holders) != 1:
        raise AssertionError(f"needle phrase must occur in exactly one concept, got {needle_holders}")
    truth["q7"]["answer"] = needle_holders[0]

    names = [c.name for c in concepts]
    if len(set(names)) != len(names):
        raise AssertionError("concept names must be unique across the bundle")

    truth_path.parent.mkdir(parents=True, exist_ok=True)
    truth_path.write_text(json.dumps(truth, indent=2, sort_keys=True) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--truth", type=Path, help="default: <out>_ground_truth.json, beside the bundle")
    ap.add_argument("--concepts", type=int, default=600)
    ap.add_argument("--seed", type=int, default=24)
    args = ap.parse_args()

    truth_path = args.truth or args.out.parent / f"{args.out.name}_ground_truth.json"
    concepts, truth = generate(args.concepts, args.seed)
    write(args.out, truth_path, concepts, truth)
    print(f"{len(concepts)} concepts -> {args.out}")
    print(json.dumps(truth["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
