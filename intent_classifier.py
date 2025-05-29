"""Module for classifying user intent in dataset interactions"""
from typing import Tuple, Any
from dataset_knowledge import DATASETS



def classify_intent(user_message: str, llm: Any) -> Tuple[str, str]: # falta parser, etc.
    """
    Classify the user's intent and identify the dataset, variables, and analysis tipe they request
    
    Returns:
        Tuple containing (intent, dataset_name)
        Intent can be: "describe", "query", "general"
    """

    intent_lst= ["ANSWER GENERAL QUESTIONS", 
                 "QUERY VARIABLE_DATABASE", 
                 "REFINE VARIABLE SELECTION", 
                 "REFINE DATASET SELECTION", 
                 "SELECT ANALYSIS TYPE", 
                 "CONFIRM OPTIONS", 
                 "RUN ANALYSIS", 
                 "END CONVERSATION"]

    prompt = f"""
    You are a helpful asisstant that helps users interact with a group of survey datasets. 
    You will analyze the following message and determine the user's intent and determine the action to take. 
    
    These are the actions that you may take from the user's intent:

      1) ANSWER GENERAL QUESTIONS ABOUT THE PROJECT AND DATASETS,
      2) QUERY VARIABLE_DATABASE,
      3) REFINE VARIABLE SELECTION, 
      4) REFINE DATASET SELECTION,
      5) SELECT ANALYSIS TYPE,
      6) CONFIRM DATASET, VARIABLES AND ANALYSIS TYPE,
      7) RUN ANALYSIS AND RETURN RESULTS -CURRENTLY IN PDF ONLY-,
      8) END CONVERSATION.

    If the user wants to know what things you can do, you can provide a list of only these available actions.

    User message: "{user_message}"
    
    Respond in JSON format:
    {{
        "intent": "{intent_lst}",
    }}
    """
    
    response = llm.invoke(prompt)
    
    # TODO: agregar parser, etc. 

    # try:
    #     # Extract the response - in a real implementation, parse the JSON
    #     # This is simplified for the example
    #     if "describe" in response.content():
    #         intent = "describe"
    #     elif "query" in response.content():
    #         intent = "query"
    #     else:
    #         intent = "general"
                
    # return intent, "none"
        
    # except Exception as e:
    #     print(f"Error parsing intent classification: {e}")
    #     return "general", "none"
