"""Module for classifying user intent in dataset interactions"""
from typing import Tuple, Any, Dict
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from utility_functions import get_answer, clean_llm_json_output

intent_dict= {
    "answer_general_questions": "If the user asks questions about the project, the datasets, the methodology or the team involved, you should return answer_general_questions.",
    "continue_conversation": "If the user asks what you can do, you should return a description of the available actions you can perform, and return intent 'continue_conversation'.",
    "query_variable_database": "If the user asks a particular question that should be answered by querying the variables in the database, but are not about the project, the datasets, the methodology or the theam involved, you should return query_variable_database.",
    "review_variable_selection": "If the user asks to review the selection of variables by adding or removing questions or topics, you should return review_variable_selection.",
    "select_analysis_type": "If the user asks for either simple or complex analysis of the selected variables, you should return select_analysis_type.",
    "confirm_and_run": "If the user asks to produce an analysis or report, you should return confirm_and_run.",
    "reset_conversation": "If the user asks to start the conversation over, you should return reset_conversation.",
    "end_conversation": "If the user asks to end the conversation, you should return end_conversation."
}

def _classify_intent(user_message: str, intent_dict: dict, llm: Any) -> str:
    """
    Classify the user's intent based on the user message
    
    Args:
        user_message: The user's input message
        intent_dict: Dictionary mapping intent names to their descriptions
        llm: The language model to use for classification
        
    Returns:
        String containing the classified intent name
    """

    intent_str = "\n".join([f"*{act}: {cond}" for act, cond in intent_dict.items()])

    # objetos para el parser y formato de salida
    class PatternIntentClass(BaseModel):
        intent: str = ""
        confidence: float = 0.0

    pattern_parser_IntentClass = PydanticOutputParser(pydantic_object=PatternIntentClass)
    pattern_format_grader_IntentClass = pattern_parser_IntentClass.get_format_instructions()

    prompt = f"""
    You are an intent classifier for a dataset analysis assistant. 
    You must classify the user's intent based on their message into exactly one of the available intents.

    Available intents and their descriptions:
    {intent_str}
    
    User message: "{user_message}"
    
    Rules:
    - Choose ONLY ONE intent from the list above
    - If the user asks about analyzing variables or querying data, choose "query_variable_database"
    - If the user asks general questions about the project or datasets, choose "answer_general_questions"
    - If the user asks what you can do, choose "continue_conversation"
    - If the user wants to approve/modify variable selections, choose "review_variable_selection"
    - If the user wants to select analysis type (simple/complex/detailed/descriptive), choose "select_analysis_type"
    - If the user wants to run/execute analysis, choose "confirm_and_run"
    - If the user wants to reset, choose "reset_conversation"
    - If the user wants to end conversation, choose "end_conversation"
    
    Respond with the exact intent name only.
    
    {pattern_format_grader_IntentClass}
    """
    
    try:
        # Use get_answer with a model name string instead of llm object
        content = get_answer(prompt, model='gpt-4o-mini-2024-07-18', temperature=0.0)
        content = clean_llm_json_output(content)
        parsed = pattern_parser_IntentClass.parse(content)
        return parsed.intent
    except Exception as e:
        print(f"Intent classification failed. Error: {e}")
        # Default fallback intent
        return "continue_conversation"


