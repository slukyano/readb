"""Time readb with and without its persistent cache, on the benchmark's own corpora.

The agent battery cannot resolve the cache's wall-clock effect — it is a fraction of a run that
sits near the instrument's noise — so the cache's speed is established here instead, directly and
without an agent. Committed so the published figures have a record that can be re-run.

    uv run python benchmarks/measure_cache.py --readb-bin /tmp/venv/bin/readb --out /tmp/m.json

Three states are timed per corpus, because they are three different questions:

* **cold** — no cache exists; the load runs and then *writes* one, so it costs more than an
  uncached load, not less. This is what a bundle nobody has queried before pays.
* **no cache** — `--no-cache`: the load runs and writes nothing. What readb did before the cache.
* **warm** — the cache exists and matches the bundle. What a repeat invocation pays.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import time
from pathlib import Path

REPEATS = 11


def time_command(command: list[str], cwd: Path, repeats: int = REPEATS) -> float:
    """Median wall seconds over ``repeats`` runs, discarding nothing."""
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        subprocess.run(command, cwd=cwd, capture_output=True, check=False)
        samples.append(time.perf_counter() - started)
    return statistics.median(samples)


def measure(corpus: Path, readb_bin: Path, sql: str, workroot: Path) -> dict:
    root = workroot / corpus.name
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(corpus, root / "corpus")
    (root / ".readb").mkdir(parents=True)
    (root / ".readb" / "config.toml").write_text('version = 1\nbundles = ["corpus"]\n')
    query = [str(readb_bin), "query", sql, "--bundle", "corpus"]
    files = sum(1 for _ in (root / "corpus").rglob("*.md"))

    def cold_once() -> float:
        shutil.rmtree(root / ".readb" / "cache", ignore_errors=True)
        return time_command(query, root, repeats=1)

    cold = statistics.median([cold_once() for _ in range(REPEATS)])
    uncached = time_command([*query, "--no-cache"], root)
    time_command(query, root, repeats=1)  # prime
    warm = time_command(query, root)
    return {
        "corpus": corpus.name,
        "files": files,
        "cold_s": round(cold, 4),
        "no_cache_s": round(uncached, 4),
        "warm_s": round(warm, 4),
        "saved_vs_no_cache_s": round(uncached - warm, 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readb-bin", required=True, type=Path)
    parser.add_argument("--corpus", action="append", required=True, help="NAME=DIR,SQL")
    parser.add_argument("--workroot", type=Path, default=Path("/tmp/readb-cache-timing"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    args.workroot.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in args.corpus:
        _, rest = spec.split("=", 1)
        directory, sql = rest.split(",", 1)
        rows.append(measure(Path(directory), args.readb_bin, sql, args.workroot))

    header = f"| {'corpus':<14} | files | cold | no cache | warm | saved |"
    print(header)
    print("|" + "---|" * 6)
    for row in rows:
        print(
            f"| {row['corpus']:<14} | {row['files']:>5} | {row['cold_s']:.3f} s "
            f"| {row['no_cache_s']:.3f} s | {row['warm_s']:.3f} s "
            f"| {row['saved_vs_no_cache_s']:.3f} s |"
        )
    if args.out:
        args.out.write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
