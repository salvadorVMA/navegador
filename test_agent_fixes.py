#!/usr/bin/env python3
"""
Test script to verify agent and variable selection functionality
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_agent_initialization():
    """Test agent initialization without persistence"""
    print("Testing agent initialization...")
    try:
        from agent import create_agent
        agent = create_agent(enable_persistence=False)
        print("✅ Agent initialized successfully")
        return agent
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return None

def test_variable_selection():
    """Test variable selection functionality"""
    print("\nTesting variable selection...")
    try:
        from variable_selector import _variable_selector
        from dataset_knowledge import tmp_topic_st
        from langchain_openai import ChatOpenAI
        
        # Create LLM instance
        llm = ChatOpenAI(model="gpt-4o-mini")
        
        # Test query
        test_query = "Show me variables about education and culture"
        
        print(f"Testing query: '{test_query}'")
        topic_ids, variables_dict, grade_dict = _variable_selector(test_query, tmp_topic_st, llm)
        
        print(f"✅ Variable selection completed:")
        print(f"   - Topic IDs: {topic_ids}")
        print(f"   - Variables found: {len(variables_dict) if variables_dict else 0}")
        print(f"   - Grades assigned: {len(grade_dict) if grade_dict else 0}")
        
        if grade_dict:
            # Show top graded variables
            sorted_vars = sorted(grade_dict.items(), key=lambda x: list(x[1].keys())[0], reverse=True)
            print(f"   - Top 3 variables:")
            for i, (var_id, grade) in enumerate(sorted_vars[:3]):
                print(f"     {i+1}. {var_id}: {list(grade.keys())[0]}")
        
        return True
    except Exception as e:
        print(f"❌ Variable selection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_query_enrichment():
    """Test query enrichment for implications targeting"""
    print("\nTesting query enrichment...")
    try:
        from variable_selector import enrich_query_for_implications
        
        test_query = "education policies"
        enriched = enrich_query_for_implications(test_query)
        
        print(f"Original query: {test_query}")
        print(f"Enriched query: {enriched}")
        print("✅ Query enrichment working")
        return True
    except Exception as e:
        print(f"❌ Query enrichment failed: {e}")
        return False

def test_agent_invocation():
    """Test basic agent invocation"""
    print("\nTesting agent invocation...")
    try:
        agent = test_agent_initialization()
        if not agent:
            return False
        
        # Create test state
        test_state = {
            "messages": [],
            "intent": "ask_for_variables",
            "user_query": "show me variables about education",
            "original_query": "show me variables about education",
            "dataset": ["all"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        print("Testing agent invocation...")
        response = agent.invoke(test_state)
        print(f"✅ Agent invocation successful: {type(response)}")
        print(f"   Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        return True
    except Exception as e:
        print(f"❌ Agent invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("NAVEGADOR AGENT AND VARIABLE SELECTION TESTS")
    print("=" * 60)
    
    results = {}
    
    # Test individual components
    results['agent_init'] = test_agent_initialization() is not None
    results['variable_selection'] = test_variable_selection()
    results['query_enrichment'] = test_query_enrichment()
    results['agent_invocation'] = test_agent_invocation()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} : {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! System is ready for testing.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
