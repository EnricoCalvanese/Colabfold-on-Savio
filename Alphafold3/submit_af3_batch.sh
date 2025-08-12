#!/bin/bash
#SBATCH --job-name=af3_batch_IMB2
#SBATCH --account=fc_rnaseq
#SBATCH --partition=savio4_gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --qos=a5k_gpu4_normal
#SBATCH --gres=gpu:A5000:1
#SBATCH --time=72:00:00
#SBATCH --mail-user=enrico_calvane@berkeley.edu
#SBATCH --mail-type=ALL
#SBATCH --output=/global/scratch/users/enricocalvane/IMB2_AF3_Analysis/logs/af3_batch_%j.log

echo "=========================================="
echo "AlphaFold3 Batch Job Started"
echo "Job ID: $SLURM_JOB_ID"
echo "Started at: $(date)"
echo "Running on: $SLURMD_NODENAME"
echo "=========================================="

# Change to working directory
cd /global/scratch/users/enricocalvane/IMB2_AF3_Analysis

# Load required modules
module load bio/alphafold3/3.0.1

# Set model parameters directory
export MODEL_PARAMETERS_DIR=/global/home/users/enricocalvane/model_param

# Verify environment
echo "Environment check:"
echo "  ALPHAFOLD_DIR: $ALPHAFOLD_DIR"
echo "  DB_DIR: $DB_DIR"
echo "  MODEL_PARAMETERS_DIR: $MODEL_PARAMETERS_DIR"
echo "  Current directory: $(pwd)"

# Check if model parameters exist
if [ ! -d "$MODEL_PARAMETERS_DIR" ] || [ ! -f "$MODEL_PARAMETERS_DIR/af3.bin" ]; then
    echo "ERROR: Model parameters not found at $MODEL_PARAMETERS_DIR/af3.bin"
    echo "Please ensure the model parameters are properly installed."
    exit 1
fi

# Check if input files exist
if [ ! -d "inputs" ] || [ $(ls inputs/*.json 2>/dev/null | wc -l) -eq 0 ]; then
    echo "ERROR: No JSON input files found in inputs/ directory"
    echo "Please run the FASTA to JSON conversion first."
    exit 1
fi

echo ""
echo "Starting sequential AlphaFold3 predictions..."
echo "This job will run for up to 72 hours, processing predictions sequentially."
echo "Progress will be logged to this output file."
echo ""

# Run the Python script
python run_alphafold3_batch.py

echo ""
echo "=========================================="
echo "AlphaFold3 Batch Job Finished"
echo "Ended at: $(date)"
echo "=========================================="
