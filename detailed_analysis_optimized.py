"""
Optimized Detailed Analysis Module

This module provides performance-optimized versions of the analysis functions
with caching, batch processing, and other performance improvements.
"""

import time
from typing import Dict, List, Tuple, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import original functions and optimization tools
from detailed_analysis import (
    get_structured_summary,
    get_structured_expert_summary, 
    get_transversal_analysis,
    format_detailed_report
)
from performance_optimization import (
    performance_timer,
    LLMBatchProcessor,
    DatabaseManager,
    OptimizedPrompts
)
from utility_functions import get_answer_optimized, environment_setup_optimized


@performance_timer("detailed_analysis_optimized")
def run_detailed_analysis_optimized(selected_variables: list, user_query: str, analysis_params: Optional[dict] = None) -> dict:
    """
    Optimized version of detailed analysis with performance improvements.
    
    Key optimizations:
    1. Singleton database connection
    2. Batch processing for expert summaries
    3. Parallel LLM calls where possible
    4. Response caching
    5. Performance monitoring
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        analysis_params (dict): Additional parameters for analysis (optional)
        
    Returns:
        dict: Comprehensive analysis results
    """
    print(f"Starting optimized detailed analysis for query: {user_query}")
    print(f"Selected variables: {selected_variables}")
    
    start_time = time.time()
    
    try:
        # Use optimized database setup (singleton)
        print("Using optimized database connection...")
        db_manager = DatabaseManager()
        client, db_f1 = db_manager.get_client()
        
        # Create mock preprocessed results (same as original)
        tmp_pre_res_dict = {}
        for var_id in selected_variables:
            tmp_pre_res_dict[f"{var_id}__question"] = f"{var_id}|Example question for {var_id}"
            tmp_pre_res_dict[f"{var_id}__summary"] = f"{var_id}|Mock summary data for variable {var_id}"
        
        tmp_grade_dict = {var_id: 1.0 for var_id in selected_variables}
        
        # Run optimized analysis pipeline
        print("Running optimized analysis pipeline...")
        tmp_preproc_dic, final_smry_dict, structured_expert_results = _deep_analyzer_optimized(
            tmp_pre_res_dict=tmp_pre_res_dict,
            tmp_grade_dict=tmp_grade_dict,
            user_query=user_query,
            db_f1=db_f1
        )
        
        # Package results
        analysis_results = {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'detailed_report_optimized',
            'success': True,
            'patterns': structured_expert_results,
            'final_analysis': final_smry_dict,
            'processed_data': {
                'filtered_data': tmp_preproc_dic,
                'expert_summaries': structured_expert_results
            },
            'report_sections': {
                'query_answer': final_smry_dict.get('QUERY_ANSWER', 'No answer available'),
                'topic_summary': final_smry_dict.get('TOPIC_SUMMARY', 'No summary available'),
                'topic_summaries': final_smry_dict.get('TOPIC_SUMMARIES', {}),
                'expert_replies': [v.get('EXPERT_REPLY', '') for v in structured_expert_results.values()]
            },
            'performance_info': {
                'total_time': time.time() - start_time,
                'optimization_enabled': True,
                'cache_enabled': True
            }
        }
        
        print(f"Optimized detailed analysis completed in {time.time() - start_time:.2f} seconds")
        return analysis_results
        
    except Exception as e:
        print(f"Error in optimized detailed analysis: {e}")
        return {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'detailed_report_optimized',
            'success': False,
            'error': str(e),
            'performance_info': {
                'total_time': time.time() - start_time,
                'optimization_enabled': True,
                'cache_enabled': True
            },
            'report_sections': {
                'query_answer': f'Error occurred during analysis: {str(e)}',
                'topic_summary': 'Analysis could not be completed due to technical issues',
                'topic_summaries': {},
                'expert_replies': []
            }
        }


def _deep_analyzer_optimized(tmp_pre_res_dict: dict, tmp_grade_dict: dict, user_query: str, db_f1) -> Tuple[dict, dict, dict]:
    """
    Optimized version of the deep analyzer with parallel processing.
    """
    print("Starting optimized deep analysis...")
    
    # Filter for questions and summaries (same as original)
    tmp_preproc_dic = {k: v for k, v in tmp_pre_res_dict.items() if k.split('__')[1] in ['question', 'summary']}
    tmp_preproc_dic = {k: v for k, v in tmp_preproc_dic.items() if any(k.startswith(grade_key) for grade_key in tmp_grade_dict.keys())}
    
    print(f"Filtered to {len(tmp_preproc_dic)} relevant items")
    
    # Combine strings for processing (same as original)
    tmp_combined_strings = []
    for i, (k, v) in enumerate(tmp_preproc_dic.items(), start=1):
        facet = k.split("__", 1)[1].upper()
        grouped_index = (i + 1) // 2 
        parts = v.split("|", 1)
        text = parts[1] if len(parts) > 1 else parts[0]
        p_id = k.split("__")[0]
        tmp_combined_strings.append(f"{facet}_{grouped_index}|{p_id}: {text}")
    
    tmp_res_st = '\n'.join(tmp_combined_strings)
    print(f"Created combined result string with {len(tmp_combined_strings)} entries")
    
    # Step 1: Get structured summary (cached)
    print("Generating structured summary (with caching)...")
    try:
        raw_content, tst_lgc_dict = get_structured_summary_optimized(
            user_query=user_query, 
            tmp_res_st=tmp_res_st, 
            tmp_grade_dict=tmp_grade_dict
        )
        print(f"Generated {len(tst_lgc_dict)} pattern groups")
    except Exception as e:
        print(f"Error in structured summary: {e}")
        tst_lgc_dict = {}
    
    # Step 2: Process expert summaries in parallel
    print("Processing expert summaries in parallel...")
    if tst_lgc_dict:
        try:
            structured_expert_results = batch_process_expert_summaries_optimized(tst_lgc_dict, db_f1)
            print(f"Generated {len(structured_expert_results)} expert summaries")
        except Exception as e:
            print(f"Error in expert summaries: {e}")
            structured_expert_results = {}
    else:
        structured_expert_results = {}
    
    # Step 3: Create transversal analysis (cached)
    print("Generating transversal analysis (with caching)...")
    if structured_expert_results:
        try:
            tmp_smry_st = ' * '.join([v['EXPERT_REPLY'] for v in structured_expert_results.values() if 'EXPERT_REPLY' in v])
            final_smry_dict = get_transversal_analysis_optimized(tmp_smry_st, user_query)
            print("Completed transversal analysis")
        except Exception as e:
            print(f"Error in transversal analysis: {e}")
            final_smry_dict = {
                'TOPIC_SUMMARIES': {'ERROR': f'Failed to generate analysis: {str(e)}'},
                'TOPIC_SUMMARY': f'Error in analysis: {str(e)}',
                'QUERY_ANSWER': f'Unable to provide answer due to error: {str(e)}'
            }
    else:
        final_smry_dict = {
            'TOPIC_SUMMARIES': {'ERROR': 'No expert summaries generated'},
            'TOPIC_SUMMARY': 'Unable to generate analysis due to lack of expert summaries',
            'QUERY_ANSWER': 'Cannot provide answer without analysis data'
        }
    
    return tmp_preproc_dic, final_smry_dict, structured_expert_results


def get_structured_summary_optimized(user_query: str, tmp_res_st: str, tmp_grade_dict: dict, 
                                   model_name: str = 'gpt-4o-mini-2024-07-18', temperature: float = 0.9) -> Tuple[str, dict]:
    """Optimized structured summary with caching."""
    from detailed_analysis import create_prompt_crosssum, pattern_parser_simdif, clean_llm_json_output
    
    # Use optimized prompt for reduced tokens
    n_topics = min(len(tmp_grade_dict) // 4, 5)
    
    # Create prompt (could be optimized further)
    prompt = create_prompt_crosssum(
        user_query=user_query, 
        tmp_res_st=tmp_res_st, 
        n_topics=n_topics, 
        format_instructions=""  # Reduced format instructions to save tokens
    )
    
    # Use cached LLM call
    content = get_answer_optimized(prompt, model=model_name, temperature=temperature)
    content = clean_llm_json_output(content)
    
    try:
        parsed = pattern_parser_simdif.parse(content)
        return content, parsed.model_dump()
    except Exception as e:
        print("Parsing failed. Raw output:")
        print(content)
        print("Error:", e)
        return content, {}


def batch_process_expert_summaries_optimized(tst_lgc_dict: dict, db_f1) -> dict:
    """
    Optimized expert summary processing with parallel execution.
    """
    print("Starting parallel expert summary processing...")
    
    # Prepare all requests for parallel processing
    llm_requests = []
    keys = list(tst_lgc_dict.keys())
    
    for key in keys:
        # Prepare prompt for this key
        from detailed_analysis import create_prompt_expt_smry, expert_summary_format_instructions
        prompt = create_prompt_expt_smry(
            tst_lgc_dict=tst_lgc_dict,
            tmp_ky=key,
            db_f1=db_f1,
            format_instructions=expert_summary_format_instructions
        )
        
        llm_requests.append({
            'prompt': prompt,
            'model': 'gpt-4o-mini-2024-07-18',
            'temperature': 0.9,
            'key': key
        })
    
    # Process in parallel
    processor = LLMBatchProcessor(max_workers=15)  # Limit to 15 parallel calls (3 per core, assuming 5 cores)
    results = processor.process_batch(llm_requests, get_answer_optimized)
    
    # Parse results
    structured_results = {}
    from detailed_analysis import expert_summary_parser
    
    for i, (key, result) in enumerate(zip(keys, results)):
        if result['success']:
            try:
                parsed = expert_summary_parser.parse(result['result'])
                structured_results[key] = parsed.model_dump()
            except Exception as e:
                print(f"Error parsing expert summary for {key}: {e}")
                structured_results[key] = {'EXPERT_REPLY': f'Error parsing response: {str(e)}'}
        else:
            structured_results[key] = {'EXPERT_REPLY': f'Error: {result.get("error", "Unknown error")}'}
    
    return structured_results


def get_transversal_analysis_optimized(tmp_smry_st: str, user_query: str, 
                                     model_name: str = 'gpt-4o-mini-2024-07-18', temperature: float = 0.9) -> dict:
    """Optimized transversal analysis with caching."""
    from detailed_analysis import create_prompt_trnsvl, transversal_parser, transversal_format_instructions
    from fix_transversal_json import fix_json_format
    
    # Generate the prompt
    prompt = create_prompt_trnsvl(
        tmp_smry_st=tmp_smry_st,
        user_query=user_query,
        n_cmn_tpc=3,
        format_instructions=transversal_format_instructions
    )
    
    # Use cached LLM call
    response = get_answer_optimized(prompt=prompt, model=model_name, temperature=temperature)
    
    if response is None:
        return {
            'TOPIC_SUMMARIES': {'ERROR': 'No response from model'},
            'TOPIC_SUMMARY': 'Error generating summary: No response from model',
            'QUERY_ANSWER': 'Error generating answer: No response from model'
        }
    
    try:
        # First attempt: try to fix JSON format issues before parsing
        fixed_response = fix_json_format(response)
        parsed = transversal_parser.parse(fixed_response)
        return parsed.model_dump()
    except Exception as e:
        print(f"Error parsing transversal analysis: {e}")
        # Second attempt: If parsing fails, try to salvage the output by extracting what we can
        try:
            import re
            import json
            
            # Try to extract the JSON part from the response if LLM added any text
            json_match = re.search(r'({[\s\S]*})', response)
            if json_match:
                json_str = json_match.group(1)
                # Fix trailing commas
                json_str = fix_json_format(json_str)
                # Try to parse as plain JSON
                data = json.loads(json_str)
                # Check if we have the required keys
                if all(k in data for k in ['TOPIC_SUMMARIES', 'TOPIC_SUMMARY', 'QUERY_ANSWER']):
                    return data
        except Exception as inner_e:
            print(f"Failed to salvage JSON: {inner_e}")
            
        # If all else fails, return error dictionary
        return {
            'TOPIC_SUMMARIES': {'ERROR': f'Failed to generate topic summaries: {str(e)}'},
            'TOPIC_SUMMARY': f'Error generating summary: {str(e)}',
            'QUERY_ANSWER': f'Error generating answer: {str(e)}'
        }


# Quick benchmark function
def benchmark_analysis_performance(selected_variables: list, user_query: str, iterations: int = 3) -> dict:
    """
    Benchmark the performance difference between original and optimized analysis.
    """
    from detailed_analysis import run_detailed_analysis
    
    print(f"Benchmarking analysis performance with {iterations} iterations...")
    
    original_times = []
    optimized_times = []
    
    # Benchmark original implementation
    print("\nTesting original implementation...")
    for i in range(iterations):
        start_time = time.time()
        try:
            result = run_detailed_analysis(selected_variables, user_query)
            if result.get('success', False):
                original_times.append(time.time() - start_time)
            else:
                print(f"Original analysis failed on iteration {i+1}")
        except Exception as e:
            print(f"Original analysis error on iteration {i+1}: {e}")
    
    # Benchmark optimized implementation
    print("\nTesting optimized implementation...")
    for i in range(iterations):
        start_time = time.time()
        try:
            result = run_detailed_analysis_optimized(selected_variables, user_query)
            if result.get('success', False):
                optimized_times.append(time.time() - start_time)
            else:
                print(f"Optimized analysis failed on iteration {i+1}")
        except Exception as e:
            print(f"Optimized analysis error on iteration {i+1}: {e}")
    
    # Calculate statistics
    if original_times and optimized_times:
        avg_original = sum(original_times) / len(original_times)
        avg_optimized = sum(optimized_times) / len(optimized_times)
        improvement = ((avg_original - avg_optimized) / avg_original) * 100
        
        return {
            'original_times': original_times,
            'optimized_times': optimized_times,
            'average_original': round(avg_original, 2),
            'average_optimized': round(avg_optimized, 2),
            'improvement_percentage': round(improvement, 2),
            'iterations': iterations
        }
    else:
        return {
            'error': 'Could not complete benchmark due to failures',
            'original_times': original_times,
            'optimized_times': optimized_times
        }
