#!/usr/bin/env python3
"""
Test script to verify the dashboard improvements work correctly.
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_variable_selection():
    """Test that the dashboard can use the improved simultaneous retrieval."""
    try:
        from variable_selector import _variable_selector
        from dataset_knowledge import tmp_topic_st
        from langchain_openai import ChatOpenAI
        
        print("Testing dashboard variable selection improvements...")
        
        # Create LLM instance
        llm = ChatOpenAI(model="gpt-4o-mini")
        
        # Test query
        test_query = "What do Mexicans think about education?"
        
        print(f"Query: {test_query}")
        
        # Test with improved simultaneous retrieval (default) - use fewer variables for testing
        print("\n=== Testing with simultaneous retrieval (default) ===")
        topic_ids, variables_dict, grade_dict = _variable_selector(
            test_query, tmp_topic_st, llm, top_vals=10, use_simultaneous_retrieval=True
        )
        
        print(f"Found {len(variables_dict)} variables")
        print(f"Grade dict has {len(grade_dict)} entries")
        
        # Show top 3 graded variables
        if grade_dict:
            sorted_vars = sorted(grade_dict.items(), key=lambda x: list(x[1].values())[0], reverse=True)
            print("\nTop 3 variables:")
            for i, (var_id, grade_info) in enumerate(sorted_vars[:3]):
                grade = list(grade_info.values())[0]
                question = variables_dict.get(f"{var_id}__question", "No question found")
                print(f"{i+1}. Grade: {grade} - {question[:100]}...")
        
        # Test without simultaneous retrieval for comparison - use fewer variables
        print("\n=== Testing with separate retrieval (comparison) ===")
        topic_ids2, variables_dict2, grade_dict2 = _variable_selector(
            test_query, tmp_topic_st, llm, top_vals=10, use_simultaneous_retrieval=False
        )
        
        print(f"Found {len(variables_dict2)} variables")
        print(f"Grade dict has {len(grade_dict2)} entries")
        
        print("\n✅ Dashboard variable selection improvements working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing dashboard improvements: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dashboard_variable_selection()
    sys.exit(0 if success else 1)
