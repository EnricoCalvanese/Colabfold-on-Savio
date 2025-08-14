#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlphaFold3 Confidence Score Extractor - Fixed Version
Extracts pLDDT, pTM, and ipTM scores from summary_confidences.json files
Author: Fixed for Enrico Calvane's analysis
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
        'mean_plddt': None,  # Will store ranking_score from AF3
        'ptm_score': None,
        'iptm_score': None,
        'fraction_disordered': None,
        'has_clash': None,
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
    
    # Find the actual summary file - it's in a subdirectory with lowercase name
    # Pattern: AT2G16950_AT1G02870.1/at2g16950_at1g02870.1/at2g16950_at1g02870.1_summary_confidences.json
    
    # Look for subdirectories that match the lowercase version of the parent directory name
    prediction_name_lower = output_dir.name.lower()
    subdirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name == prediction_name_lower]
    
    summary_file = None
    
    if subdirs:
        # Found the expected subdirectory
        subdir = subdirs[0]
        expected_summary_file = subdir / f"{prediction_name_lower}_summary_confidences.json"
        
        if expected_summary_file.exists():
            summary_file = expected_summary_file
        else:
            # Fallback: look for any file ending with _summary_confidences.json
            summary_files = list(subdir.glob("*_summary_confidences.json"))
            if summary_files:
                summary_file = summary_files[0]
    
    # If no subdirectory approach worked, try a broader search
    if summary_file is None:
        # Search recursively for any summary_confidences.json file
        summary_files = list(output_dir.rglob("*summary_confidences.json"))
        if summary_files:
            summary_file = summary_files[0]
    
    if summary_file is None:
        results['status'] = 'missing_summary'
        results['error_message'] = f'No summary_confidences.json found in {output_dir.name} or its subdirectories'
        return results
    
    try:
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
        
        # Extract the main confidence scores
        # AlphaFold3 uses ranking_score as the main confidence metric
        results['mean_plddt'] = summary_data.get('ranking_score')  # This is the main confidence score in AF3
        results['ptm_score'] = summary_data.get('ptm')  
        results['iptm_score'] = summary_data.get('iptm')
        
        # Also extract additional metrics available in AF3
        results['fraction_disordered'] = summary_data.get('fraction_disordered')
        results['has_clash'] = summary_data.get('has_clash')
        
        # Verify we got the essential scores
        if results['mean_plddt'] is None:
            results['error_message'] = f'No ranking_score in summary file: {summary_file.name}'
            
    except Exception as e:
        results['status'] = 'parsing_error'
        results['error_message'] = f"Error parsing {summary_file.name}: {str(e)}"
    
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

def assign_confidence_category(ranking_score):
    """
    Assign confidence category based on ranking score
    AlphaFold3 uses ranking_score instead of mean pLDDT
    Note: These thresholds may need adjustment based on AF3 specific ranges
    """
    if ranking_score is None:
        return 'Unknown'
    elif ranking_score >= 0.8:
        return 'Very High (≥0.8)'
    elif ranking_score >= 0.6:
        return 'High (0.6-0.8)'
    elif ranking_score >= 0.4:
        return 'Medium (0.4-0.6)'
    elif ranking_score >= 0.2:
        return 'Low (0.2-0.4)'
    else:
        return 'Very Low (<0.2)'

def main():
    """Extract confidence scores and create Excel file"""
    # Setup paths
    base_dir = Path("/global/scratch/users/enricocalvane/IMB2_AF3_Analysis")
    outputs_dir = base_dir / "outputs"
    inputs_dir = base_dir / "inputs"
    
    print(f"AlphaFold3 Confidence Score Extractor (Fixed Version)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using ranking_score from summary_confidences.json as main confidence metric")
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
            
            # Safe formatting to avoid None type errors
            plddt_str = f"{plddt:.3f}" if plddt is not None else 'N/A'
            ptm_str = f"{ptm:.3f}" if ptm is not None else 'N/A'
            iptm_str = f"{iptm:.3f}" if iptm is not None else 'N/A'
            
            print(f"  ✓ Ranking Score: {plddt_str} ({category}), "
                  f"pTM: {ptm_str}, "
                  f"ipTM: {iptm_str}")
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
        'fraction_disordered', 'has_clash',
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
        
        # High confidence predictions (ranking_score >= 0.6)
        if not completed_df.empty:
            high_conf_df = completed_df[completed_df['mean_plddt'] >= 0.6]
            if not high_conf_df.empty:
                high_conf_df.to_excel(writer, sheet_name='High_Confidence', index=False)
        
        # Summary statistics
        if not completed_df.empty:
            summary_data = {
                'Metric': [
                    'Total Predictions',
                    'Completed Successfully', 
                    'Failed/Timeout/Error',
                    'High Confidence (Ranking ≥ 0.6)',
                    'Very High Confidence (Ranking ≥ 0.8)',
                    'Mean Ranking Score (all completed)',
                    'Mean pTM (all completed)', 
                    'Mean ipTM (all completed)',
                    'Best Ranking Score',
                    'Best Interaction (by Ranking Score)'
                ],
                'Value': [
                    len(df),
                    len(completed_df),
                    len(df) - len(completed_df),
                    len(completed_df[completed_df['mean_plddt'] >= 0.6]) if not completed_df.empty else 0,
                    len(completed_df[completed_df['mean_plddt'] >= 0.8]) if not completed_df.empty else 0,
                    f"{completed_df['mean_plddt'].mean():.3f}" if not completed_df.empty else 'N/A',
                    f"{completed_df['ptm_score'].mean():.3f}" if not completed_df.empty else 'N/A',
                    f"{completed_df['iptm_score'].mean():.3f}" if not completed_df.empty else 'N/A',
                    f"{completed_df['mean_plddt'].max():.3f}" if not completed_df.empty else 'N/A',
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
        high_conf = completed_df[completed_df['mean_plddt'] >= 0.6]
        very_high_conf = completed_df[completed_df['mean_plddt'] >= 0.8]
        
        print(f"High confidence (Ranking ≥ 0.6): {len(high_conf)}")
        print(f"Very high confidence (Ranking ≥ 0.8): {len(very_high_conf)}")
        print(f"Average Ranking Score: {completed_df['mean_plddt'].mean():.3f}")
        print(f"Average pTM: {completed_df['ptm_score'].mean():.3f}")  
        print(f"Average ipTM: {completed_df['iptm_score'].mean():.3f}")
        
        print("\nTop 5 predictions by Ranking Score:")
        top_5 = completed_df.head(5)
        for _, row in top_5.iterrows():
            ranking_score = row['mean_plddt']
            ptm = row['ptm_score'] 
            iptm = row['iptm_score']
            
            ranking_str = f"{ranking_score:.3f}" if ranking_score is not None else 'N/A'
            ptm_str = f"{ptm:.3f}" if ptm is not None else 'N/A'
            iptm_str = f"{iptm:.3f}" if iptm is not None else 'N/A'
            
            print(f"  {row['interaction']:40} Ranking: {ranking_str}, "
                  f"pTM: {ptm_str}, ipTM: {iptm_str}")
    
    print(f"\n✓ Results saved to: {excel_file}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
