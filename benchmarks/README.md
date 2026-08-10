# benchmarks

The harness behind [`docs/dev/research/agent-efficiency.md`](../docs/dev/research/agent-efficiency.md):
does an agent answer questions about an OKF bundle faster and cheaper with readb than without?

Development material — excluded from the sdist, not part of the readb package.

## Layout

| File | What it is |
| --- | --- |
| `generate_corpus.py` | Deterministic synthetic OKF bundle (services, runbooks, incidents, decisions) plus its ground truth, computed in plain Python and written **outside** the bundle. |
| `battery.py` | The eight questions, their answer protocol, and the scorer. |
| `run_benchmark.py` | Runs the matrix of arm × question × repeat and appends one JSON line per run. |
| `analyze.py` | Aggregates a results file into the published tables. |
| `test_harness.py` | Tests for the scorer, the cost model, the integrity checks and the corpus invariants. |
| `results/` | Raw per-run records, full transcripts, and a `manifest.json` per batch. |

The harness has its own suite — the scorer decides what gets published, and the cost model
turns token counts into a number a reader will quote:

```sh
uv run pytest benchmarks
```

The package's own suite does not collect this directory, and the sdist does not ship it.

## Reproducing

```sh
python benchmarks/generate_corpus.py --out /tmp/corpus600 --concepts 600 --seed 24

uv venv /tmp/benchvenv
VIRTUAL_ENV=/tmp/benchvenv uv pip install "readb==0.2.0"

python benchmarks/run_benchmark.py \
    --corpus /tmp/corpus600 --truth /tmp/corpus600_ground_truth.json \
    --readb-bin /tmp/benchvenv/bin/readb \
    --results benchmarks/results/run.jsonl --repeats 3

python benchmarks/analyze.py --results benchmarks/results/run.jsonl
```

Runs cost money — a full 3-repeat matrix is 72 headless agent invocations. `run_benchmark.py`
is resumable: a cell already present in the results file is skipped.

## The three arms

| Arm | Prompt | Environment |
| --- | --- | --- |
| `baseline` | No mention of readb | readb kept off `PATH` |
| `readb-bare` | Two sentences naming `readb query` and `readb schema` | readb on `PATH` |
| `readb-skill` | Identical to `baseline` | readb on `PATH`, the repository's plugin loaded so the shipped skill is discoverable |

Every arm runs with `--setting-sources ""`, so no personal configuration, skill, hook or MCP
server reaches any of them; arm C differs from arm A by exactly one loaded skill. `--safe-mode`
is deliberately *not* used — it suppresses `--plugin-dir`, which would collapse arm C onto arm A
without any visible sign.
