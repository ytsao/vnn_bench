#!/usr/bin/env python3
"""Summarize z3 result JSON files into one CSV per benchmark folder.

z3's "json" output is not pure JSON: only the first couple of lines are
JSON records (start marker + statistics), the rest is z3's raw stdout
(constraints dump, and the final verdict word). This script parses both
parts and writes one row per instance file.

Usage:
    python3 postprocess_z3.py <root-dir> [output-dir]

<root-dir> either holds *.json result files directly (a single benchmark),
or contains one subdirectory per benchmark (e.g. z3-cpu-cersyve), each
holding *.json files directly (not recursively). One CSV is written per
benchmark, named "<benchmark-dir-name>.csv".
"""
import sys
import json
import csv
from pathlib import Path

STATUS_WORDS = {"sat", "unsat", "unknown", "timeout"}


def parse_result_file(path):
    row = {
        "configuration": path.stem,
        "vnn_verifier": "",
        "network_filename": "",
        "vnnlib_filename": "",
        "timeout": "",
        "datetime": "",
        "status": "unknown",
        "note": "",
    }

    text = path.read_text(errors="replace")
    lines = text.splitlines()

    # First couple of lines are JSON records: start marker + statistics.
    for line in lines[:5]:
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "statistics":
            stats = obj.get("statistics", {})
            row["vnn_verifier"] = stats.get("vnn_verifier", "")
            row["network_filename"] = stats.get("network_filename", "")
            row["vnnlib_filename"] = stats.get("vnnlib_filename", "")
            row["timeout"] = stats.get("timeout", "")
            row["datetime"] = stats.get("datetime", "")

    # The verification verdict is the last non-empty line of the file.
    non_empty = [l.strip() for l in lines if l.strip()]
    if non_empty and non_empty[-1].lower() in STATUS_WORDS:
        row["status"] = non_empty[-1].lower()

    # No explicit verdict word found: classify from known failure patterns.
    if row["status"] == "unknown" and (not non_empty or non_empty[-1].lower() not in STATUS_WORDS):
        lower = text.lower()
        if "segmentation fault" in lower:
            row["status"] = "error"
            row["note"] = "segfault"
        elif "cancelled" in lower and "time limit" in lower:
            row["status"] = "timeout"
            row["note"] = "killed by scheduler (time limit)"
        elif "unable to create step" in lower or "srun: error" in lower:
            row["status"] = "error"
            row["note"] = "slurm/srun error"

    return row


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <root-dir> [output-dir]")
        sys.exit(1)

    root = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else root

    out_dir.mkdir(parents=True, exist_ok=True)

    # If root itself holds *.json files directly, treat it as a single benchmark.
    # Otherwise treat each of its subdirectories as one benchmark.
    if sorted(root.glob("*.json")):
        benchmark_dirs = [root]
    else:
        benchmark_dirs = sorted(p for p in root.iterdir() if p.is_dir())

    if not benchmark_dirs:
        print(f"No *.json files or subdirectories found under {root}")
        sys.exit(1)

    for benchmark_dir in benchmark_dirs:
        json_files = sorted(benchmark_dir.glob("*.json"))
        if not json_files:
            continue

        rows = [parse_result_file(f) for f in json_files]

        csv_path = out_dir / f"{benchmark_dir.name}.csv"
        fieldnames = list(rows[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Wrote {len(rows)} rows to {csv_path}")


if __name__ == "__main__":
    main()
