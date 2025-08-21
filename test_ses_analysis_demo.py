"""
Demo test file for SES Analysis module with real survey data.
This file demonstrates the functionality of the SES analysis module
with actual survey data from los_mex_dict.
"""

import pandas as pd
import numpy as np
from ses_analysis import AnalysisConfig, create_analysis_pipeline
from secure_data_utils import load_json_with_types
from pathlib import Path
import random
from typing import Any, Dict, List, Tuple

# def print_analysis_results(results: Dict[str, Any], indent: int = 0) -> None:
#     """Pretty print analysis results with proper formatting."""
#     indent_str = " " * indent
    
#     for key, value in results.items():
#         if isinstance(value, dict):
#             print(f"{indent_str}{key}:")
#             print_analysis_results(value, indent + 2)
#         elif isinstance(value, pd.DataFrame):
#             print(f"{indent_str}{key}:")
#             print(f"{indent_str}  {value.to_string()}\n")
#         else:
#             print(f"{indent_str}{key}: {value}")

def get_questions_for_survey(pregs_dict: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
    """
    Get all questions for a specific survey from pregs_dict.
    Returns a dictionary of {var_id: (question_text, full_var_id)} where:
    - var_id is the question ID (e.g., 'p5_1')
    - question_text is the actual question
    - full_var_id is the complete ID with survey (e.g., 'p5_1|IDE')
    """
    print("DEBUG: First few items in pregs_dict:")
    for i, (k, v) in enumerate(list(pregs_dict.items())[:5]):
        print(f"  {k}: {v}")
    
    questions = {}
    for full_id, question_info in pregs_dict.items():
        try:
            if '|' not in full_id:
                print(f"DEBUG: Invalid full_id format (missing |): {full_id}")
                continue
                
            var_id, _ = full_id.split('|')

            # Split question text from survey name
            try:
                _, question_text = question_info.split('|', 1)
                questions[var_id] = (question_text, full_id)
            except ValueError:
                print(f"DEBUG: Invalid question_info format: {question_info}")
                continue
        except Exception as e:
            print(f"DEBUG: Error processing {full_id}: {str(e)}")
            continue
    
    return questions

def get_variables(tmp_pregs_dict: Dict[str, str]) -> List[Tuple[str, str, str]]:
    """
    Select n random variables from pregs_dict for a specific survey.
    Returns list of tuples: (var_id, question_text, full_var_id)
    """
    
    # Get all questions for this survey
    survey_questions = get_questions_for_survey(tmp_pregs_dict)
    
    # Filter out unsuitable variables
    suitable_vars = {
        var_id: (question, full_id) 
        for var_id, (question, full_id) in survey_questions.items()
        if not any(x in var_id.lower() for x in ['sd', 'ns', 'nc', 'otro'])
    }
    
    if not suitable_vars:
        raise ValueError(f"No suitable variables found for surveys!")
    
    # Available questions
    avail_questions = suitable_vars#list(tmp_pregs_dict.keys())

    # # Select random variables
    # selected_vars = random.sample(avail_questions, min(n, len(avail_questions)))
    
    # Return as list of tuples (var_id, question_text, full_var_id)
    
    return [(var_id, question, full_id) for var_id, (question, full_id) in suitable_vars.items()]

def format_analysis_results(results):
    """Format analysis results as a string."""
    output = []
    
    if not results:
        return "No significant results found"

    if 'crosstab' in results['tables']:
        output.append("\n  Crosstabulation results:")
        output.append("  " + str(results['tables']['crosstab']))

    # if 'contingency_table' in results:
    #     output.append("\n  Contingency table:")
    #     output.append("  " + str(results['contingency_table']))

    if 'chi_square' in results['statistics']:
        output.append("\n  Chi-square test results:")
        output.append(f"  - Chi-square statistic: {results['statistics']['chi_square']:.3f}")
        output.append(f"  - p-value: {results['statistics']['p_value']:.3f}")
        output.append(f"  - Cramer's V: {results['statistics']['cramers_v']:.3f}")

    if 'spearman_correlation' in results['statistics']:
        output.append("\n  Correlation analysis results:")
        output.append(f"  - Correlation coefficient: {results['statistics']['spearman_correlation']:.3f}")
        output.append(f"  - p-value: {results['statistics']['spearman_p_value']:.3f}")

    if 'kendall_tau' in results['statistics']:
        output.append("\n  Correlation analysis results:")
        output.append(f"  - Correlation coefficient: {results['statistics']['kendall_tau']:.3f}")
        output.append(f"  - p-value: {results['statistics']['kendall_p_value']:.3f}")
        
    if 'significant_differences' in results:
        output.append("\n  Significant differences:")
        for diff in results['significant_differences']:
            output.append(f"  - {diff}")
            
    return "\n".join(output)

def print_analysis_results(results):
    """Print formatted analysis results."""
    print(format_analysis_results(results))

def main():
    """Main function to demonstrate SES analysis with real survey data."""
    print("\n=== SES Analysis Demonstration with Real Survey Data ===\n")
    
    # Load the real data
    RUTA_BASE = Path('/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador')
    ruta_enc = RUTA_BASE / 'encuestas'
    los_mex_dict = load_json_with_types(str(ruta_enc / 'los_mex_dict.json'))
    
    # Type checking
    if not isinstance(los_mex_dict, dict):
        raise TypeError("los_mex_dict must be a dictionary")
    
    enc_dict = los_mex_dict.get('enc_dict', {})
    if not isinstance(enc_dict, dict):
        raise TypeError("enc_dict must be a dictionary")
    
    survey_names = list(enc_dict.keys())
    if not survey_names:
        raise ValueError("No surveys found in enc_dict")
    
    # Print available surveys for debugging
    print("\nDEBUG: Available surveys in enc_dict:", survey_names)
    
    # Preprocess survey data using AnalysisConfig
    preprocess_survey_data = AnalysisConfig.preprocess_survey_data

    los_mex_dict = preprocess_survey_data(los_mex_dict)

    # Get pregs_dict from los_mex_dict
    pregs_dict = los_mex_dict.get('pregs_dict', {})
    
    # Get survey names from los_mex_dict and reverse mapping
    enc_nom_dict = los_mex_dict.get('enc_nom_dict', {})
    rev_enc_nom_dict = {v: k for k, v in enc_nom_dict.items()}

    # Get 5 random questions
    pregs_dict_keys = list(pregs_dict.keys())
    target_pregs = random.sample(pregs_dict_keys, min(5, len(survey_names)))

    target_vars = {k: v for k, v in pregs_dict.items() if k in target_pregs}

    var_info_lst = get_variables(target_vars)

    print("\nSelected variables for analysis:")
    print(f'{target_pregs}')

    print("\nStarting analysis...\n")

    # analyze each variable separately
    for var_id, question, full_id in var_info_lst:
        print(f"- Variable: {var_id}")
        print(f"  Question: {question}")
        print(f"  Full ID: {full_id}\n")
    # for target_var in target_vars:
        _, survey_id = full_id.split('|')

        # get appropriate survey data
        survey_name = rev_enc_nom_dict.get(survey_id, survey_id)
        survey_data = enc_dict.get(survey_name, {})
        if not isinstance(survey_data, dict):
            raise TypeError(f"Survey data for {survey_name} must be a dictionary")
    
        df = survey_data.get('dataframe')
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"No valid DataFrame found for survey {survey_name}")
        
        print(f"\nSelected survey: {survey_name}")
        print(f"Looking for variables with survey ID: {rev_enc_nom_dict.get(survey_name, survey_name)}")
        
        # Get variable labels if available
        var_labels_dicts = survey_data['metadata'].get('variable_value_labels', {})
        if not var_id in var_labels_dicts.keys():
            var_labels = {}
        var_labels = var_labels_dicts.get(var_id, {})
        if not isinstance(var_labels, dict):
            var_labels = {}
    
        # Create analysis pipeline
        config = AnalysisConfig(
            weight_variable='Pondi2',
            min_sample_size=30,
            confidence_level=0.95
        )
        analyzer, visualizer = create_analysis_pipeline(config)
        
        # Standard preprocessed SES variables to check for
        standard_ses_vars = ['sexo', 'edad', 'escol', 'region', 'empleo']
        
        # Variable descriptions for better output
        ses_descriptions = {
            'sexo': 'Gender (01=Mujer, 02=Hombre)',
            'edad': 'Age groups (0-18, 19-24, 25-34, 35-44, 45-54, 55-64, 65+)',
            'escol': 'Education level (01=Básica, 02=Media, 03=Superior)',
            'region': 'Geographic region (01=Norte, 02=Centro, 03=Centro Occidente, 04=Sureste)',
            'empleo': 'Employment (01=Empleado, 02=No empleado, 03=Estudiante, 04=Hogar, 05=Jubilado)'
        }

        # Filter to only those that exist in the DataFrame
        ses_vars = [var for var in standard_ses_vars if var in df.columns]
        
        print("\nAvailable preprocessed SES variables:")
        for var in ses_vars:
            print(f"- {var}: {ses_descriptions[var]}")
        
        # Perform and print analyses
        print("\n=== Single Relationship Analyses ===")
        
        # Extract just the variable IDs for analysis
        var_ids = [var_id for var_id in target_vars]
        
        for ses_var in ses_vars:
            if ses_var in df.columns:
                print(f"\nAnalyzing relationships with {ses_var}:")
                # for var_id, question, full_id in target_vars:
                if var_id in df.columns:
                    print(f"\nAnalyzing Variable: {var_id}")
                    print(f"Question: {question}")
                    try:
                        results = analyzer.analyze_single_relationship(
                            df,
                            var_id,
                            ses_var,
                            #ses_labels=ses_labels,  # TODO: get appropriate ses labels
                            var_labels=var_labels
                        )
                        print(f'results')
                        print_analysis_results(results)
                        
                    ## PAUSAR visualizaciones para pruebas
                    #     # Create visualization
                    #     fig, ax = visualizer.create_relationship_plot(
                    #         df,
                    #         var_id,
                    #         ses_var,
                    #         title=f'"{question[:50]}..." by {ses_var}',
                    #         var_labels=var_labels,
                    #         plot_type='heatmap'
                    #     )
                    #     fig_path = f'{var_id}_{ses_var}_heatmap.png'
                    #     fig.savefig(fig_path)
                    #     print(f"Created visualization: {fig_path}")

                    except Exception as e:
                        print(f"Error analyzing {var_id} vs {ses_var}: {str(e)}")
    
        # # Multiple relationship analysis
        # print("\n=== Multiple Relationship Analyses ===")
        # for ses_var in ses_vars:
        #     if ses_var in df.columns:
        #         print(f"\nAnalyzing multiple relationships with {ses_var}:")
        #         try:
        #             results = analyzer.analyze_multiple_relationships(
        #                 df,
        #                 var_ids,  # Use just the variable IDs
        #                 ses_var,
        #                 var_labels=var_labels
        #             )
        #             print_analysis_results(results)
        #         except Exception as e:
        #             print(f"Error in multiple analysis with {ses_var}: {str(e)}")

if __name__ == "__main__":
    main()
