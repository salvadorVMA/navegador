#!/usr/bin/env python3
"""
Debug script to investigate why grading returns 0 entries.
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_variable_selector_grading():
    """Debug the grading issue step by step."""
    try:
        from variable_selector import _variable_selector, batch_process_expert_grader
        from dataset_knowledge import tmp_topic_st
        from langchain_openai import ChatOpenAI
        
        print("Debugging variable selector grading issue...")
        
        # Create LLM instance
        llm = ChatOpenAI(model="gpt-4o-mini")
        
        # Test query
        test_query = "What do Mexicans think about education?"
        
        print(f"Query: {test_query}")
        
        # Call with very few variables to isolate the issue
        print("\n=== Testing with 3 variables ===")
        topic_ids, variables_dict, grade_dict = _variable_selector(
            test_query, tmp_topic_st, llm, top_vals=3, use_simultaneous_retrieval=True
        )
        
        print(f"Found {len(variables_dict)} variables")
        print(f"Grade dict has {len(grade_dict)} entries")
        
        if grade_dict:
            print("Grading successful! Sample grades:")
            for var_id, grade_info in list(grade_dict.items())[:3]:
                print(f"  {var_id}: {grade_info}")
        else:
            print("❌ Grading failed - investigating further...")
            
            # Let's debug the grading process step by step
            print("\n=== Manual grading test ===")
            if variables_dict:
                # Get the first few variable IDs
                var_ids = list(set(var_id.split('__')[0] for var_id in variables_dict.keys()))[:3]
                print(f"Testing grading for: {var_ids}")
                
                # Create the same dict structure that batch_process_expert_grader expects
                tmp_pre_res_dict = {var_id: variables_dict.get(f"{var_id}__question", "") 
                                   for var_id in var_ids if f"{var_id}__question" in variables_dict}
                
                print(f"Input dict for grading: {list(tmp_pre_res_dict.keys())}")
                
                # Test batch grading directly
                try:
                    grading_results = batch_process_expert_grader(
                        test_query, var_ids, tmp_pre_res_dict, llm, batch_size=8192
                    )
                    print(f"Raw grading results: {grading_results}")
                    
                    # Check if any have GRADE_DICT
                    grade_dict_results = {k: v.get('GRADE_DICT', {}) for k, v in grading_results.items() if 'GRADE_DICT' in v}
                    print(f"GRADE_DICT results: {grade_dict_results}")
                    
                    # Check filter
                    filtered = {k: v for k, v in grade_dict_results.items() if v and list(v.keys())[0] > 0}
                    print(f"Filtered results (grade > 0): {filtered}")
                    
                except Exception as e:
                    print(f"Error in batch grading: {e}")
                    import traceback
                    traceback.print_exc()
        
        return len(grade_dict) > 0
        
    except Exception as e:
        print(f"❌ Error debugging grading: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_variable_selector_grading()
    print(f"\n{'✅' if success else '❌'} Debug complete. Grading {'working' if success else 'failed'}.")
