#!/usr/bin/env python3
import pickle
import os
import sys

def inspect_pickle_file(file_path):
    """
    Inspect the contents of a pickle file containing los_mex_dict
    """
    print(f"\n{'='*80}")
    print(f"Inspecting: {file_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(file_path):
        print(f"Error: File does not exist: {file_path}")
        return
    
    file_size = os.path.getsize(file_path)
    print(f"File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
            
        print(f"\nType of object: {type(data)}")
        
        if isinstance(data, dict):
            keys = list(data.keys())
            print(f"\nKeys in dictionary ({len(keys)}): {keys}")
            
            # Check for required components
            required_components = ['enc_dict', 'enc_nom_dict', 'pregs_dict', 'ses_dict', 'readme_dict']
            missing = [comp for comp in required_components if comp not in data]
            
            if missing:
                print(f"\nMISSING REQUIRED COMPONENTS: {missing}")
            else:
                print("\nAll required components are present! ✓")
            
            # Print details for each key
            for key in keys:
                value = data[key]
                print(f"\nKey: {key}")
                print(f"  Type: {type(value)}")
                
                # For dictionaries, show the number of items and some sample keys
                if isinstance(value, dict):
                    print(f"  Items: {len(value):,}")
                    sample_keys = list(value.keys())[:3]
                    print(f"  Sample keys: {sample_keys}")
                
                # For lists, show the length and first item type
                elif isinstance(value, list):
                    print(f"  Items: {len(value):,}")
                    if value:
                        print(f"  First item type: {type(value[0])}")
                        
                # For other types, show a representation if possible
                else:
                    try:
                        brief = str(value)[:100]
                        if len(str(value)) > 100:
                            brief += "..."
                        print(f"  Value: {brief}")
                    except:
                        print("  Value representation unavailable")
        else:
            print("Not a dictionary. Cannot inspect further.")
            
    except Exception as e:
        print(f"Error inspecting file: {str(e)}")
        import traceback
        traceback.print_exc()

# List of backup files to inspect
backup_files = [
    "/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/los_mex_dict_backup_20250723_185455.pkl",  # Oldest
    "/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/los_mex_dict_backup_20250725_132954.pkl",  # Middle
    "/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/los_mex_dict_backup_20250725_143623.pkl",  # Latest
    "/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/los_mex_dict.pkl"  # Current
]

# Inspect each backup file
for file_path in backup_files:
    inspect_pickle_file(file_path)
