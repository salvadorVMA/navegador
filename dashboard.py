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
    'datasets': ["ALL"],  # Default to using all datasets
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
        # Create agent without persistence to avoid checkpointer configuration issues
        agent = create_agent(enable_persistence=False)
        print("✅ Agent initialized successfully (without persistence)")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        agent = None
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
            'datasets': ["ALL"],  # Default to using all datasets
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
            # Enhanced query processing - extract search keywords and detect dataset preference
            search_keywords = extract_search_keywords(user_message, detected_lang)
            preferred_datasets = detect_dataset_preference(user_message, detected_lang)
            
            print(f"🔍 Original query: '{user_message}'")
            print(f"🎯 Search keywords: '{search_keywords}'")
            print(f"📊 Preferred datasets: {preferred_datasets}")
            
            # Update session with extracted information
            session_data['search_keywords'] = search_keywords
            session_data['preferred_datasets'] = preferred_datasets
            
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
    
    return format_chat_history(new_chat_data), new_chat_data, "", updated_session

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
        
        # Let the agent handle the interaction intelligently based on intent
        # For now, use intelligent mock response since it handles intents correctly
        # TODO: Fix real agent to respect our intent classification
        return get_intelligent_mock_response(user_message, agent_state, detected_lang, search_keywords, preferred_datasets)
        
        # Disabled real agent call for now due to intent classification conflicts
        if False and MODULES_AVAILABLE and agent:
            try:
                # Use the real agent to process the request (without persistence to avoid checkpointer issues)
                response = agent.invoke(agent_state)
                
                # Extract response content and session updates
                if isinstance(response, dict):
                    content = response.get('content', response.get('output', str(response)))
                    session_updates = {
                        "language": detected_lang,
                        "intent": intent
                    }
                    
                    # Add any specific session updates based on the response
                    if intent == "ask_for_datasets" and "datasets" not in session_updates:
                        datasets_info = get_available_datasets()
                        session_updates["datasets"] = list(datasets_info.keys())
                    
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
                html.P(report_sections['query_answer'], className="mb-3"),
            ])
        
        # Topic Analysis Overview
        if report_sections.get('topic_summary'):
            report_components.extend([
                html.H6("🎯 Analysis Overview", className="text-info"),
                html.P(report_sections['topic_summary'], className="mb-3"),
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
                    else:
                        var_title = var_id
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
                    html.P(f"📊 {len(plots_data)} visualizations were generated for this analysis.", 
                           className="text-muted mb-2")
                )
        
        # Analysis Metadata
        report_components.extend([
            html.Hr(className="mt-4"),
            html.H6("ℹ️ Analysis Details", className="text-info"),
            html.Ul([
                html.Li(f"Analysis Type: {analysis_type.replace('_', ' ').title()}"),
                html.Li(f"Variables Analyzed: {len(analysis_results.get('selected_variables', []))}"),
                html.Li(f"Patterns Identified: {len(analysis_results.get('patterns', {}))}"),
                html.Li(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            ], className="small text-muted")
        ])
        
        return html.Div(report_components)
        
    except Exception as e:
        print(f"Error formatting report HTML: {e}")
        # Fallback to simple text display
        return html.Div([
            html.H4("📊 Analysis Report", className="text-primary mb-3"),
            html.Hr(),
            html.P("Report generated successfully, but there was an issue with formatting.", className="text-muted"),
            html.P(f"Analysis Type: {report_data.get('analysis_type', 'unknown')}", className="small text-muted"),
            html.P(f"Status: {'Success' if report_data.get('success') else 'Failed'}", className="small text-muted")
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
            # Generate PDF content using the formatted report
            html_content = generate_pdf_html(session_data["last_report"])
            
            # Try to convert to PDF using weasyprint if available
            try:
                if MODULES_AVAILABLE:
                    import weasyprint
                    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
                    
                    # Return PDF download
                    return dict(
                        content=pdf_bytes,
                        filename=f"navegador_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        type="application/pdf"
                    )
                else:
                    # Fall back to plain text if weasyprint not available
                    formatted_report = session_data["last_report"].get("formatted_report", "No report content available")
                    return dict(
                        content=formatted_report,
                        filename=f"navegador_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                    )
            except ImportError:
                # Fall back to plain text if weasyprint not available  
                formatted_report = session_data["last_report"].get("formatted_report", "No report content available")
                return dict(
                    content=formatted_report,
                    filename=f"navegador_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                )
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return dash.no_update
    
    return dash.no_update

def generate_pdf_html(report_data: Dict) -> str:
    """Generate HTML content for PDF download"""
    
    try:
        # Get analysis results
        analysis_results = report_data.get('results', {})
        formatted_report = report_data.get('formatted_report', '')
        analysis_type = report_data.get('analysis_type', 'unknown')
        
        # Create comprehensive HTML for PDF
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Navegador Analysis Report</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 40px; 
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ 
            color: #0066cc; 
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }}
        h2 {{ 
            color: #0080ff; 
            margin-top: 30px;
            border-left: 4px solid #0080ff;
            padding-left: 15px;
        }}
        h3 {{ 
            color: #4da6ff; 
            margin-top: 20px;
        }}
        .metadata {{ 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary {{ 
            background-color: #e3f2fd; 
            padding: 15px; 
            border-radius: 5px;
            border-left: 4px solid #2196f3;
            margin: 15px 0;
        }}
        .finding {{ 
            margin: 10px 0; 
            padding-left: 20px;
        }}
        .expert {{ 
            background-color: #fff3e0; 
            padding: 15px; 
            border-radius: 5px;
            border-left: 4px solid #ff9800;
            margin: 15px 0;
        }}
        ul {{ 
            padding-left: 25px; 
        }}
        li {{ 
            margin: 5px 0; 
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>📊 Navegador Analysis Report</h1>
"""
        
        # Add analysis metadata
        html_content += f"""
    <div class="metadata">
        <h3>Analysis Information</h3>
        <ul>
            <li><strong>Analysis Type:</strong> {analysis_type.replace('_', ' ').title()}</li>
            <li><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            <li><strong>Status:</strong> {'Success' if report_data.get('success') else 'Failed'}</li>
"""
        
        if analysis_results.get('selected_variables'):
            html_content += f"            <li><strong>Variables Analyzed:</strong> {len(analysis_results['selected_variables'])}</li>\n"
        
        if analysis_results.get('patterns'):
            html_content += f"            <li><strong>Patterns Identified:</strong> {len(analysis_results['patterns'])}</li>\n"
            
        html_content += """
        </ul>
    </div>
"""
        
        # Add query information
        if analysis_results.get('query'):
            html_content += f"""
    <h2>🔍 Analysis Query</h2>
    <div class="summary">
        <p>{analysis_results['query']}</p>
    </div>
"""
        
        # Add report sections
        report_sections = analysis_results.get('report_sections', {})
        
        # Executive Summary
        if report_sections.get('query_answer'):
            html_content += f"""
    <h2>📋 Executive Summary</h2>
    <div class="summary">
        <p>{report_sections['query_answer']}</p>
    </div>
"""
        
        # Analysis Overview
        if report_sections.get('topic_summary'):
            html_content += f"""
    <h2>🎯 Analysis Overview</h2>
    <p>{report_sections['topic_summary']}</p>
"""
        
        # Topic Summaries
        topic_summaries = report_sections.get('topic_summaries', {})
        if topic_summaries:
            html_content += """
    <h2>📚 Topic Analysis</h2>
"""
            for topic, summary in topic_summaries.items():
                html_content += f"""
    <h3>▸ {topic}</h3>
    <p>{summary}</p>
"""
        
        # Variable Summaries (for quick insights)
        variable_summaries = report_sections.get('variable_summaries', {})
        if variable_summaries:
            html_content += """
    <h2>📊 Variable Analysis</h2>
"""
            for var_id, summary in variable_summaries.items():
                html_content += f"""
    <h3>▸ {var_id}</h3>
    <p>{summary}</p>
"""
        
        # Key Findings
        key_findings = report_sections.get('key_findings', [])
        if key_findings:
            html_content += """
    <h2>🔑 Key Findings</h2>
    <ul>
"""
            for finding in key_findings:
                if finding.strip():
                    html_content += f"        <li class='finding'>{finding}</li>\n"
            html_content += "    </ul>\n"
        
        # Expert Analysis
        expert_replies = report_sections.get('expert_replies', [])
        if expert_replies and any(reply.strip() for reply in expert_replies):
            html_content += """
    <h2>👨‍🎓 Expert Analysis</h2>
"""
            for i, reply in enumerate(expert_replies, 1):
                if reply.strip():
                    html_content += f"""
    <div class="expert">
        <h3>Expert Insight {i}</h3>
        <p>{reply}</p>
    </div>
"""
        
        # Visualizations
        plots_data = analysis_results.get('plots', [])
        plot_references = report_sections.get('plot_references', {})
        
        if plots_data or plot_references:
            html_content += """
    <h2>📈 Visualizations</h2>
"""
            if plot_references:
                for var_id, plot_info in plot_references.items():
                    if isinstance(plot_info, dict) and plot_info.get('description'):
                        html_content += f"    <p>📊 {plot_info['description']}</p>\n"
            
            if plots_data:
                html_content += f"    <p>📊 {len(plots_data)} visualizations were generated for this analysis.</p>\n"
        
        # Footer
        html_content += """
    <div class="footer">
        <p>Generated by Navegador - Survey Analysis Dashboard</p>
    </div>
</body>
</html>
"""
        
        return html_content
        
    except Exception as e:
        print(f"Error generating PDF HTML: {e}")
        # Fallback to simple HTML
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Navegador Analysis Report</title>
</head>
<body>
    <h1>Analysis Report</h1>
    <p>Analysis Type: {report_data.get('analysis_type', 'unknown')}</p>
    <p>Status: {'Success' if report_data.get('success') else 'Failed'}</p>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>Report Content</h2>
    <pre>{report_data.get('formatted_report', 'No content available')}</pre>
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
    print("\n🚀 Starting Navegador Dashboard...")
    print("📊 Loading survey datasets and variables...")
    print("🔍 Initializing analysis agent...")
    print("🌐 Dashboard will be available at: http://localhost:8050")
    print("💡 Use Ctrl+C to stop the server\n")
    
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8050,
        dev_tools_hot_reload=True
    )
