"""
Check unique Region values across all survey dataframes.

This script analyzes the 'Region' column in each survey dataframe to:
1. Count unique values
2. List the actual values found
3. Check for any inconsistencies with expected mapping
"""

import os
from secure_data_utils import load_json_with_types
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Set

def analyze_region_values() -> None:
    """Analyze Region values in all survey dataframes."""
    # Load the dictionary with survey data
    ruta_enc = '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas'
    los_mex_dict = load_json_with_types(os.path.join(ruta_enc, 'los_mex_dict.json'))
    
    if not isinstance(los_mex_dict, dict):
        raise ValueError("los_mex_dict is not a dictionary")
        
    enc_nom_dict = los_mex_dict.get('enc_nom_dict', {})
    enc_dict = los_mex_dict.get('enc_dict', {})
    
    # Expected region values based on mapping
    expected_values = {1.0, 2.0, 3.0, 4.0, 5.0}  # From region_mapping in ses_analysis.py
    
    # Dictionary to store results
    results: Dict[str, Dict[str, Any]] = {}
    
    # Analyze each survey's dataframe
    for survey_name in enc_nom_dict:
        if survey_name not in enc_dict:
            print(f"Warning: Survey {survey_name} not found in enc_dict")
            continue
            
        survey_data = enc_dict[survey_name]
        if not isinstance(survey_data, dict) or 'dataframe' not in survey_data:
            print(f"Warning: Invalid data structure for survey {survey_name}")
            continue
            
        df = survey_data['dataframe']
        if not isinstance(df, pd.DataFrame):
            print(f"Warning: No DataFrame found for survey {survey_name}")
            continue
        
        # Check both 'Region' and 'region' columns
        for col in ['Region', 'region']:
            if col not in df.columns:
                continue
                
            # Convert to float for consistent comparison
            unique_values = df[col].dropna().astype(float).unique()
            unique_values = sorted(unique_values)
            n_unique = len(unique_values)
            n_nulls = df[col].isna().sum()
            
            results[f"{survey_name}_{col}"] = {
                'column': col,
                'n_unique': n_unique,
                'unique_values': unique_values,
                'n_nulls': n_nulls,
                'unexpected_values': [v for v in unique_values 
                                   if v not in expected_values]
            }
    
    # Print results in a formatted way
    print("\nRegion Value Analysis")
    print("=" * 80)
    
    for key, data in sorted(results.items()):
        print(f"\nSurvey-Column: {key}")
        print("-" * 40)
        print(f"Number of unique values: {data['n_unique']}")
        print(f"Number of null values: {data['n_nulls']}")
        print(f"Unique values found: {data['unique_values']}")
        if data['unexpected_values']:
            print(f"⚠️  Unexpected values found: {data['unexpected_values']}")
        print()
    
    # Summary statistics
    print("\nSummary Statistics")
    print("=" * 80)
    columns_analyzed = len(results)
    surveys_with_region = len({k.split('_')[0] for k in results.keys()})
    surveys_with_unexpected = len({k.split('_')[0] for k, v in results.items() if v['unexpected_values']})
    
    print(f"\nTotal surveys analyzed: {len(enc_nom_dict)}")
    print(f"Surveys with Region data: {surveys_with_region}")
    print(f"Total columns analyzed: {columns_analyzed}")
    print(f"Surveys with unexpected values: {surveys_with_unexpected}")

if __name__ == '__main__':
    analyze_region_values()


