#!/usr/bin/env python3
"""Debug script to test the grading process specifically"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_grading_process():
    """Debug the grading/filtering process"""
    try:
        from variable_selector import (
            _variable_selector, create_tmp_svyinfo_dict, 
            batch_process_expert_grader, client, db_f1
        )
        from dataset_knowledge import tmp_topic_st
        from langchain_openai import ChatOpenAI
        
        # Test query
        user_query = "quiero saber qué piensan los mexicanos sobre la educación"
        
        print("🔍 DEBUGGING GRADING PROCESS")
        print("=" * 50)
        
        # Get the full variable selection process
        llm = ChatOpenAI(model="gpt-4o-mini")
        
        # Run just the retrieval part
        from variable_selector import enrich_query_for_implications, _database_selector, retrieve_by_type_and_topics, embedding_fun_openai
        
        enriched_query = enrich_query_for_implications(user_query)
        query_emb = embedding_fun_openai([enriched_query])[0]
        topic_ids = _database_selector(user_query, tmp_topic_st, llm)
        
        print(f"Query: {user_query}")
        print(f"Topic IDs: {topic_ids}")
        
        # Get retrieval results
        tmp_dist_dict = retrieve_by_type_and_topics(
            db_f1, 
            query_emb, 
            topic_ids=topic_ids,
            type_lst=["question", "summary", "implications"],
            n_results=10
        )
        
        # Process like in _variable_selector
        import pandas as pd
        
        # Remove suffixes from keys
        tmp_dist_dict_clean = { 
            outer_key: { k.split('__')[0]: v for k, v in inner_dict.items() }
            for outer_key, inner_dict in tmp_dist_dict.items() 
        }
        
        print("\nCleaned distance dictionary:")
        for doc_type, results in tmp_dist_dict_clean.items():
            print(f"  {doc_type}: {len(results)} results")
            if results:
                sample_ids = list(results.keys())[:3]
                print(f"    Sample IDs: {sample_ids}")
        
        # Create DataFrame
        tmp_dist_df = pd.DataFrame.from_dict(tmp_dist_dict_clean)
        print(f"\nDataFrame shape: {tmp_dist_df.shape}")
        print(f"DataFrame columns: {list(tmp_dist_df.columns)}")
        print(f"DataFrame index (first 5): {list(tmp_dist_df.index[:5])}")
        
        # Normalize
        tmp_dist_df = (tmp_dist_df - tmp_dist_df.min()) / (tmp_dist_df.max() - tmp_dist_df.min())
        tmp_dist_df['mean'] = tmp_dist_df.mean(axis=1)
        tmp_dist_df.sort_values(by='mean', ascending=True, inplace=True)
        
        print(f"\nNormalized DataFrame (top 10):")
        print(tmp_dist_df.head(10))
        
        # Get top IDs
        top_vals = 5  # Small number for debugging
        top_ids = tmp_dist_df.head(top_vals).index.tolist()
        print(f"\nTop {top_vals} IDs: {top_ids}")
        
        # Build document list for retrieval
        type_lst = ["question", "summary", "implications"]
        tmp_list = []
        for doc_type in type_lst:
            for id_val in top_ids:
                tmp_list.append(id_val + f'__{doc_type}')
        
        print(f"\nDocument list for retrieval: {tmp_list}")
        
        # Retrieve documents
        result_by_ids = db_f1.get(ids=tmp_list)
        tmp_pre_res_dict = dict(zip(result_by_ids['ids'], result_by_ids['documents']))
        
        print(f"\nRetrieved {len(tmp_pre_res_dict)} documents")
        for doc_id, doc_content in list(tmp_pre_res_dict.items())[:3]:
            print(f"  {doc_id}: {doc_content[:100]}...")
        
        # Test grading for just one variable
        if top_ids:
            test_id = top_ids[0]
            print(f"\n🧪 Testing grading for variable: {test_id}")
            
            tmp_svyinfo_st = create_tmp_svyinfo_dict(0, top_ids, tmp_pre_res_dict)
            print(f"Survey info string: {tmp_svyinfo_st[:200]}...")
            
            # Test the grading prompt
            from variable_selector import create_prompt_grader, pattern_format_grader_instrtuctions
            prompt = create_prompt_grader(user_query, tmp_svyinfo_st, pattern_format_grader_instrtuctions)
            print(f"\nGrading prompt (first 500 chars): {prompt[:500]}...")
            
            # Test one grading call
            from variable_selector import get_structured_summary_grader_p
            try:
                cleaned, result = get_structured_summary_grader_p(prompt, model_name="gpt-4o-mini", temperature=0.5)
                print(f"\nGrading result: {result}")
                
                if 'GRADE_DICT' in result and result['GRADE_DICT']:
                    grade_value = list(result['GRADE_DICT'].keys())[0]
                    print(f"Grade value: {grade_value}")
                    print(f"Passes filter (>1): {grade_value > 1}")
                else:
                    print("No GRADE_DICT found in result")
                    
            except Exception as e:
                print(f"Error in grading: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_grading_process()
