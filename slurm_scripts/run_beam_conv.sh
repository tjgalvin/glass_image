#!/usr/bin/env bash
#SBATCH --ntasks-per-node 6 
#SBATCH --mem 50G
#SBATCH -t 7:00:00 
#SBATCH -o logs/beamcon_%J.out
#SBATCH -e logs/beamcon_%J.err
#SBATCH --qos express

echo "slurm job id is " $SLURM_JOB_ID

echo "Source my home profile"
source /home/$(whoami)/.bashrc

conda activate racs-tools
module load singularity
module load miriad 

echo "Current directory is " $(pwd)

WORKDIR="${1}"

echo "Switching to ${WORKDIR}"
cd "$PDIR" || exit 1
echo "Current directory is " $(pwd)

echo Attempting to run beamconv_2D
beamconv_2D \
	-v \
	--ncores 4 \
        *images.fits




