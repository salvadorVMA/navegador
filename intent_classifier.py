"""Module for classifying user intent in dataset interactions"""
from typing import Tuple, Any
from dataset_knowledge import DATASETS

def classify_intent(user_message: str, llm: Any) -> Tuple[str, str]:
    """
    Classify the user's intent and identify the dataset they're referring to
    
    Returns:
        Tuple containing (intent, dataset_name)
        Intent can be: "describe", "query", "general"
    """
    prompt = f"""
    Analyze the following user message and determine:
    1. The user's intent: Is the user asking for dataset description, querying a dataset, or asking a general question?
    2. Which dataset (if any) the user is referring to.
    
    Available datasets: {', '.join(DATASETS.keys())}
    
    User message: "{user_message}"
    
    Respond in JSON format:
    {{
        "intent": ["describe", "query", or "general"],
        "dataset": "[dataset name or 'none' if no specific dataset]"
    }}
    """
    
    response = llm.invoke(prompt)
    
    try:
        # Extract the response - in a real implementation, parse the JSON
        # This is simplified for the example
        if "describe" in response.content.lower():
            intent = "describe"
        elif "query" in response.content.lower():
            intent = "query"
        else:
            intent = "general"
            
        # Extract dataset name - simplified implementation
        for dataset in DATASETS.keys():
            if dataset in response.content.lower():
                return intent, dataset
                
        return intent, "none"
        
    except Exception as e:
        print(f"Error parsing intent classification: {e}")
        return "general", "none"
