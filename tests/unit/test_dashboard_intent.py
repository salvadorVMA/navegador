#!/usr/bin/env python3
"""Test script to verify intent classification in dashboard"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_intent():
    """Test intent classification used in dashboard"""
    try:
        from intent_classifier import intent_dict, _classify_intent
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini")
        
        test_cases = [
            # Metadata queries (should be answer_general_questions)
            ("what topics are available?", "answer_general_questions"),
            ("¿qué temas están disponibles?", "answer_general_questions"),
            ("show me the datasets", "answer_general_questions"),
            ("list all surveys", "answer_general_questions"),
            
            # Data queries (should be query_variable_database)
            ("what do mexicans think about education?", "query_variable_database"),
            ("¿qué piensan los mexicanos sobre educación?", "query_variable_database"),
            ("how do people feel about corruption?", "query_variable_database"),
            ("what are opinions on democracy?", "query_variable_database"),
        ]
        
        print("🧪 Testing Dashboard Intent Classification")
        print("=" * 50)
        
        correct = 0
        total = len(test_cases)
        
        for query, expected in test_cases:
            try:
                classified = _classify_intent(query, intent_dict, llm)
                is_correct = classified == expected
                status = "✅" if is_correct else "❌"
                print(f"{status} '{query}' -> {classified} (expected: {expected})")
                if is_correct:
                    correct += 1
            except Exception as e:
                print(f"❌ Error classifying '{query}': {e}")
        
        accuracy = (correct / total) * 100
        print(f"\n🎯 Accuracy: {correct}/{total} ({accuracy:.1f}%)")
        
        return accuracy == 100.0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_intent()
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
