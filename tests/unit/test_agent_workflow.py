#!/usr/bin/env python3
"""
Test script for the three-stage agent workflow to validate intent classification and state management.
"""

from agent import create_agent
from langchain_core.messages import HumanMessage

def test_three_stage_flow():
    """Test the three-stage workflow: Query -> Analysis Selection -> Execution"""
    
    print("=" * 60)
    print("TESTING THREE-STAGE AGENT WORKFLOW")
    print("=" * 60)
    
    # Create the agent
    agent = create_agent()
    
    # Test messages for each stage
    test_scenarios = [
        {
            "name": "Stage 1: Query Variable Database",
            "message": "I want to analyze variables related to political participation in Mexico",
            "expected_intent": "query_variable_database"
        },
        {
            "name": "Stage 2: Approve Variables",
            "message": "Yes, these variables look good, proceed",
            "expected_intent": "review_variable_selection"
        },
        {
            "name": "Stage 3a: Select Analysis Type", 
            "message": "I want a detailed analysis",
            "expected_intent": "select_analysis_type"
        },
        {
            "name": "Stage 3b: Confirm and Run",
            "message": "Run the analysis now",
            "expected_intent": "confirm_and_run"
        },
        {
            "name": "General Questions",
            "message": "What datasets are available?",
            "expected_intent": "answer_general_questions"
        },
        {
            "name": "Conversation Management",
            "message": "What can you do?",
            "expected_intent": "continue_conversation"
        }
    ]
    
    # Initialize state
    state = {
        "messages": [],
        "intent": "",
        "user_query": "",
        "dataset": ["all"],
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }
    
    print("\nTesting Intent Classification:\n")
    
    for scenario in test_scenarios:
        print(f"Testing: {scenario['name']}")
        print(f"Input: '{scenario['message']}'")
        
        # Add user message
        test_state = state.copy()
        test_state["messages"] = [HumanMessage(content=scenario["message"])]
        
        try:
            # Run one step of the agent
            result = agent.invoke(test_state)
            
            detected_intent = result.get("intent", "unknown")
            print(f"Detected Intent: {detected_intent}")
            print(f"Expected Intent: {scenario['expected_intent']}")
            
            # Check if the intent was classified correctly
            intent_match = detected_intent == scenario['expected_intent']
            print(f"✓ Intent Match: {intent_match}")
            
            # Show last AI response if available
            if result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    print(f"AI Response: {last_message.content[:100]}{'...' if len(last_message.content) > 100 else ''}")
            
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("-" * 40)
    
    print("\nTesting Complete Three-Stage Flow:\n")
    
    # Test a complete flow
    flow_messages = [
        "I want to analyze variables about education in Mexico",
        "Yes, proceed with these variables", 
        "I want a detailed analysis",
        "Run the analysis now"
    ]
    
    flow_state = {
        "messages": [],
        "intent": "",
        "user_query": "",
        "dataset": ["all"],
        "selected_variables": [],
        "analysis_type": "descriptive", 
        "user_approved": False,
        "analysis_result": {}
    }
    
    for i, message in enumerate(flow_messages, 1):
        print(f"Step {i}: '{message}'")
        
        # Add user message
        flow_state["messages"].append(HumanMessage(content=message))
        
        try:
            # Run agent step
            flow_state = agent.invoke(flow_state)
            
            print(f"  Intent: {flow_state.get('intent', 'unknown')}")
            print(f"  User Approved: {flow_state.get('user_approved', False)}")
            print(f"  Analysis Type: {flow_state.get('analysis_type', 'none')}")
            print(f"  Variables Selected: {len(flow_state.get('selected_variables', []))}")
            
            # Show AI response
            if flow_state["messages"]:
                last_message = flow_state["messages"][-1]
                if hasattr(last_message, 'content') and hasattr(last_message, '__class__'):
                    if 'AI' in last_message.__class__.__name__:
                        print(f"  AI: {last_message.content[:100]}{'...' if len(last_message.content) > 100 else ''}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            print()
    
    print("=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_three_stage_flow()
