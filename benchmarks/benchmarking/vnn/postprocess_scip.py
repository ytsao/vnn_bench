#!/usr/bin/env python3
"""Summarize scip result JSON files into one CSV per benchmark folder.

scip's "json" output is not pure JSON: only the first couple of lines are
JSON records (start marker + statistics), the rest is scip's raw stdout.
Unlike ibex/z3, scip never prints "sat"/"unsat"/"timeout" itself: jet prints
"SCIP status: <code>" as the last line, where the code is a SCIP_STATUS enum
value (see jet/include/scip.hpp). jet's own convention there is what this
script mirrors: the problem is encoded as "find a counter-example", so a
feasible/optimal solution means the property is violated ("sat"), and a
proven-infeasible problem means the property holds ("unsat").

Usage:
    python3 postprocess_scip.py <root-dir> [output-dir]

<root-dir> either holds *.json result files directly (a single benchmark),
or contains one subdirectory per benchmark, each holding *.json files
directly (not recursively). One CSV is written per benchmark, named
"<benchmark-dir-name>.csv".
"""
import sys
import re
import json
import csv
from pathlib import Path

# SCIP_STATUS enum values, from scip/src/scip/type_stat.h.
SCIP_STATUS_TO_VERDICT = {
    1: "sat",      # SCIP_STATUS_OPTIMAL: optimal (feasible) solution found -> counter-example exists
    2: "unsat",    # SCIP_STATUS_INFEASIBLE: proven infeasible -> no counter-example, property holds
    23: "timeout", # SCIP_STATUS_TIMELIMIT
}

SCIP_STATUS_LINE_RE = re.compile(r"SCIP status:\s*(\d+)")


def parse_result_file(path):
    row = {
        "configuration": path.stem,
        "vnn_verifier": "",
        "network_filename": "",
        "vnnlib_filename": "",
        "timeout": "",
        "datetime": "",
        "status": "unknown",
        "scip_status_code": "",
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

    # jet prints "SCIP status: <code>" as its last line of output.
    m = SCIP_STATUS_LINE_RE.search(text)
    if m:
        code = int(m.group(1))
        row["scip_status_code"] = code
        row["status"] = SCIP_STATUS_TO_VERDICT.get(code, "unknown")
    else:
        # No "SCIP status:" line found: classify from known failure patterns.
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
        json_files = sorted(benchmark_dir.glob("scip_*.json")) or sorted(benchmark_dir.glob("*.json"))
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
