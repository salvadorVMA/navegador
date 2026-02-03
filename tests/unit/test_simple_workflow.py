#!/usr/bin/env python3
"""
Test script for the agent workflow with proper termination handling
"""

from agent import create_agent
from langchain_core.messages import HumanMessage

def test_single_step():
    """Test single step interactions to avoid infinite loops"""
    
    print("=" * 60)
    print("TESTING SINGLE-STEP AGENT INTERACTIONS")
    print("=" * 60)
    
    # Create the agent
    agent = create_agent()
    
    # Test simple cases
    test_cases = [
        {
            "name": "General Question",
            "message": "What datasets are available?",
        },
        {
            "name": "Query Variables",
            "message": "I want to analyze variables about education in Mexico",
        },
        {
            "name": "Conversation Management",
            "message": "What can you do?",
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"Input: '{test_case['message']}'")
        
        # Initialize state
        state = {
            "messages": [HumanMessage(content=test_case["message"])],
            "intent": "",
            "user_query": "",
            "dataset": ["all"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        try:
            # Run with limited recursion to prevent infinite loops
            result = agent.invoke(state, {"recursion_limit": 5})
            
            print(f"Final Intent: {result.get('intent', 'unknown')}")
            print(f"Messages Count: {len(result.get('messages', []))}")
            
            # Show last AI response if available
            if result.get("messages"):
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content') and hasattr(last_message, '__class__'):
                    if 'AI' in last_message.__class__.__name__:
                        print(f"AI Response: {last_message.content[:150]}{'...' if len(last_message.content) > 150 else ''}")
            
            print("✓ SUCCESS")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 60)
    
    print("Test completed!")

if __name__ == "__main__":
    test_single_step()
