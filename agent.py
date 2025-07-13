from typing import Dict, List, Any, Annotated, TypedDict, Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import sqlite3
import os
import time
from datetime import datetime

# Add LangSmith tracing imports
from langchain_core.tracers import LangChainTracer
import langchain_core.callbacks.manager as langchain_manager
try:
    # Import langsmith client
    from langsmith.client import Client as LangSmithClient
    from langsmith.schemas import Run as LangSmithRun
except ImportError:
    print("⚠️ LangSmith packages not found")
    LangSmithClient = None
    LangSmithRun = None

# Enable LangSmith tracing if API key is available
os.environ["LANGSMITH_TRACING"] = "true"

# Initialize tracing
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "navegador-debug")

# Initialize LangSmith client
langsmith_client = None
tracer = None

try:
    if LANGSMITH_API_KEY and LangSmithClient is not None:
        langsmith_client = LangSmithClient(api_key=LANGSMITH_API_KEY)
        tracer = LangChainTracer(project_name=LANGSMITH_PROJECT)
        # Enable tracing v2
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        print("✅ LangSmith monitoring initialized successfully")
    else:
        print("⚠️ LangSmith API key not found or package not installed, monitoring disabled")
except Exception as e:
    print(f"⚠️ Error initializing LangSmith: {e}")

from dataset_knowledge import rev_topic_dict,  tmp_topic_st, _project_describer
from intent_classifier import _classify_intent, intent_dict
from variable_selector import _variable_selector, _database_selector
from run_analysis import run_analysis as run_analysis_module


# LLM settings
mod_alto = 'gpt-4.1-2025-04-14' 
mod_bajo = 'gpt-4.1-nano-2025-04-14'
mod_med = 'gpt-4.1-mini-2025-04-14'

# Monitoring utilities
def log_agent_event(event_type, details, agent_state=None):
    """
    Logs agent events to console and LangSmith if available
    
    Args:
        event_type (str): Type of event (e.g., 'variable_search_start', 'query_received')
        details (dict): Event details
        agent_state (dict, optional): Current agent state
    """
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "details": details
    }
    
    # Add agent state if provided
    if agent_state:
        log_entry["agent_state"] = {k: v for k, v in agent_state.items() if k != "messages"}
    
    # Print to console with timestamp
    print(f"📝 [{timestamp}] {event_type}: {details}")
    
    # Log to LangSmith if available
    if langsmith_client:
        try:
            # Add feedback to LangSmith project
            metadata = {
                "event_type": event_type,
                "timestamp": timestamp,
                **{f"detail_{k}": str(v) for k, v in details.items()}
            }
            
            # Check if there's an active run ID in environment
            run_id = os.getenv("LANGCHAIN_RUN_ID", "")
            if run_id:
                # Use the API that's available in the current version
                langsmith_client.create_feedback(
                    run_id=run_id,
                    key=f"agent_event_{event_type}",
                    value=event_type,
                    comment=str(details),
                    metadata=metadata
                )
        except Exception as e:
            print(f"⚠️ Error logging to LangSmith: {e}")

# Define state schema
class AgentState(TypedDict):
    messages: Annotated[List[Any], "The chat history"]
    intent: Annotated[str, "The classified intent of the user"]
    user_query: Annotated[str, "The user's current query or question for the data"]
    original_query: Annotated[str, "The user's original query or request"]
    dataset: Annotated[List[str], "The dataset or group of datasets selected for analysis; defaults to 'ALL'"] 
    selected_variables: Annotated[List[str], "Selected variables for analysis"]
    analysis_type: Annotated[Literal["descriptive", "detailed", "quick_insights", "plots_only"], "Type of analysis requested by user"]
    user_approved: Annotated[bool, "Whether user has approved variables and analysis type"]
    analysis_result: Annotated[Dict, "Results from the analysis"]

def create_agent(enable_persistence=True):
    """
    Creates and returns the dataset agent with the defined workflow
    
    Args:
        enable_persistence (bool): Whether to enable conversation persistence using checkpointing
    
    Returns:
        Compiled LangGraph agent with optional persistence
    """
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o")
    
    # Initialize checkpointer for persistence if enabled
    checkpointer = None
    if enable_persistence:
        try:
            checkpointer = MemorySaver()
            print("✅ Persistence enabled: Using MemorySaver for conversation state")
        except Exception as e:
            print(f"⚠️ Failed to initialize persistence: {e}")
            print("📝 Continuing without persistence...")
    
    # Define agent states/nodes
    initial_state: AgentState = {
        "messages": [],
        "intent": "",
        "user_query": "",  
        "original_query": "",  # Store the original user query for analysis
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
        
        # Extract content from the last message safely
        last_message_content = ""
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, dict):
                last_message_content = last_msg.get("content", "")
            elif hasattr(last_msg, "content"):
                last_message_content = last_msg.content
            else:
                last_message_content = str(last_msg)
                
        intent = _classify_intent(last_message_content, intent_dict, llm)

        # Store user query for query-related intents
        if intent in ["query_variable_database", "review_variable_selection"]:
            state["user_query"] += last_message_content
            # Capture original query if not already set
            if not state.get("original_query"):
                state["original_query"] = last_message_content

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
            # Handle different message formats
            if isinstance(msg, dict):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            elif hasattr(msg, "type") and msg.type == "human":
                # Handle LangChain message objects
                if hasattr(msg, "content"):
                    last_user_message = msg.content
                    break
            elif isinstance(msg, HumanMessage):
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
        start_time = time.time()
        
        last_user_message = ""
        for msg in reversed(messages):
            # Handle different message formats
            if isinstance(msg, dict):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            elif hasattr(msg, "type") and msg.type == "human":
                # Handle LangChain message objects
                if hasattr(msg, "content"):
                    last_user_message = msg.content
                    break
            elif isinstance(msg, HumanMessage):
                content = msg.content
                if isinstance(content, str):
                    last_user_message = content
                break
        
        # Add error handling if no valid user message was found
        if not last_user_message:
            print("⚠️ Warning: Could not extract a valid user message")
            last_user_message = "Show general variables"

        # Log the start of variable selection
        log_agent_event(
            "query_received", 
            {
                "query": last_user_message,
                "event": "starting_variable_selection"
            }, 
            state
        )

        # Get access to required modules for proper variable selection
        try:
            from dataset_knowledge import tmp_topic_st
            from langchain_openai import ChatOpenAI
            
            print(f"🔍 Selecting variables for query: '{last_user_message}'")
            
            # Create LLM instance for variable selection
            selection_llm = ChatOpenAI(model="gpt-4o-mini")
            
            # Log selection start
            log_agent_event(
                "variable_selection_start", 
                {
                    "query": last_user_message,
                    "model": selection_llm.model_name
                }, 
                state
            )
            
            # Call the actual variable selection function
            topic_ids, variables_dict, grade_dict = _variable_selector(
                last_user_message, tmp_topic_st, selection_llm, use_simultaneous_retrieval=True
            )
            
            if variables_dict and grade_dict:
                # Get the top-graded variables
                sorted_vars = sorted(grade_dict.items(), key=lambda x: list(x[1].keys())[0], reverse=True)
                top_variables = [var_id for var_id, grade in sorted_vars[:10]]  # Top 10 most relevant variables
                
                # Collect dataset information
                if topic_ids:
                    dataset_ids = list(set([topic_id.split('|')[0] for topic_id in topic_ids]))
                else:
                    dataset_ids = ["ALL"]
                
                # Format response with variable descriptions
                variable_descriptions = []
                for var_id in top_variables:
                    if var_id in variables_dict:
                        var_info = variables_dict.get(f"{var_id}__question", "")
                        if var_info:
                            # Add just the first part of the variable description
                            variable_descriptions.append(f"- {var_info[:80]}...")
                
                # Store the variable information in the state
                selected_vars = top_variables
                state["selected_variables"] = selected_vars
                state["dataset"] = dataset_ids
                
                # Create the response message
                response = (f"Based on your query, I've selected the dataset: {', '.join(dataset_ids)}\n\n"
                           f"And these relevant variables:\n"
                           f"• {chr(10).join(variable_descriptions)}\n\n"
                           f"Would you like to proceed with these variables or modify the selection?"
                           )
            else:
                # Fallback when no variables found
                print("⚠️ No variables found for the query, using fallback")
                dataset_ids = ["ALL"]
                selected_vars = ["NA"]
                
                response = (f"I couldn't find specific variables for your query. Here are some general variables that might help:\n\n"
                           f"• {chr(10).join([f'- {var}' for var in selected_vars])}\n\n"
                           f"Would you like to proceed with these or try a more specific query?"
                           )
                           
        except Exception as e:
            # Fallback to mock response on error
            print(f"❌ Error in variable selection: {e}")
            import traceback
            traceback.print_exc()
            
            selected_vars = ["NA"]
            dataset_ids = ["NA"]
            
            response = (f"Based on your query, I've selected the dataset: {', '.join(dataset_ids)}\n\n"
                       f"And these relevant variables:\n"
                       f"• {chr(10).join([f'- {var}' for var in selected_vars])}\n\n"
                       f"Would you like to proceed with these variables or modify the selection?"
                       )
        
        # Calculate the time it took for variable selection
        elapsed_time = time.time() - start_time
        
        # Log the completion of variable selection
        log_agent_event(
            "variable_selection_complete", 
            {
                "elapsed_time_sec": round(elapsed_time, 2),
                "selected_variables_count": len(selected_vars),
                "datasets": dataset_ids
            }, 
            state
        )
        
        state["messages"].append(AIMessage(content=response))
        state["selected_variables"] = selected_vars
        state["dataset"] = dataset_ids
        
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
        
        last_lower = last_user_message.lower()
        
        if "plots only" in last_lower or "just plots" in last_lower or "only plots" in last_lower:
            state["analysis_type"] = "plots_only"
            response = "Plots-only analysis selected. I'll generate visualizations for your selected variables. Ready to run analysis?"
        elif "quick insights" in last_lower or "quick analysis" in last_lower or "summary" in last_lower:
            state["analysis_type"] = "quick_insights"
            response = "Quick insights analysis selected. I'll provide variable summaries with plots. Ready to run analysis?"
        elif "detailed" in last_lower or "complex" in last_lower or "deep analysis" in last_lower:
            state["analysis_type"] = "detailed"
            response = "Detailed analysis selected. I'll run the full multi-step analysis pipeline. Ready to run analysis?"
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
        user_query = state.get("original_query", "")
        analysis_type = state.get("analysis_type", "detailed")
        
        # Map agent analysis types to run_analysis module types
        analysis_type_mapping = {
            "detailed": "detailed_report",
            "descriptive": "detailed_report",  # Keep descriptive as detailed_report for now
            "quick_insights": "quick_insights",
            "plots_only": "plots_only"
        }
        
        mapped_analysis_type = analysis_type_mapping.get(analysis_type, "detailed_report")
        
        # Use the first dataset if multiple are selected
        dataset_name = dataset[0] if dataset else "all"
        
        try:
            # Use the new analysis system
            results = run_analysis_module(
                analysis_type=mapped_analysis_type,
                selected_variables=variables,
                user_query=user_query,
                dataset_name=dataset_name
            )
            
            if results.get('success', False):
                # Use the formatted report for the response
                response = f"Analysis complete! Here are your results:\n\n{results.get('formatted_report', 'No report available')}"
            else:
                error_msg = results.get('error', 'Unknown error occurred')
                response = f"Analysis failed: {error_msg}\n\n{results.get('formatted_report', 'No additional details available')}"
                
        except Exception as e:
            results = {"error": str(e), "success": False}
            response = f"Analysis failed with error: {str(e)}"
        
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
            # Don't append message for end conversation, let it terminate
            return state
            
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
        elif intent == "end_conversation":
            return END
        else:
            return "detect_intent"
    
    def should_continue(state: AgentState) -> str:
        """Determine if conversation should continue or end"""
        intent = state["intent"]
        
        # End conversation if requested
        if intent == "end_conversation":
            return END
        
        # End after processing to avoid loops - let the agent wait for new user input
        return END

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
    workflow.add_conditional_edges(
        "answer_general",
        should_continue,
        {
            "detect_intent": "detect_intent", 
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "handle_conversation",
        should_continue,
        {
            "detect_intent": "detect_intent",
            END: END  
        }
    )
    
    # Query flow edges - for single-step testing, end after showing variables
    workflow.add_conditional_edges(
        "handle_query",
        should_continue,
        {
            "detect_intent": "detect_intent",
            END: END
        }
    )
    workflow.add_conditional_edges(
        "process_approval",
        route_approval,
        {
            "select_analysis_type": "select_analysis_type",
            "handle_query": "handle_query"
        }
    )
    
    # Analysis flow edges
    workflow.add_conditional_edges(
        "select_analysis_type",
        should_continue,
        {
            "detect_intent": "detect_intent",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "run_analysis", 
        should_continue,
        {
            "detect_intent": "detect_intent",
            END: END
        }
    )
    
    # Compile the graph with optional persistence
    if checkpointer:
        agent = workflow.compile(checkpointer=checkpointer)
        print("🔄 Agent compiled with persistence enabled")
    else:
        agent = workflow.compile()
        print("🔄 Agent compiled without persistence")
    
    return agent

# Persistence and thread management utilities

def create_thread_config(thread_id: str | None = None) -> Dict[str, Any]:
    """
    Create a configuration dict for conversation threading
    
    Args:
        thread_id (str): Unique identifier for the conversation thread.
                        If None, a timestamp-based ID will be generated.
    
    Returns:
        Dict containing the thread configuration
    """
    import time
    if thread_id is None:
        thread_id = f"conversation_{int(time.time())}"
    
    return {
        "configurable": {
            "thread_id": thread_id
        }
    }

def get_conversation_history(agent, thread_id: str) -> List[Dict]:
    """
    Retrieve conversation history for a specific thread
    
    Args:
        agent: The compiled LangGraph agent
        thread_id (str): The thread ID to retrieve history for
    
    Returns:
        List of conversation messages
    """
    try:
        config = create_thread_config(thread_id)
        # Get the latest state from the checkpoint
        state = agent.get_state(config)
        if state and state.values:
            return state.values.get("messages", [])
        return []
    except Exception as e:
        print(f"Error retrieving conversation history: {e}")
        return []

def reset_conversation_thread(agent, thread_id: str) -> bool:
    """
    Reset a conversation thread by clearing its state
    
    Args:
        agent: The compiled LangGraph agent
        thread_id (str): The thread ID to reset
    
    Returns:
        bool: True if reset was successful, False otherwise
    """
    try:
        config = create_thread_config(thread_id)
        # Create a fresh state
        initial_state = {
            "messages": [],
            "intent": "",
            "user_query": "",
            "original_query": "",  # Store the original user query for analysis
            "dataset": ["all"],
            "selected_variables": [],
            "analysis_type": "descriptive", 
            "user_approved": False,
            "analysis_result": {}
        }
        
        # Update the state to reset the conversation
        agent.update_state(config, initial_state)
        print(f"✅ Conversation thread {thread_id} has been reset")
        return True
    except Exception as e:
        print(f"❌ Error resetting conversation thread {thread_id}: {e}")
        return False

def list_active_threads(agent) -> List[str]:
    """
    List all active conversation threads (if supported by checkpointer)
    
    Args:
        agent: The compiled LangGraph agent
    
    Returns:
        List of active thread IDs
    """
    try:
        # This functionality may vary depending on the checkpointer implementation
        # For MemorySaver, we'll need a different approach
        print("ℹ️ Thread listing functionality depends on checkpointer implementation")
        return []
    except Exception as e:
        print(f"Error listing threads: {e}")
        return []
