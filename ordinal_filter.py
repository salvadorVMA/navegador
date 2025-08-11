#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ordinal Scale Question Filter

This script identifies survey questions that use ordinal scales and creates
a filtered dictionary containing only those questions.
"""

import pickle
import re
from typing import Dict, List, Set
import os

def load_dictionary(file_path: str) -> dict:
    """Load the los_mex_dict from a pickle file."""
    with open(file_path, 'rb') as file:
        return pickle.load(file)

def identify_ordinal_patterns() -> List[str]:
    """
    Define patterns that indicate ordinal scales in Spanish survey questions.
    Returns list of regex patterns to match against question text.
    """
    patterns = [
        # Agreement scales (acuerdo/desacuerdo)
        r'(muy\s+de\s+acuerdo|de\s+acuerdo|en\s+desacuerdo|muy\s+en\s+desacuerdo)',
        r'(totalmente\s+de\s+acuerdo|parcialmente\s+de\s+acuerdo|parcialmente\s+en\s+desacuerdo|totalmente\s+en\s+desacuerdo)',
        r'(acuerdo.*desacuerdo|desacuerdo.*acuerdo)',
        
        # Intensity scales (mucho/nada, mucho/poco)
        r'(mucho|bastante|poco|nada)',
        r'(mucho|algo|poco|nada)',
        r'(muchísimo|mucho|regular|poco|nada)',
        
        # Frequency scales
        r'(siempre|frecuentemente|algunas\s+veces|rara\s+vez|nunca)',
        r'(muy\s+frecuentemente|frecuentemente|ocasionalmente|rara\s+vez|nunca)',
        r'(todos\s+los\s+días|varias\s+veces|algunas\s+veces|rara\s+vez|nunca)',
        
        # Quality scales (muy bueno/muy malo)
        r'(muy\s+bueno|bueno|regular|malo|muy\s+malo)',
        r'(excelente|muy\s+bueno|bueno|regular|malo|muy\s+malo)',
        r'(excelente|bueno|regular|malo|pésimo)',
        
        # Satisfaction scales
        r'(muy\s+satisfecho|satisfecho|poco\s+satisfecho|insatisfecho|muy\s+insatisfecho)',
        r'(completamente\s+satisfecho|satisfecho|ni\s+satisfecho\s+ni\s+insatisfecho|insatisfecho|muy\s+insatisfecho)',
        
        # Importance scales
        r'(muy\s+importante|importante|poco\s+importante|nada\s+importante)',
        r'(sumamente\s+importante|muy\s+importante|importante|poco\s+importante|nada\s+importante)',
        
        # Probability/likelihood scales
        r'(muy\s+probable|probable|poco\s+probable|nada\s+probable)',
        r'(definitivamente\s+sí|probablemente\s+sí|probablemente\s+no|definitivamente\s+no)',
        
        # Difficulty scales
        r'(muy\s+fácil|fácil|difícil|muy\s+difícil)',
        r'(muy\s+difícil|difícil|fácil|muy\s+fácil)',
        
        # Trust scales
        r'(confío\s+mucho|confío|confío\s+poco|no\s+confío)',
        r'(muchísima\s+confianza|mucha\s+confianza|poca\s+confianza|ninguna\s+confianza)',
        
        # General ordinal indicators
        r'(1\.\s*[Mm]uy|2\.\s*[Bb]astante|3\.\s*[Pp]oco|4\.\s*[Nn]ada)',
        r'(1\)\s*[Mm]uy|2\)\s*[Bb]astante|3\)\s*[Pp]oco|4\)\s*[Nn]ada)',
        r'([Ee]scala\s+de|[Oo]rdene\s+de|[Cc]alifique\s+de)',
        
        # Numbered scales with words
        r'(1.*mucho.*2.*poco|1.*poco.*2.*mucho)',
        r'(1.*acuerdo.*2.*desacuerdo|1.*desacuerdo.*2.*acuerdo)',
        
        # Common 5-point scales
        r'(totalmente|completamente|parcialmente|ligeramente|nada)',
        r'(siempre|casi\s+siempre|a\s+veces|casi\s+nunca|nunca)',
        
        # Mexican specific terms
        r'(un\s+chorro|bastante|poquito|nada)',
        r'(machín|mucho|regular|poco|nada)',
    ]
    
    return patterns

def check_ordinal_scale(question_text: str, patterns: List[str]) -> bool:
    """
    Check if a question text contains ordinal scale indicators.
    
    Parameters:
    -----------
    question_text : str
        The question text to analyze
    patterns : List[str]
        List of regex patterns to match
        
    Returns:
    --------
    bool
        True if question appears to use ordinal scales
    """
    # Convert to lowercase for matching
    text_lower = question_text.lower()
    
    # Check each pattern
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False

def filter_ordinal_questions(pregs_dict: Dict[str, str]) -> Dict[str, str]:
    """
    Filter questions that appear to use ordinal scales.
    
    Parameters:
    -----------
    pregs_dict : Dict[str, str]
        Dictionary of all survey questions
        
    Returns:
    --------
    Dict[str, str]
        Filtered dictionary containing only ordinal scale questions
    """
    patterns = identify_ordinal_patterns()
    ord_dict = {}
    
    print(f"Analyzing {len(pregs_dict)} questions for ordinal scales...")
    
    ordinal_count = 0
    for question_id, question_text in pregs_dict.items():
        if check_ordinal_scale(question_text, patterns):
            ord_dict[question_id] = question_text
            ordinal_count += 1
            
            # Print first few matches for verification
            if ordinal_count <= 5:
                print(f"\nFound ordinal question {ordinal_count}:")
                print(f"ID: {question_id}")
                print(f"Text: {question_text[:200]}...")
    
    print(f"\nFiltering complete!")
    print(f"Total questions analyzed: {len(pregs_dict)}")
    print(f"Ordinal scale questions found: {len(ord_dict)}")
    print(f"Percentage: {len(ord_dict)/len(pregs_dict)*100:.1f}%")
    
    return ord_dict

def save_ordinal_dict(ord_dict: Dict[str, str], output_path: str):
    """Save the ordinal dictionary to a pickle file."""
    with open(output_path, 'wb') as f:
        pickle.dump(ord_dict, f)
    print(f"Ordinal dictionary saved to: {output_path}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Filter ordinal scale questions from survey data.')
    parser.add_argument('--input', type=str, 
                        help='Path to the los_mex_dict pickle file')
    parser.add_argument('--output', type=str,
                        help='Output path for the ordinal dictionary')
    parser.add_argument('--show-samples', action='store_true',
                        help='Show sample questions found')
    
    args = parser.parse_args()
    
    # Auto-detect input file path
    if args.input:
        dict_file = args.input
    else:
        possible_paths = [
            '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/los_mex_dict.pkl',  # Local Mac
            '/workspaces/navegador/encuestas/los_mex_dict.pkl',  # Docker container
            '~/navegador_workspace/navegador/encuestas/los_mex_dict.pkl',  # VM path
            './encuestas/los_mex_dict.pkl',  # Relative path
            './los_mex_dict.pkl',  # Current directory
        ]
        
        dict_file = None
        for path in possible_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                dict_file = expanded_path
                break
        
        if dict_file is None:
            print("Error: Could not find los_mex_dict.pkl file!")
            print("Searched in:")
            for path in possible_paths:
                print(f"  - {os.path.expanduser(path)}")
            print("\nPlease specify the path using --input argument")
            return
    
    # Set output path
    if args.output:
        output_path = args.output
    else:
        # Default to same directory as input
        input_dir = os.path.dirname(dict_file)
        output_path = os.path.join(input_dir, 'ord_dict.pkl')
    
    print(f"Loading data from: {dict_file}")
    
    # Load the main dictionary
    try:
        los_mex_dict = load_dictionary(dict_file)
        print("Dictionary loaded successfully!")
    except Exception as e:
        print(f"Error loading dictionary: {str(e)}")
        return
    
    # Check if pregs_dict exists
    if 'pregs_dict' not in los_mex_dict:
        print("Error: 'pregs_dict' not found in los_mex_dict!")
        return
    
    pregs_dict = los_mex_dict['pregs_dict']
    print(f"Found {len(pregs_dict)} questions in pregs_dict")
    
    # Filter ordinal questions
    ord_dict = filter_ordinal_questions(pregs_dict)
    
    # Show samples if requested
    if args.show_samples and len(ord_dict) > 0:
        print("\n" + "="*80)
        print("SAMPLE ORDINAL QUESTIONS FOUND:")
        print("="*80)
        
        sample_count = min(10, len(ord_dict))
        for i, (qid, qtext) in enumerate(list(ord_dict.items())[:sample_count]):
            print(f"\n{i+1}. Question ID: {qid}")
            print(f"Text: {qtext}")
            print("-" * 40)
    
    # Save the filtered dictionary
    save_ordinal_dict(ord_dict, output_path)
    
    print(f"\nAnalysis complete!")
    print(f"Ordinal questions saved to: {output_path}")

if __name__ == "__main__":
    main()
