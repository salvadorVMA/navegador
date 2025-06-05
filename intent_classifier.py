"""Module for classifying user intent in dataset interactions"""
from typing import Tuple, Any
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from utility_functions import get_answer, clean_llm_json_output

intent_dict= {
    "answer_general_questions": "If the user asks questions about the project, the datasets, the methodology or the team involved, you should return answer_general_questions.",
    "query_variable_database": "If the user asks a particular question that should be answered by querying the variables in the database, but are not about the project, the datasets, the methodology or the theam involved, you should return query_variable_database.",
    "review_variable_selection": "If the user asks to review the selection of variables by adding or removing questions or topics, you should return review_variable_selection.",
    "select_analysis_type": "If the user asks for either simple or complex analysis of the selected variables, you should return select_analysis_type.",
    "confirm_and_run": "If the user asks to produce an analysis or report, you should return confirm_and_run.",
    "reset_conversation": "If the user asks to start the conversation over, you should return reset_conversation.",
    "continue_conversation": "If the user asks what you can do, you should return a description of the available actions you can perform, and return intent 'continue_conversation'.",
    "end_conversation": "If the user asks to end the conversation, you should return end_conversation."
}

def classify_intent(user_message: str, intent_dict: dict, llm: Any) -> Tuple[str, str]: # falta parser, etc.
    """
    Classify the user's intent and identify the dataset, variables, and analysis tipe they request
    
    Returns:
        Tuple containing (intent, dataset_name)
        Intents are included in intent_dict, which maps action names to conditions for performing the action.
    """

    intent_str = "\n".join([f"*{act}: {cond}" for act, cond in intent_dict.items()])

    prompt = f"""
    You are a helpful asisstant that helps users interact with a group of survey datasets. 
    You will return a response and an intent, which is one of the following actions you can take.

    If the user wants to know what things you can do, you can provide a list of only these available actions in your response. Otherwise, you will you will return an empty string as response.

    You will read the user's message and classify their intent based on the actions you can take.
    Note that you can only perform one action at a time, and you will return the intent of the action the user requested.
    Note the format of the actions is: "*action_name: condition to perform action". You will return action_name only for the action you choose. 
    Here is the list of actions you can take:
    {intent_str}
    
    User message: "{user_message}"
    
    Respond in JSON format:
    {{
        "intent": str,
        "response": str
    }}
    """
    
    response = llm.invoke(prompt)
    
    # objetos para el parser y formato de salida
    class PatternIntentClass(BaseModel):
        var_review_action_dict: dict[str, str] = {
            "intent": "",
            "response": ""
        }

    pattern_parser_IntentClass = PydanticOutputParser(pydantic_object=PatternIntentClass)
    pattern_format_grader_IntentClass = pattern_parser_IntentClass.get_format_instructions()


    # prompt =create_prompt_grader(user_query=user_query, tmp_svvinfo_st= tmp_svvinfo_st, format_instructions=pattern_format_grader_instrtuctions)
    content = get_answer(prompt, model=llm, temperature=0.0)
    content = clean_llm_json_output(content)
    parsed = pattern_parser_IntentClass.parse(content)
    cleaned = clean_llm_json_output(content)
    try:
        parsed = pattern_parser_IntentClass.parse(cleaned)
        return cleaned, parsed.model_dump()
    except Exception as e:
        print("Parsing failed. Raw output:")
        print(content)
        print("Cleaned output:")
        print(cleaned)
        print("Error:", e)
        return cleaned, {}


