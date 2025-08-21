"""Convert pickle files to JSON format.

This script is a one-time use utility to convert pickle files to a more secure JSON format.
After conversion, verify data integrity and then delete the original pickle files.
"""

import pickle
import json
import pandas as pd
from pathlib import Path

def extended_handler(obj):
    """Extended JSON serializer for pandas objects and sets."""
    if isinstance(obj, pd.DataFrame):
        return {
            "__pandas_dataframe__": True,
            "data": obj.to_dict(orient='split')
        }
    elif isinstance(obj, pd.Series):
        return {
            "__pandas_series__": True,
            "data": obj.to_dict()
        }
    elif isinstance(obj, set):
        return {
            "__set__": True,
            "data": list(obj)
        }
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def convert_pickle_to_json(pickle_file):
    """Convert a pickle file to JSON format."""
    json_file = pickle_file.with_suffix('.json')
    
    print(f"Converting {pickle_file} to {json_file}...")
    
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, default=extended_handler, ensure_ascii=False, indent=2)
    
    print(f"Conversion complete. New file created at {json_file}")
    
def main():
    """Find and convert all pickle files in the workspace."""
    workspace_path = Path(__file__).parent
    
    pickle_files = list(workspace_path.rglob("*.pkl"))
    
    if not pickle_files:
        print("No pickle files found in workspace.")
        return
    
    print(f"Found {len(pickle_files)} pickle files")
    
    for pickle_file in pickle_files:
        try:
            convert_pickle_to_json(pickle_file)
        except Exception as e:
            print(f"Error converting {pickle_file}: {e}")

if __name__ == "__main__":
    main()
