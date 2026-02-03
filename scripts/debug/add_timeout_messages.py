#!/usr/bin/env python3
"""
Script to add 'agent_timeout' messages to the dashboard.py MESSAGES dictionary
"""

import re
import os

def add_timeout_messages():
    """Add 'agent_timeout' messages to both English and Spanish dictionaries"""
    file_path = "dashboard.py"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return False
    
    # Read the dashboard.py file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add timeout message to English dictionary
    english_pattern = r"('agent_unavailable': \"Sorry, the agent is not available right now. Please try again later.\",)\n(\s+)('error_occurred':"
    english_replacement = r"\1\n\2'agent_timeout': \"The request is taking longer than expected. I've timed out after {timeout} seconds. Please try a simpler query or try again later.\",\n\2\3"
    
    # Add timeout message to Spanish dictionary
    spanish_pattern = r"('agent_unavailable': \"Lo siento, el agente no está disponible en este momento. Por favor, inténtalo de nuevo más tarde.\",)\n(\s+)('error_occurred':"
    spanish_replacement = r"\1\n\2'agent_timeout': \"La solicitud está tomando más tiempo de lo esperado. Se agotó el tiempo de espera después de {timeout} segundos. Intenta una consulta más simple o inténtalo más tarde.\",\n\2\3"
    
    # Apply the replacements
    modified_content = re.sub(english_pattern, english_replacement, content)
    modified_content = re.sub(spanish_pattern, spanish_replacement, modified_content)
    
    # Write the modified content back to the file
    if modified_content != content:
        with open(file_path, 'w') as f:
            f.write(modified_content)
        print("✅ Successfully added 'agent_timeout' messages to MESSAGES dictionary")
        return True
    else:
        print("❌ Failed to add 'agent_timeout' messages (no changes made)")
        return False

if __name__ == "__main__":
    add_timeout_messages()
