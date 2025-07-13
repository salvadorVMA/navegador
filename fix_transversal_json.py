"""
This module fixes the JSON parsing error in the transversal analysis.
"""

import re
import json
from typing import Dict, Any


def fix_json_format(json_str: str) -> str:
    """
    Fix common JSON formatting errors like trailing commas.
    
    Args:
        json_str: The JSON string with potential formatting issues
        
    Returns:
        A properly formatted JSON string
    """
    # First, try to fix trailing commas in objects (dictionaries)
    # This regex looks for a comma followed by optional whitespace and then a closing brace
    json_str = re.sub(r',(\s*})', r'\1', json_str)
    
    # Fix trailing commas in arrays (lists)
    # This regex looks for a comma followed by optional whitespace and then a closing bracket
    json_str = re.sub(r',(\s*\])', r'\1', json_str)
    
    return json_str


def fix_transversal_json(json_response: str) -> Dict[str, Any]:
    """
    Try to fix and parse the transversal analysis JSON response.
    
    Args:
        json_response: The raw JSON response from the LLM
        
    Returns:
        Parsed JSON dictionary
    """
    try:
        # First try parsing the raw response
        return json.loads(json_response)
    except json.JSONDecodeError:
        # If it fails, apply fixes and try again
        fixed_json = fix_json_format(json_response)
        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError as e:
            # If still failing, extract JSON parts manually
            print(f"Could not fix JSON formatting, error: {e}")
            # Return empty structure with error
            return {
                'TOPIC_SUMMARIES': {'ERROR': f'Failed to parse JSON: {str(e)}'},
                'TOPIC_SUMMARY': f'Error parsing JSON: {str(e)}',
                'QUERY_ANSWER': f'Error parsing JSON: {str(e)}'
            }
