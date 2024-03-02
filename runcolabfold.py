	# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 16:32:38 2023

@author: enric
"""
#SCRIPT FOR SAVIO HPC TO RUN COLABFOLD MULTIMER PREDICTIONS
#imports
import os
from Bio import SeqIO


os.chdir('/global/scratch/users/enricocalvane/IMB2ColabFold/fastas')
#assign the name of all fasta files to a single vector
fastas= [x for x in os.listdir() if x.startswith("AT")]

#IMPORTANT: for loop to reiterate the colabfold command for each file

for f in fastas:
    os.chdir(f)
    if "colab.running" not in os.listdir() and "colab.done" not in os.listdir():        
        outputname=f+"_output"
        seq=SeqIO.read(f+".fasta", "fasta")
        with open ("colab.running", "w") as o:
            o.write("hi")
        os.system(f"colabfold_batch {f}.fasta {outputname} --model-type alphafold2_multimer_v3")
        with open ("colab.done", "w") as o:
            o.write("bye")
    os.chdir("..")
    
