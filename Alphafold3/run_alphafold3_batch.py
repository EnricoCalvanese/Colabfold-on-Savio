#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlphaFold3 Sequential Batch Runner for IMB2-RBF Multimer Predictions on Savio
Simple approach following the proven ColabFold workflow pattern
Author: Simplified for Enrico Calvane's workflow
"""

import os
import json
import subprocess
import time
from pathlib import Path
import sys

def main():
    """Main sequential prediction loop - simple approach like the original ColabFold script"""
    # Setup paths
    base_dir = Path("/global/scratch/users/enricocalvane/IMB2_AF3_Analysis")
    inputs_dir = base_dir / "inputs"
    outputs_dir = base_dir / "outputs"
    model_params_dir = "/global/home/users/enricocalvane/model_param"
    
    # Change to the outputs directory (like the original script)
    os.chdir(outputs_dir)
    
    # Get all JSON files and create corresponding directory names
    json_files = sorted(list(inputs_dir.glob("*.json")))
    
    if not json_files:
        print("No JSON files found in inputs directory!")
        sys.exit(1)
    
    print(f"AlphaFold3 Sequential Batch Runner")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Found {len(json_files)} JSON files for processing")
    print(f"Working directory: {os.getcwd()}")
    print(f"Process ID: {os.getpid()}")
    print(f"SLURM Job ID: {os.environ.get('SLURM_JOB_ID', 'unknown')}")
    
    # Create list of directory names (like the original "fastas" list)
    job_dirs = [json_file.stem for json_file in json_files]
    
    successful_predictions = 0
    failed_predictions = 0
    skipped_predictions = 0
    
    # Main loop - exactly like the original ColabFold script
    for job_name in job_dirs:
        # Create job directory if it doesn't exist
        os.makedirs(job_name, exist_ok=True)
        os.chdir(job_name)
        
        # Simple check - exactly like the original script
        if "af3.running" not in os.listdir() and "af3.done" not in os.listdir():
            print(f"\\n{'='*60}")
            print(f"Starting prediction: {job_name}")
            print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Process ID: {os.getpid()}")
            print(f"SLURM Job ID: {os.environ.get('SLURM_JOB_ID', 'unknown')}")
            print(f"{'='*60}")
            
            # Create running marker immediately (like original script)
            with open("af3.running", "w") as o:
                o.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
                o.write(f"Process ID: {os.getpid()}\\n")
                o.write(f"Job ID: {os.environ.get('SLURM_JOB_ID', 'unknown')}\\n")
            
            # Get the corresponding JSON file
            json_file = inputs_dir / f"{job_name}.json"
            
            # Create temporary directories
            temp_input_dir = f"/tmp/af_input_{job_name}_{os.getpid()}"
            temp_output_dir = f"/tmp/af_output_{job_name}_{os.getpid()}"
            
            try:
                os.makedirs(temp_input_dir, exist_ok=True)
                os.makedirs(temp_output_dir, exist_ok=True)
                
                # Copy JSON input to temporary directory with required name
                temp_json = os.path.join(temp_input_dir, "fold_input.json")
                subprocess.run(['cp', str(json_file), temp_json], check=True)
                
                # Run AlphaFold3 (equivalent to the original os.system call)
                af3_command = [
                    'apptainer', 'exec', '--nv',
                    '--bind', f'{temp_input_dir}:/root/af_input',
                    '--bind', f'{temp_output_dir}:/root/af_output', 
                    '--bind', f'{model_params_dir}:/root/models',
                    '--bind', f'{os.environ["DB_DIR"]}:/root/public_databases',
                    os.environ['ALPHAFOLD_DIR'] + '/alphafold3.sif',
                    'python', '/app/alphafold/run_alphafold.py',
                    '--json_path=/root/af_input/fold_input.json',
                    '--model_dir=/root/models',
                    '--db_dir=/root/public_databases',
                    '--output_dir=/root/af_output'
                ]
                
                print(f"Running AlphaFold3...")
                start_time = time.time()
                
                # Run the command (like os.system in original)
                result = subprocess.run(af3_command, timeout=14400)  # 4 hour timeout
                
                end_time = time.time()
                duration = end_time - start_time
                
                if result.returncode == 0:
                    # Success - copy results back
                    print(f"✓ AlphaFold3 completed successfully in {duration:.1f} seconds")
                    subprocess.run(['cp', '-r', f'{temp_output_dir}/.', '.'], check=True)
                    successful_predictions += 1
                else:
                    print(f"✗ AlphaFold3 failed with return code: {result.returncode}")
                    failed_predictions += 1
                
                # Create done marker (like original script)
                with open("af3.done", "w") as o:
                    o.write(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
                    o.write(f"Duration: {duration:.1f} seconds\\n")
                    o.write(f"Success: {result.returncode == 0}\\n")
                
                print(f"✓ Finished: {job_name}")
                
            except subprocess.TimeoutExpired:
                print(f"✗ AlphaFold3 timed out after 4 hours")
                with open("af3.timeout", "w") as o:
                    o.write(f"Timed out at: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
                failed_predictions += 1
                
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                with open("af3.error", "w") as o:
                    o.write(f"Error at: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
                    o.write(f"Error: {str(e)}\\n")
                failed_predictions += 1
                
            finally:
                # Clean up temporary directories
                subprocess.run(['rm', '-rf', temp_input_dir], check=False)
                subprocess.run(['rm', '-rf', temp_output_dir], check=False)
        
        else:
            # Skip this job (like original script)
            if "af3.done" in os.listdir():
                print(f"⏭  Skipping {job_name} (already completed)")
            elif "af3.running" in os.listdir():
                print(f"⏭  Skipping {job_name} (already running)")
            skipped_predictions += 1
        
        # Go back to outputs directory for next iteration
        os.chdir("..")
        
        # Show progress
        remaining = len(job_dirs) - successful_predictions - failed_predictions - skipped_predictions
        print(f"Progress: {successful_predictions} successful, {failed_predictions} failed, {skipped_predictions} skipped, {remaining} remaining")
    
    # Final summary
    print(f"\\n{'='*60}")
    print(f"Batch run completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Successful predictions: {successful_predictions}")
    print(f"Failed predictions: {failed_predictions}")
    print(f"Skipped predictions: {skipped_predictions}")
    print(f"Total processed: {len(job_dirs)}")
    
    if successful_predictions + skipped_predictions == len(job_dirs):
        print("🎉 All predictions completed!")
    else:
        print(f"To retry failed predictions, remove error/timeout files and resubmit.")

if __name__ == "__main__":
    main()
