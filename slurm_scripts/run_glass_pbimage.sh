#!/usr/bin/env bash
#SBATCH --ntasks-per-node 2 
#SBATCH --mem 20G
#SBATCH -t 7:00:00 
#SBATCH -o logs/glass_pbimg_%J.out
#SBATCH -e logs/glass_pbimg_%J.err
#SBATCH --qos express

echo "slurm job id is " $SLURM_JOB_ID

echo "Source my home profile"
source /home/$(whoami)/.bashrc

conda activate glass_image
module load singularity

echo "Current directory is " $(pwd)

SRC="${1}"
IMAGE=$(basename "${SRC}")
PDIR=$(dirname "${SRC}")

echo $IMAGE
echo $SRC
echo Switching to  $PDIR

cd "$PDIR" || exit 1
echo "Current directory is " $(pwd)

echo Attempting to run glass_image script
glass_pbimage \
	-v \
        "$IMAGE"




