#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlphaFold3 Confidence Score Extractor - Simplified Version
Extracts pLDDT, pTM, and ipTM scores from summary_confidences.json files
Author: Simplified for Enrico Calvane's analysis
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def extract_confidence_scores(output_dir):
    """
    Extract confidence scores from AlphaFold3 summary_confidences.json
    This file contains the final scores for the top-ranked model
    """
    results = {
        'prediction_name': output_dir.name,
        'status': 'unknown',
        'mean_plddt': None,
        'ptm_score': None,
        'iptm_score': None,
        'error_message': None
    }
    
    # Check prediction status
    if (output_dir / "af3.done").exists():
        results['status'] = 'completed'
    elif (output_dir / "af3.running").exists():
        results['status'] = 'running'
        return results
    elif (output_dir / "af3.error").exists():
        results['status'] = 'failed'
        try:
            with open(output_dir / "af3.error", 'r') as f:
                results['error_message'] = f.read().strip()[:200]
        except:
            results['error_message'] = 'Error reading error file'
        return results
    elif (output_dir / "af3.timeout").exists():
        results['status'] = 'timeout'
        return results
    else:
        results['status'] = 'not_started'
        return results
    
    # Extract scores from summary_confidences.json (the authoritative source)
    summary_file = output_dir / "summary_confidences.json"
    
    if not summary_file.exists():
        results['status'] = 'missing_summary'
        results['error_message'] = 'summary_confidences.json not found'
        return results
    
    try:
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
        
        # Extract the main confidence scores
        # These are the final scores for the top-ranked model
        results['mean_plddt'] = summary_data.get('confidence_score')
        results['ptm_score'] = summary_data.get('ptm')  
        results['iptm_score'] = summary_data.get('iptm')
        
        # Verify we got the essential scores
        if results['mean_plddt'] is None:
            results['error_message'] = 'No confidence_score in summary file'
            
    except Exception as e:
        results['status'] = 'parsing_error'
        results['error_message'] = f"Error parsing summary_confidences.json: {str(e)}"
    
    return results

def get_sequence_lengths_from_input(json_file):
    """
    Get sequence lengths from original input JSON file
    """
    try:
        with open(json_file, 'r') as f:
            input_data = json.load(f)
        
        sequences = input_data.get('sequences', [])
        if len(sequences) >= 2:
            seq_a = sequences[0].get('protein', {}).get('sequence', '')
            seq_b = sequences[1].get('protein', {}).get('sequence', '')
            
            return len(seq_a), len(seq_b)
    except:
        pass
    
    return None, None

def parse_protein_names(prediction_name):
    """
    Parse protein names from prediction directory name
    Format: AT2G16950_AT1G02870.1 -> IMB2 (AT2G16950) + RBF (AT1G02870.1)
    """
    try:
        parts = prediction_name.split('_', 1)  # Split on first underscore only
        if len(parts) >= 2:
            return parts[0], parts[1]  # AT2G16950, AT1G02870.1
    except:
        pass
    
    return prediction_name, 'unknown'

def assign_confidence_category(plddt):
    """
    Assign confidence category based on pLDDT score
    Standard AlphaFold confidence levels
    """
    if plddt is None:
        return 'Unknown'
    elif plddt >= 90:
        return 'Very High (>90)'
    elif plddt >= 70:
        return 'High (70-90)'
    elif plddt >= 50:
        return 'Low (50-70)'
    else:
        return 'Very Low (<50)'

def main():
    """Extract confidence scores and create Excel file"""
    # Setup paths
    base_dir = Path("/global/scratch/users/enricocalvane/IMB2_AF3_Analysis")
    outputs_dir = base_dir / "outputs"
    inputs_dir = base_dir / "inputs"
    
    print(f"AlphaFold3 Confidence Score Extractor (Simplified)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using summary_confidences.json as authoritative source")
    print("="*60)
    
    # Get all output directories
    output_dirs = [d for d in outputs_dir.iterdir() if d.is_dir()]
    
    if not output_dirs:
        print("No output directories found!")
        return
    
    print(f"Found {len(output_dirs)} prediction directories")
    print()
    
    # Process each prediction
    all_results = []
    
    for output_dir in sorted(output_dirs):
        print(f"Processing: {output_dir.name}")
        
        # Extract confidence scores
        results = extract_confidence_scores(output_dir)
        
        # Add protein information
        imb2_id, rbf_id = parse_protein_names(output_dir.name)
        results['IMB2_protein'] = imb2_id
        results['RBF_protein'] = rbf_id
        results['interaction'] = f"{imb2_id} + {rbf_id}"
        
        # Add sequence lengths from input JSON
        input_json = inputs_dir / f"{output_dir.name}.json"
        if input_json.exists():
            seq_len_a, seq_len_b = get_sequence_lengths_from_input(input_json)
            results['IMB2_length'] = seq_len_a
            results['RBF_length'] = seq_len_b
            results['total_residues'] = (seq_len_a + seq_len_b) if (seq_len_a and seq_len_b) else None
        
        # Add confidence category
        results['confidence_category'] = assign_confidence_category(results['mean_plddt'])
        
        all_results.append(results)
        
        # Print summary for this prediction
        if results['status'] == 'completed':
            plddt = results['mean_plddt']
            ptm = results['ptm_score']
            iptm = results['iptm_score']
            category = results['confidence_category']
            print(f"  ✓ pLDDT: {plddt:.1f if plddt else 'N/A'} ({category}), "
                  f"pTM: {ptm:.3f if ptm else 'N/A'}, "
                  f"ipTM: {iptm:.3f if iptm else 'N/A'}")
        else:
            print(f"  ✗ Status: {results['status']}")
            if results['error_message']:
                print(f"    Error: {results['error_message'][:60]}...")
        print()
    
    # Create DataFrame with organized columns
    df = pd.DataFrame(all_results)
    
    # Organize columns logically
    column_order = [
        'prediction_name', 'IMB2_protein', 'RBF_protein', 'interaction',
        'status', 'confidence_category',
        'mean_plddt', 'ptm_score', 'iptm_score',
        'IMB2_length', 'RBF_length', 'total_residues',
        'error_message'
    ]
    
    df = df[[col for col in column_order if col in df.columns]]
    
    # Sort by pLDDT score (best predictions first)
    df = df.sort_values('mean_plddt', ascending=False, na_position='last')
    
    # Create Excel file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    excel_file = base_dir / f"IMB2_RBF_confidence_scores_{timestamp}.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # All results
        df.to_excel(writer, sheet_name='All_Predictions', index=False)
        
        # Successful predictions only
        completed_df = df[df['status'] == 'completed'].copy()
        if not completed_df.empty:
            completed_df.to_excel(writer, sheet_name='Completed', index=False)
        
        # High confidence predictions (pLDDT >= 70)
        if not completed_df.empty:
            high_conf_df = completed_df[completed_df['mean_plddt'] >= 70]
            if not high_conf_df.empty:
                high_conf_df.to_excel(writer, sheet_name='High_Confidence', index=False)
        
        # Summary statistics
        if not completed_df.empty:
            summary_data = {
                'Metric': [
                    'Total Predictions',
                    'Completed Successfully', 
                    'Failed/Timeout/Error',
                    'High Confidence (pLDDT ≥ 70)',
                    'Very High Confidence (pLDDT ≥ 90)',
                    'Mean pLDDT (all completed)',
                    'Mean pTM (all completed)', 
                    'Mean ipTM (all completed)',
                    'Best pLDDT Score',
                    'Best Interaction (by pLDDT)'
                ],
                'Value': [
                    len(df),
                    len(completed_df),
                    len(df) - len(completed_df),
                    len(completed_df[completed_df['mean_plddt'] >= 70]) if not completed_df.empty else 0,
                    len(completed_df[completed_df['mean_plddt'] >= 90]) if not completed_df.empty else 0,
                    f"{completed_df['mean_plddt'].mean():.2f}" if not completed_df.empty else 'N/A',
                    f"{completed_df['ptm_score'].mean():.3f}" if not completed_df.empty else 'N/A',
                    f"{completed_df['iptm_score'].mean():.3f}" if not completed_df.empty else 'N/A',
                    f"{completed_df['mean_plddt'].max():.2f}" if not completed_df.empty else 'N/A',
                    completed_df.iloc[0]['interaction'] if not completed_df.empty else 'N/A'
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Print final summary
    print("="*60)
    print("FINAL SUMMARY:")
    print(f"Total predictions: {len(df)}")
    print(f"Completed successfully: {len(completed_df)}")
    print(f"Failed/timeout/error: {len(df) - len(completed_df)}")
    
    if not completed_df.empty:
        high_conf = completed_df[completed_df['mean_plddt'] >= 70]
        very_high_conf = completed_df[completed_df['mean_plddt'] >= 90]
        
        print(f"High confidence (pLDDT ≥ 70): {len(high_conf)}")
        print(f"Very high confidence (pLDDT ≥ 90): {len(very_high_conf)}")
        print(f"Average pLDDT: {completed_df['mean_plddt'].mean():.2f}")
        print(f"Average pTM: {completed_df['ptm_score'].mean():.3f}")  
        print(f"Average ipTM: {completed_df['iptm_score'].mean():.3f}")
        
        print("\\nTop 5 predictions by pLDDT:")
        top_5 = completed_df.head(5)
        for _, row in top_5.iterrows():
            print(f"  {row['interaction']:40} pLDDT: {row['mean_plddt']:.1f}, "
                  f"pTM: {row['ptm_score']:.3f}, ipTM: {row['iptm_score']:.3f}")
    
    print(f"\\n✓ Results saved to: {excel_file}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
