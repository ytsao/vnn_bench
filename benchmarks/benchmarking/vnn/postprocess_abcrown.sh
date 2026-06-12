#!/bin/bash

set -x

# Check if a directory was provided as an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <campaign-directory>"
    exit 1
fi

# Create a temporary directory with all the yaml files for mzn-bench.
VNNBENCH_TMP=$1/tmp
mkdir -p $VNNBENCH_TMP
VNNBENCH_TMP=$(realpath $VNNBENCH_TMP)
for file in $1/*.json; do
  python3 postprocess_abcrown.py $VNNBENCH_TMP $file
done

python3 $(dirname "$0")/collect_json_results.py $VNNBENCH_TMP $1/../$(basename $1)_json.csv


python3 $(dirname "$0")/collect_statistics.py $VNNBENCH_TMP $1/../$(basename $1).csv

