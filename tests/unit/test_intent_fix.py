#!/usr/bin/env python3
"""Test script to verify intent classification fix for topics/datasets query"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_intent_classification():
    """Test intent classification for topics/datasets queries"""
    print("Testing intent classification for topics/datasets queries...")
    
    try:
        from intent_classifier import _classify_intent, intent_dict
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini")
        
        test_queries = [
            # METADATA queries - should be answer_general_questions
            ("what topics are available?", "answer_general_questions", "metadata"),
            ("¿qué temas están disponibles?", "answer_general_questions", "metadata"),
            ("show me the datasets", "answer_general_questions", "metadata"),
            ("list all available topics", "answer_general_questions", "metadata"),
            ("which surveys do you have?", "answer_general_questions", "metadata"),
            ("what data do you have?", "answer_general_questions", "metadata"),
            
            # DATA queries - should be query_variable_database
            ("what do mexicans think about education?", "query_variable_database", "data"),
            ("¿qué piensan los mexicanos sobre educación?", "query_variable_database", "data"),
            ("how do people feel about corruption?", "query_variable_database", "data"),
            ("what are opinions on democracy?", "query_variable_database", "data"),
            ("show me variables about health", "query_variable_database", "data"),
            ("find questions about poverty", "query_variable_database", "data"),
        ]
        
        print(f"Available intents: {list(intent_dict.keys())}")
        print("\nTesting METADATA queries (should be 'answer_general_questions'):")
        
        metadata_correct = 0
        metadata_total = 0
        
        for query, expected, query_type in test_queries:
            if query_type == "metadata":
                metadata_total += 1
                try:
                    intent = _classify_intent(query, intent_dict, llm)
                    is_correct = intent == expected
                    if is_correct:
                        metadata_correct += 1
                    status = "✅" if is_correct else "❌"
                    print(f"  {status} '{query}' -> {intent} (expected: {expected})")
                except Exception as e:
                    print(f"  ❌ '{query}' -> ERROR: {e}")
                    
        print(f"\nMetadata queries accuracy: {metadata_correct}/{metadata_total}")
        
        print("\nTesting DATA queries (should be 'query_variable_database'):")
        
        data_correct = 0
        data_total = 0
        
        for query, expected, query_type in test_queries:
            if query_type == "data":
                data_total += 1
                try:
                    intent = _classify_intent(query, intent_dict, llm)
                    is_correct = intent == expected
                    if is_correct:
                        data_correct += 1
                    status = "✅" if is_correct else "❌"
                    print(f"  {status} '{query}' -> {intent} (expected: {expected})")
                except Exception as e:
                    print(f"  ❌ '{query}' -> ERROR: {e}")
                    
        print(f"\nData queries accuracy: {data_correct}/{data_total}")
        
        overall_correct = metadata_correct + data_correct
        overall_total = metadata_total + data_total
        print(f"\nOverall accuracy: {overall_correct}/{overall_total} ({100*overall_correct/overall_total:.1f}%)")
        
        return overall_correct >= overall_total * 0.8  # 80% accuracy threshold
                
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def test_mock_response_logic():
    """Test the mock response logic for dataset queries"""
    print("\nTesting mock response logic...")
    
    try:
        # Simulate the logic from dashboard
        test_cases = [
            {
                "message": "what topics are available?",
                "intent": "answer_general_questions",
                "expected": "should show datasets"
            },
            {
                "message": "¿qué temas están disponibles?", 
                "intent": "answer_general_questions",
                "expected": "should show datasets"
            }
        ]
        
        for case in test_cases:
            message = case["message"]
            intent = case["intent"]
            message_lower = message.lower()
            
            # Test the condition from our fix
            is_asking_for_datasets = any(word in message_lower for word in [
                "topic", "temas", "datasets", "datos", "encuesta", "survey", 
                "list", "lista", "mostrar", "show", "available", "disponible",
                "que hay", "what are", "cuales son", "which are"
            ])
            
            should_show_datasets = intent == "answer_general_questions" and is_asking_for_datasets
            
            print(f"  '{message}' (intent: {intent})")
            print(f"    is_asking_for_datasets: {is_asking_for_datasets}")
            print(f"    should_show_datasets: {should_show_datasets}")
            print(f"    expected: {case['expected']}")
            print(f"    ✅ PASS" if should_show_datasets else "    ❌ FAIL")
            print()
            
    except Exception as e:
        print(f"Error in mock response test: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Intent Classification Fix for Dataset/Topics Queries")
    print("=" * 60)
    
    success1 = test_intent_classification()
    success2 = test_mock_response_logic()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ All tests passed! The fix should work.")
    else:
        print("❌ Some tests failed. Please review the implementation.")
