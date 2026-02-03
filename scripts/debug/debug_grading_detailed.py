#!/usr/bin/env python3
"""
Debug script to investigate the grading process specifically.
"""

import os
import sys
from utility_functions import environment_setup, embedding_fun_openai, get_answer
from variable_selector import (
    _variable_selector, retrieve_by_type_and_topics, enrich_query_for_implications,
    create_tmp_svyinfo_dict, create_prompt_grader, get_structured_summary_grader_p,
    batch_process_expert_grader
)
from dataset_knowledge import tmp_topic_st, rev_topic_dict
import pandas as pd

# Set up models
mod_alto = 'gpt-4.1-2025-04-14' 
mod_bajo = 'gpt-4.1-nano-2025-04-14'
mod_med = 'gpt-4.1-mini-2025-04-14'

def debug_grading_process():
    """Debug the grading process specifically"""
    
    print("=== DEBUG: Grading Process Analysis ===")
    
    # Set up ChromaDB
    client, db_f1 = environment_setup(embedding_fun_openai)
    
    # Test query
    user_query = "What do Mexicans think about education?"
    print(f"🔍 Query: {user_query}")
    
    # Get the enriched query and embedding
    enriched_query = enrich_query_for_implications(user_query)
    query_emb = embedding_fun_openai([enriched_query])[0]
    
    # Retrieve education documents
    tmp_dist_dict = retrieve_by_type_and_topics(
        db_f1, 
        query_emb, 
        topic_ids=['EDU'],
        type_lst=["question", "summary", "implications"],
        n_results=100
    )
    
    # Remove suffixes from keys
    tmp_dist_dict = { outer_key: { k.split('__')[0]: v for k, v in inner_dict.items() }
        for outer_key, inner_dict in tmp_dist_dict.items() }
    
    # Create DataFrame and get top variables
    tmp_dist_df = pd.DataFrame.from_dict(tmp_dist_dict)
    tmp_dist_df = (tmp_dist_df - tmp_dist_df.min()) / (tmp_dist_df.max() - tmp_dist_df.min())
    tmp_dist_df['mean'] = tmp_dist_df.mean(axis=1)
    tmp_dist_df.sort_values(by='mean', ascending=True, inplace=True)
    
    top_ids = tmp_dist_df.head(5).index.tolist()  # Just test with 5 variables
    print(f"📊 Top variable IDs: {top_ids}")
    
    # Retrieve documents for these IDs
    tmp_list = []
    for type in ["question", "summary", "implications"]:
        for id in top_ids:
            tmp_list.append(id + f'__{type}')
    
    result_by_ids = db_f1.get(ids=tmp_list)
    tmp_pre_res_dict = dict(zip(result_by_ids['ids'], result_by_ids['documents']))
    
    print(f"📋 Retrieved {len(tmp_pre_res_dict)} documents")
    
    # Test grading for each variable
    print(f"\n--- Testing Grading for Each Variable ---")
    
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model=mod_med, temperature=0.5)
    
    for i, var_id in enumerate(top_ids):
        print(f"\n🎯 Variable {i+1}: {var_id}")
        
        # Create survey info
        tmp_svyinfo_st = create_tmp_svyinfo_dict(i, top_ids, tmp_pre_res_dict)
        print(f"📝 Survey info: {tmp_svyinfo_st[:200]}..." if len(tmp_svyinfo_st) > 200 else tmp_svyinfo_st)
        
        # Create grading prompt
        prompt = create_prompt_grader(user_query, tmp_svyinfo_st)
        print(f"🤖 Grading prompt length: {len(prompt)} characters")
        
        # Get grade
        try:
            cleaned_output, grade_result = get_structured_summary_grader_p(prompt, model_name=mod_med, temperature=0.5)
            print(f"✅ Raw LLM output: {cleaned_output}")
            print(f"📊 Parsed grade result: {grade_result}")
            
            # Extract the actual grade
            grade_dict = grade_result.get('GRADE_DICT', {})
            if grade_dict:
                grade = list(grade_dict.keys())[0]
                explanation = list(grade_dict.values())[0]
                print(f"🎯 Grade: {grade}")
                print(f"💬 Explanation: {explanation}")
                
                # Check if it would pass the filter
                passes_filter = grade > 0
                print(f"✅ Passes filter (grade > 0): {passes_filter}")
            else:
                print(f"❌ No grade in result")
                
        except Exception as e:
            print(f"❌ Grading failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Test batch processing
    print(f"\n--- Testing Batch Processing ---")
    try:
        # Pass model name instead of LLM object for batch processing
        tst_res = batch_process_expert_grader(user_query, top_ids, tmp_pre_res_dict, mod_med, batch_size=8192)
        print(f"✅ Batch processing completed")
        print(f"📊 Results: {len(tst_res)} variables processed")
        
        # Check grades
        tmp_grade_dict = {k: v.get('GRADE_DICT', {}) for k, v in tst_res.items() if 'GRADE_DICT' in v}
        print(f"🎯 Variables with grades: {len(tmp_grade_dict)}")
        
        # Filter elements with grade > 0
        filtered_grades = {k: v for k, v in tmp_grade_dict.items() if v and list(v.keys())[0] > 0}
        print(f"✅ Variables passing filter (grade > 0): {len(filtered_grades)}")
        
        # Show all grades
        print(f"\nAll grades:")
        for var_id, grade_info in tmp_grade_dict.items():
            if grade_info:
                grade = list(grade_info.keys())[0]
                explanation = list(grade_info.values())[0]
                print(f"  {var_id}: Grade {grade} - {explanation}")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_grading_process()
