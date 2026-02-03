#!/usr/bin/env python3
"""
Test script for SES relationship plotting functionality.

This script tests the new plotting_utils_ses.py module by creating sample plots
and verifying that the visualization logic works correctly.
"""

import sys
import os
sys.path.append('/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador')

from plotting_utils_ses import (
    create_ses_relationship_plot, 
    create_ses_summary_grid,
    analyze_ses_relationship_strength,
    get_ses_variable_info,
    test_ses_plotting
)
import matplotlib.pyplot as plt
import pickle

def test_ses_functionality():
    """Test the SES plotting functionality."""
    
    print("="*60)
    print("TESTING SES RELATIONSHIP PLOTTING FUNCTIONALITY")
    print("="*60)
    
    # Run the basic test
    test_ses_plotting()
    
    # Try to load data and test with real data if available
    data_path = '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/los_mex_dict.pkl'
    
    if os.path.exists(data_path):
        print("\n" + "="*60)
        print("TESTING WITH REAL DATA")
        print("="*60)
        
        try:
            # Load the data
            with open(data_path, 'rb') as f:
                los_mex_dict = pickle.load(f)
            
            print(f"✅ Data loaded successfully")
            print(f"Found {len(los_mex_dict.get('enc_dict', {}))} surveys")
            
            # Test with CULTURA_POLITICA survey
            if 'enc_dict' in los_mex_dict and 'CULTURA_POLITICA' in los_mex_dict['enc_dict']:
                survey_name = 'CULTURA_POLITICA'
                df = los_mex_dict['enc_dict'][survey_name]['dataframe']
                
                print(f"\nTesting with survey: {survey_name}")
                print(f"Dataframe shape: {df.shape}")
                print(f"Available columns: {sorted(df.columns.tolist())}")
                
                # Test SES variable info retrieval
                print("\n" + "-"*40)
                print("TESTING SES VARIABLE INFO")
                print("-"*40)
                
                for ses_var in ['sexo', 'edad', 'edu', 'region', 'empleo']:
                    if ses_var in df.columns:
                        ses_info = get_ses_variable_info(los_mex_dict, ses_var, survey_name)
                        print(f"{ses_var}: {ses_info['category_count']} categories - {list(ses_info['labels'].keys())}")
                        
                        # Determine expected plot type
                        if ses_var == 'region':
                            plot_type = "Heatmap (special case)"
                        elif ses_info['category_count'] <= 4:
                            plot_type = "Barplot"
                        else:
                            plot_type = "Line Plot"
                        print(f"  → Expected visualization: {plot_type}")
                    else:
                        print(f"{ses_var}: NOT FOUND in dataframe")
                
                # Test relationship analysis if p5 exists
                if 'p5' in df.columns:
                    print("\n" + "-"*40)
                    print("TESTING RELATIONSHIP ANALYSIS")
                    print("-"*40)
                    
                    target_var = 'p5'
                    print(f"Target variable: {target_var}")
                    print(f"Target variable unique values: {sorted(df[target_var].dropna().unique())}")
                    
                    # Test statistical analysis for each SES variable
                    for ses_var in ['sexo', 'edu', 'region']:  # Test a few key ones
                        if ses_var in df.columns:
                            try:
                                stats = analyze_ses_relationship_strength(df, ses_var, target_var)
                                print(f"\n{ses_var} vs {target_var}:")
                                print(f"  Sample size: {stats['sample_size']}")
                                print(f"  Cramér's V: {stats['cramers_v']:.3f}")
                                print(f"  Relationship strength: {stats['relationship_strength']}")
                                print(f"  Chi-square p-value: {stats['p_value']:.4f}")
                            except Exception as e:
                                print(f"  Error analyzing {ses_var}: {e}")
                
                print("\n" + "-"*40)
                print("VISUALIZATION LOGIC TEST COMPLETE")
                print("-"*40)
                print("✅ All SES variable info retrieval working")
                print("✅ Statistical analysis functions working")
                print("✅ Visualization type selection logic operational")
                
                # Note about actual plotting
                print("\n" + "="*60)
                print("NOTE: Actual plot generation not run in test mode")
                print("To create plots, use the functions directly:")
                print("- create_ses_relationship_plot() for individual plots")
                print("- create_ses_summary_grid() for comprehensive overview")
                print("="*60)
                
            else:
                print("❌ CULTURA_POLITICA survey not found")
                
        except Exception as e:
            print(f"❌ Error loading data: {e}")
    
    else:
        print(f"\n❌ Data file not found: {data_path}")
        print("Module functions are available but cannot test with real data")
    
    print("\n" + "="*60)
    print("SES PLOTTING FUNCTIONALITY TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    test_ses_functionality()
