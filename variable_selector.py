"""Module for selecting relevant variables from datasets based on user queries"""
from typing import List, Any
from dataset_knowledge import get_variables

def select_variables(user_query: str, dataset_name: str, llm: Any) -> List[str]:
    """
    Select relevant variables from a dataset based on the user's query
    
    Args:
        user_query: The user's query about the dataset
        dataset_name: Name of the dataset
        llm: Language model for reasoning
        
    Returns:
        List of variable names relevant to the query
    """
    # Get all variables for the dataset
    all_variables = get_variables(dataset_name)
    
    if not all_variables:
        return []
        
    # Use LLM to select relevant variables
    prompt = f"""
    Based on the user's query about the {dataset_name} dataset, select the most relevant variables.
    
    User query: "{user_query}"
    
    Available variables in the {dataset_name} dataset:
    {', '.join(all_variables)}
    
    Return only the variable names most relevant to answering this query, as a comma-separated list.
    Your selection should be focused on what's needed to answer the query effectively.
    """
    
    response = llm.invoke(prompt)
    
    # Parse the response - in a real implementation, use more robust parsing
    selected_vars = []
    for var in all_variables:
        if var in response.content:
            selected_vars.append(var)
            
    # If somehow no variables were selected, return a sensible default
    if not selected_vars and all_variables:
        return all_variables[:3]  # Return the first few as a fallback
        
    return selected_vars
