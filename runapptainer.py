apptainer run --bind /global/scratch/users/enricocalvane/colabfold_cache:/cache --bind /global/scratch/users/enricocalvane/colabfold_inputs:/inputs colabfold_1.5.5-cuda12.2.2.sif python -m colabfold.batch
#imports
import os
from Bio import SeqIO

# Set working directory
os.chdir('/global/scratch/users/enricocalvane/SIZ1/fastas')

# Assign the name of all fasta files to a single vector
fastas = [x for x in os.listdir() if x.startswith("AT")]

# IMPORTANT: for loop to reiterate the colabfold command for each file
for f in fastas:
    os.chdir(f)
    if "colab.running" not in os.listdir() and "colab.done" not in os.listdir():
        outputname = f + "_output"
        seq = SeqIO.read(f + ".fasta", "fasta")
        
        # Create 'colab.running' file
        with open("colab.running", "w") as o:
            o.write("hi")
        
        # Run ColabFold using Apptainer
        os.system(f"apptainer exec --bind /global/scratch/users/enricocalvane/colabfold_cache:/cache /global/scratch/users/enricocalvane/SIZ1/colabfold_1.5.5-cuda12.2.2.sif python -m colabfold.batch {f}.fasta {outputname} --model-type alphafold2_multimer_v3")
        
        # Create 'colab.done' file
        with open("colab.done", "w") as o:
            o.write("bye")
    
    os.chdir("..")
