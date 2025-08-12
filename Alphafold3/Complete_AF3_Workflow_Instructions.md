# AlphaFold 3 Workflow for IMB2-RBF Multimer Predictions

## Overview
This workflow converts your existing ColabFold FASTA files to AlphaFold 3 JSON format and runs batch predictions on Savio HPC cluster. The workflow is optimized for your specific directory structure and maintains the same prediction scope as your original analysis.

## Prerequisites Verification

### 1. Model Parameters
**CRITICAL**: Verify your model parameters file format:
```bash
# Check if the file needs decompression
ls -la /global/home/users/enricocalvane/af3-model-param.bin.zst
file /global/home/users/enricocalvane/af3-model-param.bin.zst
```

If the file shows as "Zstandard compressed data", it needs decompression. The preparation script will handle this.

### 2. Account Information
You'll need to update the SLURM account in the batch runner script:
- Replace `fc_bioinf` with your actual Savio account name
- Check your allocation: `sacctmgr show associations user=$USER`

## Step-by-Step Workflow

### Step 1: Run Preparation Script
```bash
# Make the preparation script executable and run it
chmod +x AF3_preparation_steps.sh
./AF3_preparation_steps.sh
```

This will:
- Create optimized directory structure
- Decompress model parameters if needed
- Verify your existing FASTA files

### Step 2: Convert FASTA to JSON Format
```bash
# Navigate to the new working directory
cd /global/scratch/users/enricocalvane/IMB2_AF3_Analysis

# Load required modules
module load python
module load bio/biopython

# Run the conversion script
python convert_fasta_to_af3_json.py
```

Expected output: 43 JSON files in the `inputs/` directory, each containing properly formatted AlphaFold 3 input.

### Step 3: Run Batch Predictions (Your Preferred Sequential Method)
```bash
# Ensure you're in the analysis directory
cd /global/scratch/users/enricocalvane/IMB2_AF3_Analysis

# Make the SLURM submission script executable
chmod +x submit_af3_batch.sh

# Submit the 72-hour batch job (processes predictions sequentially)
sbatch submit_af3_batch.sh

# Or use the convenience script:
chmod +x cleanup_and_restart.sh
./cleanup_and_restart.sh submit
```

### Step 4: Monitor Progress and Manage Jobs
```bash
# Check job queue
squeue -u $USER

# Check detailed status of all predictions
./cleanup_and_restart.sh status

# View the running job output
tail -f logs/af3_batch_JOBID.out

# When job finishes (due to wall-time or completion), restart if needed:
./cleanup_and_restart.sh submit

# If some predictions failed, reset them and resubmit:
./cleanup_and_restart.sh reset-failed
./cleanup_and_restart.sh submit
```

## Directory Structure After Setup

```
/global/scratch/users/enricocalvane/IMB2_AF3_Analysis/
├── inputs/                    # JSON files for AF3
│   ├── AT2G16950_AT1G02870.1.json
│   ├── AT2G16950_AT1G31970.1.json
│   └── ... (43 total files)
├── outputs/                   # AF3 prediction results
│   ├── AT2G16950_AT1G02870.1/
│   │   ├── fold_input.json
│   │   ├── summary_confidences.json
│   │   ├── ranking_debug.json
│   │   └── ... (prediction files)
│   └── ...
├── logs/                      # SLURM job logs
├── scripts/                   # Generated SLURM scripts
└── conversion_report.txt      # Summary of FASTA→JSON conversion
```

## Key Differences from ColabFold

### Input Format
- **ColabFold**: Single FASTA with `:` separator
- **AlphaFold 3**: JSON with structured protein entries

### Job Management Strategy
- **ColabFold**: Sequential processing within long-running jobs (your successful approach)
- **AlphaFold 3**: Same sequential strategy - one 72-hour job processes multiple predictions
- **Advantage**: Maximum resource utilization, simple job management

### Status Tracking
- **ColabFold**: `colab.running` and `colab.done` files
- **AlphaFold 3**: `af3.running`, `af3.done`, `af3.error`, `af3.timeout` files
- **Same principle**: Skip completed work, resume after interruptions

## Resource Requirements

### Computational Resources
- **GPU**: A5000 (as specified in Savio documentation)
- **Time**: 4 hours per job (conservative estimate)
- **CPUs**: 4 per job
- **Memory**: Handled by unified memory in AF3 3.0.1

### Storage Requirements
- **Input**: ~1 MB per JSON file (43 files)
- **Output**: ~100-500 MB per prediction (depends on complex size)
- **Total estimated**: ~20-50 GB for all predictions

## Quality Control and Validation

### Verification Steps
1. **JSON Validation**: Each JSON file is validated during conversion
2. **Sequence Integrity**: Original FASTA sequences are preserved exactly
3. **Job Tracking**: Status markers prevent duplicate submissions
4. **Error Logging**: Comprehensive logging for troubleshooting

### Expected Results Comparison
Your AlphaFold 3 predictions should show:
- **Improved accuracy** for protein-protein interfaces
- **Better confidence scores** (pLDDT and other metrics)
- **Enhanced structural quality** especially at interaction sites
- **Similar overall topology** with refined details

## Troubleshooting

### Common Issues
1. **Model Parameters Error**: Ensure file is properly decompressed
2. **Account/Partition Issues**: Verify Savio account and GPU availability
3. **Memory Issues**: Use `3.0.1_largemem` for large complexes (>5120 tokens)
4. **JSON Format Errors**: Check conversion report for any parsing issues

### Job Failure Recovery
```bash
# Remove failed job markers to restart
rm outputs/COMPLEX_NAME/af3.failed
rm outputs/COMPLEX_NAME/af3.running

# Resubmit failed jobs
python run_alphafold3_batch.py
```

## Performance Optimization

### Concurrent Job Management
- Start with 5 concurrent jobs to test system load
- Monitor with `squeue` and adjust based on cluster availability
- Savio4_gpu partition typically allows good throughput

### Resource Utilization
- Jobs use temporary storage ($TMPDIR) to reduce I/O load
- Results are copied to permanent storage only upon completion
- Failed jobs clean up temporary files automatically

## Results Analysis

### Output Interpretation
AlphaFold 3 provides several confidence metrics:
- **pLDDT**: Per-residue confidence (similar to AF2)
- **Interface confidence**: Specific to protein-protein interactions
- **Summary confidences**: Overall complex quality assessment

### Comparison with ColabFold Results
To compare with your previous ColabFold predictions:
1. Focus on interface regions where AF3 typically shows improvement
2. Compare confidence scores at interaction sites
3. Analyze conformational
