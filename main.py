from typing import Dict, List, Any
from langchain_core.messages import HumanMessage, AIMessage
from agent import create_agent

def main():
    """Entry point for the dataset agent application"""
    agent = create_agent()
    
    print("Welcome to the Dataset Agent! Type 'exit' to quit.")
    print("You can ask about datasets, request queries, or run analyses.")
    
    chat_history = []
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        # Add user message to history
        chat_history.append(HumanMessage(content=user_input))
        
        # Get response from agent
        result = agent.invoke({"messages": chat_history})
        response = result["messages"][-1].content
        
        # Add agent response to history
        chat_history.append(AIMessage(content=response))
        
        print(f"\nAgent: {response}")

if __name__ == "__main__":
    main()
