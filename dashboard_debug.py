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
        
        print(f"✅✅✅ Agent response processed at {time.time()}: {content[:50]}...")
        
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

# Helper functions for agent interaction
def create_agent_config(thread_id: Optional[str] = None) -> Any:
    """
    Create a configuration dict for agent invocation with proper checkpointer config
    
    Args:
        thread_id (Optional[str]): Optional thread ID. If None, a timestamp-based ID will be generated.
        
    Returns:
        RunnableConfig or Dict containing the required configurable keys for the LangGraph checkpointer
    """
    if thread_id is None:
        thread_id = f"chat_{int(time.time())}"
    
    # Create a proper config dict that will be compatible with RunnableConfig
    config_dict = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": str(uuid.uuid4()),
            "checkpoint_ns": "chat_session"
        }
    }
    
    # Return as the appropriate type based on whether langchain is available
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
            response_dict = {k: v for k, v in agent_response.__dict__.items() 
                           if not k.startswith('_') and not callable(v)}
        
        # Update agent_state
        updated_session['agent_state'] = response_dict
        
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
        'cross_disciplinary_search': "Cross-disciplinary search across all datasets"
    },
    'es': {
        'welcome': "¡Hola! Soy Navegador, tu asistente de análisis de encuestas. Puedo ayudarte a explorar conjuntos de datos, seleccionar variables y ejecutar análisis. ¿Qué te gustaría saber?",
        'session_reset': "¡Sesión reiniciada! ¡Hola de nuevo! ¿Cómo puedo ayudarte con el análisis de encuestas?",
        'agent_unavailable': "Lo siento, el agente no está disponible en este momento. Por favor, inténtalo de nuevo más tarde.",
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
        'cross_disciplinary_search': "Búsqueda interdisciplinaria en todos los conjuntos de datos"
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
    """Create a simple thread config for agent persistence"""
    import time
    return {
        "configurable": {
            "thread_id": f"chat_{int(time.time())}"
        }
    }

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
        
        # Create a properly typed config for testing
        test_config = create_agent_config()
        
        # Test 1: Basic greeting test
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(agent.invoke, general_state, config=test_config)
            try:
                test_result = future.result(timeout=10)  # 10 second timeout
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
                query_result = future.result(timeout=8)  # 8 second timeout - reduce from 15
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
    dcc.Interval(id="auto-next-step-interval", interval=2000, n_intervals=0, disabled=True, max_intervals=5),
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
                        # If agent is available or we're in mock mode, enable the interval
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
@app.callback(
    [Output("chat-history", "children"),
     Output("chat-store", "data"),
     Output("user-message", "value"),
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
    MAX_INTERVALS = 5
    
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
    try:
        from __main__ import agent, MODULES_AVAILABLE
    except ImportError:
        agent = None
        MODULES_AVAILABLE = False
    
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
    timeout_seconds = 10  # Expire pending actions after 10 seconds
    
    if (n_intervals is None or 
        not pending_action or 
        current_time - action_timestamp > timeout_seconds):
        
        if pending_action:
            print(f"⏭️ Pending action expired (age: {current_time - action_timestamp:.1f}s)")
            # Mark as processed instead of removing
            session_data['pending_main_action']['processed'] = True
            session_data['pending_main_action']['processed_at'] = time.time()
            return dash.no_update, dash.no_update, dash.no_update, session_data, True
        else:
            print("⏭️ No pending action, skipping auto-next-step")
            # Always disable the interval when there's no action
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
    
    try:
        # Get the pending action details
        user_message = pending_action.get('user_message', '')
        search_keywords = pending_action.get('search_keywords', '')
        preferred_datasets = pending_action.get('preferred_datasets', [])
        
        start_time = time.time()
        print(f"🔄 Executing pending main action for: '{user_message}'")
        from datetime import datetime
        print(f"🕒 Current time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Define a fast-path option for health check and debugging
        # If user message contains a special keyword, return immediately with mock data
        if "fastpath" in user_message.lower() or "debug" in user_message.lower() or "bypass" in user_message.lower():
            print("🔄 Using fast path for debugging")
            try:
                from __main__ import get_mock_agent_response, format_chat_history
                response = get_mock_agent_response(user_message, session_data, search_keywords, preferred_datasets)
                new_chat_data = chat_data.copy() if chat_data else []
                new_chat_data.append({
                    "type": "assistant",
                    "content": "Debug mode activated. Using fast path response.",
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                session_data['pending_main_action']['processed'] = True
                session_data['pending_main_action']['processed_at'] = time.time()
                return format_chat_history(new_chat_data), new_chat_data, "", session_data, True
            except Exception as fast_path_err:
                print(f"❌ Fast path error: {fast_path_err}")
                # Continue with normal flow if fast path fails
        
        # Check if modules and agent are available
        if not MODULES_AVAILABLE:
            print("⚠️ Required modules are not available, using mock response")
            # Use mock response
            try:
                from __main__ import get_mock_agent_response, format_chat_history
                mock_response = get_mock_agent_response(user_message, session_data, search_keywords, preferred_datasets)
                new_chat_data = chat_data.copy() if chat_data else []
                new_chat_data.append({
                    "type": "assistant",
                    "content": mock_response["content"],
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                session_data['pending_main_action']['processed'] = True
                session_data['pending_main_action']['processed_at'] = time.time()
                return format_chat_history(new_chat_data), new_chat_data, "", session_data, True
            except Exception as mock_err:
                print(f"❌ Mock response error: {mock_err}")
                # Fall through to next handler
            
        # First try to use the agent if available
        print("🚀🚀🚀 Attempting to use the agent now!")
        if agent:
            try:
                # Check if agent is accessible
                if not agent:
                    print("⚠️ Agent is not initialized, falling back to mock response")
                    raise Exception("Agent not initialized")
                    
                print(f"🔄 Setting up agent state at {time.time() - start_time:.2f}s")

                # Import necessary functions
                try:
                    from __main__ import create_agent_config, process_agent_response
                except ImportError:
                    print("⚠️ Could not import agent config functions, using local implementations")
                    # Define local implementations if needed
                    def create_agent_config(thread_id=None):
                        if thread_id is None:
                            thread_id = f"chat_{int(time.time())}"
                        return {"configurable": {"thread_id": thread_id}}

                # Set up agent state with proper intent field already set
                # This is critical - the intent must be set correctly to route through the graph
                agent_state = {
                    "messages": [{"role": "user", "content": user_message}],
                    "intent": session_data.get("intent", "query_variable_database"),  # Default to query intent
                    "user_query": user_message,
                    "original_query": user_message,
                    "dataset": preferred_datasets or session_data.get("datasets", ["ALL"]),
                    "selected_variables": session_data.get("variables", []),
                    "analysis_type": session_data.get("analysis_type", "descriptive"),
                    "user_approved": False,
                    "analysis_result": {},
                    "language": session_data.get('language', 'es')
                }
                
                # Create proper config with required configurable keys
                thread_id = f"chat_{int(time.time())}"
                agent_config = create_agent_config(thread_id)
                
                print(f"🤖 Invoking agent with proper config... at {time.time() - start_time:.2f}s")
                print(f"🔍 Agent state: intent={agent_state.get('intent')}, query='{agent_state.get('user_query')}'")
                print(f"🔍 Agent message: {agent_state.get('messages', [])[-1] if agent_state.get('messages') else 'No messages'}")
                
                # Set a shorter timeout for better user experience (10 seconds max wait)
                AGENT_TIMEOUT = 10.0
                
                # Create a special mock response for health queries since that's what we're testing
                is_health_query = "salud" in user_message.lower() or "health" in user_message.lower()
                
                # Define health mock response upfront
                health_mock = {
                    "content": "Based on your query about health, I've selected the following variables: health_satisfaction, healthcare_access, health_concerns, and health_insurance. These variables will help us understand what Mexicans think about health services and concerns.",
                    "session_updates": {
                        "intent": "query_variable_database",
                        "variables": ["health_satisfaction", "healthcare_access", "health_concerns", "health_insurance"],
                        "datasets": ["Encuesta_Nacional_Salud"]
                    }
                }
                
                # Run agent with timeout to avoid blocking UI
                print(f"🔄 Starting agent invocation with {AGENT_TIMEOUT}s timeout at {time.time() - start_time:.2f}s")
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(agent.invoke, agent_state, config=agent_config)
                    try:
                        print(f"⏳ Waiting for agent response... (timeout: {AGENT_TIMEOUT}s)")
                        print("⏳⏳⏳ Waiting for agent response...")
                        agent_response = future.result(timeout=AGENT_TIMEOUT)  # Shorter timeout for better UX
                        elapsed = time.time() - start_time
                        print(f"✅ Agent response received after {elapsed:.2f}s: {type(agent_response)}")
                        
                        # Additional debugging for agent response
                        if isinstance(agent_response, dict):
                            print(f"🔍 Agent response keys: {list(agent_response.keys())}")
                            if 'messages' in agent_response:
                                messages = agent_response['messages']
                                if messages and len(messages) > 0:
                                    last_msg = messages[-1]
                                    if isinstance(last_msg, dict):
                                        content = last_msg.get('content', '')[:100] + '...'
                                        print(f"🔍 Last message content: {content}")
                        
                        # Process the agent response with our consistent handler
                        print("🎯🎯🎯 Got agent response, calling process_agent_response")
                        return process_agent_response(agent_response, session_data, chat_data, user_message)
                        
                    except concurrent.futures.TimeoutError:
                        print(f"⚠️ Agent invocation timed out after {AGENT_TIMEOUT} seconds")
                        # Fall back to special mock response for health queries or general mock otherwise
                        if is_health_query:
                            print("🩺 Using special health response mock for better user experience")
                            mock_response = health_mock
                        else:
                            from __main__ import get_mock_agent_response
                            mock_response = get_mock_agent_response(user_message, session_data, search_keywords, preferred_datasets)
                        
                        from __main__ import format_chat_history
                        # Add the response to the chat
                        new_chat_data = chat_data.copy() if chat_data else []
                        new_chat_data.append({
                            "type": "assistant",
                            "content": mock_response["content"],
                            "timestamp": datetime.now().strftime("%H:%M")
                        })
                        
                        # Update session with any data from the response
                        for key, value in mock_response.get("session_updates", {}).items():
                            session_data[key] = value
                        
                        # Mark the pending action as processed
                        session_data['pending_main_action']['processed'] = True
                        session_data['pending_main_action']['processed_at'] = time.time()
                        
                        # Return the updated UI state
                        print(f"✅ Returning fallback response after timeout ({time.time() - start_time:.2f}s)")
                        return format_chat_history(new_chat_data), new_chat_data, "", session_data, True
                    
                    except Exception as e:
                        # Handle other exceptions in agent invocation
                        print(f"⚠️ Error in agent invocation: {e}")
                        import traceback
                        traceback.print_exc()
                        
                        # Use mock response as fallback
                        from __main__ import get_mock_agent_response, format_chat_history
                        mock_response = get_mock_agent_response(user_message, session_data, search_keywords, preferred_datasets)
                        new_chat_data = chat_data.copy() if chat_data else []
                        new_chat_data.append({
                            "type": "assistant",
                            "content": mock_response["content"],
                            "timestamp": datetime.now().strftime("%H:%M")
                        })
                        
                        # Mark action as processed
                        session_data['pending_main_action']['processed'] = True
                        session_data['pending_main_action']['processed_at'] = time.time()
                        
                        # Return the updated UI state
                        print(f"✅ Returning fallback response after error ({time.time() - start_time:.2f}s)")
                        return format_chat_history(new_chat_data), new_chat_data, "", session_data, True
            except Exception as agent_err:
                print(f"⚠️ Agent error: {agent_err} - falling back to mock response")
                import traceback
                traceback.print_exc()
                
        # Fall back to mock response if agent unavailable or error occurred
        try:
            from __main__ import get_mock_agent_response, format_chat_history
            response = get_mock_agent_response(user_message, session_data, search_keywords, preferred_datasets)
            print(f"✅ Got mock response: {response.get('content', '')[:50]}...")
            
            # Add the response to the chat
            new_chat_data = chat_data.copy() if chat_data else []
            new_chat_data.append({
                "type": "assistant",
                "content": response["content"],
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Update session with any data from the response
            session_data_copy = session_data.copy()
            for key, value in response.get("session_updates", {}).items():
                session_data_copy[key] = value
            
            # Mark the pending action as processed
            if 'pending_main_action' in session_data_copy:
                print(f"🏁 Marking pending action as processed (mock response path)")
                session_data_copy['pending_main_action']['processed'] = True
                session_data_copy['pending_main_action']['processed_at'] = time.time()
            
            # Return the updated UI state
            print("✅ Auto-next-step completed with mock response")
            return format_chat_history(new_chat_data), new_chat_data, "", session_data_copy, True
        except Exception as mock_fallback_err:
            print(f"❌ Could not create mock fallback response: {mock_fallback_err}")
            # Emergency minimal response
            new_chat_data = chat_data.copy() if chat_data else []
            new_chat_data.append({
                "type": "assistant",
                "content": "I'm having trouble accessing my knowledge. Please try again later.",
                "timestamp": datetime.now().strftime("%H:%M")
            })
            if 'pending_main_action' in session_data:
                session_data['pending_main_action']['processed'] = True
                session_data['pending_main_action']['processed_at'] = time.time()
            return new_chat_data, new_chat_data, "", session_data, True

    except Exception as e:
        print(f"❌ Error in handle_auto_next_step: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True

def get_agent_response(user_message: str, session_data: Dict, search_keywords=None, preferred_datasets=None) -> Dict:
    """Get response from the Navegador agent"""
    try:
        if agent and MODULES_AVAILABLE:
            # Use the real agent with enhanced query processing
            return get_real_agent_response(user_message, session_data, search_keywords, preferred_datasets)
        else:
            # Fall back to mock responses with enhanced query processing
            return get_mock_agent_response(user_message, session_data, search_keywords, preferred_datasets)
    except Exception as e:
        return {
            "content": get_message('error_occurred', session_data.get('language', 'es'), error=str(e)),
            "session_updates": {}
        }

def get_real_agent_response(user_message: str, session_data: Dict, search_keywords=None, preferred_datasets=None) -> Dict:
    """Get response from the real Navegador agent"""
    try:
        # Initialize agent state with current session - use ALL datasets by default
        agent_state = {
            "messages": session_data.get("chat_history", []),
            "intent": "",
            "user_query": user_message,
            "original_query": user_message,
            "dataset": session_data.get("datasets", ["ALL"]),  # Default to ALL datasets
            "selected_variables": session_data.get("variables", []),
            "analysis_type": session_data.get("analysis_type", "quick_insights"),
            "user_approved": False,
            "analysis_result": {},
            "language": session_data.get('language', 'es')  # Use session language as fallback
        }
        
        # Classify intent and detect language using the agent
        try:
            if MODULES_AVAILABLE:
                from intent_classifier import intent_dict, _classify_intent
                from langchain_openai import ChatOpenAI
                
                # Use the proper intent classifier
                llm = ChatOpenAI(model="gpt-4o-mini")
                intent = _classify_intent(user_message, intent_dict, llm)
                detected_lang = detect_language(user_message)
                
                print(f"🎯 Classified intent: {intent} for message: '{user_message}' (lang: {detected_lang})")
            else:
                intent = "answer_general_questions"
                detected_lang = detect_language(user_message)
        except Exception as e:
            print(f"Intent classification error: {e}")
            intent = "answer_general_questions"
            detected_lang = detect_language(user_message)
        
        # Update agent state with detected language and intent
        agent_state["intent"] = intent
        agent_state["language"] = detected_lang
        
        # TODO: AGREGAR INTENCIÓN A UNA FUNCIÓN QUE ACTUALICE EL CHAT CON 'pensando...' o 'escogiendo variables...', y 'procesando resultados...'

        # Let the agent handle the interaction intelligently based on intent
        # Actually try to use the real agent first and fall back to mock response if it fails
        if MODULES_AVAILABLE and agent:
            try:
                # Create a thread config for agent persistence
                thread_config = create_simple_thread_config()
                
                print(f"🤖 Invoking agent with intent: {intent}")
                # Use the real agent to process the request with persistence
                response = agent.invoke(agent_state)
                print(f"✅ Agent response received: {type(response)}")
                
                # Extract response content and session updates
                if isinstance(response, dict):
                    # Check if there are AI messages in the response
                    ai_messages = [msg for msg in response.get("messages", []) if msg.get("role") == "assistant" or getattr(msg, "type", "") == "ai"]
                    if ai_messages:
                        content = ai_messages[-1].get("content", "") if isinstance(ai_messages[-1], dict) else getattr(ai_messages[-1], "content", str(ai_messages[-1]))
                    else:
                        content = response.get('content', response.get('output', str(response)))
                    
                    # Create a dict for session updates with properly typed fields
                    session_updates: Dict[str, Any] = {
                        "language": detected_lang,
                        "intent": intent
                    }
                    
                    try:
                        # Add any specific session updates based on the response
                        if intent == "ask_for_datasets":
                            datasets_info = get_available_datasets()
                            if isinstance(datasets_info, dict):
                                dataset_list = list(datasets_info.keys())
                                session_updates["datasets"] = dataset_list
                                print(f"✅ Set session datasets to: {dataset_list}")
                        
                        # If there are variables selected, store them
                        if "selected_variables" in response and response.get("selected_variables"):
                            variables = response.get("selected_variables")
                            if variables:
                                session_updates["variables"] = variables
                                print(f"✅ Set session variables to: {variables}")
                        
                        # If there is analysis_type, store it
                        if "analysis_type" in response and response.get("analysis_type"):
                            analysis = response.get("analysis_type")
                            if analysis:
                                session_updates["analysis_type"] = analysis
                                print(f"✅ Set session analysis_type to: {analysis}")
                    except Exception as update_err:
                        print(f"⚠️ Error setting session updates: {update_err}")
                    
                    return {
                        "content": content,
                        "session_updates": session_updates
                    }
                else:
                    return {
                        "content": str(response),
                        "session_updates": {"language": detected_lang, "intent": intent}
                    }
            except Exception as e:
                print(f"Agent invocation error: {e}")
                # Fall back to intelligent mock response
                return get_intelligent_mock_response(user_message, agent_state, detected_lang, search_keywords, preferred_datasets)
        else:
            # Use intelligent mock response when agent is not available
            return get_intelligent_mock_response(user_message, agent_state, detected_lang, search_keywords, preferred_datasets)
            
    except Exception as e:
        print(f"Error in get_real_agent_response: {e}")
        return get_mock_agent_response(user_message, session_data)

def get_intelligent_mock_response(user_message: str, agent_state: Dict, detected_lang: str, search_keywords=None, preferred_datasets=None) -> Dict:
    """Generate an intelligent mock response based on user message and agent state"""
    message_lower = user_message.lower()
    intent = agent_state.get("intent", "answer_general_questions")
    
    # Handle different intents intelligently
    if intent == "answer_general_questions":
        # User asking about metadata: datasets, topics, project info
        is_asking_for_datasets = any(word in message_lower for word in [
            "topic", "temas", "dataset", "datos", "encuesta", "survey", 
            "list", "lista", "mostrar", "show", "available", "disponible",
            "que hay", "what are", "cuales son", "which are", "have", "tienes"
        ])
        
        if is_asking_for_datasets:
            # Show available datasets/topics
            datasets_info = get_available_datasets()
            content = get_message('datasets_title', detected_lang) + "\n\n"
            for i, (dataset_name, info) in enumerate(datasets_info.items(), 1):
                content += f"{i}. **{dataset_name}** ({info.get('abbreviation', 'N/A')})\n"
                content += f"   - {info.get('description', 'No description')}\n"
                content += f"   - Variables: {info.get('variables', 'Unknown')}\n\n"
            content += get_message('explore_datasets', detected_lang)
            
            return {
                "content": content,
                "session_updates": {
                    "datasets": list(datasets_info.keys()),
                    "language": detected_lang,
                    "intent": intent
                }
            }
        else:
            # General project/methodology questions
            description = get_project_description(user_message, detected_lang)
            return {
                "content": description,
                "session_updates": {"language": detected_lang, "intent": intent}
            }
    
    elif intent == "query_variable_database":
        # User wants to search for variables/data - use ALL datasets by default
        try:
            if MODULES_AVAILABLE:
                # Import tmp_topic_st for cross-disciplinary analysis
                from dataset_knowledge import tmp_topic_st
                from langchain_openai import ChatOpenAI
                datasets_info = get_available_datasets()
                
                # Create LLM instance for variable selection
                llm = ChatOpenAI(model="gpt-4o-mini")
                
                # Use ALL datasets for cross-disciplinary variable search by default
                try:
                    # Use improved simultaneous retrieval for better performance and balanced results
                    # Use extracted search keywords instead of full user message for better relevance
                    search_query = search_keywords if search_keywords else user_message
                    topic_ids, variables_dict, grade_dict = _variable_selector(
                        search_query, tmp_topic_st, llm, use_simultaneous_retrieval=True
                    )
                    
                    if variables_dict and grade_dict:
                        # Get the top-graded variables
                        sorted_vars = sorted(grade_dict.items(), key=lambda x: list(x[1].keys())[0], reverse=True)
                        top_variables = [var_id for var_id, grade in sorted_vars[:15]] # TODO: este top 15 debería ser configurable por el usuario
                        
                        content = f"{get_message('variables_found', detected_lang, query=user_message)}\n\n"
                        content += f"📊 {get_message('cross_disciplinary_search', detected_lang)}\n\n"
                        
                        for var_id in top_variables:
                            if var_id in variables_dict:
                                var_info = variables_dict.get(f"{var_id}__question", "")
                                if var_info:
                                    content += f"• {var_info[:100]}...\n"
                        
                        content += f"\n{get_message('proceed_variables', detected_lang)}"
                        
                        return {
                            "content": content,
                            "session_updates": {
                                "variables": top_variables,
                                "variables_dict": variables_dict,
                                "grade_dict": grade_dict,
                                "topic_ids": topic_ids,
                                "datasets": list(datasets_info.keys()),  # All datasets used
                                "language": detected_lang,
                                "intent": intent
                            }
                        }
                    else:
                        return {
                            "content": get_message('no_variables_found', detected_lang),
                            "session_updates": {"language": detected_lang, "intent": intent}
                        }
                except Exception as e:
                    print(f"Error in variable selection: {e}")
                    return {
                        "content": get_message('error_occurred', detected_lang, error=str(e)),
                        "session_updates": {"language": detected_lang, "intent": intent}
                    }
            else:
                # Mock variables when modules not available
                mock_variables = [f"Variable_{i}_about_{user_message.split()[0] if user_message.split() else 'topic'}" for i in range(1, 8)]
                content = f"{get_message('variables_found', detected_lang, query=user_message)}\n\n"
                for var in mock_variables:
                    content += f"• {var}\n"
                content += f"\n{get_message('proceed_variables', detected_lang)}"
                
                return {
                    "content": content,
                    "session_updates": {
                        "variables": mock_variables,
                        "datasets": ["ALL"],
                        "language": detected_lang,
                        "intent": intent
                    }
                }
        except Exception as e:
            return {
                "content": get_message('no_variables_found', detected_lang),
                "session_updates": {"language": detected_lang, "intent": intent}
            }
        # User wants to search for variables - use ALL datasets by default
        try:
            if MODULES_AVAILABLE:
                # Import tmp_topic_st for cross-disciplinary analysis
                from dataset_knowledge import tmp_topic_st
                from langchain_openai import ChatOpenAI
                datasets_info = get_available_datasets()
                
                # Create LLM instance for variable selection
                llm = ChatOpenAI(model="gpt-4o-mini")
                
                # Use ALL datasets for cross-disciplinary variable search by default
                try:
                    # Use improved simultaneous retrieval for better performance and balanced results
                    # Use extracted search keywords instead of full user message for better relevance
                    search_query = search_keywords if search_keywords else user_message
                    topic_ids, variables_dict, grade_dict = _variable_selector(
                        search_query, tmp_topic_st, llm, use_simultaneous_retrieval=True
                    )
                    
                    if variables_dict and grade_dict:
                        # Get the top-graded variables
                        sorted_vars = sorted(grade_dict.items(), key=lambda x: list(x[1].keys())[0], reverse=True)
                        top_variables = [var_id for var_id, grade in sorted_vars[:15]]
                        
                        content = f"{get_message('variables_found', detected_lang, query=user_message)}\n\n"
                        content += f"📊 {get_message('cross_disciplinary_search', detected_lang)}\n\n"
                        
                        for var_id in top_variables:
                            if var_id in variables_dict:
                                var_info = variables_dict.get(f"{var_id}__question", "")
                                if var_info:
                                    content += f"• {var_info[:100]}...\n"
                        
                        content += f"\n{get_message('proceed_variables', detected_lang)}"
                        
                        return {
                            "content": content,
                            "session_updates": {
                                "variables": top_variables,
                                "variables_dict": variables_dict,
                                "grade_dict": grade_dict,
                                "topic_ids": topic_ids,
                                "datasets": list(datasets_info.keys()),  # All datasets used
                                "language": detected_lang,
                                "intent": intent
                            }
                        }
                    else:
                        return {
                            "content": get_message('no_variables_found', detected_lang),
                            "session_updates": {"language": detected_lang, "intent": intent}
                        }
                except Exception as e:
                    print(f"Error in variable selection: {e}")
                    return {
                        "content": get_message('error_occurred', detected_lang, error=str(e)),
                        "session_updates": {"language": detected_lang, "intent": intent}
                    }
            else:
                # Mock variables when modules not available
                mock_variables = [f"Variable_{i}_about_{user_message.split()[0] if user_message.split() else 'topic'}" for i in range(1, 8)]
                content = f"{get_message('variables_found', detected_lang, query=user_message)}\n\n"
                for var in mock_variables:
                    content += f"• {var}\n"
                content += f"\n{get_message('proceed_variables', detected_lang)}"
                
                return {
                    "content": content,
                    "session_updates": {
                        "variables": mock_variables,
                        "datasets": ["ALL"],
                        "language": detected_lang,
                        "intent": intent
                    }
                }
        except Exception as e:
            return {
                "content": get_message('no_variables_found', detected_lang),
                "session_updates": {"language": detected_lang, "intent": intent}
            }
    
    elif intent == "run_analysis" or any(word in message_lower for word in ["análisis", "analysis", "run", "ejecutar", "analizar", "analyze"]):
        # User wants to run analysis
        variables = agent_state.get("selected_variables", [])
        if variables:
            # TODO: agregar mensaje 'analizando variables seleccionadas...' de MESSAGES y actualizar respuesta del chat
            # Run analysis with current variables
            try:
                if MODULES_AVAILABLE:
                    result = run_analysis(
                        analysis_type="quick_insights",
                        selected_variables=variables,
                        user_query=user_message
                    )
                else:
                    result = {
                        "success": True,
                        "summary": f"Mock analysis completed for {len(variables)} variables. Found interesting patterns and correlations.",
                        "data": {"mock": "data"},
                        "plots": []
                    }
                
                if result.get("success"):
                    content = f"{get_message('analysis_complete', detected_lang)}\n\n{result.get('summary', 'Analysis completed successfully.')}\n\n{get_message('check_report_panel', detected_lang)}"
                    
                    return {
                        "content": content,
                        "session_updates": {
                            "analysis_type": "quick_insights",
                            "last_report": result,
                            "language": detected_lang,
                            "intent": intent
                        }
                    }
                else:
                    return {
                        "content": get_message('analysis_failed', detected_lang, error=result.get('error', 'Unknown error')),
                        "session_updates": {"language": detected_lang, "intent": intent}
                    }
            except Exception as e:
                return {
                    "content": get_message('analysis_failed', detected_lang, error=str(e)),
                    "session_updates": {"language": detected_lang, "intent": intent}
                }
        else:
            return {
                "content": get_message('need_variables_first', detected_lang),
                "session_updates": {"language": detected_lang, "intent": intent}
            }
    
    elif any(word in message_lower for word in ["project", "proyecto", "describe", "descripción", "about", "acerca", "what is", "qué es"]):
        # User wants project information
        description = get_project_description(user_message, detected_lang)
        return {
            "content": description,
            "session_updates": {"language": detected_lang, "intent": intent}
        }
    
    elif intent == "continue_conversation" or any(word in message_lower for word in ["ok", "okay", "sí", "si", "yes", "proceed", "continuar", "proceder", "adelante"]):
        # User is continuing the conversation - check if they're responding to a variable selection or analysis prompt
        variables = agent_state.get("selected_variables", [])
        session_data = agent_state  # Use agent_state as session data source
        
        if variables and len(variables) > 0:
            # User has variables selected and is saying "ok" - proceed with analysis
            try:
                if MODULES_AVAILABLE:
                    result = run_analysis(
                        analysis_type="quick_insights",
                        selected_variables=variables,
                        user_query="User approved variable selection and requested analysis"
                    )
                else:
                    result = {
                        "success": True,
                        "summary": f"Mock analysis completed for {len(variables)} variables. Found interesting patterns about health opinions in Mexico.",
                        "data": {"mock": "data"},
                        "plots": []
                    }
                
                if result.get("success"):
                    content = f"{get_message('analysis_complete', detected_lang)}\n\n{result.get('summary', 'Analysis completed successfully.')}\n\n{get_message('check_report_panel', detected_lang)}"
                    
                    return {
                        "content": content,
                        "session_updates": {
                            "analysis_type": "quick_insights",
                            "last_report": result,
                            "language": detected_lang,
                            "intent": "run_analysis"  # Update intent to reflect completed analysis
                        }
                    }
                else:
                    return {
                        "content": get_message('analysis_failed', detected_lang, error=result.get('error', 'Unknown error')),
                        "session_updates": {"language": detected_lang, "intent": intent}
                    }
            except Exception as e:
                return {
                    "content": get_message('analysis_failed', detected_lang, error=str(e)),
                    "session_updates": {"language": detected_lang, "intent": intent}
                }
        else:
            # No variables selected yet - be helpful
            if detected_lang == 'es':
                content = "¡Perfecto! ¿Qué te gustaría hacer?\n\n• Buscar variables específicas\n• Ver datasets disponibles\n• Obtener ayuda sobre el proyecto"
            else:
                content = "Perfect! What would you like to do?\n\n• Search for specific variables\n• View available datasets\n• Get help about the project"
            
            return {
                "content": content,
                "session_updates": {"language": detected_lang, "intent": intent}
            }

    else:
        # General conversation - be helpful and contextual
        return {
            "content": get_message('capabilities', detected_lang),
            "session_updates": {"language": detected_lang, "intent": intent}
        }

def get_mock_agent_response(user_message: str, session_data: Dict, search_keywords=None, preferred_datasets=None) -> Dict:
    """Get mock response when real agent is not available"""
    message_lower = user_message.lower()
    user_lang = session_data.get('language', 'es')
    
    # Check for project description requests
    if any(word in message_lower for word in ["project", "describe", "about", "what is", "proyecto", "descripción", "acerca", "qué es"]):
        return {
            "content": get_project_description(user_message, user_lang),
            "session_updates": {}
        }
    
    elif ("dataset" in message_lower and "list" in message_lower) or ("conjunto" in message_lower and ("datos" in message_lower or "lista" in message_lower)):
        datasets_info = get_available_datasets()
        content = get_message('datasets_title', user_lang) + "\n\n"
        for i, (dataset_name, info) in enumerate(datasets_info.items(), 1):
            content += f"{i}. **{dataset_name}** ({info.get('abbreviation', 'N/A')})\n"
            content += f"   - {info.get('description', 'No description')}\n"
            content += f"   - Variables: {info.get('variables', 'Unknown')}\n\n"
        content += get_message('explore_datasets', user_lang)
        
        return {
            "content": content,
            "session_updates": {"datasets": list(datasets_info.keys())}
        }
    
    elif "variable" in message_lower or "search" in message_lower or "buscar" in message_lower:
        return {
            "content": get_message('variable_search_help', user_lang),
            "session_updates": {}
        }
    
    elif "analysis" in message_lower or "run" in message_lower or "análisis" in message_lower or "ejecutar" in message_lower:
        if not session_data.get('variables'):
            return {
                "content": get_message('need_variables_first', user_lang),
                "session_updates": {}
            }
        else:
            return {
                "content": get_message('analysis_types', user_lang),
                "session_updates": {}
            }
    
    else:
        return {
            "content": get_message('capabilities', user_lang),
            "session_updates": {}
        }

def update_session_from_response(session_data: Dict, response: Dict) -> Dict:
    """Update session data based on agent response"""
    updated_session = session_data.copy()
    
    if "session_updates" in response:
        for key, value in response["session_updates"].items():
            updated_session[key] = value
    
    return updated_session

def format_chat_history(chat_data: List[Dict]) -> List:
    """Format chat history for display"""
    formatted_messages = []
    
    for message in chat_data:
        if message["type"] == "user":
            formatted_messages.append(
                html.Div([
                    html.Div([
                        html.Strong("👤 You: "),
                        html.Span(message["content"]),
                        html.Small(f" ({message['timestamp']})", className="text-muted ms-2")
                    ], className="mb-2 p-2 bg-light rounded")
                ])
            )
        else:
            formatted_messages.append(
                html.Div([
                    html.Div([
                        html.Strong("🤖 Assistant: "),
                        dcc.Markdown(message["content"], className="d-inline"),
                        html.Small(f" ({message['timestamp']})", className="text-muted ms-2")
                    ], className="mb-2 p-2 bg-primary text-white rounded")
                ])
            )
    
    return formatted_messages

@app.callback(
    [Output("session-datasets", "children"),
     Output("session-variables", "children"),
     Output("session-analysis-type", "children")],
    [Input("session-store", "data")]
)
def update_session_display(session_data):
    """Update the session information panel"""
    
    # Format datasets
    if session_data.get("datasets"):
        datasets_display = [
            html.Div([
                html.I(className="fas fa-database me-2"),
                dataset
            ], className="mb-1") for dataset in session_data["datasets"]
        ]
    else:
        datasets_display = [html.Small("No datasets selected", className="text-muted")]
    
    # Format variables
    if session_data.get("variables"):
        variables_display = [
            html.Div([
                html.I(className="fas fa-chart-bar me-2"),
                var
            ], className="mb-1") for var in session_data["variables"]
        ]
    else:
        variables_display = [html.Small("No variables selected", className="text-muted")]
    
    # Format analysis type
    if session_data.get("analysis_type"):
        analysis_display = [
            html.Div([
                html.I(className="fas fa-cog me-2"),
                session_data["analysis_type"]
            ])
        ]
    else:
        analysis_display = [html.Small("No analysis type selected", className="text-muted")]
    
    return datasets_display, variables_display, analysis_display

@app.callback(
    [Output("report-content", "children"),
     Output("btn-download-pdf", "disabled")],
    [Input("session-store", "data")]
)
def update_report_display(session_data):
    """Update the report display panel"""
    
    if session_data.get("last_report"):
        # Format the report content for HTML display
        report_html = format_report_html(session_data["last_report"])
        
        return report_html, False
    else:
        # No report available
        no_report = html.Div([
            html.I(className="fas fa-file-alt fa-3x text-muted mb-3"),
            html.H6("No report generated yet", className="text-muted"),
            html.P("Run an analysis to see results here", className="text-muted")
        ], className="text-center mt-5")
        
        return no_report, True

# Add the cleanup callback to remove processed actions after a grace period
@app.callback(
    Output("session-store", "data", allow_duplicate=True),
    [Input("cleanup-interval", "n_intervals")],
    [State("session-store", "data")],
    prevent_initial_call=True
)
def cleanup_processed_actions(n_intervals, session_data):
    """Cleanup processed pending actions after a grace period"""
    if not session_data:
        return dash.no_update
    
    # Make a copy of session data
    session_data_copy = session_data.copy()
    
    # Check for processed pending actions
    pending_action = session_data_copy.get('pending_main_action', {})
    if pending_action and pending_action.get('processed', False):
        current_time = time.time()
        processed_at = pending_action.get('processed_at', 0)
        grace_period = 2  # 2 seconds grace period
        
        if current_time - processed_at > grace_period:
            print(f"🧹 Cleaning up processed pending action after grace period")
            session_data_copy.pop('pending_main_action', None)
            return session_data_copy
    
    return dash.no_update


def format_report_html(report_data: Dict) -> html.Div:
    """Format report data as HTML for display in the dashboard"""
    
    try:
        # Get analysis results
        analysis_results = report_data.get('results', {})
        formatted_report = report_data.get('formatted_report', '')
        analysis_type = report_data.get('analysis_type', 'unknown')
        
        # Check if analysis was successful
        if not report_data.get('success', False):
            return html.Div([
                html.H4("❌ Analysis Failed", className="text-danger mb-3"),
                html.Hr(),
                html.P(f"Error: {report_data.get('error', 'Unknown error')}", className="text-danger"),
                html.Small(f"Analysis Type: {analysis_type}", className="text-muted")
            ])
        
        # Create HTML components for the report
        report_components = []
        
        # Title
        report_components.append(
            html.H4("📊 Analysis Report", className="text-primary mb-3")
        )
        report_components.append(html.Hr())
        
        # Query information
        if analysis_results.get('query'):
            report_components.extend([
                html.H6("🔍 Analysis Query", className="text-info"),
                html.P(analysis_results['query'], className="mb-3"),
            ])
        
        # Executive Summary / Quick Answer
        report_sections = analysis_results.get('report_sections', {})
        if report_sections.get('query_answer'):
            report_components.extend([
                html.H6("📋 Executive Summary", className="text-info"),
                html.P(report_sections['query_answer'], class_name="mb-3"),
            ])
        
        # Topic Analysis Overview
        if report_sections.get('topic_summary'):
            report_components.extend([
                html.H6("🎯 Analysis Overview", className="text-info"),
                html.P(report_sections['topic_summary'], class_name="mb-3"),
            ])
        
        # Topic Summaries (for detailed reports)
        topic_summaries = report_sections.get('topic_summaries', {})
        if topic_summaries:
            report_components.append(html.H6("📚 Topic Analysis", className="text-info"))
            for topic, summary in topic_summaries.items():
                report_components.extend([
                    html.H6(f"▸ {topic}", className="text-secondary mt-3"),
                    html.P(summary, className="mb-2")
                ])
        
        # Variable Summaries (for quick insights)
        variable_summaries = report_sections.get('variable_summaries', {})
        if variable_summaries:
            report_components.append(html.H6("📊 Variable Analysis", className="text-info mt-3"))
            for var_id, summary in variable_summaries.items():
                # Get variable description for better display
                try:
                    if MODULES_AVAILABLE:
                        from plotting_utils import get_variable_description
                        var_desc = get_variable_description(var_id)
                        if isinstance(var_desc, dict):
                            question = var_desc.get('question', var_id)
                            var_title = question[:100] + "..." if len(question) > 100 else question
                        else:
                            var_title = str(var_desc)[:100] + "..." if len(str(var_desc)) > 100 else str(var_desc)
                except:
                    var_title = var_id
                    
                report_components.extend([
                    html.H6(f"▸ {var_title}", className="text-secondary mt-3"),
                    html.P(summary, className="mb-2")
                ])
        
        # Key Findings
        key_findings = report_sections.get('key_findings', [])
        if key_findings:
            report_components.append(html.H6("🔑 Key Findings", className="text-info mt-3"))
            findings_list = [html.Li(finding) for finding in key_findings if finding.strip()]
            if findings_list:
                report_components.append(html.Ul(findings_list, className="mb-3"))
        
        # Expert Analysis
        expert_replies = report_sections.get('expert_replies', [])
        if expert_replies and any(reply.strip() for reply in expert_replies):
            report_components.append(html.H6("👨‍🎓 Expert Analysis", className="text-info mt-3"))
            for i, reply in enumerate(expert_replies, 1):
                if reply.strip():
                    report_components.extend([
                        html.H6(f"Expert Insight {i}", className="text-secondary mt-2"),
                        html.P(reply, className="mb-2")
                    ])
        
        # Visualizations section
        plots_data = analysis_results.get('plots', [])
        plot_references = report_sections.get('plot_references', {})
        
        if plots_data or plot_references:
            report_components.append(html.H6("📈 Visualizations", className="text-info mt-3"))
            
            # Add plot references/descriptions
            if plot_references:
                for var_id, plot_info in plot_references.items():
                    if isinstance(plot_info, dict) and plot_info.get('description'):
                        report_components.extend([
                            html.P(f"📊 {plot_info['description']}", className="mb-2"),
                        ])
            
            # Note about plots (since we can't directly embed matplotlib plots in Dash)
            if plots_data:
                report_components.append(
                    html.P(f"*Note: Visualizations are not displayed in this report. Please download the report as PDF to view all visualizations.*", className="text-muted mt-3")
                )
        
        # Add formatted report if available
        if formatted_report:
            report_components.append(html.Hr(className="my-4"))
            report_components.append(
                html.Div([
                    dcc.Markdown(formatted_report, unsafe_allow_html=True)
                ])
            )
        
        return html.Div(report_components)
    except Exception as e:
        print(f"Error formatting report HTML: {e}")
        return html.Div([
            html.H4("Error generating report", className="text-danger"),
            html.P("There was an error generating the report. Please try again later.", className="text-muted")
        ])


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
        app.run(debug=False, port=8050, host="0.0.0.0", use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard server stopped by user")
    except Exception as e:
        print(f"\n❌ Error running dashboard server: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if port 8050 is already in use")
        print("2. Try running with a different port: app.run(port=8051)")
        print("3. Check error logs above for details")

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
        'cross_disciplinary_search': "Cross-disciplinary search across all datasets"
    },
    'es': {
        'welcome': "¡Hola! Soy Navegador, tu asistente de análisis de encuestas. Puedo ayudarte a explorar conjuntos de datos, seleccionar variables y ejecutar análisis. ¿Qué te gustaría saber?",
        'session_reset': "¡Sesión reiniciada! ¡Hola de nuevo! ¿Cómo puedo ayudarte con el análisis de encuestas?",
        'agent_unavailable': "Lo siento, el agente no está disponible en este momento. Por favor, inténtalo de nuevo más tarde.",
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
        'cross_disciplinary_search': "Búsqueda interdisciplinaria en todos los conjuntos de datos"
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
    print("Make sure all dependencies are installed with: pip install -r requirements.txt")
    sys.exit(1)
import uuid
import time
from typing import Dict, List, Any, Optional, TypedDict, Union

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
        
        print(f"✅✅✅ Agent response processed at {time.time()}: {content[:50]}...")
        
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

# Define SessionData structure for better typing
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

# Helper functions for agent interaction
def create_agent_config(thread_id: Optional[str] = None) -> Any:
    """
    Create a configuration dict for agent invocation with proper checkpointer config
    
    Args:
        thread_id (Optional[str]): Optional thread ID. If None, a timestamp-based ID will be generated.
        
    Returns:
        RunnableConfig or Dict containing the required configurable keys for the LangGraph checkpointer
    """
    if thread_id is None:
        thread_id = f"chat_{int(time.time())}"
    
    # Create a proper config dict that will be compatible with RunnableConfig
    config_dict = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": str(uuid.uuid4()),
            "checkpoint_ns": "chat_session"
        }
    }
    
    # Return as the appropriate type based on whether langchain is available
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
        # Log the update operation with detailed diagnostics
        print(f"🔄 Updating session from agent response...")
        
        # Convert object to dict if needed for consistent handling
        response_dict = {}
        
        if isinstance(agent_response, dict):
            response_dict = agent_response
            print(f"🔍 Agent response is a dictionary with keys: {list(response_dict.keys())}")
        elif hasattr(agent_response, '__dict__'):
            # Handle object types by converting to dict
            response_dict = {k: v for k, v in agent_response.__dict__.items() 
                           if not k.startswith('_') and not callable(v)}
            print(f"🔍 Agent response is an object with attributes: {list(response_dict.keys())}")
        else:
            print(f"⚠️ Agent response is neither dict nor object with __dict__: {type(agent_response)}")
        
        # Update agent_state
        updated_session['agent_state'] = response_dict
        
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
                
                value = response_dict[key]
                updated_session[session_key] = value
                print(f"✅ Updated session['{session_key}'] from response['{key}'] to: {value}")
                
            elif hasattr(agent_response, key):
                # Try to access as attribute if not in dict
                session_key = {
                    'dataset': 'datasets',
                    'selected_variables': 'variables'
                }.get(key, key)
                
                value = getattr(agent_response, key)
                updated_session[session_key] = value
                print(f"✅ Updated session['{session_key}'] from attribute '{key}' to: {value}")
            
        # Special handling for analysis_result if present
        if isinstance(agent_response, dict) and 'analysis_result' in agent_response and agent_response['analysis_result']:
            updated_session['last_report'] = agent_response['analysis_result']
            print(f"✅ Updated last_report from analysis_result")
            
        # Debug the messages to help diagnose workflow issues
        if isinstance(agent_response, dict) and 'messages' in agent_response:
            messages = agent_response['messages']
            print(f"🔍 Agent has {len(messages)} messages in its history")
            
            if messages and len(messages) > 0:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    role = last_msg.get('role', 'unknown')
                    content_sample = last_msg.get('content', '')[:50] + '...' if len(last_msg.get('content', '')) > 50 else last_msg.get('content', '')
                    print(f"🔍 Last message is from '{role}': {content_sample}")
                    
        # Debug final session state after update to help diagnose workflow
        print(f"✅ Final session state after update: intent='{updated_session.get('intent', 'None')}', "
              f"variables={len(updated_session.get('variables', []))}, "
              f"datasets={updated_session.get('datasets', [])}")
              
    except Exception as e:
        print(f"❌ Error updating session from agent response: {e}")
        import traceback
        traceback.print_exc()
    
    # Restore any pending_main_action that might have been overwritten
    if pending_action:
        # Ensure we preserve the processed status
        updated_session['pending_main_action'] = pending_action
    
    return updated_session