#!/bin/bash
# AlphaFold 3 Preparation Steps for IMB2-RBF Predictions
# Run these commands step by step to prepare your data structure

# 1. Create new organized directory structure
mkdir -p /global/scratch/users/enricocalvane/IMB2_AF3_Analysis
cd /global/scratch/users/enricocalvane/IMB2_AF3_Analysis

# Create subdirectories
mkdir -p inputs
mkdir -p outputs
mkdir -p logs
mkdir -p scripts

# 2. Verify and prepare model parameters
echo "Checking model parameters file..."
MODEL_PARAM_DIR="/global/home/users/enricocalvane/model_param"
mkdir -p $MODEL_PARAM_DIR

# Check if your file needs decompression
if [ -f "/global/home/users/enricocalvane/af3-model-param.bin.zst" ]; then
    echo "Found model parameters file. Checking if decompression is needed..."
    
    # If the file is compressed, decompress it
    if [[ "/global/home/users/enricocalvane/af3-model-param.bin.zst" == *.zst ]]; then
        echo "Decompressing model parameters..."
        zstd -d /global/home/users/enricocalvane/af3-model-param.bin.zst -o $MODEL_PARAM_DIR/af3.bin
    else
        echo "Copying model parameters..."
        cp /global/home/users/enricocalvane/af3-model-param.bin.zst $MODEL_PARAM_DIR/af3.bin
    fi
else
    echo "ERROR: Model parameters file not found at specified path!"
    echo "Please verify the path: /global/home/users/enricocalvane/af3-model-param.bin.zst"
    exit 1
fi

# 3. List all your current FASTA directories for verification
echo "Current FASTA directories in RBFs:"
ls -la /global/scratch/users/enricocalvane/IMB2ColabFold/RBFs/ | head -10
echo "Total directories found:"
ls -d /global/scratch/users/enricocalvane/IMB2ColabFold/RBFs/AT*/ | wc -l

echo ""
echo "Preparation steps completed. Please run the conversion script next."
echo "New working directory: /global/scratch/users/enricocalvane/IMB2_AF3_Analysis"
