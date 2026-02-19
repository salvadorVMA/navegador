## Módulo para confirmar la selección de variables

### Module for selecting relevant variables from datasets based on user queries

from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser

from utility_functions import environment_setup, embedding_fun_openai, get_answer, clean_llm_json_output, batch_documents

from utility_functions import get_answer, clean_llm_json_output
from variable_selector import _variable_selector
from dataset_knowledge import rev_topic_dict,  tmp_topic_st

# Module for reviewing and modifying variable selections based on user feedback
# LLM settings
mod_alto = 'gpt-4.1-2025-04-14' 
mod_bajo = 'gpt-4.1-nano-2025-04-14'
mod_med = 'gpt-4.1-mini-2025-04-14'

### SETUP

client, db_f1 = environment_setup(embedding_fun_openai)

#########
def _variable_reviewer(user_query: str, user_feedback: str, tmp_pre_res_dict_in: dict[str, str], tmp_grade_dict_in: dict[str, str]) -> dict[str, Any]:
    

    # tmp_pre_res_dict, tmp_grade_dict llegan con el llamado a variable_reviewer.p
    tmp_preproc_dic_in  = {k: v for k, v in tmp_pre_res_dict_in.items() if k.split('__')[1] in ['question'] }

    # filtro de las preguntas relevantes
    tmp_preproc_dic_in ={k: v for k, v in tmp_preproc_dic_in.items() if any(k.startswith(grade_key) for grade_key in tmp_grade_dict_in.keys())}

    tmp_combined_strings = []

    for i, (k, v) in enumerate(tmp_preproc_dic_in.items(), start=1):
        facet = k.split("__", 1)[1].upper()
        p_id = k

        q_id = v.split("|")[0]
        parts = v.split("|", 1)
        text = parts[1] if len(parts) > 1 else parts[0]

        p_id = p_id.split("__")[0]

        tmp_combined_strings.append(f"{p_id}: {text}")

    # tmp_res_st es el string con las variables filtradas - contiene sólo las preguntas
    tmp_res_st = '\n'.join(tmp_combined_strings)

    # objetos para el parser y formato de salida
    class PatternVarRevAction(BaseModel):
        var_review_action_dict: dict[str, str] = {
            "ACTION": "",
            "QUESTION_IDS": "",
            "USER_QUERY": ""
        }

    pattern_parser_VarRevAction = PydanticOutputParser(pydantic_object=PatternVarRevAction)
    pattern_format_grader_VarRevAction = pattern_parser_VarRevAction.get_format_instructions()

    # prompt
    def create_prompt_var_reviewer(user_query, user_feedback, tmp_res_st ,format_instructions=""):
        """
        prompt for selecting items against a query
        """
        prompt = f"""
    Your task is to review a list of survey questions that have been selected based on a user query and modify it according to the USER FEEDBACK. 
    You will read a list of question IDs and their associated questions, as well as the USER FEEDBACK. 
    Note that the question IDs have format 'question_id|table_id' (e.g., pxx|YYY where xx is any combination of numbers and '_', and YYY are any three capital letters). 

    To modify the list, you have to read the USER FEEDBACK and choose one of the following actions:
    1. ADD_QUERY: if the user asks to add questions by topic or area of interest, but not the specific question IDs, you will summarize the user original query and the new feedback in the langugue of the query, and retrun a single phrase to query the vector database.
        For example: if the user QUERY is "do people like strawberry ice cream?" and the SELECTED_QUESTION contains item 'p01|ABC: Do you like strawberry ice cream?', and the user USER FEEDBACK is "add questions about chocolate ice cream", you will return the USER_QUERY as "do people like strawberry or chocolate ice cream?".
        You will return field SELECTED QUESTIONS as an emtpy list. 
    In any other case, you will return the USER_QUERY as an empty string.    
    2. ADD_QUESTION: if the user asks to add specific question IDs,  you will return them in the QUESTION_IDS field. Make sure with format format 'question_id|table_id' (e.g., pxx|YYY where xx is any combination of numbers and '_', and YYY are any three capital letters). 
    3. REMOVE_QUERY: if the user asks to remove questions by topic or area of interest, but not the specific question IDs, you will select the questions IDs that apply to the user request and return them in the QUESTION_IDS field.
    4. REMOVE_QUESTION: if the user asks to remove specific question IDs, you will return them in the QUESTION_IDS field. If the user requested any variable that is not in the current selection, you will return a string containg 'variable xxx NOT FOUND' in the QUESTION_IDS field, where xxx is the variable name that the user requested to remove.
    5. RESTART_QUERY: if the user asks to start over and select new questions based on a new query.
    6. NO_CHANGE: if the user feedback is not applicable or does not require any changes to the current selection.

    You will retun a JSON object with the following fields:
    ```json
    {
    "ACTION": "ADD_QUERY" | "ADD_QUESTION" | "REMOVE_QUERY" | "REMOVE_QUESTION" | "RESTART_QUERY" | "NO_CHANGE",
    "QUESTION_IDS": "the question IDs that the user mentioned to add or remove, separated by commas, or an empty string if not applicable",
    "USER_QUERY": 'the new information that the user requested to add to the variable query, or an empty string if not applicable',
    } ``` 

    QUERY: {user_query}             
    USER FEEDBACK: {user_feedback}
    SELECTED QUESTIONS: {tmp_res_st}
    {format_instructions}
    """
        return prompt

    # llamada al LLM para revisar variables
    # TODO: recuperar en agent.py la primera pregunta user_query y el último comentario como user_feedback

    prompt= create_prompt_var_reviewer(
        user_query=user_query, 
        user_feedback=user_feedback, 
        tmp_res_st=tmp_res_st, 
        format_instructions=pattern_format_grader_VarRevAction
    )


    content = get_answer(prompt, model=mod_bajo, temperature=0.0)
    content = clean_llm_json_output(content)
    # parsed = pattern_parser_VarRevAction.parse(content)

    tst= pattern_parser_VarRevAction.parse(content)
    var_review_action_dict = tst.model_dump()["var_review_action_dict"]


    tmp_act = var_review_action_dict["ACTION"]

    return_dict = {}
    return_dict['action_message'] = ""
    return_dict[tmp_act] = {}

    if tmp_act == "ADD_QUERY":
        tmp_query = var_review_action_dict["USER_QUERY"]

        # TODO: generalizar a todos los datasets o a un dataset específico
        dataset= 'all'  # 'all' for all variables, or a specific variable name

        _, tmp_pre_res_dict_out, tmp_grade_dict_out, _ = _variable_selector(tmp_query, dataset, mod_alto, top_vals=30)
        return_dict[tmp_act]['tmp_pre_res_dict_out'] = tmp_pre_res_dict_out
        return_dict[tmp_act]['tmp_grade_dict_out'] = tmp_grade_dict_out
        return_dict['action_message'] = f"Added query: {tmp_query}. New variables selected based on the query."

    elif tmp_act == "ADD_QUESTION":
        # Remove the specified question IDs from the selection
        question_ids_to_add = var_review_action_dict["QUESTION_IDS"].split(",")
        print(f"Adding question IDs: {question_ids_to_add}")


        tmp_tst_pgs_dict = {k.split('__')[0]: v for k, v in tmp_pre_res_dict_in.items() if k.split('__')[1] in ['question'] }

        tmp_pregs_add_lst = []
        tmp_pregs_noid_lst = []

        for name in question_ids_to_add:
            if name in tmp_tst_pgs_dict.keys():
                tmp_pregs_add_lst.append(name)
            else:
                tmp_pregs_noid_lst.append(name)
        return_dict['action_message'] = f"added questions: {tmp_pregs_add_lst}. Questions not found: {tmp_pregs_noid_lst}"

        print(f"Preguntas a agregar: {tmp_pregs_add_lst}")
        print(f"Preguntas no encontradas: {tmp_pregs_noid_lst}")

    elif var_review_action_dict["ACTION"] == "REMOVE_QUESTION":
        # Remove the specified question IDs from the selection
        question_ids_to_remove = var_review_action_dict["QUESTION_IDS"].split(",")
        print(f"Removing question IDs: {question_ids_to_remove}")


        tmp_tst_pgs_dict = {k.split('__')[0]: v for k, v in tmp_pre_res_dict_in.items() if k.split('__')[1] in ['question'] }

        tmp_pregs_drop_lst = []
        tmp_pregs_noid_lst = []

        for name in question_ids_to_remove:
            if name in tmp_tst_pgs_dict.keys():
                tmp_pregs_drop_lst.append(name)
            else:
                tmp_pregs_noid_lst.append(name)

        tmp_pre_res_dict_out = {k: v for k, v in tmp_pre_res_dict_in.items() if k.split('__')[0] not in tmp_pregs_drop_lst}

        return_dict['action_message'] = f"dropped questions: {tmp_pregs_drop_lst}. Questions not found: {tmp_pregs_noid_lst}"

        print(f"Preguntas a eliminar: {tmp_pregs_drop_lst}")
        print(f"Preguntas no encontradas: {tmp_pregs_noid_lst}")

    elif var_review_action_dict["ACTION"] == "REMOVE_QUERY":
        return_dict['action_message'] = f"user requested dropping topic, which is not currently possible. Query reset was recommended."
        print(f'{var_review_action_dict['USER_QUERY']}')

    elif var_review_action_dict["ACTION"] == "NO_CHANGE":
        return_dict['action_message'] = f"user did not request any changes to the variable selection."

        print("No changes to the variable selection.")

    else:
        return_dict['action_message'] = f"Unknown action: {var_review_action_dict['ACTION']}"

        print(f"Unknown action: {var_review_action_dict['ACTION']}")
        return_dict["error"] = "Unknown action"



