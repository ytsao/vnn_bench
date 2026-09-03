#!/usr/bin/env python3
"""Summarize ibex result JSON files into one CSV per benchmark folder.

ibex's "json" output is not pure JSON: only the first couple of lines are
JSON records (start marker + statistics), the rest is ibex's raw stdout
(constraints dump, timing, and the final verdict word). This script parses
both parts and writes one row per instance file.

Usage:
    python3 postprocess_ibex.py <root-dir> [output-dir]

<root-dir> contains one subdirectory per benchmark (e.g. ibex-default-cpu-cersyve),
each holding *.json result files directly (not recursively). One CSV is written
per benchmark subdirectory, named "<subdir-name>.csv".
"""
import sys
import os
import re
import json
import csv
from pathlib import Path

STATUS_WORDS = {"sat", "unsat", "unknown", "timeout"}

CPU_TIME_RE = re.compile(r"cpu time used:\s*([\d.]+)s")
CELLS_RE = re.compile(r"number of cells:\s*(\S+)")
SOLUTION_BOXES_RE = re.compile(r"number of solution boxes:\s*(\S+)")
BOUNDARY_BOXES_RE = re.compile(r"number of boundary boxes:\s*(\S+)")
UNKNOWN_BOXES_RE = re.compile(r"number of unknown boxes:\s*(\S+)")
PENDING_BOXES_RE = re.compile(r"number of pending boxes:\s*(\S+)")


def parse_result_file(path):
    row = {
        "configuration": path.stem,
        "vnn_verifier": "",
        "network_filename": "",
        "vnnlib_filename": "",
        "timeout": "",
        "datetime": "",
        "status": "unknown",
        "cpu_time": "",
        "cells": "",
        "solution_boxes": "",
        "boundary_boxes": "",
        "unknown_boxes": "",
        "pending_boxes": "",
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

    m = CPU_TIME_RE.search(text)
    if m:
        row["cpu_time"] = m.group(1)
    m = CELLS_RE.search(text)
    if m:
        row["cells"] = m.group(1)
    m = SOLUTION_BOXES_RE.search(text)
    if m:
        row["solution_boxes"] = m.group(1)
    m = BOUNDARY_BOXES_RE.search(text)
    if m:
        row["boundary_boxes"] = m.group(1)
    m = UNKNOWN_BOXES_RE.search(text)
    if m:
        row["unknown_boxes"] = m.group(1)
    m = PENDING_BOXES_RE.search(text)
    if m:
        row["pending_boxes"] = m.group(1)

    # No explicit verdict word found: classify from known failure patterns.
    if row["status"] == "unknown":
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
