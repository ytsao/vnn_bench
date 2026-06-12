#!/usr/bin/env python3
import sys
from pathlib import Path
import pandas as pd


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: collect_json_results.py <stats-dir> <output-csv>",
            file=sys.stderr,
        )
        return 1

    stats_dir = Path(sys.argv[1]).resolve()
    output_csv = Path(sys.argv[2])

    if not stats_dir.is_dir():
        print(f"Input directory does not exist: {stats_dir}", file=sys.stderr)
        return 1

    frames = []
    for csv_file in sorted(stats_dir.rglob("*_json.csv")):
        try:
            df = pd.read_csv(csv_file)
        except Exception as exc:
            print(f"Failed to read {csv_file}: {exc}", file=sys.stderr)
            return 1
        df["source_file"] = csv_file.name
        frames.append(df)

    if not frames:
        print(f"No JSON CSV files found in {stats_dir}", file=sys.stderr)
        return 1

    combined = pd.concat(frames, ignore_index=True, sort=False)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_csv, index=False, lineterminator="\n")
    print(f"Collected JSON results from {len(frames)} files.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
