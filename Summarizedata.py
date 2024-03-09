# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 10:45:45 2023

@author: enric
"""

import os
import json
import pandas as pd

# Create an empty DataFrame to hold the results
results_df = pd.DataFrame(columns=["Subdirectory", "pLDDT", "iPTM", "pTM"])


# Set the path to the parent directory
parent_dir = "/global/scratch/users/enricocalvane/IMB2ColabFold/olivia"
os.chdir(parent_dir)
# Loop over all subdirectories
for subdirectory in os.listdir(parent_dir):
    subdirectory_path = os.path.join(parent_dir, subdirectory)
    if not os.path.isdir(subdirectory_path):
        continue
    
    #print(f"Processing {subdirectory}")
    
    # Loop over all output directories in the subdirectory
    for output_dir in os.listdir(subdirectory_path):
        if not output_dir.endswith("_output"):
            continue
        
        output_dir_path = os.path.join(subdirectory_path, output_dir)
        if not os.path.isdir(output_dir_path):
            continue
        
        #change directory to output directory
        os.chdir(output_dir_path)
        
        # Get the name of the top-ranked model json file
        json_file = [f for f in os.listdir(output_dir_path) if "rank_001" in f and f.endswith(".json")]
        if not json_file:
            continue
        if len(json_file) > 0:
            json_file = json_file[0]
            # continue with processing the JSON file...
        else:
            print(f"No JSON files found in {json_file}")
        # print(json_file)
        
        with open(json_file) as f:
            data = json.load(f)

        
        predicted_lddt = data['plddt']
        avglddt=sum(predicted_lddt)/len(predicted_lddt)
        predicted_tm_score = data['ptm']
        predicted_iptm_score = data['iptm']
        
        results_df = results_df.append({"Subdirectory": output_dir_path, "pLDDT": avglddt, "iPTM": predicted_iptm_score, "pTM": predicted_tm_score}, ignore_index=True)

# Write the results DataFrame to an Excel file
os.chdir(parent_dir)
results_df.to_excel("Metrics.xlsx", index=False)
       
