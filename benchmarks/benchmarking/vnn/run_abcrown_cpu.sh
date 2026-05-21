#!/bin/bash -l
#SBATCH --time=00:10:00
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --exclusive
#SBATCH --ntasks-per-node=4 # 4 GPUs so 4 tasks per nodes.
#SBATCH --mem=0
#SBATCH -A p201230
#SBATCH --qos=dev
#SBATCH --export=ALL
#SBATCH --output=slurm-abcrown-cpu.out

# Shortcuts of paths to benchmarking directories.
VNN_WORKFLOW_PATH=$(dirname $(realpath "run.sh"))
BENCHMARKING_DIR_PATH="$VNN_WORKFLOW_PATH/.."
BENCHMARKS_DIR_PATH="$VNN_WORKFLOW_PATH/../.."

# Configure the environment.
if [ -z "$1" ]; then
  echo "Usage: $0 <machine.sh>"
  echo "  Name of the machine running the experiments with the configuration of the environment."
  exit 1
fi

source $1
source ${BENCHMARKS_DIR_PATH}/../pybench/bin/activate

# If it has an argument, we retry the jobs that failed on a previous run.
# If the experiments were not complete, you can simply rerun the script, parallel will ignore the jobs that are already done.
if [ -n "$2" ]; then
  parallel --retry-failed --joblog $2
  exit 0
fi

# I. Define the campaign to run.
VNN_VERIFIER="abcrown"
CATEGORY="acasxu_2023"
DEVICE="cpu"
VERSION="$DEVICE-$CATEGORY" # Note that this is only for the naming of the output directory, we do not verify the actual version of the solver.
CORES=1 # The number of cores used on the node.
MACHINE=$(basename "$1" ".sh")
INSTANCES_PATH="$BENCHMARKS_DIR_PATH/data/vnncomp2025_benchmarks/benchmarks/$CATEGORY/instances.csv"

# II. Prepare the command lines and output directory.
CONDA_PYTHON="/project/home/p201230/conda_base_path/miniconda3/envs/alpha-beta-crown/bin/python"
VNN_COMMAND="$CONDA_PYTHON $VNN_WORKFLOW_PATH/../../../../../alpha-beta-CROWN/complete_verifier/vnncomp_main.py"
OUTPUT_DIR="$BENCHMARKS_DIR_PATH/campaign/$MACHINE/$VNN_VERIFIER-$VERSION"
mkdir -p $OUTPUT_DIR

# If we are on the HPC, we encapsulate the command in a srun command to reserve the resources needed.
if [ -n "${SLURM_JOB_NODELIST}" ]; then
  SRUN_COMMAND="srun --exclusive --cpus-per-task=$CORES --gpus-per-task=1 --nodes=1 --ntasks=1 --cpu-bind=verbose"
  NUM_PARALLEL_EXPERIMENTS=$((SLURM_JOB_NUM_NODES * 4)) # How many experiments are we running in parallel? One per GPU per default.
else
  NUM_PARALLEL_EXPERIMENTS=1
fi

DUMP_PY_PATH="$VNN_WORKFLOW_PATH/dump.py"

# For replicability.
cp -r $VNN_WORKFLOW_PATH $OUTPUT_DIR/
cp $INSTANCES_PATH $OUTPUT_DIR/$(basename "$VNN_WORKFLOW_PATH")/

# Store the description of the hardware on which this campaign is run.
lshw -json > $OUTPUT_DIR/$(basename "$VNN_WORKFLOW_PATH")/hardware-"$MACHINE".json 2> /dev/null

# III. Run the experiments in parallel.
# The `parallel` command spawns one `srun` command per experiment, which executes the orca verifier with the right resources.
COMMANDS_LOG="$OUTPUT_DIR/$(basename "$VNN_WORKFLOW_PATH")/jobs.log"
parallel --verbose --no-run-if-empty --rpl '{} uq()' -k --colsep ',' -j $NUM_PARALLEL_EXPERIMENTS --resume --joblog $COMMANDS_LOG $SRUN_COMMAND $VNN_COMMAND $CATEGORY ${BENCHMARKS_DIR_PATH}/data/vnncomp2025_benchmarks/benchmarks/${CATEGORY}/{1} ${BENCHMARKS_DIR_PATH}/data/vnncomp2025_benchmarks/benchmarks/${CATEGORY}/{2} "${VNN_VERIFIER}_${VERSION}.csv" {3} --NOPGD --TRY_CROWN '2>&1' '|' python3 $DUMP_PY_PATH $OUTPUT_DIR $VNN_VERIFIER {1} {2} {3} :::: $INSTANCES_PATH
