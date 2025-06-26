"""
Navegador Dashboard - Interactive Web Interface
==============================================

A Dash-based web interface for the Navegador survey analysis agent.
Provides a chatbot interface with real-time analysis and reporting capabilities.
"""

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
import os
import sys
from typing import Dict, List, Any, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent import create_agent, AgentState
    from dataset_knowledge import (
        rev_topic_dict, tmp_topic_st, tmp_data_describer_st, 
        enc_nom_dict, rev_enc_nom_dict, pregs_dict, mkdown_tables, 
        df_tables, _project_describer
    )
    from variable_selector import _variable_selector, _database_selector
    from run_analysis import run_analysis
    from intent_classifier import _classify_intent
    from plotting_utils import create_plot, get_variable_description
    from performance_optimization import get_cache_stats, clear_cache
    import weasyprint  # For PDF generation
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    print("Some features may not be available.")
    MODULES_AVAILABLE = False

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
        'explore_datasets': "Would you like to explore variables from any of these datasets?"
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
        'explore_datasets': "¿Te gustaría explorar variables de alguno de estos conjuntos de datos?"
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
            # Return dataset information from the imported dictionaries
            datasets = {}
            for abbrev, full_name in rev_enc_nom_dict.items():
                # Clean up the name for display
                clean_name = full_name.replace('_', ' ').title()
                datasets[clean_name] = {
                    "abbreviation": abbrev,
                    "full_name": full_name,
                    "description": f"Survey on {clean_name.lower()}",
                    "variables": len([k for k in pregs_dict.keys() if k.endswith(f"|{abbrev}")]) if pregs_dict else 0
                }
            return datasets
        except Exception as e:
            print(f"Error getting datasets: {e}")
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
            # Import LLM for project description
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o-mini")
            
            if user_query:
                # Add language instruction to the query if needed
                if language == 'en' and not any(eng_word in user_query.lower() for eng_word in ['english', 'in english']):
                    enhanced_query = f"{user_query}. Please respond in English."
                else:
                    enhanced_query = user_query
                return _project_describer(enhanced_query, tmp_data_describer_st, llm)
            else:
                # Return basic project info
                return get_mock_project_description(language)
        except Exception as e:
            print(f"Error getting project description: {e}")
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

# Global variables for session state
chat_history = []
current_session = {
    'datasets': [],
    'variables': [],
    'analysis_type': None,
    'last_report': None,
    'agent_state': {},
    'language': 'es'  # Default to Spanish since data is in Spanish
}

# Initialize the agent
agent = None
if MODULES_AVAILABLE:
    try:
        agent = create_agent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        agent = None
else:
    print("⚠️ Modules not available, running in mock mode")

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
                    className="me-2",
                    disabled=True
                ),
                dbc.Button(
                    [html.I(className="fas fa-code me-2"), "Download HTML"],
                    id="btn-download-html",
                    color="primary",
                    size="sm",
                    disabled=True
                ),
                dcc.Download(id="download-pdf"),
                dcc.Download(id="download-html")
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
    
    # Header
    create_header(),
    
    # Main content
    dbc.Row([
        # Left column - Chat interface
        dbc.Col([
            create_chat_interface()
        ], width=4),
        
        # Middle column - Session panel
        dbc.Col([
            create_session_panel()
        ], width=3),
        
        # Right column - Report panel
        dbc.Col([
            create_report_panel()
        ], width=5)
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
    [Output("chat-history", "children"),
     Output("chat-store", "data"),
     Output("user-input", "value"),
     Output("session-store", "data")],
    [Input("send-button", "n_clicks"),
     Input("btn-datasets", "n_clicks"),
     Input("btn-variables", "n_clicks"),
     Input("btn-analysis", "n_clicks"),
     Input("btn-reset", "n_clicks"),
     Input("user-input", "n_submit")],
    [State("user-input", "value"),
     State("chat-store", "data"),
     State("session-store", "data")]
)
def handle_chat_interaction(send_clicks, datasets_clicks, variables_clicks, 
                           analysis_clicks, reset_clicks, input_submit,
                           user_message, chat_data, session_data):
    """Handle all chat interactions and quick action buttons"""
    
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle reset button
    if triggered_id == "btn-reset":
        new_chat = [{
            "type": "assistant",
            "content": get_message('session_reset', 'es'),  # Default to Spanish for reset
            "timestamp": datetime.now().strftime("%H:%M")
        }]
        new_session = {
            'datasets': [],
            'variables': [],
            'analysis_type': None,
            'last_report': None,
            'agent_state': {},
            'language': 'es'  # Reset to default Spanish
        }
        return format_chat_history(new_chat), new_chat, "", new_session
    
    # Determine user message based on trigger
    if triggered_id == "btn-datasets":
        user_message = "List available datasets"
    elif triggered_id == "btn-variables":
        user_message = "Help me search for variables"
    elif triggered_id == "btn-analysis":
        user_message = "I want to run an analysis"
    elif not user_message or user_message.strip() == "":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
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
            # Simulate agent conversation (replace with actual agent call)
            response = get_agent_response(user_message, session_data)
            
            # Update session data based on response
            updated_session = update_session_from_response(session_data, response)
        else:
            response = {
                "content": get_message('agent_unavailable', session_data.get('language', 'es')),
                "session_updates": {}
            }
            updated_session = session_data
            
    except Exception as e:
        response = {
            "content": get_message('error_occurred', session_data.get('language', 'es'), error=str(e)),
            "session_updates": {}
        }
        updated_session = session_data
    
    # Add assistant response to chat
    new_chat_data.append({
        "type": "assistant",
        "content": response["content"],
        "timestamp": datetime.now().strftime("%H:%M")
    })
    
    return format_chat_history(new_chat_data), new_chat_data, "", updated_session

def get_agent_response(user_message: str, session_data: Dict) -> Dict:
    """Get response from the Navegador agent"""
    try:
        if agent and MODULES_AVAILABLE:
            # Use the real agent
            return get_real_agent_response(user_message, session_data)
        else:
            # Fall back to mock responses
            return get_mock_agent_response(user_message, session_data)
    except Exception as e:
        return {
            "content": get_message('error_occurred', session_data.get('language', 'es'), error=str(e)),
            "session_updates": {}
        }

def get_real_agent_response(user_message: str, session_data: Dict) -> Dict:
    """Get response from the real Navegador agent"""
    try:
        # Get user's language preference
        user_lang = session_data.get('language', 'es')
        
        # Initialize agent state with current session
        agent_state = {
            "messages": session_data.get("chat_history", []),
            "intent": "",
            "user_query": user_message,
            "original_query": user_message,
            "dataset": session_data.get("datasets", ["ALL"]),
            "selected_variables": session_data.get("variables", []),
            "analysis_type": session_data.get("analysis_type", "quick_insights"),
            "user_approved": False,
            "analysis_result": {},
            "language": user_lang
        }
        
        # Classify intent
        try:
            if MODULES_AVAILABLE:
                from intent_classifier import intent_dict
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(model="gpt-4o-mini")
                intent = _classify_intent(user_message, intent_dict, llm)
            else:
                intent = "answer_general_questions"  # Default intent
        except Exception:
            intent = "answer_general_questions"
        agent_state["intent"] = intent
        
        # Process based on intent
        if intent == "ask_for_datasets":
            # Get available datasets
            try:
                datasets_info = get_available_datasets()
                dataset_list = list(datasets_info.keys()) if datasets_info else []
                
                content = get_message('datasets_title', user_lang) + "\n\n"
                for i, (dataset_name, info) in enumerate(datasets_info.items(), 1):
                    content += f"{i}. **{dataset_name}** ({info.get('abbreviation', 'N/A')})\n"
                    content += f"   - {info.get('description', 'No description')}\n"
                    content += f"   - Variables: {info.get('variables', 'Unknown')}\n\n"
                content += get_message('which_dataset', user_lang)
                
                return {
                    "content": content,
                    "session_updates": {"datasets": dataset_list}
                }
            except Exception as e:
                return get_mock_agent_response(user_message, session_data)
        
            # Get variables from selected dataset
            if session_data.get("datasets"):
                try:
                    # Use the first dataset for variable selection
                    dataset = session_data["datasets"][0]
                    if MODULES_AVAILABLE:
                        variables = _variable_selector(user_message, dataset, "gpt-4o-mini")
                    else:
                        # Mock variables
                        variables = [f"VAR_{i}" for i in range(1, 11)]
                    
                    if variables:
                        content = f"{get_message('variables_found', user_lang, query=user_message)}\n\n"
                        for var in variables[:15]:  # Limit to 15 variables
                            content += f"• {var}\n"
                        content += f"\n{get_message('proceed_variables', user_lang)}"
                        
                        return {
                            "content": content,
                            "session_updates": {"variables": variables[:15]}
                        }
                    else:
                        return {
                            "content": get_message('no_variables_found', user_lang),
                            "session_updates": {}
                        }
                except Exception as e:
                    return get_mock_agent_response(user_message, session_data)
            else:
                return {
                    "content": get_message('select_dataset_first', user_lang),
                    "session_updates": {}
                }
        
        elif intent == "run_analysis":
            # Run analysis with selected variables
            if session_data.get("variables"):
                try:
                    # Determine analysis type from message
                    message_lower = user_message.lower()
                    if "detailed" in message_lower:
                        analysis_type = "detailed_report"
                    elif "quick" in message_lower:
                        analysis_type = "quick_insights"
                    elif "plot" in message_lower or "chart" in message_lower:
                        analysis_type = "plots_only"
                    else:
                        analysis_type = "quick_insights"  # Default
                    
                    # Run the analysis
                    if MODULES_AVAILABLE:
                        result = run_analysis(
                            analysis_type=analysis_type,
                            selected_variables=session_data["variables"],
                            user_query=user_message
                        )
                    else:
                        # Mock analysis result
                        result = {
                            "success": True,
                            "summary": "Mock analysis completed successfully. In production, this would contain real analysis results.",
                            "data": {"mock": "data"},
                            "plots": []
                        }
                    
                    if result.get("success"):
                        content = f"{get_message('analysis_complete', user_lang)}\n\n{result.get('summary', 'Analysis completed successfully.')}\n\n{get_message('check_report_panel', user_lang)}"
                        
                        return {
                            "content": content,
                            "session_updates": {
                                "analysis_type": analysis_type,
                                "last_report": result
                            }
                        }
                    else:
                        return {
                            "content": f"❌ Analysis failed: {result.get('error', 'Unknown error')}",
                            "session_updates": {}
                        }
                except Exception as e:
                    return {
                        "content": get_message('analysis_failed', user_lang, error=str(e)),
                        "session_updates": {}
                    }
            else:
                return {
                    "content": get_message('need_variables_first', user_lang),
                    "session_updates": {}
                }
        
        else:
            # Default response for other intents - try project description for general questions
            try:
                if any(word in user_message.lower() for word in ["project", "describe", "about", "what is", "tell me"]):
                    description = get_project_description(user_message, user_lang)
                    return {
                        "content": description,
                        "session_updates": {}
                    }
                else:
                    return get_mock_agent_response(user_message, session_data)
            except Exception:
                return get_mock_agent_response(user_message, session_data)
            
    except Exception as e:
        return get_mock_agent_response(user_message, session_data)

def get_mock_agent_response(user_message: str, session_data: Dict) -> Dict:
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
     Output("btn-download-pdf", "disabled"),
     Output("btn-download-html", "disabled")],
    [Input("session-store", "data")]
)
def update_report_display(session_data):
    """Update the report display panel"""
    
    if session_data.get("last_report"):
        # Format the report content
        report_html = format_report_html(session_data["last_report"])
        
        return report_html, False, False
    else:
        # No report available
        no_report = html.Div([
            html.I(className="fas fa-file-alt fa-3x text-muted mb-3"),
            html.H6("No report generated yet", className="text-muted"),
            html.P("Run an analysis to see results here", className="text-muted")
        ], className="text-center mt-5")
        
        return no_report, True, True

def format_report_html(report_data: Dict) -> html.Div:
    """Format report data as HTML for display"""
    
    # This is a mock report formatter - replace with actual report formatting
    return html.Div([
        html.H4("📊 Analysis Report", className="text-primary mb-3"),
        html.Hr(),
        html.H6("Summary"),
        html.P("This is a sample report. In production, this would contain the actual analysis results."),
        html.H6("Key Findings"),
        html.Ul([
            html.Li("Finding 1: Sample insight"),
            html.Li("Finding 2: Another insight"),
            html.Li("Finding 3: More insights")
        ]),
        html.H6("Visualizations"),
        html.P("Charts and plots would appear here."),
        html.Small(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                  className="text-muted")
    ])

@app.callback(
    Output("download-pdf", "data"),
    [Input("btn-download-pdf", "n_clicks")],
    [State("session-store", "data")],
    prevent_initial_call=True
)
def download_pdf_report(n_clicks, session_data):
    """Generate and download PDF report"""
    if n_clicks and session_data.get("last_report"):
        try:
            # Generate PDF content
            html_content = generate_pdf_html(session_data["last_report"])
            
            # Try to convert to PDF using weasyprint if available
            try:
                if MODULES_AVAILABLE:
                    import weasyprint
                    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
                    
                    # Return download - use dict format instead of send_bytes
                    return dict(
                        content=pdf_bytes,
                        filename=f"navegador_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        type="application/pdf"
                    )
                else:
                    # Fall back to HTML download if weasyprint not available
                    return dict(
                        content=html_content,
                        filename=f"navegador_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
                    )
            except ImportError:
                # Fall back to HTML download if weasyprint not available
                return dict(
                    content=html_content,
                    filename=f"navegador_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
                )
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return dash.no_update
    
    return dash.no_update

@app.callback(
    Output("download-html", "data"),
    [Input("btn-download-html", "n_clicks")],
    [State("session-store", "data")],
    prevent_initial_call=True
)
def download_html_report(n_clicks, session_data):
    """Generate and download HTML report"""
    if n_clicks and session_data.get("last_report"):
        try:
            # Generate HTML content
            html_content = generate_pdf_html(session_data["last_report"])
            
            # Return download
            return dict(
                content=html_content,
                filename=f"navegador_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
            )
        except Exception as e:
            print(f"Error generating HTML: {e}")
            return dash.no_update
    
    return dash.no_update

def generate_pdf_html(report_data: Dict) -> str:
    """Generate HTML content for PDF/HTML download"""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Navegador Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #0066cc; }}
            h2 {{ color: #0080ff; border-bottom: 1px solid #ccc; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Navegador Analysis Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <h2>Analysis Summary</h2>
        <p>This report contains the results of your survey data analysis.</p>
        
        <h2>Key Findings</h2>
        <ul>
            <li>Sample finding 1</li>
            <li>Sample finding 2</li>
            <li>Sample finding 3</li>
        </ul>
        
        <h2>Methodology</h2>
        <p>Analysis performed using the Navegador survey analysis system.</p>
        
        <div class="footer">
            <p>Generated by Navegador Survey Analysis Dashboard</p>
        </div>
    </body>
    </html>
    """

@app.callback(
    [Output("cache-stats", "children"),
     Output("performance-metrics", "children")],
    [Input("btn-refresh-stats", "n_clicks"),
     Input("btn-clear-cache", "n_clicks")],
    prevent_initial_call=False
)
def update_performance_stats(refresh_clicks, clear_clicks):
    """Update performance statistics and handle cache clearing"""
    
    ctx_triggered = ctx.triggered
    if ctx_triggered and ctx_triggered[0]["prop_id"] == "btn-clear-cache.n_clicks":
        # Clear cache if button was clicked
        try:
            if MODULES_AVAILABLE:
                clear_cache()
                cache_message = "✅ Cache cleared successfully"
            else:
                cache_message = "⚠️ Cache clearing not available (modules not loaded)"
        except Exception as e:
            cache_message = f"❌ Error clearing cache: {str(e)}"
    else:
        cache_message = ""
    
    # Get cache statistics
    try:
        if MODULES_AVAILABLE:
            stats = get_cache_stats()
            cache_stats = [
                html.Div([
                    html.Strong("Cache Hits: "),
                    html.Span(f"{stats.get('hits', 0):,}", className="text-success")
                ]),
                html.Div([
                    html.Strong("Cache Misses: "),
                    html.Span(f"{stats.get('misses', 0):,}", className="text-warning")
                ]),
                html.Div([
                    html.Strong("Hit Rate: "),
                    html.Span(f"{stats.get('hit_rate', 0):.1%}", className="text-info")
                ]),
                html.Div([
                    html.Strong("Cache Size: "),
                    html.Span(f"{stats.get('size', 0):,} items", className="text-muted")
                ])
            ]
            if cache_message:
                cache_stats.append(html.Div(cache_message, className="mt-2 small"))
        else:
            cache_stats = [html.Small("Cache statistics not available", className="text-muted")]
    except Exception as e:
        cache_stats = [html.Small(f"Error loading cache stats: {str(e)}", className="text-danger")]
    
    # Get performance metrics
    try:
        import psutil
        import os
        
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        performance_metrics = [
            html.Div([
                html.Strong("CPU Usage: "),
                html.Span(f"{cpu_percent:.1f}%", 
                         className="text-danger" if cpu_percent > 80 else "text-warning" if cpu_percent > 60 else "text-success")
            ]),
            html.Div([
                html.Strong("Memory Usage: "),
                html.Span(f"{memory.percent:.1f}%",
                         className="text-danger" if memory.percent > 80 else "text-warning" if memory.percent > 60 else "text-success")
            ]),
            html.Div([
                html.Strong("Available Memory: "),
                html.Span(f"{memory.available / (1024**3):.1f} GB", className="text-info")
            ]),
            html.Div([
                html.Strong("Process ID: "),
                html.Span(str(os.getpid()), className="text-muted")
            ])
        ]
    except ImportError:
        performance_metrics = [html.Small("System metrics not available (psutil not installed)", className="text-muted")]
    except Exception as e:
        performance_metrics = [html.Small(f"Error loading performance metrics: {str(e)}", className="text-danger")]
    
    return cache_stats, performance_metrics

@app.callback(
    Output("collapse-performance", "is_open"),
    [Input("btn-toggle-performance", "n_clicks")],
    [State("collapse-performance", "is_open")],
    prevent_initial_call=True
)
def toggle_performance_panel(n_clicks, is_open):
    """Toggle the performance monitoring panel"""
    if n_clicks:
        return not is_open
    return is_open

# Run the app
if __name__ == "__main__":
    print("🚀 Starting Navegador Dashboard...")
    print("📱 Access the dashboard at: http://localhost:8050")
    
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8050,
        dev_tools_hot_reload=True
    )
