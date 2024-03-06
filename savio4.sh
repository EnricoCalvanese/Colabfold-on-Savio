#!/bin/bash
# Job name:
#SBATCH --job-name=colabfold
#SBATCH --account=fc_rnaseq
#SBATCH --partition=savio4_gpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --qos=a5k_gpu4_normal
#SBATCH --gres=gpu:A5000:1
#SBATCH --time=72:00:00
##Command(s) to run:
python runcolabfold.py
