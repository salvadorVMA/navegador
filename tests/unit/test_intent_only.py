#!/usr/bin/env python3
"""
Simple test for intent classification only
"""

from intent_classifier import _classify_intent, intent_dict

def test_intent_classification():
    """Test only the intent classification function"""
    
    print("=" * 60)
    print("TESTING INTENT CLASSIFICATION ONLY")
    print("=" * 60)
    
    # Test messages for each expected intent
    test_cases = [
        {
            "message": "I want to analyze variables related to political participation in Mexico",
            "expected": "query_variable_database"
        },
        {
            "message": "What datasets are available?",
            "expected": "answer_general_questions"
        },
        {
            "message": "What can you do?",
            "expected": "continue_conversation"
        },
        {
            "message": "Yes, these variables look good, proceed",
            "expected": "review_variable_selection"
        },
        {
            "message": "I want a detailed analysis",
            "expected": "select_analysis_type"
        },
        {
            "message": "Run the analysis now",
            "expected": "confirm_and_run"
        },
        {
            "message": "Start over",
            "expected": "reset_conversation"
        },
        {
            "message": "Goodbye",
            "expected": "end_conversation"
        },
    ]
    
    print(f"Available intents: {list(intent_dict.keys())}")
    print()
    
    correct = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: '{test_case['message']}'")
        
        try:
            # Test intent classification
            detected_intent = _classify_intent(test_case["message"], intent_dict, None)
            
            print(f"  Expected: {test_case['expected']}")
            print(f"  Detected: {detected_intent}")
            
            is_correct = detected_intent == test_case['expected']
            print(f"  Result: {'✓ CORRECT' if is_correct else '✗ WRONG'}")
            
            if is_correct:
                correct += 1
                
        except Exception as e:
            print(f"  Error: {e}")
        
        print("-" * 40)
    
    print(f"\nResults: {correct}/{total} correct ({100*correct/total:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    test_intent_classification()
