#!/bin/bash
# Cleanup and Restart Script for AlphaFold3 Batch Jobs
# This script cleans up stale running markers and failed predictions,
# similar to removing colab.running files in your original workflow

ANALYSIS_DIR="/global/scratch/users/enricocalvane/IMB2_AF3_Analysis"
OUTPUTS_DIR="$ANALYSIS_DIR/outputs"

echo "AlphaFold3 Cleanup and Restart Utility"
echo "======================================"
echo "Analysis directory: $ANALYSIS_DIR"
echo ""

cd "$ANALYSIS_DIR" || exit 1

# Function to count status markers
count_status() {
    local completed=$(find "$OUTPUTS_DIR" -name "af3.done" 2>/dev/null | wc -l)
    local running=$(find "$OUTPUTS_DIR" -name "af3.running" 2>/dev/null | wc -l)
    local failed=$(find "$OUTPUTS_DIR" -name "af3.error" 2>/dev/null | wc -l)
    local timeout=$(find "$OUTPUTS_DIR" -name "af3.timeout" 2>/dev/null | wc -l)
    local total_inputs=$(ls inputs/*.json 2>/dev/null | wc -l)
    local remaining=$((total_inputs - completed))
    
    echo "Current Status:"
    echo "  Completed: $completed"
    echo "  Running: $running"
    echo "  Failed: $failed"
    echo "  Timeout: $timeout"
    echo "  Remaining: $remaining"
    echo "  Total: $total_inputs"
}

# Show current status
count_status

# Parse command line arguments
case "${1:-status}" in
    "status")
        echo ""
        echo "Detailed status by prediction:"
        for json_file in inputs/*.json; do
            if [ -f "$json_file" ]; then
                basename=$(basename "$json_file" .json)
                output_dir="$OUTPUTS_DIR/$basename"
                
                if [ -f "$output_dir/af3.done" ]; then
                    status="COMPLETED"
                elif [ -f "$output_dir/af3.running" ]; then
                    status="RUNNING"
                elif [ -f "$output_dir/af3.error" ]; then
                    status="FAILED"
                elif [ -f "$output_dir/af3.timeout" ]; then
                    status="TIMEOUT"
                else
                    status="READY"
                fi
                
                printf "  %-30s: %s\\n" "$basename" "$status"
            fi
        done
        ;;
        
    "cleanup")
        echo ""
        echo "Cleaning up stale 'running' markers..."
        
        running_files=$(find "$OUTPUTS_DIR" -name "af3.running" 2>/dev/null)
        if [ -n "$running_files" ]; then
            echo "Removing running markers:"
            for file in $running_files; do
                echo "  Removing: $file"
                rm "$file"
            done
        else
            echo "  No running markers found."
        fi
        
        echo ""
        count_status
        ;;
        
    "reset-failed")
        echo ""
        echo "Resetting failed predictions for retry..."
        
        # Remove error and timeout markers
        error_files=$(find "$OUTPUTS_DIR" -name "af3.error" -o -name "af3.timeout" 2>/dev/null)
        if [ -n "$error_files" ]; then
            echo "Removing error/timeout markers:"
            for file in $error_files; do
                echo "  Removing: $file"
                rm "$file"
            done
        else
            echo "  No error/timeout markers found."
        fi
        
        echo ""
        count_status
        ;;
        
    "clean-all")
        echo ""
        echo "WARNING: This will reset ALL predictions except completed ones!"
        read -p "Are you sure? (y/N): " confirm
        
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            echo "Removing all non-completion markers..."
            find "$OUTPUTS_DIR" -name "af3.running" -delete 2>/dev/null
            find "$OUTPUTS_DIR" -name "af3.error" -delete 2>/dev/null
            find "$OUTPUTS_DIR" -name "af3.timeout" -delete 2>/dev/null
            
            echo ""
            count_status
        else
            echo "Operation cancelled."
        fi
        ;;
        
    "submit")
        echo ""
        echo "Submitting new batch job..."

        #Change to scripts directory 
        cd "$ANALYSIS_DIR/scripts"
        
        # Submit the job
        sbatch submit_af3_batch.sh
        
        if [ $? -eq 0 ]; then
            echo "✓ Job submitted successfully"
            echo "Monitor with: squeue -u $USER"
        else
            echo "✗ Job submission failed"
        fi
        ;;
        
    "help"|"-h"|"--help")
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  status      Show detailed status of all predictions (default)"
        echo "  cleanup     Remove stale 'running' markers only"
        echo "  reset-failed Reset failed predictions for retry"
        echo "  clean-all   Reset all non-completed predictions (interactive)"
        echo "  submit      Submit new batch job"
        echo "  help        Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                    # Show status"
        echo "  $0 cleanup           # Clean stale markers"
        echo "  $0 reset-failed      # Reset failed jobs for retry"
        echo "  $0 submit            # Submit new batch job"
        ;;
        
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information."
        exit 1
        ;;
esac
