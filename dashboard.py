"""
Navegador Dashboard - Interactive Web Interface
==============================================

A Dash-based web interface for the Navegador survey analysis agent.
Provides a chatbot interface with real-time analysis and reporting capabilities.
"""

# Basic setup for error handling to avoid silent hangs
import sys
import os
import traceback

# Initialize early to catch import errors
print("Starting Navegador Dashboard initialization...")
print("Python version:", sys.version)
print("Current working directory:", os.getcwd())

# Enable LangSmith tracing if available
os.environ["LANGSMITH_TRACING"] = "true"
LANGSMITH_API_KEY = os.getenv('LANGSMITH_API_KEY')
LANGSMITH_PROJECT = os.getenv('LANGSMITH_PROJECT', 'navegador-dashboard-monitoring')

try:
    # Essential imports for the dashboard
    import dash
    from dash import dcc, html, Input, Output, State, callback, ctx
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    import json
    import base64
    import io
    from datetime import datetime
    import threading
    import concurrent.futures
    import time
    
    # Import LangSmith monitoring if available
    try:
        # LangSmith tracing is now handled differently
        from langsmith.client import Client as LangSmithClient
        
        # Initialize LangSmith client
        langsmith_client = None
        if LANGSMITH_API_KEY:
            langsmith_client = LangSmithClient(api_key=LANGSMITH_API_KEY)
            # Enable tracing v2
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            print("✅ LangSmith monitoring initialized in dashboard")
        else:
            print("⚠️ LangSmith API key not found, monitoring disabled in dashboard")
    except ImportError:
        print("⚠️ LangSmith packages not available, monitoring disabled")
        langsmith_client = None
    
    print("Successfully imported all required packages")
except ImportError as e:
    print("❌ CRITICAL ERROR: Failed to import required package")
    print(f"Error details: {e}")
    traceback.print_exc()
    print("\nPlease ensure all dependencies are installed with:")
    print("pip install dash dash-bootstrap-components plotly pandas langchain langchain-openai")
    sys.exit(1)
import uuid
import time
from typing import Dict, List, Any, Optional, TypedDict, Union

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import state normalizer for consistent agent state handling
try:
    from state_normalizer import normalize_state, normalize_config, create_agent_state
    print("✅ Successfully imported state_normalizer")
except ImportError:
    print("⚠️ state_normalizer not available - will use default state construction")
    normalize_state = lambda state: state  # Fallback function
    normalize_config = lambda config: config  # Fallback function
    create_agent_state = None  # Will use manual state creation
    
# Function to format chat messages for display
def format_chat_history(chat_data):
    """
    Formats chat history data into Dash components for display
    
    Args:
        chat_data: List of chat message dictionaries with type, content, and timestamp
        
    Returns:
        List of Dash HTML components representing the chat messages
    """
    if not chat_data:
        return []
        
    chat_components = []
    
    for message in chat_data:
        message_type = message.get("type", "assistant")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        is_progress = message.get("is_progress", False)
        
        if message_type == "user":
            # User message styling
            message_component = html.Div(
                [
                    html.Div(content, className="message-content"),
                    html.Div(timestamp, className="message-timestamp")
                ],
                className="message user-message"
            )
        else:
            # Assistant message styling with optional progress indicator
            timestamp_content = [timestamp]
            if is_progress:
                # Simple loading indicator without using dbc.Spinner
                loading_indicator = html.Span("⏳", className="loading-indicator")
                timestamp_content.append(loading_indicator)
                
            message_component = html.Div(
                [
                    html.Div(dcc.Markdown(content), className="message-content"),
                    html.Div(timestamp_content, className="message-timestamp")
                ],
                className="message assistant-message"
            )
            
        chat_components.append(message_component)
    
    return chat_components

# Flag to check if required modules are available
MODULES_AVAILABLE = True
try:
    # Try importing key modules
    import langchain
    from langchain.schema.runnable import RunnableConfig
except ImportError:
    MODULES_AVAILABLE = False
    print("⚠️ Some required modules are not available. Limited functionality will be used.")

# Define a type for session data that can be stored in a Dash Store
SessionDataDict = Dict[str, Any]


def process_agent_response(agent_response, session_data, chat_data, user_message):
    """
    Process an agent response and update session data
    
    This function handles agent responses consistently, keeping track of processed actions
    and ensuring the chat history is properly updated.
    """
    from datetime import datetime
    import time
    import dash
    
    # Make a deep copy of session data to avoid reference issues
    session_data_copy = session_data.copy() if session_data else {}
    
    try:
        # Extract response content
        content = extract_agent_content(agent_response)
        
        # Debug agent response
        print(f"🔍 Agent response type: {type(agent_response)}")
        if hasattr(agent_response, 'keys'):
            print(f"🔍 Agent response keys: {list(agent_response.keys())}")
        elif hasattr(agent_response, '__dict__'):
            print(f"🔍 Agent response attributes: {[k for k in agent_response.__dict__ if not k.startswith('_') and not callable(getattr(agent_response, k))]}")
        
        # Update session with agent state, but keep the processed flag
        pending_action = session_data_copy.get('pending_main_action', {})
        
        try:
            session_data_copy = update_session_from_agent_response(session_data_copy, agent_response)
        except Exception as update_err:
            print(f"⚠️ Error updating session from agent response: {update_err}")
            # Continue even if update fails
        
        # Mark the pending action as processed
        if 'pending_main_action' in session_data_copy:
            print(f"🏁 Marking pending action as processed")
            session_data_copy['pending_main_action']['processed'] = True
            session_data_copy['pending_main_action']['processed_at'] = time.time()
        
        # Create assistant message with timestamp
        assistant_message = {
            "type": "assistant", 
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M")
        }
        
        # Update chat history
        new_chat_data = chat_data + [assistant_message]
        formatted_chat = format_chat_history(new_chat_data)
        
        print(f"✅ Agent response processed: {content[:50]}...")
        
        # Return all updated UI components
        return formatted_chat, new_chat_data, "", session_data_copy, True
        
    except Exception as e:
        print(f"❌ Error processing agent response: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            # Fallback to mock response on error
            mock_response = get_mock_agent_response(
                user_message, 
                session_data_copy,
                session_data_copy.get('pending_main_action', {}).get('search_keywords', ''),
                session_data_copy.get('pending_main_action', {}).get('preferred_datasets', ['ALL'])
            )
            
            # Add the mock response to chat
            new_chat_data = chat_data.copy() if chat_data else []
            new_chat_data.append({
                "type": "assistant",
                "content": mock_response["content"],
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Mark pending action as processed
            if 'pending_main_action' in session_data_copy:
                session_data_copy['pending_main_action']['processed'] = True
                session_data_copy['pending_main_action']['processed_at'] = time.time()
                
            return format_chat_history(new_chat_data), new_chat_data, "", session_data_copy, True
            
        except Exception as nested_err:
            print(f"❌❌ Critical error in error handling: {nested_err}")
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True

def create_agent_config(thread_id: Optional[str] = None) -> Any:
    """
    Create a configuration dict for agent invocation with proper checkpointer config
    
    Args:
        thread_id (Optional[str]): Optional thread ID. If None, a timestamp-based ID will be generated.
        
    Returns:
        RunnableConfig or Dict containing the required configurable keys for the LangGraph checkpointer
    """
    # Build the initial config dict
    if thread_id is None:
        thread_id = f"chat_{int(time.time())}"
    
    # Create a base config with thread_id
    config_dict = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # Use normalize_config to ensure consistent format
    normalized_config = normalize_config(config_dict)
    
    # Convert to RunnableConfig if langchain is available
    if MODULES_AVAILABLE and 'langchain' in sys.modules:
        try:
            from langchain.schema.runnable import RunnableConfig
            return RunnableConfig(configurable=normalized_config["configurable"])
        except (ImportError, AttributeError):
            pass
            
    # Fall back to dict if conversion failed or not available
    return normalized_config
    if MODULES_AVAILABLE:
        try:
            # Convert to RunnableConfig when available
            from langchain.schema.runnable import RunnableConfig
            return RunnableConfig(configurable=config_dict["configurable"])
        except Exception:
            # Fallback to dict if conversion fails
            return config_dict
    else:
        # Return as plain dict otherwise
        return config_dict

def extract_agent_content(agent_response: Any) -> str:
    """
    Extract the content from an agent response
    
    Args:
        agent_response: The response from the agent.invoke() call
        
    Returns:
        String content of the agent message
    """
    try:
        if isinstance(agent_response, dict):
            # Try to extract content from messages
            messages = agent_response.get('messages', [])
            if messages and isinstance(messages, list) and len(messages) > 0:
                last_message = messages[-1]
                if isinstance(last_message, dict):
                    return last_message.get('content', '')
                elif hasattr(last_message, 'content'):
                    return last_message.content
                else:
                    return str(last_message)
            # If no content in messages, try other common keys
            return agent_response.get('content', agent_response.get('response', ''))
        elif hasattr(agent_response, 'content'):
            # Handle object with content attribute
            return agent_response.content
        return str(agent_response)
    except Exception as e:
        print(f"Error extracting agent content: {e}")
        return "I encountered an issue processing your request. Please try again."

def update_session_from_agent_response(session_data: Dict[str, Any], agent_response: Any) -> Dict[str, Any]:
    """
    Update session data with information from agent response
    
    Args:
        session_data: The current session data dictionary
        agent_response: The response from agent.invoke()
        
    Returns:
        Updated session data dictionary
    """
    # Make a copy to avoid modifying the original
    updated_session = session_data.copy()
    
    # Preserve any existing pending_main_action settings
    pending_action = updated_session.get('pending_main_action', {})
    pending_action_processed = False
    if pending_action:
        pending_action_processed = pending_action.get('processed', False)
        print(f"📝 Preserving pending action status in session update (processed: {pending_action_processed})")
    
    try:
        # Convert object to dict if needed for consistent handling
        response_dict = {}
        
        if isinstance(agent_response, dict):
            response_dict = agent_response
        elif hasattr(agent_response, '__dict__'):
            # Handle object types by converting to dict
            response_dict = {k: v for k in agent_response.__dict__.items() 
                           if not k.startswith('_') and not callable(v)}
        
        # Update agent_state - normalize it first for consistency
        normalized_response = normalize_state(response_dict)
        updated_session['agent_state'] = normalized_response
        
        # Save the status of any pending_main_action before we update other fields
        pending_action = updated_session.get('pending_main_action', {})
        
        # Extract and update individual fields if present in agent response
        for key in ['dataset', 'selected_variables', 'analysis_type', 'analysis_result', 'intent']:
            if key in response_dict:
                # Map agent key names to session key names
                session_key = {
                    'dataset': 'datasets',
                    'selected_variables': 'variables'
                }.get(key, key)
                
                updated_session[session_key] = response_dict[key]
            elif hasattr(agent_response, key):
                # Try to access as attribute if not in dict
                session_key = {
                    'dataset': 'datasets',
                    'selected_variables': 'variables'
                }.get(key, key)
                
                updated_session[session_key] = getattr(agent_response, key)
            
            # Special handling for analysis_result if present
            if 'analysis_result' in agent_response and agent_response['analysis_result']:
                updated_session['last_report'] = agent_response['analysis_result']
    except Exception as e:
        print(f"Error updating session from agent response: {e}")
    
    # Restore any pending_main_action that might have been overwritten
    if pending_action:
        # Ensure we preserve the processed status
        updated_session['pending_main_action'] = pending_action
    
    return updated_session

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
app.title = "Navegador - Survey Analysis Dashboard"
app.config.suppress_callback_exceptions = True  # Allow callbacks to components not yet in layout

# Language detection and bilingual support
def detect_language(text: str) -> str:
    """Detect if user message is in English or Spanish"""
    # Simple keyword-based detection (can be enhanced with proper language detection)
    spanish_keywords = [
        'hola', 'gracias', 'por favor', 'sí', 'no', 'qué', 'cómo', 'cuál', 'dónde', 'cuándo',
        'encuesta', 'datos', 'análisis', 'variables', 'proyecto', 'mexicanos', 'cultura',
        'identidad', 'valores', 'medio ambiente', 'política', 'educación', 'economía'
    ]
    
    english_keywords = [
        'hello', 'thanks', 'please', 'yes', 'no', 'what', 'how', 'which', 'where', 'when',
        'survey', 'data', 'analysis', 'variables', 'project', 'mexicans', 'culture',
        'identity', 'values', 'environment', 'politics', 'education', 'economy'
    ]
    
# TODO: add keywords for all datasets

    text_lower = text.lower()
    
    # Count matches for each language
    spanish_matches = sum(1 for word in spanish_keywords if word in text_lower)
    english_matches = sum(1 for word in english_keywords if word in text_lower)
    
    # Default to Spanish if no clear indication (since data is in Spanish)
    if spanish_matches > english_matches:
        return 'es'
    elif english_matches > spanish_matches:
        return 'en'
    else:
        # Default to Spanish for Mexican context
        return 'es'

# TODO: agregar mensajes de 'pensando...' o 'escogiendo variables...', y 'procesando resultados...'
# Bilingual message templates
MESSAGES = {
    'en': {
        'welcome': "Hello! I'm Navegador, your survey analysis assistant. I can help you explore datasets, select variables, and run analyses. What would you like to know?",
        'session_reset': "Session reset! Hello again! How can I help you with survey analysis?",
        'agent_unavailable': "Sorry, the agent is not available right now. Please try again later.",
        'agent_timeout': "The request is taking longer than expected. I've timed out after {timeout} seconds. Please try a simpler query or try again later.",
        'error_occurred': "Sorry, I encountered an error: {error}. Please try rephrasing your question.",
        'datasets_title': "Here are the available datasets:",
        'which_dataset': "Which dataset would you like to explore?",
        'variables_found': "I found relevant variables for '{query}':",
        'proceed_variables': "Would you like to proceed with these variables for analysis?",
        'no_variables_found': "I couldn't find specific variables for your query. Could you be more specific about what you're looking for?",
        'select_dataset_first': "Please first select a dataset, then I can help you find variables.",
        'analysis_complete': "✅ Analysis complete! Here's a summary:",
        'check_report_panel': "Check the report panel for detailed results.",
        'analysis_failed': "❌ Analysis failed: {error}",
        'need_variables_first': "To run an analysis, I first need you to select some variables. Would you like me to help you find variables?",
        'analysis_types': "Great! I can run several types of analysis:\n\n• **Quick Insights** - Basic descriptive statistics\n• **Detailed Report** - Comprehensive analysis with visualizations\n• **Cross-tabulation** - Relationship analysis between variables\n\nWhich type would you prefer?",
        'variable_search_help': "I can help you search for variables! Please tell me:\n\n1. Which dataset interests you?\n2. What topic are you researching?\n\nFor example, you could say 'Show me variables about education from the identity survey'",
        'capabilities': "I'm here to help you analyze survey data! I can:\n\n• Tell you about the project and methodology 📖\n• Show you available datasets 📊\n• Help you find relevant variables 🔍\n• Run various types of analysis 📈\n• Generate reports and visualizations 📑\n\nWhat would you like to explore?",
        'explore_datasets': "Would you like to explore variables from any of these datasets?",
        'cross_disciplinary_search': "Cross-disciplinary search across all datasets",
        'variables_next_steps': "What would you like to do next?\n\n• Refine your query to get different variables\n• Select an analysis type (descriptive, correlation, etc.)\n• Proceed with default analysis\n• Start a new conversation"
    },
    'es': {
        'welcome': "¡Hola! Soy Navegador, tu asistente de análisis de encuestas. Puedo ayudarte a explorar conjuntos de datos, seleccionar variables y ejecutar análisis. ¿Qué te gustaría saber?",
        'session_reset': "¡Sesión reiniciada! ¡Hola de nuevo! ¿Cómo puedo ayudarte con el análisis de encuestas?",
        'agent_unavailable': "Lo siento, el agente no está disponible en este momento. Por favor, inténtalo de nuevo más tarde.",
        'agent_timeout': "La solicitud está tomando más tiempo de lo esperado. Se agotó el tiempo de espera después de {timeout} segundos. Intenta una consulta más simple o inténtalo más tarde.",
        'error_occurred': "Lo siento, encontré un error: {error}. Por favor, reformula tu pregunta.",
        'datasets_title': "Aquí están los conjuntos de datos disponibles:",
        'which_dataset': "¿Qué conjunto de datos te gustaría explorar?",
        'variables_found': "Encontré variables relevantes para '{query}':",
        'proceed_variables': "¿Te gustaría proceder con estas variables para el análisis?",
        'no_variables_found': "No pude encontrar variables específicas para tu consulta. ¿Podrías ser más específico sobre lo que buscas?",
        'select_dataset_first': "Por favor, primero selecciona un conjunto de datos, luego te puedo ayudar a encontrar variables.",
        'analysis_complete': "✅ ¡Análisis completo! Aquí tienes un resumen:",
        'check_report_panel': "Revisa el panel de reportes para resultados detallados.",
        'analysis_failed': "❌ El análisis falló: {error}",
        'need_variables_first': "Para ejecutar un análisis, primero necesito que selecciones algunas variables. ¿Te gustaría que te ayude a encontrar variables?",
        'analysis_types': "¡Excelente! Puedo ejecutar varios tipos de análisis:\n\n• **Insights Rápidos** - Estadísticas descriptivas básicas\n• **Reporte Detallado** - Análisis comprehensivo con visualizaciones\n• **Tabulación cruzada** - Análisis de relaciones entre variables\n\n¿Cuál prefieres?",
        'variable_search_help': "¡Puedo ayudarte a buscar variables! Por favor dime:\n\n1. ¿Qué conjunto de datos te interesa?\n2. ¿Qué tema estás investigando?\n\nPor ejemplo, podrías decir 'Muéstrame variables sobre educación de la encuesta de identidad'",
        'capabilities': "¡Estoy aquí para ayudarte a analizar datos de encuestas! Puedo:\n\n• Contarte sobre el proyecto y metodología 📖\n• Mostrarte conjuntos de datos disponibles 📊\n• Ayudarte a encontrar variables relevantes 🔍\n• Ejecutar varios tipos de análisis 📈\n• Generar reportes y visualizaciones 📑\n\n¿Qué te gustaría explorar?",
        'explore_datasets': "¿Te gustaría explorar variables de alguno de estos conjuntos de datos?",
        'cross_disciplinary_search': "Búsqueda interdisciplinaria en todos los conjuntos de datos",
        'variables_next_steps': "¿Qué te gustaría hacer a continuación?\n\n• Refinar tu búsqueda para obtener diferentes variables\n• Seleccionar un tipo de análisis (descriptivo, correlación, etc.)\n• Continuar con el análisis predeterminado\n• Iniciar una nueva conversación"
    }
}

def get_message(key: str, lang: str = 'es', **kwargs) -> str:
    """Get a message in the specified language with optional formatting"""
    message = MESSAGES.get(lang, MESSAGES['es']).get(key, MESSAGES['es'].get(key, key))
    if kwargs:
        try:
            return message.format(**kwargs)
        except KeyError:
            return message
    return message

# Helper functions for dataset information
def get_available_datasets():
    """Get list of available datasets from the survey collection"""
    if MODULES_AVAILABLE:
        try:
            # Import locally to ensure we get the most up-to-date reference
            from dataset_knowledge import rev_topic_dict, pregs_dict
            
            # Return dataset information from the imported dictionaries
            datasets = {}
            print(f"🔍 Processing {len(rev_topic_dict)} datasets from rev_topic_dict")
            
            for abbrev, full_name in rev_topic_dict.items():
                # Clean up the name for display
                clean_name = full_name.replace('_', ' ').title()
                datasets[clean_name] = {
                    "abbreviation": abbrev,
                    "full_name": full_name,
                    "description": f"Survey on {clean_name.lower()}",
                    "variables": len([k for k in pregs_dict.keys() if k.endswith(f"|{abbrev}")]) if pregs_dict else 0
                }
            print(f"✅ Successfully processed {len(datasets)} datasets")
            return datasets
        except Exception as e:
            print(f"Error getting datasets: {e}")
            import traceback
            traceback.print_exc()
            return get_mock_datasets()
    else:
        return get_mock_datasets()

def get_mock_datasets():
    """Get mock dataset information when real functions aren't available"""
    return {
        "Identidad Y Valores": {
            "abbreviation": "IDE",
            "description": "Survey on identity and values in Mexico",
            "variables": 150,
            "year": 2015
        },
        "Medio Ambiente": {
            "abbreviation": "MED", 
            "description": "Survey on environmental attitudes",
            "variables": 120,
            "year": 2015
        },
        "Cultura Política": {
            "abbreviation": "POL",
            "description": "Survey on political culture",
            "variables": 180,
            "year": 2014
        }
    }

def get_project_description(user_query: str = "", language: str = "es"):
    """Get project description using the _project_describer function"""
    if MODULES_AVAILABLE:
        try:
            # Import LLM for project description and required variables
            from langchain_openai import ChatOpenAI
            from dataset_knowledge import _project_describer, tmp_topic_st
            
            # Create an empty string for tmp_data_describer_st since it's not defined in dataset_knowledge
            tmp_data_describer_st = ""
            
            llm = ChatOpenAI(model="gpt-4o-mini")
            
            if user_query:
                # Add language instruction to the query if needed
                if language == 'en' and not any(eng_word in user_query.lower() for eng_word in ['english', 'in english']):
                    enhanced_query = f"{user_query}. Please respond in English."
                else:
                    enhanced_query = user_query
                
                print(f"🔍 Calling _project_describer with query: '{enhanced_query[:50]}...'")
                return _project_describer(enhanced_query, tmp_data_describer_st, llm)
            else:
                # Return basic project info
                return get_mock_project_description(language)
        except Exception as e:
            print(f"Error getting project description: {e}")
            import traceback
            traceback.print_exc()
            return get_mock_project_description(language)
    else:
        return get_mock_project_description(language)

def get_mock_project_description(language: str = "es"):
    """Mock project description when real function isn't available"""
    if language == 'en':
        return """
        Project: "Los mexicanos vistos por sí mismos" (Mexicans as seen by themselves)
        
        This is a comprehensive collection of public opinion surveys conducted in Mexico between 2014-2015, 
        covering topics like identity, environment, politics, culture, and society. 
        
        Each survey has 1000 representative respondents with 3% margin of error and 95% confidence level.
        
        Coordinated by UNAM's Public Opinion Research Unit.
        """
    else:
        return """
        Proyecto: "Los mexicanos vistos por sí mismos"
        
        Esta es una colección comprensiva de encuestas de opinión pública realizadas en México entre 2014-2015, 
        cubriendo temas como identidad, medio ambiente, política, cultura y sociedad.
        
        Cada encuesta tiene 1000 encuestados representativos con 3% de margen de error y 95% de nivel de confianza.
        
        Coordinado por la Unidad de Investigación de Opinión Pública de la UNAM.
        """

# Define TypedDict for session data to support proper type checking
class SessionData(TypedDict, total=False):
    """Type definition for the session data store"""
    datasets: List[str]
    variables: List[str]
    analysis_type: Optional[str]
    last_report: Optional[Any]
    agent_state: Dict[str, Any]
    language: str
    search_keywords: Optional[str]
    preferred_datasets: Optional[List[str]]
    intent: Optional[str]
    pending_main_action: Optional[Dict[str, Any]]

# Global variables for session state
chat_history = []
current_session: SessionDataDict = {
    'datasets': ["ALL"],  # Default to using all datasets
    'variables': [],
    'analysis_type': None,
    'last_report': None,
    'agent_state': {},
    'language': 'es'  # Default to Spanish since data is in Spanish
}

# Initialize the agent with proper persistence
agent = None

# Define a simple thread config function if not available from agent module
def create_simple_thread_config():
    """
    Create a simple thread config for agent persistence that's compatible with LangGraph
    
    Returns:
        Either a RunnableConfig (if langchain is available) or a Dict with the proper format
    """
    import time
    
    # Create a basic config with thread_id
    base_config = {
        "configurable": {
            "thread_id": f"chat_{int(time.time())}"
        }
    }
    
    # Use normalize_config to ensure proper formatting
    config_dict = normalize_config(base_config)
    
    # Convert to RunnableConfig if langchain is available
    if MODULES_AVAILABLE and 'langchain' in sys.modules:
        try:
            from langchain.schema.runnable import RunnableConfig
            return RunnableConfig(configurable=config_dict["configurable"])
        except (ImportError, AttributeError):
            return config_dict
    else:
        return config_dict

# Global variables for agent and status
agent = None
agent_ready = False

# Define thread_config function for persistence
def create_thread_config():
    """Create a thread config for agent persistence"""
    import time
    return {
        "configurable": {
            "thread_id": f"chat_{int(time.time())}"
        }
    }

def initialize_agent_in_background():
    """Initialize the agent in a background thread to avoid blocking the UI"""
    global agent, agent_ready
    
    if MODULES_AVAILABLE:
        try:
            # Create agent with persistence
            print("🔄 Creating agent with persistence (background thread)...")
            from agent import create_agent  # Ensure it's imported in this scope
            
            # Create agent in this thread
            agent = create_agent(enable_persistence=True)
            agent_ready = True
            print("✅ Agent initialized successfully (with persistence)")
            
            # Run a simple test in this thread to verify it works
            test_agent_async()
            
        except Exception as e:
            print(f"❌ Failed to initialize agent in background thread: {e}")
            agent_ready = False
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ Required modules not available, agent initialization skipped")
        agent_ready = False

# Test agent function
def test_agent_async():
    """Test the agent to verify it's working"""
    global agent
    if not agent:
        print("⚠️ Cannot test agent - not initialized")
        return
        
    try:
        print("🔄 Testing agent with general greeting...")
        # Create a simple general state test
        if create_agent_state:
            # Use the normalized state creation function
            general_state = create_agent_state(
                user_message="Hello",
                intent="answer_general_questions",
                dataset=["all"]
            )
        else:
            # Fallback to manual state creation
            general_state = {
                "messages": [{"role": "user", "content": "Hello"}],
                "intent": "answer_general_questions",
                "user_query": "Hello",
                "original_query": "Hello",
                "dataset": ["all"],
                "selected_variables": [],
                "analysis_type": "descriptive",
                "user_approved": False,
                "analysis_result": {}
            }
            
        # Normalize state for consistency
        general_state = normalize_state(general_state)
        
        # Create a properly typed config for testing
        test_config = create_agent_config()
        
        # Ensure state is normalized
        general_state = normalize_state(general_state)
        
        # Test 1: Basic greeting test
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(agent.invoke, general_state, config=test_config)
            try:
                test_result = future.result(timeout=60)  # 60 second timeout (increased from 20)  # 20 second timeout (increased from 10)
                print(f"✅ Agent greeting test successful: {type(test_result)}")
                if isinstance(test_result, dict) and 'messages' in test_result:
                    msgs = test_result.get('messages', [])
                    if msgs and len(msgs) > 0:
                        last_msg = msgs[-1]
                        content = last_msg.get('content', '') if isinstance(last_msg, dict) else str(last_msg)
                        print(f"   Response: {content[:100]}...")
            except concurrent.futures.TimeoutError:
                print("⚠️ Agent greeting test timed out after 10 seconds")
            except Exception as e:
                print(f"⚠️ Agent greeting test error: {e}")
        
        # Test 2: Query test
        print("🔄 Testing agent with a query about health...")
        query_state = {
            "messages": [{"role": "user", "content": "What do Mexicans think about health?"}],
            "intent": "query_variable_database",
            "user_query": "What do Mexicans think about health?",
            "original_query": "What do Mexicans think about health?",
            "dataset": ["all"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        print("🔄 Testing health query routing through agent workflow...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Use a shorter timeout for better diagnostics
            start_time = time.time()
            future = executor.submit(agent.invoke, query_state, config=test_config)
            try:
                query_result = future.result(timeout=120)  # 120 second timeout (increased from 30)  # 30 second timeout (increased from 8) - reduce from 15
                elapsed = time.time() - start_time
                print(f"✅ Agent query test successful after {elapsed:.2f}s: {type(query_result)}")
                print(f"   Agent state keys: {list(query_result.keys()) if isinstance(query_result, dict) else 'Not a dict'}")
                if isinstance(query_result, dict):
                    # Check selected variables and dataset
                    selected_vars = query_result.get('selected_variables', [])
                    dataset = query_result.get('dataset', [])
                    intent = query_result.get('intent', '')
                    print(f"   Final intent: {intent}")
                    print(f"   Selected dataset: {dataset}")
                    print(f"   Selected variables: {selected_vars[:5]}...")
                    # Check messages
                    if 'messages' in query_result:
                        msgs = query_result.get('messages', [])
                        if msgs and len(msgs) > 0:
                            last_msg = msgs[-1]
                            content = last_msg.get('content', '') if isinstance(last_msg, dict) else str(last_msg)
                            print(f"   Response: {content[:100]}...")
                            
                    # Detailed agent response check - looking for cause of hanging
                    print(f"   Message type: {type(query_result.get('messages', [])[-1]) if query_result.get('messages') else 'No messages'}")
                    print(f"   Path taken: detect_intent -> handle_query")
            except concurrent.futures.TimeoutError:
                elapsed = time.time() - start_time
                print(f"⚠️ Agent query test timed out after {elapsed:.2f}s")
                print("This indicates the agent is hanging on query processing")
                print("The dashboard will still run but with mock responses")
            except Exception as e:
                print(f"⚠️ Agent query test error: {e}")
                import traceback
                traceback.print_exc()
    except Exception as test_err:
        print(f"⚠️ Agent tests failed: {test_err}")
        import traceback
        traceback.print_exc()

if MODULES_AVAILABLE:
    try:
        # Start agent initialization in background thread
        print("🔄 Starting agent initialization in background thread...")
        bg_thread = threading.Thread(target=initialize_agent_in_background)
        bg_thread.daemon = True
        bg_thread.start()
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        agent = None
        print(f"Error details: {str(e)}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️ Modules not available, running in mock mode")

# Enhanced query processing and state management functions

def extract_search_keywords(user_query: str, detected_lang: str = "es") -> str:
    """
    Extract key search terms from user query for variable retrieval.
    
    Examples:
    - "quiero saber sobre las opiniones de la salud en México" -> "salud"
    - "I want to know about attitudes about health" -> "health attitudes"
    - "tell me about corruption in government" -> "corruption government"
    """
    import re
    
    query_lower = user_query.lower()
    
    # More comprehensive filler patterns with better Spanish support
    filler_patterns = [
        # English fillers
        r'\bi want to know\b', r'\btell me about\b', r'\bshow me\b', r'\bfind\b',
        r'\bif mexicans?\b', r'\bwhat do mexicans?\b', r'\bhow do mexicans?\b',
        r'\babout mexicans?\b', r'\bin mexico\b', r'\bmexican people\b',
        r'\bbased on the survey about\b', r'\bfrom the survey\b', r'\bin the data\b',
        r'\baccording to\b', r'\bdo\b', r'\bdoes\b', r'\bare\b', r'\bis\b',
        r'\bopinions?\b', r'\bviews?\b', r'\bthoughts?\b', r'\battitudes?\b',
        r'\babout the\b', r'\bof the\b', r'\bin the\b', r'\bon the\b',
        
        # Spanish fillers - much more comprehensive
        r'\bquiero saber\b', r'\bquisiera saber\b', r'\bme gustaría saber\b',
        r'\bdime sobre\b', r'\bmuéstrame\b', r'\bencuentra\b', r'\bbusca\b',
        r'\bsi los mexicanos?\b', r'\bqué piensan los mexicanos?\b', r'\bcómo ven los mexicanos?\b',
        r'\bsobre los mexicanos?\b', r'\ben méxico\b', r'\bel pueblo mexicano\b',
        r'\bbasado en la encuesta sobre\b', r'\bde la encuesta\b', r'\ben los datos\b',
        r'\bsegún\b', r'\bhacen\b', r'\bhace\b', r'\bson\b', r'\bes\b',
        r'\bopiniones?\b', r'\blas opiniones?\b', r'\bpensamiento\b', r'\bactitudes?\b',
        r'\bpareceres?\b', r'\bcriterios?\b', r'\bjuicios?\b',
        # More Spanish stop words and phrases
        r'\bsobre las?\b', r'\bde las?\b', r'\ben las?\b', r'\bcon las?\b',
        r'\bsobre los?\b', r'\bde los?\b', r'\ben los?\b', r'\bcon los?\b',
        r'\bsobre la\b', r'\bde la\b', r'\ben la\b', r'\bcon la\b',
        r'\bsobre el\b', r'\bde el\b', r'\bdel\b', r'\ben el\b', r'\bcon el\b',
        r'\bque\b', r'\bcomo\b', r'\bcómo\b', r'\bpor que\b', r'\bporque\b',
        r'\bdonde\b', r'\bdónde\b', r'\bcuando\b', r'\bcuándo\b',
        r'\bcual\b', r'\bcuál\b', r'\bcuales\b', r'\bcuáles\b',
        r'\bpara\b', r'\bpor\b', r'\bcon\b', r'\bsin\b', r'\bentre\b',
        r'\bhacia\b', r'\bdesde\b', r'\bhasta\b', r'\bante\b', r'\bbajo\b',
        r'\bun\b', r'\buna\b', r'\bunos\b', r'\bunas\b', r'\bel\b', r'\bla\b', r'\blos\b', r'\blas\b'
    ]
    
    # Apply filler removal
    cleaned_query = query_lower
    for pattern in filler_patterns:
        cleaned_query = re.sub(pattern, ' ', cleaned_query)
    
    # Remove extra whitespace and punctuation
    cleaned_query = re.sub(r'[^\w\s]', ' ', cleaned_query)
    cleaned_query = ' '.join(cleaned_query.split())
    
    # Filter out remaining very short words (< 3 characters) which are usually not informative
    words = cleaned_query.split()
    meaningful_words = [word for word in words if len(word) >= 3]
    
    # If we have meaningful words, use them; otherwise fall back to original
    if meaningful_words:
        return ' '.join(meaningful_words)
    elif len(cleaned_query.strip()) >= 3:
        return cleaned_query.strip()
    else:
        return user_query.strip()

def detect_dataset_preference(user_query: str, detected_lang: str = "es") -> list:
    """
    Detect if user is referring to a specific dataset/survey.
    
    Examples:
    - "based on the survey about health" -> ["ENCUESTA_NACIONAL_DE_SALUD"] 
    - "from the education survey" -> ["ENCUESTA_NACIONAL_DE_EDUCACION"]
    """
    query_lower = user_query.lower()
    datasets_info = get_available_datasets()
    
    # TODO: add and improve keywords for all datasets
    # Dataset keywords mapping
    dataset_keywords = {
        "ENCUESTA_NACIONAL_DE_SALUD": ["health", "salud", "healthcare", "medicina"],
        "ENCUESTA_NACIONAL_DE_EDUCACION": ["education", "educación", "escuela", "school", "teaching"],
        "ENCUESTA_NACIONAL_DE_ECONOMIA_Y_EMPLEO": ["economy", "economía", "employment", "empleo", "work", "trabajo"],
        "ENCUESTA_NACIONAL_DE_CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD": ["corruption", "corrupción", "legal", "legalidad"],
        "ENCUESTA_NACIONAL_DE_CULTURA_POLITICA": ["politics", "política", "political", "gobierno", "government"],
        "ENCUESTA_NACIONAL_DE_GENERO": ["gender", "género", "women", "mujeres", "men", "hombres"],
        "ENCUESTA_NACIONAL_DE_MEDIO_AMBIENTE": ["environment", "medio ambiente", "climate", "clima"],
        "ENCUESTA_NACIONAL_DE_DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES": ["human rights", "derechos humanos", "discrimination", "discriminación"],
        "ENCUESTA_NACIONAL_DE_JUSTICIA": ["justice", "justicia", "legal system", "sistema legal"],
        "TERCERA_ENCUESTA_NACIONAL_DE_CULTURA_CONSTITUCIONAL": ["constitution", "constitución", "constitutional", "constitucional"]
    }
    
    detected_datasets = []
    
    # Check for explicit dataset mentions
    for dataset_key, keywords in dataset_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            if dataset_key in datasets_info:
                detected_datasets.append(dataset_key)
    
    # If no specific dataset detected, use ALL
    return detected_datasets if detected_datasets else ["ALL"]

# Layout Components
def create_header():
    """Create the dashboard header"""
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Datasets", href="#datasets")),
            dbc.NavItem(dbc.NavLink("Analysis", href="#analysis")),
            dbc.NavItem(dbc.NavLink("Reports", href="#reports")),
        ],
        brand="🔍 Navegador - Survey Analysis Assistant",
        brand_href="#",
        color="primary",
        dark=True,
        className="mb-4"
    )

def create_chat_interface():
    """Create the chat interface panel"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("💬 Chat with Navegador Assistant", className="mb-0"),
            html.Small("Ask questions about datasets, select variables, or run analyses", 
                      className="text-muted")
        ]),
        dbc.CardBody([
            # Chat history display
            html.Div(
                id="chat-history",
                style={
                    "height": "400px",
                    "overflow-y": "auto",
                    "border": "1px solid #dee2e6",
                    "border-radius": "0.375rem",
                    "padding": "10px",
                    "background-color": "#f8f9fa"
                },
                children=[
                    html.Div([
                        html.Strong("🤖 Asistente: "),
                        get_message('welcome', 'es')
                    ], className="mb-2")
                ]
            ),
            # Input area
            html.Div([
                dbc.InputGroup([
                    dbc.Input(
                        id="user-input",
                        placeholder="Type your message here...",
                        type="text",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Send",
                        id="send-button",
                        color="primary",
                        n_clicks=0
                    )
                ], className="mt-3")
            ]),
            # Quick action buttons
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button("📊 List Datasets", id="btn-datasets", size="sm", outline=True),
                    dbc.Button("🔍 Search Variables", id="btn-variables", size="sm", outline=True),
                    dbc.Button("📈 Run Analysis", id="btn-analysis", size="sm", outline=True),
                    dbc.Button("🔄 Reset", id="btn-reset", size="sm", outline=True, color="secondary")
                ], className="mt-2")
            ])
        ])
    ], className="h-100")

def create_session_panel():
    """Create the session information panel"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("📋 Current Session", className="mb-0"),
            html.Small("Track your selected datasets, variables, and analysis type", 
                      className="text-muted")
        ]),
        dbc.CardBody([
            # Datasets section
            html.Div([
                html.H6("📂 Datasets", className="text-primary"),
                html.Div(id="session-datasets", children=[
                    html.Small("No datasets selected", className="text-muted")
                ])
            ], className="mb-3"),
            
            # Variables section
            html.Div([
                html.H6("📊 Variables", className="text-primary"),
                html.Div(id="session-variables", children=[
                    html.Small("No variables selected", className="text-muted")
                ])
            ], className="mb-3"),
            
            # Analysis type section
            html.Div([
                html.H6("⚙️ Analysis Type", className="text-primary"),
                html.Div(id="session-analysis-type", children=[
                    html.Small("No analysis type selected", className="text-muted")
                ])
            ], className="mb-3"),
            
            # Action buttons
            html.Div([
                dbc.Button(
                    "📥 Export Session",
                    id="btn-export",
                    color="info",
                    size="sm",
                    className="me-2"
                ),
                dbc.Button(
                    "🗑️ Clear Session",
                    id="btn-clear",
                    color="warning",
                    size="sm",
                    outline=True
                )
            ])
        ])
    ], className="h-100")

def create_report_panel():
    """Create the report display panel"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("📑 Analysis Report", className="mb-0"),
            html.Small("View and download your analysis results", className="text-muted")
        ]),
        dbc.CardBody([
            # Report content
            html.Div(
                id="report-content",
                style={
                    "min-height": "300px",
                    "border": "1px solid #dee2e6",
                    "border-radius": "0.375rem",
                    "padding": "15px",
                    "background-color": "#ffffff"
                },
                children=[
                    html.Div([
                        html.I(className="fas fa-file-alt fa-3x text-muted mb-3"),
                        html.H6("No report generated yet", className="text-muted"),
                        html.P("Run an analysis to see results here", className="text-muted")
                    ], className="text-center mt-5")
                ]
            ),
            
            # Download buttons
            html.Div([
                dbc.Button(
                    [html.I(className="fas fa-download me-2"), "Download PDF"],
                    id="btn-download-pdf",
                    color="success",
                    size="sm",
                    disabled=True
                ),
                dcc.Download(id="download-pdf")
            ], className="mt-3")
        ])
    ], className="h-100")

def create_performance_panel():
    """Create the performance monitoring panel"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("⚡ Performance Monitor", className="mb-0"),
            html.Small("Cache statistics and system performance", className="text-muted")
        ]),
        dbc.CardBody([
            # Cache statistics
            html.Div([
                html.H6("💾 Cache Statistics", className="text-primary"),
                html.Div(id="cache-stats", children=[
                    html.Small("Loading cache statistics...", className="text-muted")
                ])
            ], className="mb-3"),
            
            # Performance metrics
            html.Div([
                html.H6("📊 Performance Metrics", className="text-primary"),
                html.Div(id="performance-metrics", children=[
                    html.Small("No metrics available", className="text-muted")
                ])
            ], className="mb-3"),
            
            # Control buttons
            html.Div([
                dbc.Button(
                    "🔄 Refresh Stats",
                    id="btn-refresh-stats",
                    color="info",
                    size="sm",
                    className="me-2"
                ),
                dbc.Button(
                    "🗑️ Clear Cache",
                    id="btn-clear-cache",
                    color="warning",
                    size="sm",
                    outline=True
                )
            ])
        ])
    ], className="h-100")

# Main layout
app.layout = dbc.Container([
    # Store components for session data
    dcc.Store(id="session-store", data=current_session),
    dcc.Store(id="chat-store", data=chat_history),
    # Add a hidden interval for automating next step after pre-action message
    # Higher interval (2000ms instead of 1000ms) and ensure it's disabled by default
    dcc.Interval(id="auto-next-step-interval", interval=15000, n_intervals=0, disabled=True, max_intervals=10),  # 15 seconds interval (increased from 2)
    dcc.Interval(id="cleanup-interval", interval=1*1000, n_intervals=0, disabled=False),  # 1 second interval for cleanup
    
    # Header
    create_header(),
    
    # Main content
    dbc.Row([
        # Left column - Chat interface (expanded)
        dbc.Col([
            create_chat_interface()
        ], width=6),
        
        # Middle column - Session panel (temporarily hidden)
        # dbc.Col([
        #     create_session_panel()
        # ], width=3),
        
        # Right column - Report panel (expanded)
        dbc.Col([
            create_report_panel()
        ], width=6)
    ], className="g-3"),
    
    # Performance monitoring toggle button
    dbc.Row([
        dbc.Col([
            dbc.Button(
                [html.I(className="fas fa-chart-line me-2"), "Show Performance Monitor"],
                id="btn-toggle-performance",
                color="info",
                size="sm",
                outline=True,
                className="mb-2"
            )
        ])
    ], className="g-3 mt-2"),
    
    # Performance monitoring row (collapsed by default)
    dbc.Row([
        dbc.Col([
            dbc.Collapse(
                create_performance_panel(),
                id="collapse-performance",
                is_open=False
            )
        ])
    ], className="g-3"),
    
    # Footer
    html.Hr(className="mt-5"),
    html.Footer([
        html.P([
            "Navegador Survey Analysis Dashboard | ",
            html.A("Documentation", href="#", className="text-decoration-none"),
            " | ",
            html.A("Support", href="#", className="text-decoration-none")
        ], className="text-center text-muted small")
    ])
], fluid=True)

# Callbacks

@app.callback(
    [Output("chat-history", "children", allow_duplicate=True),
     Output("chat-store", "data", allow_duplicate=True),
     Output("user-input", "value", allow_duplicate=True),
     Output("session-store", "data", allow_duplicate=True),
     Output("auto-next-step-interval", "disabled", allow_duplicate=True)],
    [Input("send-button", "n_clicks"),
     Input("btn-datasets", "n_clicks"),
     Input("btn-variables", "n_clicks"),
     Input("btn-analysis", "n_clicks"),
     Input("btn-reset", "n_clicks"),
     Input("user-input", "n_submit")],
    [State("user-input", "value"),
     State("chat-store", "data"),
     State("session-store", "data")],
    prevent_initial_call=True
)
def handle_chat_interaction(send_clicks, datasets_clicks, variables_clicks, 
                           analysis_clicks, reset_clicks, input_submit,
                           user_message, chat_data, session_data):
    """Handle all chat interactions and quick action buttons"""
    
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle reset button
    if triggered_id == "btn-reset":
        new_chat = [{
            "type": "assistant",
            "content": get_message('session_reset', 'es'),  # Default to Spanish for reset
            "timestamp": datetime.now().strftime("%H:%M")
        }]
        new_session = {
            'datasets': ["ALL"],  # Default to using all datasets
            'variables': [],
            'analysis_type': None,
            'last_report': None,
            'agent_state': {},
            'language': 'es'  # Reset to default Spanish
        }
        return format_chat_history(new_chat), new_chat, "", new_session, True
    
    # TODO: remove these buttons and logic for a basic UI, leave them for a more analytic UI
    # Determine user message based on trigger
    if triggered_id == "btn-datasets":
        user_message = "List available datasets"
    elif triggered_id == "btn-variables":
        user_message = "Help me search for variables"
    elif triggered_id == "btn-analysis":
        user_message = "I want to run an analysis"
    elif not user_message or user_message.strip() == "":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
    
    # Detect user language and update session
    detected_lang = detect_language(user_message)
    session_data['language'] = detected_lang
    
    # Add user message to chat
    new_chat_data = chat_data.copy() if chat_data else []
    new_chat_data.append({
        "type": "user",
        "content": user_message,
        "timestamp": datetime.now().strftime("%H:%M")
    })
    
    # Get agent response
    try:
        if agent:
            # Enhanced query processing - extract search keywords and detect dataset preference
            search_keywords = extract_search_keywords(user_message, detected_lang)
            preferred_datasets = detect_dataset_preference(user_message, detected_lang)

            print(f"🔍 Original query: '{user_message}'")
            print(f"🎯 Search keywords: '{search_keywords}'")
            print(f"📊 Preferred datasets: {preferred_datasets}")
            
            # Log the query event with detailed information
            log_dashboard_event('query_received', {
                'query': user_message,
                'search_keywords': search_keywords,
                'preferred_datasets': str(preferred_datasets),
                'language': detected_lang
            })

            # Update session with extracted information
            session_data['search_keywords'] = search_keywords
            session_data['preferred_datasets'] = preferred_datasets

            # --- NEW: Add pre-action message to chat history and RETURN immediately ---
            try:
                # Try to get a more accurate intent classification if the modules are available
                try:
                    from intent_classifier import intent_dict, _classify_intent
                    from langchain_openai import ChatOpenAI
                    llm = ChatOpenAI(model="gpt-4o-mini")
                    intent = _classify_intent(user_message, intent_dict, llm)
                    print(f"🎯 Classified intent: {intent}")
                except Exception as e:
                    print(f"⚠️ Error in intent classification: {e}")
                    # Fallback to a simpler method
                    if "variable" in user_message.lower():
                        intent = "query_variable_database"
                    elif "analys" in user_message.lower() or "analyze" in user_message.lower():
                        intent = "run_analysis"
                    else:
                        intent = "answer_general_questions"
                
                # Save the intent in session data for use in handle_auto_next_step
                session_data["intent"] = intent
                
                # Generate a pre-action message based on the intent
                pre_action_message = None
                if intent == "query_variable_database":
                    pre_action_message = get_message('variables_found', detected_lang, query=search_keywords) or "Searching for variables..."
                elif intent == "run_analysis":
                    pre_action_message = get_message('analysis_types', detected_lang) or "Running analysis..."
                elif intent == "answer_general_questions":
                    pre_action_message = get_message('datasets_title', detected_lang) or "Listing datasets..."
                # Add more intent cases as needed
                
                if pre_action_message:
                    # Add the message to chat history
                    new_chat_data.append({
                        "type": "assistant",
                        "content": pre_action_message,
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                    
                    # Set up the pending action with all necessary data
                    import time
                    import uuid
                    request_id = str(uuid.uuid4())  # Generate unique ID for this request
                    session_data['pending_main_action'] = {
                        'user_message': user_message,
                        'search_keywords': search_keywords,
                        'preferred_datasets': preferred_datasets,
                        'intent': intent,
                        'timestamp': time.time(),  # Add timestamp for expiration check
                        'request_id': request_id,  # Add unique request ID for tracking
                        'processed': False  # Flag to track if this request has been processed
                    }
                    
                    print(f"⏱️ Enabling auto-next-step-interval with message: '{user_message}'")
                    
                    # Ensure the interval is enabled (disabled=False) only if agent is available
                    if agent is not None or not MODULES_AVAILABLE:
                        # If agent is available or we're in mock mode, enable the interval and RETURN IMMEDIATELY
                        print("🔄 Returning with auto-next-step interval ENABLED")
                        return format_chat_history(new_chat_data), new_chat_data, "", session_data, False
                    else:
                        # If agent isn't available, don't enable the interval and show error
                        session_data.pop('pending_main_action', None)  # Remove the pending action
                        error_msg = get_message('agent_unavailable', session_data.get('language', 'es'))
                        new_chat_data.append({
                            "type": "assistant",
                            "content": error_msg,
                            "timestamp": datetime.now().strftime("%H:%M")
                        })
                        return format_chat_history(new_chat_data), new_chat_data, "", session_data, True
            except Exception as e:
                print(f"⚠️ Error in pre-action processing: {e}")
                import traceback
                traceback.print_exc()
            # --- END NEW ---

            # This code should never be reached if pre-action message was added,
            # as we should have returned already
            print("⚠️ WARNING: No pre-action message was set, proceeding with direct agent response")
            
            # Process query with enhanced information
            response = get_agent_response(user_message, session_data, search_keywords, preferred_datasets)

            # Update session data based on response
            updated_session = update_session_from_response(session_data, response)
        else:
            response = {
                "content": get_message('agent_unavailable', detected_lang),
                "session_updates": {}
            }
            updated_session = session_data
            
    except Exception as e:
        response = {
            "content": get_message('error_occurred', detected_lang, error=str(e)),
            "session_updates": {}
        }
        updated_session = session_data
    
    # Add assistant response to chat
    new_chat_data.append({
        "type": "assistant",
        "content": response["content"],
        "timestamp": datetime.now().strftime("%H:%M")
    })
    
    return format_chat_history(new_chat_data), new_chat_data, "", updated_session, True

# Adding the proper handle_auto_next_step callback implementation
# Replacement for handle_auto_next_step function

@app.callback(
    [Output("chat-history", "children"),
     Output("chat-store", "data"),
     Output("user-input", "value"),
     Output("session-store", "data", allow_duplicate=True),
     Output("auto-next-step-interval", "disabled", allow_duplicate=True)],
    [Input("auto-next-step-interval", "n_intervals")],
    [State("chat-store", "data"),
     State("session-store", "data")],
    prevent_initial_call=True
)
def handle_auto_next_step(n_intervals, chat_data, session_data):
    """Handle automatic next step after pre-action message"""
    
    # Safety mechanism: max number of intervals before auto-disabling
    MAX_INTERVALS = 10  # Increased from 5 to handle longer operations
    
    # Ensure we have session_data to work with
    if session_data is None:
        print("⚠️ Session data is None, skipping auto-next-step")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
    
    # Make a copy of session data to ensure we're not modifying the original
    session_data = session_data.copy()
    
    if n_intervals is not None and n_intervals > MAX_INTERVALS:
        print(f"⚠️ Auto-next-step reached maximum intervals ({MAX_INTERVALS}), forcing disable")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
    
    # Get access to global agent
    global agent
    
    # Detailed logging to understand function flow
    pending_action = session_data.get('pending_main_action', {})
    request_id = pending_action.get('request_id', 'none')
    processed = pending_action.get('processed', False)
    
    print(f"🔄 handle_auto_next_step called with n_intervals={n_intervals}")
    print(f"   request_id: {request_id}")
    print(f"   processed: {processed}")
    print(f"   agent available: {agent is not None}")
    
    # Skip if the action has already been processed
    if pending_action.get('processed', False):
        print("🔄 Pending action already processed, stopping interval")
        return dash.no_update, dash.no_update, dash.no_update, session_data, True
    
    # Check for missing action or expired timeout
    current_time = time.time()
    action_timestamp = pending_action.get('timestamp', 0)
    timeout_seconds = 180  # Expire pending actions after 180 seconds (increased from 60)  # Expire pending actions after 60 seconds (increased from 30) (increased from 10 to allow more processing time)
    
    if (n_intervals is None or 
        not pending_action or 
        current_time - action_timestamp > timeout_seconds):
        
        if pending_action:
            print(f"⏭️ Pending action expired (age: {current_time - action_timestamp:.1f}s)")
            # Mark as processed instead of removing
            session_data['pending_main_action']['processed'] = True
            session_data['pending_main_action']['processed_at'] = time.time()
            
            # Add a timeout message to the chat history
            timeout_message = "The variable search is taking longer than expected. Please wait while we continue processing your query... This may take up to 3 minutes for complex searches."
            new_chat_data = chat_data.copy() if chat_data else []
            new_chat_data.append({
                "type": "assistant",
                "content": timeout_message,
                "timestamp": datetime.now().strftime("%H:%M"),
                "is_progress": True  # Mark as progress message
            })
            return format_chat_history(new_chat_data), new_chat_data, "", session_data, True
        else:
            print("⏭️ No pending action, skipping auto-next-step")
            # Always disable the interval when there's no action
            return dash.no_update, dash.no_update, dash.no_update, session_data, True
    
    try:
        # Get the pending action details
        user_message = pending_action.get('user_message', '')
        search_keywords = pending_action.get('search_keywords', '')
        preferred_datasets = pending_action.get('preferred_datasets', [])
        intent = pending_action.get('intent', '')
        request_id = pending_action.get('request_id', str(uuid.uuid4()))
        
        print(f"🔄 Executing pending main action for: '{user_message}'")
        print(f"   Intent: {intent}")
        print(f"   Search keywords: {search_keywords}")
        print(f"   Preferred datasets: {preferred_datasets}")
        
        # Log the step with detailed information
        log_dashboard_event('processing_query', {
            'query': user_message,
            'intent': intent,
            'search_keywords': search_keywords,
            'preferred_datasets': str(preferred_datasets),
            'request_id': request_id,
            'interval': n_intervals
        })
        
        # First try to use the agent if available
        if agent and MODULES_AVAILABLE:
            try:
                # Create state manually for safety
                detected_lang = session_data.get('language', 'es')
                
                # Import the state_normalizer module
                state_normalizer_module = None
                try:
                    import state_normalizer
                    state_normalizer_module = state_normalizer
                    print("✅ Successfully imported state_normalizer module")
                except ImportError:
                    print("⚠️ state_normalizer module not available")
                
                if state_normalizer_module:
                    # Use the state_normalizer
                    try:
                        agent_state = state_normalizer_module.create_agent_state(
                            user_message=user_message,
                            intent=intent or "query_variable_database",  # Default to variable search
                            dataset=preferred_datasets or session_data.get("datasets", ["ALL"]),
                            selected_variables=session_data.get("variables", []),
                            language=detected_lang
                        )
                    except Exception as normalizer_err:
                        print(f"⚠️ Error using state_normalizer: {normalizer_err}")
                        # Fallback to manual creation
                        agent_state = {
                            "messages": [{"role": "user", "content": user_message}],
                            "intent": intent or "query_variable_database",
                            "user_query": user_message,
                            "original_query": user_message,
                            "dataset": preferred_datasets or session_data.get("datasets", ["ALL"]),
                            "selected_variables": session_data.get("variables", []),
                            "analysis_type": session_data.get("analysis_type", "descriptive"),
                            "user_approved": False,
                            "analysis_result": {}
                        }
                else:
                    # Create state manually
                    agent_state = {
                        "messages": [{"role": "user", "content": user_message}],
                        "intent": intent or "query_variable_database",
                        "user_query": user_message,
                        "original_query": user_message,
                        "dataset": preferred_datasets or session_data.get("datasets", ["ALL"]),
                        "selected_variables": session_data.get("variables", []),
                        "analysis_type": session_data.get("analysis_type", "descriptive"),
                        "user_approved": False,
                        "analysis_result": {},
                        "language": detected_lang
                    }
                
                print(f"🤖 Invoking agent with state: {json.dumps(agent_state, indent=2)[:200]}...")
                
                # Create thread config
                thread_id = f"chat_{int(time.time())}"
                
                # Use the built-in create_agent_config function which should handle normalization internally
                agent_config = create_agent_config(thread_id)
                
                # Invoke agent with properly normalized state and config
                print(f"🔄 Invoking agent for query: '{user_message}'...")
                print(f"🔄 Agent invocation starting at: {datetime.now().strftime('%H:%M:%S.%f')}")
                
                start_time = time.time()
                try:
                    agent_response = agent.invoke(agent_state, config=agent_config)
                    elapsed_time = time.time() - start_time
                    print(f"✅ Agent response received after {elapsed_time:.2f} seconds: {type(agent_response)}")
                    print(f"✅ Agent invocation completed at: {datetime.now().strftime('%H:%M:%S.%f')}")
                except Exception as agent_error:
                    print(f"❌ Agent invocation failed after {time.time() - start_time:.2f} seconds with error: {agent_error}")
                    raise agent_error
                
                # Process response to extract content and session updates
                if isinstance(agent_response, dict):
                    # Extract content from messages or other fields
                    ai_messages = []
                    
                    # Handle different message formats (dict, AIMessage, or other objects)
                    for msg in agent_response.get("messages", []):
                        is_assistant = False
                        
                        # Check if it's a dictionary
                        if isinstance(msg, dict) and msg.get("role") == "assistant":
                            is_assistant = True
                        # Check if it's a LangChain message object
                        elif hasattr(msg, "type") and getattr(msg, "type", "") == "ai":
                            is_assistant = True
                        # Handle AIMessage from langchain
                        elif type(msg).__name__ == "AIMessage":
                            is_assistant = True
                        
                        if is_assistant:
                            ai_messages.append(msg)
                    
                    if ai_messages:
                        content = (
                            ai_messages[-1].get("content", "") 
                            if isinstance(ai_messages[-1], dict) 
                            else getattr(ai_messages[-1], "content", str(ai_messages[-1]))
                        )
                    else:
                        content = agent_response.get('content', agent_response.get('output', str(agent_response)))
                    
                    # Create a dict for session updates with properly typed fields
                    session_updates: Dict[str, Any] = {
                        "language": detected_lang,
                        "intent": intent
                    }
                    
                    try:
                        # Add any specific session updates based on the agent response
                        if intent == "ask_for_datasets":
                            datasets_info = get_available_datasets()
                            if isinstance(datasets_info, dict):
                                dataset_list = list(datasets_info.keys())
                                session_updates["datasets"] = dataset_list
                                print(f"✅ Set session datasets to: {dataset_list}")
                        
                        # If there are variables selected in the agent response, store them
                        if isinstance(agent_response, dict) and "selected_variables" in agent_response:
                            variables = agent_response.get("selected_variables")
                            if variables:
                                session_updates["variables"] = variables
                                print(f"✅ Set session variables to: {variables}")
                                
                                # Modify content to include the variables list
                                variables_formatted = "\n".join([f"• {var}" for var in variables])
                                
                                # Check if content already mentions variables but doesn't list them
                                if "relevant variables" in content and "•" not in content.split("relevant variables")[1].split("\n")[0]:
                                    # Replace the placeholder with actual variables
                                    content_parts = content.split("relevant variables:")
                                    if len(content_parts) > 1:
                                        content = content_parts[0] + "relevant variables:\n\n" + variables_formatted + "\n\n" + "\n".join(content_parts[1].split("\n")[1:])
                                else:
                                    # Append the variables section if not already mentioned
                                    content += f"\n\n**Selected Variables:**\n\n{variables_formatted}"
                        
                        # If there is analysis_type in the agent response, store it
                        if isinstance(agent_response, dict) and "analysis_type" in agent_response:
                            analysis = agent_response.get("analysis_type")
                            if analysis:
                                session_updates["analysis_type"] = analysis
                                print(f"✅ Set session analysis_type to: {analysis}")
                    except Exception as update_err:
                        print(f"⚠️ Error setting session updates: {update_err}")
                    
                    # Process the content into the chat data structure
                    new_chat_data = chat_data.copy() if chat_data else []
                    new_chat_data.append({
                        "type": "assistant",
                        "content": content,
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                    
                    # Update session data with our updates
                    session_data_copy = session_data.copy()
                    for key, value in session_updates.items():
                        session_data_copy[key] = value
                    
                    # Mark the action as processed
                    if 'pending_main_action' in session_data_copy:
                        session_data_copy['pending_main_action']['processed'] = True
                        session_data_copy['pending_main_action']['processed_at'] = time.time()
                    
                    # Return properly formatted tuple as expected by the callback
                    return format_chat_history(new_chat_data), new_chat_data, "", session_data_copy, True
                else:
                    # Handle non-dict response
                    content = str(agent_response)
                    session_updates = {
                        "language": detected_lang,
                        "intent": intent
                    }
                    
                    # Process the content into the chat data structure
                    new_chat_data = chat_data.copy() if chat_data else []
                    new_chat_data.append({
                        "type": "assistant",
                        "content": content,
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                    
                    # Update session data with our updates
                    session_data_copy = session_data.copy()
                    for key, value in session_updates.items():
                        session_data_copy[key] = value
                    
                    # Mark the action as processed
                    if 'pending_main_action' in session_data_copy:
                        session_data_copy['pending_main_action']['processed'] = True
                        session_data_copy['pending_main_action']['processed_at'] = time.time()
                    
                    # Return properly formatted tuple as expected by the callback
                    return format_chat_history(new_chat_data), new_chat_data, "", session_data_copy, True
                
                print(f"✅ Processed agent response")
                
            except Exception as agent_err:
                print(f"⚠️ Agent error in auto-next-step: {agent_err}")
                traceback.print_exc()
                
                # Create a fallback error response
                error_msg = f"Sorry, I encountered an error processing your request: {str(agent_err)[:100]}... Please try again."
                
                # Add error message to chat
                new_chat_data = chat_data.copy() if chat_data else []
                new_chat_data.append({
                    "type": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                # Update session data and mark as processed
                session_data_copy = session_data.copy()
                session_data_copy["last_error"] = str(agent_err)
                
                if 'pending_main_action' in session_data_copy:
                    session_data_copy['pending_main_action']['processed'] = True
                    session_data_copy['pending_main_action']['processed_at'] = time.time()
                    session_data_copy['pending_main_action']['error'] = str(agent_err)
                
                # Return formatted error response
                return format_chat_history(new_chat_data), new_chat_data, "", session_data_copy, True
        else:
            # Create a response for when agent is unavailable
            unavailable_msg = "The AI agent is currently initializing or unavailable. Please try again in a moment."
            
            # Add message to chat
            new_chat_data = chat_data.copy() if chat_data else []
            new_chat_data.append({
                "type": "assistant", 
                "content": unavailable_msg,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Update session data and mark as processed
            session_data_copy = session_data.copy()
            if 'pending_main_action' in session_data_copy:
                session_data_copy['pending_main_action']['processed'] = True
                session_data_copy['pending_main_action']['processed_at'] = time.time()
                session_data_copy['pending_main_action']['error'] = "Agent unavailable"
            
            print(f"⚠️ Agent unavailable, returning fallback message")
            return format_chat_history(new_chat_data), new_chat_data, "", session_data_copy, True
        
        # At this point we should have already handled the response and returned,
        # but we'll add this as a fallback just in case
        print("⚠️ WARNING: Reached fallback code path in handle_auto_next_step")
        new_chat_data = chat_data.copy() if chat_data else []
        new_chat_data.append({
            "type": "assistant",
            "content": "I processed your request but encountered an issue with the response formatting. Please try again.",
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        # Update session as a fallback
        session_data_copy = session_data.copy()
        if 'pending_main_action' in session_data_copy:
            session_data_copy['pending_main_action']['processed'] = True
            session_data_copy['pending_main_action']['processed_at'] = time.time()
        
        # Mark the pending action as processed
        if 'pending_main_action' in session_data_copy:
            print(f"🏁 Marking pending action as processed")
            session_data_copy['pending_main_action']['processed'] = True
            process_time = time.time()
            session_data_copy['pending_main_action']['processed_at'] = process_time
            
            # Calculate and store completion time
            action_timestamp = session_data_copy['pending_main_action'].get('timestamp', process_time)
            completion_time = process_time - action_timestamp
            session_data_copy['pending_main_action']['completion_time'] = completion_time
            
            # Log successful query completion with details
            log_dashboard_event('query_completed', {
                'query': session_data_copy['pending_main_action'].get('user_message', 'unknown'),
                'intent': session_data_copy['pending_main_action'].get('intent', 'unknown'),
                'completion_time_sec': round(completion_time, 2),
                'request_id': session_data_copy['pending_main_action'].get('request_id', 'unknown'),
                'selected_variables_count': len(session_data_copy.get('variables', [])),
                'datasets': str(session_data_copy.get('datasets', [])),
                'success': True
            })
        
        # Return the updated UI state
        print("✅ Auto-next-step completed successfully")
        return format_chat_history(new_chat_data), new_chat_data, "", session_data_copy, True
        
    except Exception as e:
        print(f"❌ Error in handle_auto_next_step: {e}")
        traceback.print_exc()
        
        try:
            # Add error message to chat
            error_msg = get_message('error_occurred', session_data.get('language', 'es'), error=str(e))
            new_chat_data = chat_data.copy() if chat_data else []
            new_chat_data.append({
                "type": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Mark pending action as processed to prevent getting stuck
            session_data_copy = session_data.copy() if session_data else {}
            if 'pending_main_action' in session_data_copy:
                    print(f"🏁 Marking pending action as processed (error handling path)")
                    session_data_copy['pending_main_action']['processed'] = True
                    process_time = time.time()
                    session_data_copy['pending_main_action']['processed_at'] = process_time
                    
                    # Calculate time spent on failed request
                    action_timestamp = session_data_copy['pending_main_action'].get('timestamp', process_time)
                    error_time = process_time - action_timestamp
                    session_data_copy['pending_main_action']['error_time'] = error_time
                    
                    # Log the error event for monitoring
                    log_dashboard_event('query_error', {
                        'query': session_data_copy['pending_main_action'].get('user_message', 'unknown'),
                        'error': str(e),
                        'processing_time_sec': round(error_time, 2),
                        'request_id': session_data_copy['pending_main_action'].get('request_id', 'unknown'),
                        'success': False
                    })
                
            # Always disable the interval (disabled=True) to stop the cycling
            return format_chat_history(new_chat_data), new_chat_data, "", session_data_copy, True
            
        except Exception as nested_error:
            # Failsafe to ensure interval is disabled even if error handling itself fails
            print(f"❌❌ Critical error in error handling: {nested_error}")
            # Return minimal updates, but ensure interval is disabled
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
# Add agent event logging for monitoring
def log_dashboard_event(event_type, details, run_id=None):
    """
    Logs dashboard events to console and LangSmith if available
    
    Args:
        event_type (str): Type of event (e.g., 'query_received', 'agent_response')
        details (dict): Event details
        run_id (str, optional): LangSmith run ID to associate with this event
    """
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "details": details
    }
    
    # Print to console with timestamp
    print(f"📝 [{timestamp}] DASHBOARD {event_type}: {details}")
    
    # Log to LangSmith if available
    if langsmith_client:
        try:
            # Add feedback to LangSmith project
            metadata = {
                "event_type": event_type,
                "timestamp": timestamp,
                **{f"detail_{k}": str(v) for k, v in details.items()}
            }
            
            if run_id:
                # Use the API that's available in the current version
                langsmith_client.create_feedback(
                    run_id=run_id,
                    key=f"dashboard_event_{event_type}",
                    value=event_type,
                    comment=str(details),
                    metadata=metadata
                )
        except Exception as e:
            print(f"⚠️ Error logging to LangSmith: {e}")
# Standard library imports
import os
import sys
import time
import uuid
import json
import inspect
import threading
import traceback
from typing import Dict, Any, List, Optional, Tuple, Union, Callable

# Third-party imports - handle gracefully
try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from dash import Dash, html, dcc, callback, Output, Input, State, no_update
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    from datetime import datetime
    
    # Application-specific modules
    # Import with error handling to avoid crashing
    try:
        # Import dataset_knowledge module first and verify it loads properly
        import dataset_knowledge
        print("✅ dataset_knowledge module imported successfully")
        print(f"🔍 Available objects in dataset_knowledge: {[k for k in dir(dataset_knowledge) if not k.startswith('_')]}")
        
        # Now import specific objects
        from dataset_knowledge import rev_topic_dict, tmp_topic_st, _project_describer, pregs_dict
        
        # Import other required modules
        from variable_selector import _variable_selector, _database_selector
        from run_analysis import run_analysis
        
        # Verify rev_topic_dict is loaded correctly (this should be rev_topic_dict instead of rev_enc_nom_dict)
        if hasattr(dataset_knowledge, 'rev_topic_dict'):
            print(f"✅ rev_topic_dict loaded correctly with {len(dataset_knowledge.rev_topic_dict)} items")
        else:
            print("⚠️ rev_topic_dict not found in dataset_knowledge")
            
        # Flag that modules are available
        MODULES_AVAILABLE = True
    except Exception as module_err:
        print(f"⚠️ Some application modules could not be imported: {module_err}")
        print("The dashboard will run in limited functionality mode")
        traceback.print_exc()
        MODULES_AVAILABLE = False
    
except Exception as e:
    print(f"❌ Error importing required libraries: {e}")
    # Define fallback functions for exception handling


# Add server run code to ensure the dashboard continues running
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Starting Navegador Dashboard Server...")
    print("📊 Dashboard will be available at: http://localhost:8050")
    print("💡 Press Ctrl+C to stop the server")
    print("="*80 + "\n")
    
    print("👉 The dashboard will continue to load even if agent initialization is still running.")
    print("👉 You can access the dashboard in your browser while the agent completes setup.")
    
    # Use verbose mode to see more information about the server
    # and set threaded=True to avoid blocking
    try:
        app.run(debug=False, port=8050, host="127.0.0.1", use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard server stopped by user")
    except Exception as e:
        print(f"\n❌ Error running dashboard server: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if port 8050 is already in use")
        print("2. Try running with a different port: app.run(port=8051)")
        print("3. Check error logs above for details")
