"""Common utility functions shared across modules."""

from typing import Dict, Any

# Message dictionary that was previously duplicated
MESSAGES = {
    'es': {
        'explore_datasets': "¿Te gustaría explorar variables de alguno de estos conjuntos de datos?",
        'cross_disciplinary_search': "Búsqueda interdisciplinaria en todos los conjuntos de datos"
    }
}

def get_message(key: str, lang: str = 'es', **kwargs) -> str:
    """Get a message in the specified language with optional formatting."""
    message = MESSAGES.get(lang, MESSAGES['es']).get(key, MESSAGES['es'].get(key, key))
    if kwargs:
        try:
            return message.format(**kwargs)
        except KeyError:
            return message
    return message

def get_timestamp() -> str:
    """Get current time formatted for display."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M")
