from typing import Dict, List, Any, Annotated, TypedDict, Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from dataset_knowledge import get_dataset_info, list_datasets
from intent_classifier import classify_intent
from variable_selector import select_variables
from run_analysis import execute_analysis

# Define state schema
class AgentState(TypedDict):
    messages: Annotated[List[Any], "The chat history"]
    intent: Annotated[str, "The classified intent of the user"]
    dataset: Annotated[str, "The dataset or group of datasets being discussed"] # todas las encuestas o sólo una en particular
    selected_variables: Annotated[List[str], "Selected variables for analysis"]
    analysis_type: Annotated[Literal["descriptive", "detailed"], "Type of analysis requested by user"]
    user_approved: Annotated[bool, "Whether user has approved variables and analysis type"]
    analysis_result: Annotated[Dict, "Results from the analysis"]

def create_agent():
    """Creates and returns the dataset agent with the defined workflow"""
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o")
    
    # Define agent states/nodes
    initial_state: AgentState = {
        "messages": [],
        "intent": "",
        "dataset": "",  # This can be a specific dataset or a group of datasets
        "selected_variables": [],
        "analysis_type": "descriptive",  # Default analysis type
        "user_approved": False,
        "analysis_result": {}
    }


    ## Opciones: describe datasets, query datasets, or general questions
    def detect_intent(state: AgentState) -> AgentState:
        """
        Intent classifier: INTENT --> ACTIONS AVAILABLE:
      1) ANSWER GENERAL QUESTIONS ABOUT THE PROJECT AND DATASETS,
      2) QUERY VARIABLE DATABASE,
      3) REFINE VARIABLE SELECTION -IF USER REQUESTS IT-, 
      4) REFINE DATASET SELECTION -IF USER REQUESTS IT-,
      5) SELECT ANALYSIS TYPE -DESCRIPTIVE OR DETAILED, IF USER REQUESTS IT-,
      6) CONFIRM DATASET, VARIABLES AND ANALYSIS TYPE,
      7) RUN ANALYSIS,
      8) RETURN RESULTS -CURRENTLY IN PDF ONLY-,
      9) END CONVERSATION.
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        intent, dataset = classify_intent(last_message, llm)
        
        return {
            **state,
            "intent": intent,
            #"dataset": dataset # TODO: all datasets or just a subset
        }
    
    # # Describe dataset handler
    # def describe_dataset(state: AgentState) -> AgentState:
    #     """Handle requests to describe datasets"""
    #     dataset = state["dataset"]
    #     dataset_info = get_dataset_info(dataset)
        
    #     response = f"Here's information about the {dataset} dataset:\n\n{dataset_info}"
    #     state["messages"].append(AIMessage(content=response))
        
    #     return state
    
    # Select variables for query
    def handle_query(state: AgentState) -> AgentState:
        """Handle dataset query requests by selecting relevant variables"""
        messages = state["messages"]
        last_user_message = next((msg.content for msg in reversed(messages) 
                              if isinstance(msg, HumanMessage)), "")
        
        ## TODO: get dataset from message describe which to use (single , selection, or all)
        #dataset = state["dataset"]
        
        selected_vars = select_variables(last_user_message, dataset, llm)
        
        response = (f"Based on your query about {dataset}, I've selected these variables:\n"
                   f"{', '.join(selected_vars)}\n\n"
                   f"Would you like to approve these variables or modify the selection?")
        
        state["messages"].append(AIMessage(content=response))
        state["selected_variables"] = selected_vars
        
        return state
    
    # Handle user approval
    def process_approval(state: AgentState) -> Dict:
        """Process user approval or modification of variables"""
        messages = state["messages"]
        last_user_message = next((msg.content for msg in reversed(messages) 
                              if isinstance(msg, HumanMessage)), "")
        
        # Check if user approves variable selection
        approved = any(keyword in last_user_message.lower() 
                      for keyword in ["yes", "approve", "good", "ok", "correct"])
        
        if approved:
            response = "Variables approved. Running analysis..."
            state["user_approved"] = True
            state["messages"].append(AIMessage(content=response))
            return state
        else:
            # Parse requested changes
            response = "Please specify which variables you'd like to add or remove."
            state["messages"].append(AIMessage(content=response))
            return state
    
    # Run analysis
    def run_analysis(state: AgentState) -> Dict:
        """Execute analysis with approved variables"""
        dataset = state["dataset"]
        variables = state["selected_variables"]
        
        results = execute_analysis(dataset, variables)
        
        response = f"Analysis complete on {dataset} using variables: {', '.join(variables)}.\n\nResults:\n{results}"
        state["messages"].append(AIMessage(content=response))
        state["analysis_result"] = results
        
        return state
    
    # General questions handler
    def answer_general(state: AgentState) -> Dict:
        """Answer general questions about datasets"""
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        if "list" in last_message.lower() and "dataset" in last_message.lower():
            datasets = list_datasets()
            response = f"Here are the available datasets:\n\n{datasets}"
        else:
            response = ("I can help with dataset information, querying datasets, "
                      "and running analyses. What would you like to know?")
            
        state["messages"].append(AIMessage(content=response))
        return state
    
    # Define the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("describe_dataset", describe_dataset)
    workflow.add_node("handle_query", handle_query)
    workflow.add_node("process_approval", process_approval)
    workflow.add_node("run_analysis", run_analysis)
    workflow.add_node("answer_general", answer_general)
    
    # Set entry point
    workflow.set_entry_point("detect_intent")
    
    # Define edges
    workflow.add_edge("detect_intent", "describe_dataset", 
                    condition=lambda state: state["intent"] == "describe")
    workflow.add_edge("detect_intent", "handle_query", 
                    condition=lambda state: state["intent"] == "query")
    workflow.add_edge("detect_intent", "answer_general", 
                    condition=lambda state: state["intent"] == "general")
    
    workflow.add_edge("describe_dataset", "detect_intent")
    workflow.add_edge("answer_general", "detect_intent")
    
    workflow.add_edge("handle_query", "process_approval")
    workflow.add_edge("process_approval", "run_analysis", 
                    condition=lambda state: state.get("user_approved", False))
    workflow.add_edge("process_approval", "handle_query", 
                    condition=lambda state: not state.get("user_approved", False))
    
    workflow.add_edge("run_analysis", "detect_intent")
    
    # Compile the graph
    agent = workflow.compile()
    
    return agent
