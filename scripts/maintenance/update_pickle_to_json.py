#!/usr/bin/env python3

"""
Utility script to convert pickle files to JSON format.
"""

import os
import pickle
from secure_data_utils import save_json_with_types

def convert_pickle_to_json(pickle_path):
    """Convert a pickle file to JSON format."""
    json_path = os.path.splitext(pickle_path)[0] + '.json'
    
    try:
        # Load pickle data
        with open(pickle_path, 'rb') as f:
            data = pickle.load(f)
        
        # Handle different data types
        if isinstance(data, (dict, list)):
            save_json_with_types(data, json_path)
            print(f"Converted {pickle_path} to {json_path}")
        else:
            print(f"Skipping {pickle_path} - unsupported data type: {type(data)}")
    except Exception as e:
        print(f"Error converting {pickle_path}: {str(e)}")

def main():
    """Convert all pickle files in the workspace."""
    pickle_files = []
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.pkl'):
                pickle_path = os.path.join(root, file)
                try:
                    convert_pickle_to_json(pickle_path)
                except Exception as e:
                    print(f"Error converting {pickle_path}: {e}")

if __name__ == '__main__':
    main()
