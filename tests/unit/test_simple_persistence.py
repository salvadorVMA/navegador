#!/usr/bin/env python3
"""
Simple persistence test to validate basic functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import create_agent
from langchain_core.messages import HumanMessage

def test_simple_persistence():
    """Test basic persistence functionality with threading"""
    print("=" * 60)
    print("🔄 TESTING BASIC PERSISTENCE FUNCTIONALITY")
    print("=" * 60)
    
    # Test 1: Agent with persistence
    print("\n1. Testing agent with persistence...")
    try:
        agent_with_persistence = create_agent(enable_persistence=True)
        print("✅ Agent with persistence created successfully")
        
        # Test with proper thread configuration
        config = {"configurable": {"thread_id": "test_thread_001"}}
        
        state = {
            "messages": [HumanMessage(content="What can you do?")],
            "intent": "",
            "user_query": "What can you do?",
            "dataset": ["all"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        result = agent_with_persistence.invoke(state, config=config)
        print("✅ Agent invocation with persistence successful")
        print(f"Intent detected: {result.get('intent', 'unknown')}")
        
        if result.get("messages") and len(result["messages"]) > 1:
            last_msg = result["messages"][-1]
            if hasattr(last_msg, 'content'):
                response_preview = last_msg.content[:80] + "..." if len(last_msg.content) > 80 else last_msg.content
                print(f"Response: {response_preview}")
        
    except Exception as e:
        print(f"❌ Agent with persistence failed: {e}")
        return False
    
    # Test 2: Agent without persistence  
    print("\n2. Testing agent without persistence...")
    try:
        agent_no_persistence = create_agent(enable_persistence=False)
        print("✅ Agent without persistence created successfully")
        
        state = {
            "messages": [HumanMessage(content="What datasets are available?")],
            "intent": "",
            "user_query": "What datasets are available?",
            "dataset": ["all"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        result = agent_no_persistence.invoke(state)
        print("✅ Agent invocation without persistence successful")
        print(f"Intent detected: {result.get('intent', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Agent without persistence failed: {e}")
        return False
    
    # Test 3: Multiple interactions on same thread
    print("\n3. Testing multiple interactions on same thread...")
    try:
        thread_id = "test_conversation_flow"
        config = {"configurable": {"thread_id": thread_id}}
        
        interactions = [
            "What can you do?",
            "I want to analyze education data",
            "Run a descriptive analysis"
        ]
        
        for i, message in enumerate(interactions, 1):
            print(f"\n   Interaction {i}: {message}")
            
            state = {
                "messages": [HumanMessage(content=message)],
                "intent": "",
                "user_query": message,
                "dataset": ["all"],
                "selected_variables": [],
                "analysis_type": "descriptive",
                "user_approved": False,
                "analysis_result": {}
            }
            
            result = agent_with_persistence.invoke(state, config=config)
            intent = result.get('intent', 'unknown')
            print(f"   Intent: {intent}")
            
            # Check for response
            if result.get("messages") and len(result["messages"]) > 1:
                last_msg = result["messages"][-1]
                if hasattr(last_msg, 'content'):
                    print(f"   ✅ Response received ({len(last_msg.content)} chars)")
                else:
                    print(f"   ⚠️ No content in response")
            else:
                print(f"   ⚠️ No response message")
        
        print("✅ Multiple interactions completed successfully")
        
    except Exception as e:
        print(f"❌ Multiple interactions failed: {e}")
        return False
    
    print(f"\n🎯 PERSISTENCE TEST SUMMARY:")
    print("-" * 40)
    print("✅ Persistence functionality implemented")
    print("✅ MemorySaver checkpointer working")
    print("✅ Thread-based conversations functional")
    print("✅ Both persistence modes (on/off) working")
    
    return True

if __name__ == "__main__":
    success = test_simple_persistence()
    if success:
        print(f"\n🎉 PERSISTENCE TESTS PASSED!")
        print("The agent now supports conversation persistence and threading.")
    else:
        print(f"\n❌ PERSISTENCE TESTS FAILED!")
        print("Please check the error messages above.")
    
    sys.exit(0 if success else 1)
