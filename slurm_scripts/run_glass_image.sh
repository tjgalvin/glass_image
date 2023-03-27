#!/usr/bin/env bash 
#SBATCH --ntasks-per-node 12 
#SBATCH --mem 105G
#SBATCH -t 7:00:00 
#SBATCH -o logs/glass_img_%J.out
#SBATCH -e logs/glass_img_%J.err
#SBATCH --qos express

echo "slurm job id is " $SLURM_JOB_ID

echo "Source my home profile"
source /home/$(whoami)/.bashrc

conda activate glass_image
module load singularity

echo "Current directory is " $(pwd)

SRC="${1}"
MS=$(basename "${SRC}")
PDIR=$(dirname "${SRC}")

echo $MS
echo $SRC
echo Switching to  $PDIR

cd "$PDIR" || exit 1
echo "Current directory is " $(pwd)

echo Attempting to run glass_image script
glass_image \
	-v \
	--wsclean-image "/scratch2/projects/spiceracs/field_test/modwsclean.sif" \
	"${MS}" \
	"/scratch2/projects/cass_glass/tjg-wsclean/glass_cband_config.yaml"



