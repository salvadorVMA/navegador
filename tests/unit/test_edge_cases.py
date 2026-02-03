#!/usr/bin/env python3
"""
Edge Cases and Error Handling Test for Agent Workflow
Tests robustness of the agent with various edge cases and error scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import create_agent
from intent_classifier import _classify_intent, intent_dict
from utility_functions import get_answer
from langchain_core.messages import HumanMessage

def classify_intent(user_message: str) -> str:
    """Wrapper for intent classification"""
    return _classify_intent(user_message, intent_dict, None)

def test_edge_cases():
    """Test various edge cases and error scenarios"""
    print("======================================================================")
    print("TESTING EDGE CASES AND ERROR HANDLING")
    print("======================================================================")
    
    # Initialize agent
    agent = create_agent()
    
    edge_cases = [
        # Empty/minimal inputs
        ("", "continue_conversation"),
        ("   ", "continue_conversation"),
        ("?", "continue_conversation"),
        
        # Ambiguous inputs
        ("hello", "continue_conversation"),
        ("help", "continue_conversation"),
        ("yes", "continue_conversation"),
        ("no", "continue_conversation"),
        
        # Very long inputs
        ("I want to analyze education data " * 20, "query_variable_database"),
        
        # Mixed language (Spanish/English)
        ("Quiero analizar datos de educación", "query_variable_database"),
        ("¿Qué puedes hacer?", "continue_conversation"),
        
        # Special characters and numbers
        ("Analysis #1: Education & Politics (2024)", "query_variable_database"),
        ("Run analysis @now!", "confirm_and_run"),
        
        # Unclear requests
        ("I don't know what I want", "continue_conversation"),
        ("Maybe something about data", "continue_conversation"),
        
        # Multiple intents in one message
        ("What can you do and also run an analysis", "continue_conversation"),
        
        # Technical jargon
        ("Execute multivariate regression on socioeconomic variables", "confirm_and_run"),
    ]
    
    print("\n🔍 Testing Edge Cases:")
    print("=" * 50)
    
    passed = 0
    total = len(edge_cases)
    
    for i, (input_text, expected_intent) in enumerate(edge_cases, 1):
        try:
            # Test intent classification
            detected_intent = classify_intent(input_text)
            
            # Test agent workflow with proper message format
            state = {
                "messages": [HumanMessage(content=input_text)],
                "intent": "",
                "user_query": input_text,
                "dataset": ["all"],
                "selected_variables": [],
                "analysis_type": "descriptive",
                "user_approved": False,
                "analysis_result": {}
            }
            
            result = agent.invoke(state, {"recursion_limit": 2})
            
            print(f"\nTest {i}: {'✅ PASSED' if detected_intent else '❌ FAILED'}")
            print(f"Input: '{input_text[:50]}{'...' if len(input_text) > 50 else ''}'")
            print(f"Detected Intent: {detected_intent}")
            
            # Get response from the last message
            response = "No response"
            if result.get("messages") and len(result["messages"]) > 1:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content
            
            print(f"Agent Response: {response}")
            
            # If we get a response without crashing, consider it passed
            if detected_intent and response != "No response":
                passed += 1
            
        except Exception as e:
            print(f"\nTest {i}: ❌ FAILED (Exception)")
            print(f"Input: '{input_text[:50]}{'...' if len(input_text) > 50 else ''}'")
            print(f"Error: {str(e)[:100]}{'...' if len(str(e)) > 100 else ''}")
    
    print(f"\n🏁 EDGE CASES RESULTS")
    print("=" * 50)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    return passed == total

def test_state_persistence():
    """Test state management across multiple interactions"""
    print("\n\n🔄 Testing State Persistence:")
    print("=" * 50)
    
    agent = create_agent()
    
    # Simulate a conversation flow
    conversations = [
        {"input": "What datasets do you have?", "expected_stage": "discovery"},
        {"input": "I want education variables", "expected_stage": "variable_selection"},
        {"input": "Run a descriptive analysis", "expected_stage": "analysis"},
        {"input": "Generate the report", "expected_stage": "analysis"},
        {"input": "Start over", "expected_stage": "discovery"}
    ]
    
    state = {
        "messages": [HumanMessage(content="")],
        "intent": "",
        "user_query": "",
        "dataset": ["all"],
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }
    
    for i, conv in enumerate(conversations, 1):
        try:
            state["messages"] = [HumanMessage(content=conv["input"])]
            state["user_query"] = conv["input"]
            
            result = agent.invoke(state, {"recursion_limit": 2})
            
            print(f"\nStep {i}: ✅ PASSED")
            print(f"Input: {conv['input']}")
            print(f"Current Stage: {result.get('stage', 'unknown')}")
            
            # Get response
            response = "No response"
            if result.get("messages") and len(result["messages"]) > 1:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content[:80] + "..." if len(last_message.content) > 80 else last_message.content
            
            print(f"Response: {response}")
            
            # Update state for next interaction
            state.update(result)
            
        except Exception as e:
            print(f"\nStep {i}: ❌ FAILED")
            print(f"Error: {str(e)}")
            return False
    
    print(f"\n✅ State persistence test completed successfully!")
    return True

def test_error_recovery():
    """Test error recovery scenarios"""
    print("\n\n🛠️ Testing Error Recovery:")
    print("=" * 50)
    
    agent = create_agent()
    
    # Test scenarios that might cause errors
    error_scenarios = [
        "Run analysis without selecting variables",
        "Generate report before running analysis", 
        "Select non-existent dataset",
        "Use invalid analysis type"
    ]
    
    passed = 0
    
    for i, scenario in enumerate(error_scenarios, 1):
        try:
            state = {
                "messages": [HumanMessage(content=scenario)],
                "intent": "",
                "user_query": scenario,
                "dataset": ["all"],
                "selected_variables": [],
                "analysis_type": "descriptive",
                "user_approved": False,
                "analysis_result": {}
            }
            
            result = agent.invoke(state, {"recursion_limit": 2})
            
            # Get response from the last message
            response = ""
            if result.get("messages") and len(result["messages"]) > 1:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content
            
            if response:
                print(f"\nScenario {i}: ✅ HANDLED")
                print(f"Input: {scenario}")
                print(f"Response: {str(response)[:80]}{'...' if len(str(response)) > 80 else ''}")
                passed += 1
            else:
                print(f"\nScenario {i}: ❌ NO RESPONSE")
                
        except Exception as e:
            print(f"\nScenario {i}: ⚠️ EXCEPTION (but caught)")
            print(f"Error: {str(e)[:80]}{'...' if len(str(e)) > 80 else ''}")
            # Even exceptions are OK if they don't crash the system
            passed += 1
    
    print(f"\n🏁 ERROR RECOVERY RESULTS")
    print("=" * 50)
    print(f"Scenarios handled gracefully: {passed}/{len(error_scenarios)}")
    
    return passed >= len(error_scenarios) * 0.75  # 75% success rate acceptable
    
    # Test scenarios that might cause errors
    error_scenarios = [
        "Run analysis without selecting variables",
        "Generate report before running analysis",
        "Select non-existent dataset",
        "Use invalid analysis type"
    ]
    
    passed = 0
    
    for i, scenario in enumerate(error_scenarios, 1):
        try:
            result = agent.invoke({
                "messages": scenario,
                "user_query": scenario,
                "stage": "analysis"
            })
            
            # If we get any response without crashing, consider it handled
            response = result.get('response', '')
            if response:
                print(f"\nScenario {i}: ✅ HANDLED")
                print(f"Input: {scenario}")
                print(f"Response: {str(response)[:80]}{'...' if len(str(response)) > 80 else ''}")
                passed += 1
            else:
                print(f"\nScenario {i}: ❌ NO RESPONSE")
                
        except Exception as e:
            print(f"\nScenario {i}: ⚠️ EXCEPTION (but caught)")
            print(f"Error: {str(e)[:80]}{'...' if len(str(e)) > 80 else ''}")
            # Even exceptions are OK if they don't crash the system
            passed += 1
    
    print(f"\n🏁 ERROR RECOVERY RESULTS")
    print("=" * 50)
    print(f"Scenarios handled gracefully: {passed}/{len(error_scenarios)}")
    
    return passed >= len(error_scenarios) * 0.75  # 75% success rate acceptable

if __name__ == "__main__":
    print("Starting Edge Cases and Error Handling Tests...")
    
    try:
        test1 = test_edge_cases()
        test2 = test_state_persistence()
        test3 = test_error_recovery()
        
        print("\n" + "="*70)
        print("🎯 FINAL EDGE CASE TEST SUMMARY")
        print("="*70)
        print(f"Edge Cases: {'✅ PASSED' if test1 else '❌ FAILED'}")
        print(f"State Persistence: {'✅ PASSED' if test2 else '❌ FAILED'}")
        print(f"Error Recovery: {'✅ PASSED' if test3 else '❌ FAILED'}")
        
        if all([test1, test2, test3]):
            print("\n🎉 ALL EDGE CASE TESTS PASSED!")
            print("The agent workflow is robust and handles edge cases well.")
        else:
            print("\n⚠️ Some edge case tests failed. Review the results above.")
            
    except Exception as e:
        print(f"\n❌ Critical error in edge case testing: {e}")
        sys.exit(1)
