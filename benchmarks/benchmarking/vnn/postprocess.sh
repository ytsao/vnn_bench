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
#for file in $1/*.json; do
#  python3 postprocess.py $VNNBENCH_TMP $file
#done

cd ..  # mzn-bench needs to access the model and data files from "../data".
#mzn-bench check-solutions $MZNBENCH_TMP || exit 1
mzn-bench check-statuses $VNNBENCH_TMP || exit 1
cd minizinc

Vnn-bench collect-objectives $VNNBENCH_TMP $1/../$(basename $1)-objectives.csv
vnn-bench collect-statistics $VNNBENCH_TMP $1/../$(basename $1).csv
