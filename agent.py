from typing import Dict, List, Any, Annotated, TypedDict, Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from dataset_knowledge import rev_topic_dict,  tmp_topic_st, _project_describer
from intent_classifier import _classify_intent, intent_dict
from variable_selector import _variable_selector, _database_selector
from run_analysis import execute_analysis


# LLM settings
mod_alto = 'gpt-4.1-2025-04-14' 
mod_bajo = 'gpt-4.1-nano-2025-04-14'
mod_med = 'gpt-4.1-mini-2025-04-14'


# Define state schema
class AgentState(TypedDict):
    messages: Annotated[List[Any], "The chat history"]
    intent: Annotated[str, "The classified intent of the user"]
    user_query: Annotated[str, "The user's current query or question for the data"]
    dataset: Annotated[List[str], "The dataset or group of datasets selected for analysis; defaults to 'ALL'"] 
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
        "user_query": "",  
        "dataset": ["all"], 
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }


    ## Opciones: describe datasets, query datasets, or general questions
    def detect_intent(state: AgentState) -> AgentState:
        """
        Intent classifier: INTENT --> ACTIONS AVAILABLE
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        intent = _classify_intent(last_message, intent_dict, llm)

        # agregar último mensaje si el identificador lo detectó como pregunta
        
        if intent == "query_variable_database":
            state["user_query"] = last_message

        if intent == "end_conversation":
            state["messages"].append(AIMessage(content="Goodbye!"))
            return END
        
        return {
            **state,
            "intent": intent,
        }
    
    # Describe dataset handler
    def describe_project(state: AgentState) -> AgentState:
        """Handle requests to describe the project or datasets"""

        messages = state["messages"]
        last_user_message = next((msg.content for msg in reversed(messages)
                              if isinstance(msg, HumanMessage)), "")
        # response = project_describer(last_user_message, tmp_data_describer_st="", llm=llm)
        response = _project_describer(last_user_message,  tmp_data_describer_st="", llm=llm)  # Assuming tmp_data_describer_st is handled inside
        state["messages"].append(AIMessage(content=response))
        
        return state
    
    # Select dataset handler
    def select_dataset(state: AgentState) -> AgentState:
        """Select a dataset based on user request"""
        messages = state["messages"]
        dataset = state["dataset"]      

        last_user_message = next((msg.content for msg in reversed(messages) 
                              if isinstance(msg, HumanMessage)), "")
        
        response = _database_selector(last_user_message, '', llm)

        if response != []:
            state["dataset"] = response[0]
        
        state["messages"].append(AIMessage(content=response))

        return state
        

    # Select variables for query
    def handle_query(state: AgentState) -> AgentState:
        """Handle dataset query requests by selecting relevant variables"""
        messages = state["messages"]
        last_user_message = next((msg.content for msg in reversed(messages) 
                              if isinstance(msg, HumanMessage)), "")
        
        topic_ids, _, tmp_grade_dict = _variable_selector(last_user_message, tmp_topic_st, mod_alto, top_vals=30)

        selected_vars = list(tmp_grade_dict.keys())

        response = (f"Based on your query, I've selected these dataset IDs:"
                   f"{', '.join(topic_ids)}\n\n"
                   f"And these variables:\n"
                   f"{', '.join(selected_vars)}\n\n"
                   )
        
        state["messages"].append(AIMessage(content=response))
        state["selected_variables"] = selected_vars
        state["dataset"] = topic_ids
        
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
    workflow.add_node("describe_dataset", describe_project)
    workflow.add_node("select_dataset", select_dataset)

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
