#!/usr/bin/env python3
"""
Comprehensive test for the three-stage agent workflow
"""

from agent import create_agent
from langchain_core.messages import HumanMessage

def test_full_three_stage_flow():
    """Test the complete three-stage workflow with proper progression"""
    
    print("=" * 70)
    print("TESTING COMPREHENSIVE THREE-STAGE WORKFLOW")
    print("=" * 70)
    
    # Create the agent without persistence to maintain existing test compatibility
    agent = create_agent(enable_persistence=False)
    
    # Define a complete workflow sequence
    workflow_stages = [
        {
            "stage": "Stage 1: Discovery",
            "tests": [
                {
                    "name": "General Project Question",
                    "message": "What is this project about?",
                    "expected_intent": "answer_general_questions"
                },
                {
                    "name": "Available Datasets", 
                    "message": "What datasets are available?",
                    "expected_intent": "answer_general_questions"
                },
                {
                    "name": "Agent Capabilities",
                    "message": "What can you do?", 
                    "expected_intent": "continue_conversation"
                }
            ]
        },
        {
            "stage": "Stage 2: Variable Selection & Dataset Querying",
            "tests": [
                {
                    "name": "Query Education Variables",
                    "message": "I want to analyze variables about education in Mexico",
                    "expected_intent": "query_variable_database"
                },
                {
                    "name": "Query Political Variables", 
                    "message": "Show me variables related to political participation",
                    "expected_intent": "query_variable_database"
                },
                {
                    "name": "Variable Review Request",
                    "message": "I want to modify the variable selection",
                    "expected_intent": "review_variable_selection"
                }
            ]
        },
        {
            "stage": "Stage 3: Analysis Configuration & Execution",
            "tests": [
                {
                    "name": "Select Analysis Type - Descriptive",
                    "message": "I want a simple descriptive analysis", 
                    "expected_intent": "select_analysis_type"
                },
                {
                    "name": "Select Analysis Type - Detailed",
                    "message": "I want a detailed complex analysis",
                    "expected_intent": "select_analysis_type"
                },
                {
                    "name": "Run Analysis",
                    "message": "Run the analysis now",
                    "expected_intent": "confirm_and_run"
                },
                {
                    "name": "Generate Report",
                    "message": "Create the analysis report",
                    "expected_intent": "confirm_and_run"
                }
            ]
        },
        {
            "stage": "Conversation Management",
            "tests": [
                {
                    "name": "Reset Conversation",
                    "message": "Start over from the beginning",
                    "expected_intent": "reset_conversation"
                },
                {
                    "name": "End Conversation",
                    "message": "Goodbye, thank you",
                    "expected_intent": "end_conversation"
                }
            ]
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for stage_info in workflow_stages:
        print(f"\n🔄 {stage_info['stage']}")
        print("=" * 50)
        
        for test in stage_info['tests']:
            total_tests += 1
            print(f"\nTest: {test['name']}")
            print(f"Input: '{test['message']}'")
            print(f"Expected Intent: {test['expected_intent']}")
            
            # Initialize fresh state for each test
            state = {
                "messages": [HumanMessage(content=test["message"])],
                "intent": "",
                "user_query": "",
                "dataset": ["all"],
                "selected_variables": [],
                "analysis_type": "descriptive",
                "user_approved": False,
                "analysis_result": {}
            }
            
            try:
                # Run the agent
                result = agent.invoke(state, {"recursion_limit": 3})
                
                detected_intent = result.get('intent', 'unknown')
                intent_match = detected_intent == test['expected_intent']
                
                print(f"Detected Intent: {detected_intent}")
                print(f"Intent Match: {'✅' if intent_match else '❌'}")
                
                if intent_match:
                    passed_tests += 1
                
                # Show response summary
                if result.get("messages") and len(result["messages"]) > 1:
                    last_message = result["messages"][-1]
                    if hasattr(last_message, 'content'):
                        response_preview = last_message.content[:80] + "..." if len(last_message.content) > 80 else last_message.content
                        print(f"Response: {response_preview}")
                
                # Show state changes for relevant tests
                if detected_intent == "query_variable_database":
                    selected_vars = result.get('selected_variables', [])
                    datasets = result.get('dataset', [])
                    if selected_vars:
                        print(f"Variables Selected: {len(selected_vars)} variables")
                    if datasets and datasets != ["all"]:
                        print(f"Datasets: {', '.join(datasets)}")
                
                print("Status: ✅ PASSED" if intent_match else "Status: ❌ FAILED")
                
            except Exception as e:
                print(f"Status: ❌ ERROR - {str(e)}")
            
            print("-" * 40)
    
    # Final summary
    print(f"\n🏁 FINAL RESULTS")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {100 * passed_tests / total_tests:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Three-stage workflow is working correctly.")
    elif passed_tests >= total_tests * 0.8:
        print(f"\n✅ MOSTLY WORKING! {passed_tests}/{total_tests} tests passed.")
    else:
        print(f"\n⚠️  NEEDS IMPROVEMENT. Only {passed_tests}/{total_tests} tests passed.")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_full_three_stage_flow()
