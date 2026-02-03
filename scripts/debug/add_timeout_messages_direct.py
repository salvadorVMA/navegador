#!/usr/bin/env python3
"""
Add 'agent_timeout' messages to MESSAGES dictionary in dashboard.py
"""

import os
import re

def add_timeout_messages():
    """Add timeout messages to dashboard.py"""
    dashboard_path = 'dashboard.py'
    if not os.path.exists(dashboard_path):
        print(f"Error: {dashboard_path} not found")
        return False
    
    # Read the file
    with open(dashboard_path, 'r') as f:
        content = f.readlines()
    
    # Find the MESSAGES dictionary
    new_content = []
    in_en_dict = False
    in_es_dict = False
    
    for line in content:
        if "'agent_unavailable':" in line and "Sorry, the agent is not available" in line:
            # We're in English dictionary
            new_content.append(line)
            new_content.append("        'agent_timeout': \"The request is taking longer than expected. I've timed out after {timeout} seconds. Please try a simpler query or try again later.\",\n")
        elif "'agent_unavailable':" in line and "Lo siento, el agente no está disponible" in line:
            # We're in Spanish dictionary
            new_content.append(line)
            new_content.append("        'agent_timeout': \"La solicitud está tomando más tiempo de lo esperado. Se agotó el tiempo de espera después de {timeout} segundos. Intenta una consulta más simple o inténtalo más tarde.\",\n")
        else:
            new_content.append(line)
    
    # Write the updated content
    with open(dashboard_path, 'w') as f:
        f.writelines(new_content)
    
    print(f"✅ Successfully added 'agent_timeout' messages to {dashboard_path}")
    return True

if __name__ == "__main__":
    add_timeout_messages()
