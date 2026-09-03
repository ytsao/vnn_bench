#!/usr/bin/env python3
"""Summarize gurobi result JSON files into one CSV per benchmark folder.

gurobi's "json" output is not pure JSON: only the first couple of lines are
JSON records (start marker + statistics), the rest is gurobi's raw solver
log. Like scip, jet never prints "sat"/"unsat"/"timeout" for gurobi itself:
it prints the raw GRB_IntAttr_Status code as the very last line (see
jet/include/gurobi.hpp). jet's own convention there is what this script
mirrors: the problem is encoded as "find a counter-example", so an optimal
(feasible) solution means the property is violated ("sat"), and a proven-
infeasible problem means the property holds ("unsat").

Usage:
    python3 postprocess_gurobi.py <root-dir> [output-dir]

<root-dir> either holds *.json result files directly (a single benchmark),
or contains one subdirectory per benchmark (e.g. gurobi-cpu-cersyve), each
holding *.json files directly (not recursively). One CSV is written per
benchmark, named "<benchmark-dir-name>.csv".
"""
import sys
import re
import json
import csv
from pathlib import Path

# GRB_IntAttr_Status values, from gurobi_c.h / the Gurobi reference manual.
GRB_STATUS_TO_VERDICT = {
    2: "sat",      # GRB_OPTIMAL: optimal (feasible) solution found -> counter-example exists
    3: "unsat",    # GRB_INFEASIBLE: proven infeasible -> no counter-example, property holds
    9: "timeout",  # GRB_TIME_LIMIT
}

# The status line is just a bare integer, printed as the last line of stdout.
STATUS_LINE_RE = re.compile(r"^\d+$")


def parse_result_file(path):
    row = {
        "configuration": path.stem,
        "vnn_verifier": "",
        "network_filename": "",
        "vnnlib_filename": "",
        "timeout": "",
        "datetime": "",
        "status": "unknown",
        "grb_status_code": "",
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

    # jet prints the bare GRB status code as its last line of output.
    non_empty = [l.strip() for l in lines if l.strip()]
    if non_empty and STATUS_LINE_RE.match(non_empty[-1]):
        code = int(non_empty[-1])
        row["grb_status_code"] = code
        row["status"] = GRB_STATUS_TO_VERDICT.get(code, "unknown")
    else:
        # No bare status code found: classify from known failure patterns.
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

    # If root itself holds gurobi_*.json files directly, treat it as a single
    # benchmark. Otherwise scan its subdirectories, keeping only those that
    # actually contain gurobi result files (skips unrelated leftover folders,
    # e.g. a copied workflow directory holding a stray hardware-info json).
    if sorted(root.glob("gurobi_*.json")):
        benchmark_dirs = [root]
    else:
        benchmark_dirs = sorted(
            p for p in root.iterdir() if p.is_dir() and sorted(p.glob("gurobi_*.json"))
        )

    if not benchmark_dirs:
        print(f"No gurobi_*.json files found under {root}")
        sys.exit(1)

    for benchmark_dir in benchmark_dirs:
        json_files = sorted(benchmark_dir.glob("gurobi_*.json"))
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
