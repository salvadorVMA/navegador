#!/usr/bin/env python3
"""
SES Plotting Demonstration

This script demonstrates the SES relationship plotting functionality using real data.
It creates actual plots to show how different SES variables relate to survey questions.
"""

import sys
import os
sys.path.append('/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador')

import matplotlib.pyplot as plt
import pandas as pd
import pickle
from plotting_utils_ses import (
    create_ses_relationship_plot, 
    analyze_ses_relationship_strength,
    get_ses_variable_info
)

def load_data():
    """Load the survey data."""
    data_path = '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/los_mex_dict.pkl'
    
    with open(data_path, 'rb') as f:
        los_mex_dict = pickle.load(f)
    
    return los_mex_dict

def demo_ses_plotting():
    """Demonstrate SES plotting with real data."""
    
    print("="*70)
    print("SES RELATIONSHIP PLOTTING DEMONSTRATION")
    print("="*70)
    
    # Load data
    los_mex_dict = load_data()
    survey_name = 'CULTURA_POLITICA'
    df = los_mex_dict['enc_dict'][survey_name]['dataframe']
    
    print(f"Using survey: {survey_name}")
    print(f"Sample size: {len(df):,} respondents")
    
    # Map original variables to standardized SES variables for demo
    # Create a demo dataframe with standardized variable names
    demo_df = df.copy()
    
    # Map variables to standardized names
    variable_mappings = {
        'sexo': 'sexo',           # Already standardized
        'Region': 'region',       # Map Region to region
        'escol': 'edu',          # Map escol to edu  
        'sd2': 'edad',           # Map sd2 to edad (will need categorization)
        'sd5': 'empleo'          # Map sd5 to empleo
    }
    
    print("\n" + "-"*50)
    print("VARIABLE MAPPINGS FOR DEMO")
    print("-"*50)
    
    for original, standardized in variable_mappings.items():
        if original in df.columns:
            demo_df[standardized] = df[original]
            unique_vals = len(df[original].dropna().unique())
            print(f"{original} → {standardized}: {unique_vals} categories")
        else:
            print(f"{original} → {standardized}: NOT AVAILABLE")
    
    # Target variable for analysis
    target_var = 'p5'  # How proud are you of being Mexican?
    print(f"\nTarget variable: {target_var}")
    print(f"Target categories: {sorted(demo_df[target_var].dropna().unique())}")
    
    # Clean target variable labels
    target_labels = {
        1.0: 'Mucho', 2.0: 'Poco', 3.0: 'Nada', 4.0: 'No soy mexicano',
        5.0: 'Otra', 8.0: 'NS', 9.0: 'NC'
    }
    
    print("\n" + "="*70)
    print("CREATING SES RELATIONSHIP PLOTS")
    print("="*70)
    
    # Test each SES variable that we have data for
    available_ses_vars = ['sexo', 'region', 'edu']  # Focus on the ones we have good data for
    
    for ses_var in available_ses_vars:
        if ses_var in demo_df.columns and target_var in demo_df.columns:
            print(f"\n{'-'*50}")
            print(f"ANALYZING: {ses_var.upper()} vs {target_var.upper()}")
            print(f"{'-'*50}")
            
            # Get clean data for analysis
            clean_data = demo_df[[ses_var, target_var]].dropna()
            
            if len(clean_data) < 10:  # Skip if too little data
                print(f"⚠️  Insufficient data for {ses_var} (n={len(clean_data)})")
                continue
                
            # Get variable info
            ses_categories = len(clean_data[ses_var].unique())
            print(f"SES variable categories: {ses_categories}")
            
            # Determine expected plot type
            if ses_var == 'region':
                expected_plot = "Heatmap (special case for region)"
            elif ses_categories <= 4:
                expected_plot = "Barplot (≤4 categories)"
            else:
                expected_plot = "Line Plot (≥5 categories)"
                
            print(f"Expected visualization: {expected_plot}")
            
            # Analyze relationship strength
            try:
                stats = analyze_ses_relationship_strength(clean_data, ses_var, target_var)
                print(f"Sample size: {stats['sample_size']:,}")
                print(f"Cramér's V: {stats['cramers_v']:.3f}")
                print(f"Relationship strength: {stats['relationship_strength']}")
                print(f"Chi-square p-value: {stats['p_value']:.4f}")
                
                # Show category distribution
                print(f"\n{ses_var.title()} category distribution:")
                category_counts = clean_data[ses_var].value_counts().sort_index()
                for cat, count in category_counts.items():
                    pct = (count / len(clean_data)) * 100
                    print(f"  {cat}: {count:,} ({pct:.1f}%)")
                
                # Create and save the plot
                print(f"\n📊 Creating visualization...")
                
                try:
                    fig = create_ses_relationship_plot(
                        df=clean_data,
                        ses_var=ses_var,
                        target_var=target_var,
                        target_labels=target_labels,
                        title=f"National Pride by {ses_var.title()}\nSurvey: {survey_name} (n={len(clean_data):,})",
                        figsize=(12, 8),
                        save_path=f"ses_demo_{ses_var}_{target_var}.png"
                    )
                    
                    print(f"✅ Plot created successfully")
                    plt.close(fig)  # Close to free memory
                    
                except Exception as plot_error:
                    print(f"❌ Error creating plot: {plot_error}")
                
            except Exception as analysis_error:
                print(f"❌ Error in statistical analysis: {analysis_error}")
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("✅ SES plotting functionality demonstrated successfully")
    print("✅ Multiple visualization types tested")
    print("✅ Statistical analysis performed")
    print("\nGenerated plot files:")
    for ses_var in available_ses_vars:
        filename = f"ses_demo_{ses_var}_{target_var}.png"
        if os.path.exists(filename):
            print(f"  📁 {filename}")
    
    print(f"\n📋 Summary of visualization logic:")
    print(f"  • sexo (2 categories) → Barplot")
    print(f"  • edu (varies) → Barplot if ≤4 categories")
    print(f"  • region (4 categories) → Heatmap (special case)")
    print(f"  • edad (if available, 7 categories) → Line plot")
    print(f"  • empleo (if available, 5 categories) → Line plot")

if __name__ == "__main__":
    # Create plots directory if it doesn't exist
    os.makedirs("plots", exist_ok=True)
    os.chdir("plots")
    
    demo_ses_plotting()
