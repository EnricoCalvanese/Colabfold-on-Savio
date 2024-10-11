#!/bin/bash
# Job name:
#SBATCH --job-name=colabfold
#SBATCH --account=fc_rnaseq
#SBATCH --partition=savio3_gpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --qos=savio_lowprio
#SBATCH --gres=gpu:A40:1
#SBATCH --time=72:00:00
##Command(s) to run:
module load python
python runcolabfold.py
