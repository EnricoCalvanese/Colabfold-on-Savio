#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlphaFold3 Sequential Batch Runner for IMB2-RBF Multimer Predictions on Savio
Follows the proven workflow pattern: one Python script runs sequentially through
multiple predictions within long-running SLURM jobs (up to 72 hours)
Author: Adapted for Enrico Calvane's workflow preferences
"""

import os
import json
import subprocess
import time
from pathlib import Path
import sys

def check_job_status(json_file, outputs_dir):
    """Check if job is already running, completed, or ready to start"""
    job_name = json_file.stem
    output_subdir = outputs_dir / job_name
    
    # Create output directory if it doesn't exist
    output_subdir.mkdir(exist_ok=True)
    
    # Check for status markers (similar to colab.done/colab.running)
    if (output_subdir / "af3.done").exists():
        return "completed"
    elif (output_subdir / "af3.running").exists():
        return "running"
    else:
        return "ready"

def run_single_prediction(json_file, outputs_dir, model_params_dir):
    """Run a single AlphaFold3 prediction"""
    job_name = json_file.stem
    output_subdir = outputs_dir / job_name
    output_subdir.mkdir(exist_ok=True)
    
    print(f"\\n{'='*60}")
    print(f"Starting prediction: {job_name}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Create running marker
    running_marker = output_subdir / "af3.running"
    with open(running_marker, 'w') as f:
        f.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
    
    try:
        # Create temporary directories for this prediction
        temp_input_dir = f"/tmp/af_input_{job_name}_{os.getpid()}"
        temp_output_dir = f"/tmp/af_output_{job_name}_{os.getpid()}"
        
        os.makedirs(temp_input_dir, exist_ok=True)
        os.makedirs(temp_output_dir, exist_ok=True)
        
        # Copy JSON input to temporary directory with required name
        temp_json = os.path.join(temp_input_dir, "fold_input.json")
        subprocess.run(['cp', str(json_file), temp_json], check=True)
        
        # Construct AlphaFold3 command
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
        
        print(f"Running AlphaFold3 command...")
        print(f"Input: {json_file}")
        print(f"Output: {output_subdir}")
        
        # Run AlphaFold3
        start_time = time.time()
        result = subprocess.run(af3_command, 
                              capture_output=True, 
                              text=True, 
                              timeout=14400)  # 4 hour timeout per prediction
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            # Success - copy results back
            print(f"✓ AlphaFold3 completed successfully in {duration:.1f} seconds")
            
            # Copy all results from temporary to permanent location
            subprocess.run(['cp', '-r', f'{temp_output_dir}/.', str(output_subdir)], check=True)
            
            # Create completion marker and remove running marker
            with open(output_subdir / "af3.done", 'w') as f:
                f.write(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
                f.write(f"Duration: {duration:.1f} seconds\\n")
            
            running_marker.unlink(missing_ok=True)
            
            # Log success
            print(f"✓ Results saved to: {output_subdir}")
            
            return True
            
        else:
            # Failure
            print(f"✗ AlphaFold3 failed with return code: {result.returncode}")
            print("STDOUT:")
            print(result.stdout)
            print("STDERR:")
            print(result.stderr)
            
            # Save error information
            with open(output_subdir / "af3.error", 'w') as f:
                f.write(f"Failed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
                f.write(f"Return code: {result.returncode}\\n")
                f.write(f"Duration: {duration:.1f} seconds\\n")
                f.write("\\nSTDOUT:\\n")
                f.write(result.stdout)
                f.write("\\nSTDERR:\\n")
                f.write(result.stderr)
            
            running_marker.unlink(missing_ok=True)
            
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ AlphaFold3 timed out after 4 hours")
        with open(output_subdir / "af3.timeout", 'w') as f:
            f.write(f"Timed out at: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
        running_marker.unlink(missing_ok=True)
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        with open(output_subdir / "af3.error", 'w') as f:
            f.write(f"Error at: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Error: {str(e)}\\n")
        running_marker.unlink(missing_ok=True)
        return False
        
    finally:
        # Clean up temporary directories
        subprocess.run(['rm', '-rf', temp_input_dir], check=False)
        subprocess.run(['rm', '-rf', temp_output_dir], check=False)

def main():
    """Main sequential prediction loop - runs until wall time or all predictions complete"""
    # Setup paths
    base_dir = Path("/global/scratch/users/enricocalvane/IMB2_AF3_Analysis")
    inputs_dir = base_dir / "inputs"
    outputs_dir = base_dir / "outputs"
    model_params_dir = "/global/home/users/enricocalvane/model_param"
    
    # Ensure output directory exists
    outputs_dir.mkdir(exist_ok=True)
    
    # Get all JSON files
    json_files = sorted(list(inputs_dir.glob("*.json")))
    
    if not json_files:
        print("No JSON files found in inputs directory!")
        sys.exit(1)
    
    print(f"AlphaFold3 Sequential Batch Runner")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Found {len(json_files)} JSON files for processing")
    print(f"Model parameters: {model_params_dir}")
    print(f"Database directory: {os.environ.get('DB_DIR', 'NOT SET')}")
    
    # Check initial status
    completed = 0
    ready = 0
    running = 0
    
    for json_file in json_files:
        status = check_job_status(json_file, outputs_dir)
        if status == "completed":
            completed += 1
        elif status == "ready":
            ready += 1
        elif status == "running":
            running += 1
    
    print(f"\\nInitial status: {completed} completed, {ready} ready, {running} running")
    
    # Clean up any stale "running" markers (from previous interrupted runs)
    if running > 0:
        print(f"Cleaning up {running} stale 'running' markers...")
        for json_file in json_files:
            if check_job_status(json_file, outputs_dir) == "running":
                running_marker = outputs_dir / json_file.stem / "af3.running"
                running_marker.unlink(missing_ok=True)
                print(f"  Removed: {running_marker}")
    
    # Run predictions sequentially
    successful_predictions = 0
    failed_predictions = 0
    
    for json_file in json_files:
        status = check_job_status(json_file, outputs_dir)
        
        if status == "completed":
            print(f"⏭  Skipping {json_file.stem} (already completed)")
            continue
        elif status == "running":
            print(f"⏭  Skipping {json_file.stem} (running - this shouldn't happen after cleanup)")
            continue
        
        # Run the prediction
        success = run_single_prediction(json_file, outputs_dir, model_params_dir)
        
        if success:
            successful_predictions += 1
            print(f"✓ Completed prediction {successful_predictions}")
        else:
            failed_predictions += 1
            print(f"✗ Failed prediction {failed_predictions}")
        
        # Quick status update
        remaining = sum(1 for jf in json_files if check_job_status(jf, outputs_dir) == "ready")
        print(f"Status: {successful_predictions} successful, {failed_predictions} failed, {remaining} remaining")
    
    # Final summary
    print(f"\\n{'='*60}")
    print(f"Batch run completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Successful predictions this run: {successful_predictions}")
    print(f"Failed predictions this run: {failed_predictions}")
    
    # Overall status
    final_completed = sum(1 for jf in json_files if check_job_status(jf, outputs_dir) == "completed")
    final_remaining = len(json_files) - final_completed
    
    print(f"Overall status: {final_completed}/{len(json_files)} completed, {final_remaining} remaining")
    
    if final_remaining == 0:
        print("🎉 All predictions completed!")
    else:
        print(f"To continue with remaining predictions, resubmit this job.")
        print(f"Failed predictions can be restarted by removing error/timeout files:")
        print(f"  find {outputs_dir} -name 'af3.error' -o -name 'af3.timeout' | xargs rm")

if __name__ == "__main__":
    main()
