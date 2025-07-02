#!/usr/bin/env python3
"""
Test script for enhanced query processing and progress indicator improvements.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the functions we want to test
from dashboard import extract_search_keywords, detect_dataset_preference, agent_state_tracker

def test_keyword_extraction():
    """Test the keyword extraction functionality"""
    print("🔍 Testing keyword extraction...")
    
    test_cases = [
        {
            "input": "I want to know about attitudes about health",
            "expected_contains": ["health", "attitudes"],
            "language": "en"
        },
        {
            "input": "I want to know if mexicans approve health policies", 
            "expected_contains": ["health", "policies"],
            "language": "en"
        },
        {
            "input": "tell me about corruption in government",
            "expected_contains": ["corruption", "government"],
            "language": "en"
        },
        {
            "input": "quiero saber sobre educación en México",
            "expected_contains": ["educación"],
            "language": "es"
        },
        {
            "input": "i want to know if mexican approve health policy, based on the survey about health",
            "expected_contains": ["health", "policy"],
            "language": "en"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n  Test {i}: '{case['input']}'")
        result = extract_search_keywords(case['input'], case['language'])
        print(f"  Result: '{result}'")
        
        # Check if expected keywords are preserved
        success = all(keyword.lower() in result.lower() for keyword in case['expected_contains'])
        status = "✅" if success else "❌"
        print(f"  Status: {status} (Expected: {case['expected_contains']})")

def test_dataset_detection():
    """Test the dataset preference detection"""
    print("\n📊 Testing dataset detection...")
    
    test_cases = [
        {
            "input": "based on the survey about health",
            "expected": ["ENCUESTA_NACIONAL_DE_SALUD"],
            "language": "en"
        },
        {
            "input": "from the education survey",
            "expected": ["ENCUESTA_NACIONAL_DE_EDUCACION"], 
            "language": "en"
        },
        {
            "input": "tell me about corruption",
            "expected": ["ENCUESTA_NACIONAL_DE_CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD"],
            "language": "en"
        },
        {
            "input": "something random without keywords",
            "expected": ["ALL"],
            "language": "en"
        },
        {
            "input": "encuesta sobre género",
            "expected": ["ENCUESTA_NACIONAL_DE_GENERO"],
            "language": "es"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n  Test {i}: '{case['input']}'")
        result = detect_dataset_preference(case['input'], case['language'])
        print(f"  Result: {result}")
        
        # Check if expected datasets are detected
        success = all(dataset in result for dataset in case['expected'])
        status = "✅" if success else "❌"
        print(f"  Status: {status} (Expected: {case['expected']})")

def test_agent_state_tracker():
    """Test the agent state tracker"""
    print("\n🔄 Testing agent state tracker...")
    
    test_states = [
        ("waiting", "en"),
        ("classifying", "es"),
        ("searching", "en"),
        ("filtering", "es"),
        ("analyzing", "en"),
        ("generating", "es"),
        ("complete", "en")
    ]
    
    for state, language in test_states:
        print(f"\n  Setting state: {state} (lang: {language})")
        agent_state_tracker.set_state(state, language)
        
        progress_msg = agent_state_tracker.get_progress_message(language)
        print(f"  Progress message: {progress_msg}")
        
        # Verify state was set correctly
        success = agent_state_tracker.current_state == state
        status = "✅" if success else "❌"
        print(f"  Status: {status}")

def test_integration():
    """Test integration of all components"""
    print("\n🧪 Testing integration...")
    
    # Simulate a user query
    user_query = "I want to know about attitudes about health policies in Mexico"
    detected_lang = "en"
    
    print(f"Original query: '{user_query}'")
    
    # Extract keywords
    keywords = extract_search_keywords(user_query, detected_lang)
    print(f"Extracted keywords: '{keywords}'")
    
    # Detect dataset preference  
    datasets = detect_dataset_preference(user_query, detected_lang)
    print(f"Preferred datasets: {datasets}")
    
    # Simulate state changes
    agent_state_tracker.set_state("classifying", detected_lang)
    agent_state_tracker.set_state("searching", detected_lang)
    agent_state_tracker.set_state("filtering", detected_lang)
    agent_state_tracker.set_state("complete", detected_lang)
    
    print("✅ Integration test completed")

if __name__ == "__main__":
    print("🚀 Starting enhanced query processing tests...\n")
    
    try:
        test_keyword_extraction()
        test_dataset_detection()
        test_agent_state_tracker()
        test_integration()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
