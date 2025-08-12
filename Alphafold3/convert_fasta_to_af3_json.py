#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASTA to AlphaFold3 JSON Converter for IMB2-RBF Multimer Predictions
Converts ColabFold FASTA format to AlphaFold3 JSON input format
Author: Automated conversion for Enrico Calvane's analysis
"""

import os
import json
import re
from Bio import SeqIO
from pathlib import Path

def parse_colabfold_fasta(fasta_file):
    """
    Parse ColabFold FASTA format with ':' separator
    Returns tuple of (protein1_seq, protein2_seq, complex_name)
    """
    with open(fasta_file, 'r') as f:
        record = SeqIO.read(f, 'fasta')
        
    # Extract sequences split by ':'
    full_sequence = str(record.seq)
    if ':' not in full_sequence:
        raise ValueError(f"No ':' separator found in {fasta_file}")
    
    sequences = full_sequence.split(':')
    if len(sequences) != 2:
        raise ValueError(f"Expected exactly 2 sequences in {fasta_file}, found {len(sequences)}")
    
    protein1_seq = sequences[0].strip()
    protein2_seq = sequences[1].strip()
    complex_name = record.id
    
    return protein1_seq, protein2_seq, complex_name

def create_af3_json(protein1_seq, protein2_seq, complex_name, model_seeds=[1]):
    """
    Create AlphaFold3 JSON input structure
    """
    af3_input = {
        "name": complex_name,
        "sequences": [
            {
                "protein": {
                    "id": ["A"],
                    "sequence": protein1_seq
                }
            },
            {
                "protein": {
                    "id": ["B"], 
                    "sequence": protein2_seq
                }
            }
        ],
        "modelSeeds": model_seeds,
        "dialect": "alphafold3",
        "version": 1
    }
    
    return af3_input

def convert_all_fasta_files():
    """
    Convert all FASTA files from RBFs directory structure to AF3 JSON format
    """
    # Source and destination directories
    source_dir = "/global/scratch/users/enricocalvane/IMB2ColabFold/RBFs"
    dest_dir = "/global/scratch/users/enricocalvane/IMB2_AF3_Analysis/inputs"
    
    # Ensure destination directory exists
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    
    # Track conversion statistics
    converted_count = 0
    error_count = 0
    error_log = []
    
    print(f"Starting conversion from {source_dir} to {dest_dir}")
    print("="*60)
    
    # Get all subdirectories that start with AT
    subdirs = [d for d in os.listdir(source_dir) if d.startswith("AT") and os.path.isdir(os.path.join(source_dir, d))]
    
    print(f"Found {len(subdirs)} directories to process")
    
    for subdir in sorted(subdirs):
        subdir_path = os.path.join(source_dir, subdir)
        fasta_file = os.path.join(subdir_path, f"{subdir}.fasta")
        
        if not os.path.exists(fasta_file):
            print(f"WARNING: FASTA file not found: {fasta_file}")
            error_count += 1
            error_log.append(f"Missing FASTA: {subdir}")
            continue
        
        try:
            # Parse FASTA file
            protein1_seq, protein2_seq, complex_name = parse_colabfold_fasta(fasta_file)
            
            # Create JSON structure
            af3_json = create_af3_json(protein1_seq, protein2_seq, complex_name)
            
            # Save JSON file
            json_filename = f"{subdir}.json"
            json_path = os.path.join(dest_dir, json_filename)
            
            with open(json_path, 'w') as json_file:
                json.dump(af3_json, json_file, indent=2)
            
            print(f"✓ Converted: {subdir} -> {json_filename}")
            print(f"   Protein 1: {len(protein1_seq)} residues")
            print(f"   Protein 2: {len(protein2_seq)} residues")
            converted_count += 1
            
        except Exception as e:
            print(f"✗ ERROR processing {subdir}: {str(e)}")
            error_count += 1
            error_log.append(f"Error in {subdir}: {str(e)}")
    
    # Summary report
    print("="*60)
    print("CONVERSION SUMMARY:")
    print(f"Successfully converted: {converted_count}")
    print(f"Errors encountered: {error_count}")
    print(f"Total directories processed: {len(subdirs)}")
    
    if error_log:
        print("\nERROR DETAILS:")
        for error in error_log:
            print(f"  - {error}")
    
    # Save conversion report
    report_path = os.path.join("/global/scratch/users/enricocalvane/IMB2_AF3_Analysis", "conversion_report.txt")
    with open(report_path, 'w') as report_file:
        report_file.write("FASTA to AF3 JSON Conversion Report\n")
        report_file.write("="*50 + "\n")
        report_file.write(f"Successfully converted: {converted_count}\n")
        report_file.write(f"Errors encountered: {error_count}\n")
        report_file.write(f"Total directories processed: {len(subdirs)}\n\n")
        
        if error_log:
            report_file.write("Error Details:\n")
            for error in error_log:
                report_file.write(f"  - {error}\n")
    
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    convert_all_fasta_files()
