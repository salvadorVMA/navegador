#!/usr/bin/env python3
"""Test script to verify dashboard response logic"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_response_logic():
    """Test that dashboard handles intent correctly"""
    try:
        # Mock the dashboard response logic without running the full app
        from dashboard import get_intelligent_mock_response, detect_language
        
        test_cases = [
            # Metadata queries - should show datasets/topics
            {
                "query": "what topics are available?",
                "expected_intent": "answer_general_questions",
                "should_show_datasets": True
            },
            {
                "query": "¿qué temas están disponibles?", 
                "expected_intent": "answer_general_questions",
                "should_show_datasets": True
            },
            {
                "query": "show me the datasets",
                "expected_intent": "answer_general_questions", 
                "should_show_datasets": True
            },
            # Data queries - should search variables
            {
                "query": "what do mexicans think about education?",
                "expected_intent": "query_variable_database",
                "should_show_datasets": False
            },
            {
                "query": "¿qué piensan los mexicanos sobre educación?",
                "expected_intent": "query_variable_database",
                "should_show_datasets": False
            },
            {
                "query": "how do people feel about corruption?",
                "expected_intent": "query_variable_database", 
                "should_show_datasets": False
            }
        ]
        
        print("🧪 Testing Dashboard Response Logic")
        print("=" * 50)
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            query = case["query"]
            expected_intent = case["expected_intent"]
            should_show_datasets = case["should_show_datasets"]
            
            try:
                # Simulate agent state with the expected intent
                agent_state = {"intent": expected_intent}
                detected_lang = detect_language(query)
                
                response = get_intelligent_mock_response(query, agent_state, detected_lang)
                
                # Check if response contains dataset info when it should
                content = response.get("content", "")
                contains_datasets = any(word in content.lower() for word in [
                    "dataset", "encuesta", "conjunto de datos", "surveys", "datos disponibles", 
                    "available data", "1.", "2.", "3."  # numbered lists typically indicate datasets
                ])
                
                is_correct = contains_datasets == should_show_datasets
                status = "✅" if is_correct else "❌"
                
                print(f"{status} '{query}' (intent: {expected_intent})")
                print(f"   Should show datasets: {should_show_datasets}, Contains datasets: {contains_datasets}")
                
                if is_correct:
                    correct += 1
                else:
                    print(f"   Response preview: {content[:100]}...")
                    
            except Exception as e:
                print(f"❌ Error processing '{query}': {e}")
        
        accuracy = (correct / total) * 100
        print(f"\n🎯 Logic accuracy: {correct}/{total} ({accuracy:.1f}%)")
        
        return accuracy == 100.0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dashboard_response_logic()
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
