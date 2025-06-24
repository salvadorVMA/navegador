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

        # Store user query for query-related intents
        if intent in ["query_variable_database", "review_variable_selection"]:
            state["user_query"] += last_message

        print(f"Detected intent: {intent}")
        
        return {
            **state,
            "intent": intent,
        }
    
    # Describe dataset handler
    def describe_project(state: AgentState) -> AgentState:
        """Handle requests to describe the project or datasets"""
        messages = state["messages"]
        last_user_message = ""
        
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                content = msg.content
                if isinstance(content, str):
                    last_user_message = content
                break
                
        response = _project_describer(last_user_message, tmp_data_describer_st="", llm=llm)
        state["messages"].append(AIMessage(content=response))
        
        return state
    
    # Select dataset handler
    def select_dataset(state: AgentState) -> AgentState:
        """Select a dataset based on user request"""
        messages = state["messages"]
        
        last_user_message = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                content = msg.content
                if isinstance(content, str):
                    last_user_message = content
                break
        
        response = _database_selector(last_user_message, '', llm)

        if isinstance(response, list) and response:
            state["dataset"] = response
            response_text = f"Selected datasets: {', '.join(response)}"
        else:
            response_text = "No datasets found matching your request."
        
        state["messages"].append(AIMessage(content=response_text))
        return state
        

    # Select variables for query
    def handle_query(state: AgentState) -> AgentState:
        """Handle dataset query requests by selecting relevant variables"""
        messages = state["messages"]
        
        last_user_message = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                content = msg.content
                if isinstance(content, str):
                    last_user_message = content
                break
        
        topic_ids, _, tmp_grade_dict = _variable_selector(last_user_message, tmp_topic_st, mod_alto, top_vals=30)

        selected_vars = list(tmp_grade_dict.keys())

        response = (f"Based on your query, I've selected these dataset IDs:"
                   f"{', '.join(topic_ids)}\n\n"
                   f"And these variables:\n"
                   f"{', '.join(selected_vars)}\n\n"
                   f"Would you like to proceed with these variables or modify the selection?"
                   )
        
        state["messages"].append(AIMessage(content=response))
        state["selected_variables"] = selected_vars
        state["dataset"] = topic_ids
        
        return state
    
    # Handle user approval
    def process_approval(state: AgentState) -> AgentState:
        """Process user approval or modification of variables"""
        messages = state["messages"]
        
        last_user_message = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                content = msg.content
                if isinstance(content, str):
                    last_user_message = content
                break
        
        # Check if user approves variable selection
        approved = any(keyword in last_user_message.lower() 
                      for keyword in ["yes", "approve", "good", "ok", "correct", "proceed", "sí", "aprobar", "bien", "ok", "correcto"])
        
        if approved:
            response = "Variables approved. What type of analysis would you like? (descriptive or detailed)"
            state["user_approved"] = True
            state["messages"].append(AIMessage(content=response))
            return state
        else:
            # Parse requested changes
            response = "Please specify which variables you'd like to add or remove."
            state["messages"].append(AIMessage(content=response))
            return state
    
    # Handle analysis type selection
    def select_analysis_type(state: AgentState) -> AgentState:
        """Handle analysis type selection"""
        messages = state["messages"]
        
        last_user_message = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                content = msg.content
                if isinstance(content, str):
                    last_user_message = content
                break
        
        if "detailed" in last_user_message.lower() or "complex" in last_user_message.lower():
            state["analysis_type"] = "detailed"
            response = "Detailed analysis selected. Ready to run analysis?"
        else:
            state["analysis_type"] = "descriptive"
            response = "Descriptive analysis selected. Ready to run analysis?"
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    # Run analysis
    def run_analysis(state: AgentState) -> AgentState:
        """Execute analysis with approved variables"""
        dataset = state["dataset"]
        variables = state["selected_variables"]
        
        # Use the first dataset if multiple are selected
        dataset_name = dataset[0] if dataset else "all"
        
        try:
            results = execute_analysis(dataset_name, variables)
            response = f"Analysis complete on {dataset_name} using variables: {', '.join(variables)}.\n\nResults:\n{results}"
        except Exception as e:
            results = {"error": str(e)}
            response = f"Analysis failed: {str(e)}"
        
        state["messages"].append(AIMessage(content=response))
        state["analysis_result"] = results
        
        return state
    
    # General questions handler
    def answer_general(state: AgentState) -> AgentState:
        """Answer general questions about datasets"""
        messages = state["messages"]
        last_message_content = ""
        
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'content') and isinstance(last_msg.content, str):
                last_message_content = last_msg.content
        
        if "list" in last_message_content.lower() and "dataset" in last_message_content.lower():
            # Get available datasets from rev_topic_dict -- TODO: IMPORTARLO DE dataset_knowledge.py
            if 'rev_topic_dict' in globals():
                available_datasets = list(rev_topic_dict.keys())
            else:
                available_datasets = ["No datasets available"]
            response = f"Here are the available datasets:\n\n{', '.join(available_datasets)}"
        else:
            response = ("I can help with dataset information, querying datasets, "
                      "and running analyses. What would you like to know?")
            
        state["messages"].append(AIMessage(content=response))
        return state
    
    # Handle conversation management
    def handle_conversation(state: AgentState) -> AgentState:
        """Handle conversation management requests"""
        intent = state["intent"]
        
        if intent == "continue_conversation":
            response = (
                "I can help you with the following:\n"
                "- Ask general questions about datasets and methodology\n"
                "- Query specific variables in the database\n"
                "- Review and modify variable selections\n"
                "- Select analysis types (descriptive or detailed)\n"
                "- Run analyses and generate reports\n"
                "- Reset or end the conversation\n\n"
                "What would you like to do?"
            )
        elif intent == "reset_conversation":
            # Reset state to initial values
            state["user_query"] = ""
            state["dataset"] = ["all"]
            state["selected_variables"] = []
            state["analysis_type"] = "descriptive"
            state["user_approved"] = False
            state["analysis_result"] = {}
            response = "Conversation reset. How can I help you?"
        else:  # end_conversation
            response = "Thank you for using the dataset analysis assistant. Goodbye!"
            
        state["messages"].append(AIMessage(content=response))
        return state
    
    # Define routing functions
    def route_intent(state: AgentState) -> str:
        """Route based on detected intent"""
        intent = state["intent"]
        # TODO: detectar idioma de usuario, fijarlo como state de la conersación y adaptar textos predefinidos para ambos idiomas
        # Map intents to node names
        intent_routing = {
            "answer_general_questions": "answer_general",
            "continue_conversation": "handle_conversation", 
            "query_variable_database": "handle_query",
            "review_variable_selection": "handle_query",
            "select_analysis_type": "select_analysis_type",
            "confirm_and_run": "run_analysis",
            "reset_conversation": "handle_conversation",
            "end_conversation": "handle_conversation"
        }
        
        return intent_routing.get(intent, "answer_general")
    
    def route_approval(state: AgentState) -> str:
        """Route based on user approval status"""
        if state.get("user_approved", False):
            return "select_analysis_type"
        else:
            return "handle_query"
    
    def route_analysis_ready(state: AgentState) -> str:
        """Route when analysis is ready to run"""
        intent = state["intent"]
        if intent == "confirm_and_run":
            return "run_analysis"
        else:
            return "detect_intent"

    # Define the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("describe_project", describe_project)
    workflow.add_node("select_dataset", select_dataset)
    workflow.add_node("handle_query", handle_query)
    workflow.add_node("process_approval", process_approval)
    workflow.add_node("select_analysis_type", select_analysis_type)
    workflow.add_node("run_analysis", run_analysis)
    workflow.add_node("answer_general", answer_general)
    workflow.add_node("handle_conversation", handle_conversation)
    
    # Set entry point
    workflow.set_entry_point("detect_intent")
    
    # Define conditional edges from intent detection
    workflow.add_conditional_edges(
        "detect_intent",
        route_intent,
        {
            "answer_general": "answer_general",
            "handle_conversation": "handle_conversation",
            "handle_query": "handle_query", 
            "select_analysis_type": "select_analysis_type",
            "run_analysis": "run_analysis"
        }
    )
    
    # Standard edges back to intent detection for conversation flow
    workflow.add_edge("answer_general", "detect_intent")
    workflow.add_edge("handle_conversation", "detect_intent")
    
    # Query flow edges
    workflow.add_edge("handle_query", "process_approval")
    workflow.add_conditional_edges(
        "process_approval",
        route_approval,
        {
            "select_analysis_type": "select_analysis_type",
            "handle_query": "handle_query"
        }
    )
    
    # Analysis flow edges
    workflow.add_edge("select_analysis_type", "detect_intent")
    workflow.add_edge("run_analysis", "detect_intent")
    
    # Compile the graph
    agent = workflow.compile()
    
    return agent
