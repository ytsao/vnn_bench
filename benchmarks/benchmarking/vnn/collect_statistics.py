#!/usr/bin/env python3
import sys
import pandas as pd
from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML(typ="safe")

STANDARD_KEYS = [
    "configuration",
    "problem",
    "model",
    "data_file",
    "status",
    "time",
]


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: collect_statistics.py <stats-dir> <output-csv>",
            file=sys.stderr,
        )
        return 1

    stats_dir = Path(sys.argv[1]).resolve()
    output_csv = Path(sys.argv[2])

    if not stats_dir.is_dir():
        print(f"Input directory does not exist: {stats_dir}", file=sys.stderr)
        return 1

    # Load all stats files into a list of dictionaries
    rows = []
    for yaml_file in sorted(stats_dir.rglob("*_stats.yml")):
        with yaml_file.open() as fp:
            stats = yaml.load(fp)
        if stats:
            stats["run"] = stats_dir.name
            rows.append(stats)

    if not rows:
        print(f"No statistics files found in {stats_dir}", file=sys.stderr)
        return 1

    # Create DataFrame from all rows
    df = pd.DataFrame(rows)

    # Determine column order: standard keys first, then extra keys alphabetically
    extra_keys = sorted([c for c in df.columns if c not in STANDARD_KEYS])
    ordered_columns = STANDARD_KEYS + extra_keys
    
    # Select only columns that exist in the dataframe
    ordered_columns = [c for c in ordered_columns if c in df.columns]
    df = df[ordered_columns]

    # Write to CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, lineterminator="\n")

    print(f"Collected statistics from {len(rows)} files.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
