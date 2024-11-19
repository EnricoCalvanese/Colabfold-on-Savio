import os
from Bio import SeqIO

print("Starting ColabFold processing script...")

# Set working directory
parent_dir = '/global/scratch/users/enricocalvane/SIZ1/fastas'
os.chdir(parent_dir)
print(f"Changed to parent directory: {parent_dir}")

# Assign the name of all fasta files to a single vector
fastas = [x for x in os.listdir() if x.startswith("AT")]
print(f"Found {len(fastas)} directories to process: {', '.join(fastas)}")

# IMPORTANT: for loop to reiterate the colabfold command for each file
for i, f in enumerate(fastas, 1):
    print(f"\nProcessing directory {i}/{len(fastas)}: {f}")
    os.chdir(f)
    
    if "colab.running" in os.listdir():
        print(f"Found colab.running - skipping {f} as it's currently being processed")
        os.chdir("..")
        continue
        
    if "colab.done" in os.listdir():
        print(f"Found colab.done - skipping {f} as it's already completed")
        os.chdir("..")
        continue

    outputname = f + "_output"
    print(f"Reading fasta file: {f}.fasta")
    seq = SeqIO.read(f + ".fasta", "fasta")
    
    # Create 'colab.running' file
    with open("colab.running", "w") as o:
        o.write("hi")
    print("Created colab.running flag file")
    
    # Run ColabFold using Apptainer
    current_dir = os.getcwd()
    cmd = (
        f"apptainer run --nv "
        f"--bind /global/scratch/users/enricocalvane/colabfold_cache:/cache "
        f"--bind {current_dir}:/work "
        f"/global/scratch/users/enricocalvane/SIZ1/colabfold_1.5.5-cuda12.2.2.sif "
        f"colabfold_batch /work/{f}.fasta /work/{outputname} "
        f"--model-type alphafold2_multimer_v3"
    )
    print("Running ColabFold prediction...")
    result = os.system(cmd)
    
    if result == 0:
        print("ColabFold prediction completed successfully")
        # Create 'colab.done' file
        with open("colab.done", "w") as o:
            o.write("bye")
        print("Created colab.done flag file")
    else:
        print(f"Error: ColabFold prediction failed with exit code {result}")
        # Remove the running flag if there was an error
        if os.path.exists("colab.running"):
            os.remove("colab.running")
            print("Removed colab.running flag file due to error")
    
    os.chdir("..")

print("\nScript completed!")
