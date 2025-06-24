### Module for selecting relevant variables from datasets based on user queries

from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

import pandas as pd
import tqdm
from typing import List, Any

from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser

from utility_functions import environment_setup, embedding_fun_openai, get_answer, clean_llm_json_output, batch_documents
from dataset_knowledge import rev_topic_dict,  tmp_topic_st


# LLM settings
mod_alto = 'gpt-4.1-2025-04-14' 
mod_bajo = 'gpt-4.1-nano-2025-04-14'
mod_med = 'gpt-4.1-mini-2025-04-14'

### SETUP

client, db_f1 = environment_setup(embedding_fun_openai)

#########


class PatternItemGrader(BaseModel):
    GRADE_DICT: dict[float, str] = {
        0.0: "",
    }

pattern_parser_grader = PydanticOutputParser(pydantic_object=PatternItemGrader)
pattern_format_grader_instrtuctions = pattern_parser_grader.get_format_instructions()


def create_prompt_grader(user_query, tmp_svvinfo_st ,format_instructions=""):
    """
    prompt for gradig items against a query
    """
    prompt = f"""
You are an expert in survey research and in qualitative research, and you are fluent in English and Spanish. You will reply in English only.  
Your task is to read the following SURVEY INFORMATION, and a user QUERY, and then grade the SURVEY INFORMATION against the QUERY and write a one-sentence explanation of your grade.

THE SURVEY INFORMATION has 3 parts
- QUESTION: the question asked in the survey
- SUMMARY: a summary of the results of the survey
- IMPLICATIONS: a statement of the importance of the results written by an expert in the field of the survey. 

The GRADE will will be a number between 0 and 3, where: 
- 0: the QUESTION and the SUMMARY are NOT relevant to the QUERY, and the IMPLICATIONS are NOT relevant to the QUERY
- 1: the QUESTION and the SUMMARY are NOT relevant to the QUERY, but the IMPLICATIONS seem relevant to the QUERY
- 2: the QUESTION and the SUMMARY are somewhat relevant to the QUERY, but the IMPLICATIONS seem relevant to the QUERY
- 3: the QUESTION and the SUMMARY are relevant to the QUERY, and the IMPLICATIONS are relevant to the QUERY

You will write a one-sentence EXPLANATION of your grade, paying attention to how QUESTION, SUMMARY and IMPLICATIONS are related to the QUERY. Be detailed and specific in your explanation.
IMPORTANT: return an EXPLANATION regardless of the GRADE, this is, explain all your grades, even if they are 0.
IMPORTANT: make sure to match your GRADE to your EXPLANATION, this is, that they correspond to the criteria above. 

Here are some examples of the GRADE and the explanation:
- EXAMPLE_QUERY : "Would selling strawberry ice cream is a good idea?"

- EXAMPLE_SURVEY_INFORMATION_1 : "QUESTION: Do you like strawberry ice cream? SUMMARY: 50% of people like strawberry ice cream. IMPLICATIONS: Selling strawberry ice cream is a good idea."
- EXAMPLE_GRADE_1 : 3
- EXAMPLE_EXPLANATION_1 : "The QUESTION is relevant to the QUERY because it asks about strawberry ice cream, the SUMMARY is relevant because it provides information about people's preferences, and the IMPLICATIONS are relevant because they suggest that selling strawberry ice cream is a good idea."

- EXAMPLE_SURVEY_INFORMATION_2 : "QUESTION: Do you like chocolate ice cream? SUMMARY: 50% of people like chocolate ice cream. IMPLICATIONS: Selling chocolate ice cream is a good idea."  
- EXAMPLE_GRADE_2 : 2
- EXAMPLE_EXPLANATION_2 : "The QUESTION is not relevant to the QUERY because it asks about chocolate ice cream, but the SUMMARY is relevant because it provides information about people's preferences, and the IMPLICATIONS are relevant because they suggest that selling chocolate ice cream is a good idea for alternate flavors."

- EXAMPLE_SURVEY_INFORMATION_3 : "QUESTION: Have you seen the movie 'Wild Strawberries' by Ingmar Bergman? SUMMARY: 50% of people have seen the movie. IMPLICATIONS: The movie is a classic and is worth watching."
- EXAMPLE_GRADE_3 : 1
- EXAMPLE_EXPLANATION_3 : "The QUESTION is not relevant to the QUERY because it asks about a movie, and the SUMMARY is not relevant because it talks about movies, not ice cream, and the IMPLICATIONS are seem relevant because they talk about a movie with 'ice cream' in the title."

- EXAMPLE_SURVEY_INFORMATION_4 : "QUESTION: How many times have you gone to the beach? SUMMARY: 50% of people go to the beach once a year. IMPLICATIONS: The beach is a popular destination."
- EXAMPLE_GRADE_4 : 0
- EXAMPLE_EXPLANATION_4 : "The QUESTION is not relevant to the QUERY because it asks about going to the beach, and the SUMMARY is not relevant because it talks about the beach, not ice cream, and the IMPLICATIONS are not relevant because they talk about a beach, not ice cream."

Example output (strict JSON, no markdown, no code block, no extra text).
{{
  GRADE: EXPLANATION
}}

QUERY: {user_query}
SURVEY_INFORMATION: {tmp_svvinfo_st}

{format_instructions}

Checklist before submitting:
- [ ] GRADE has been calculated.
- [ ] EXPLANATION has been written.
- [ ] No field is left empty.
"""
    return prompt

def get_structured_summary_grader_p(prompt, model_name: str = mod_alto, temperature: float = 0.9):
    # This function combines the prompt creation and LLM call,
    # then parses the response using the PydanticOutputParser.

    # prompt =create_prompt_grader(user_query=user_query, tmp_svvinfo_st= tmp_svvinfo_st, format_instructions=pattern_format_grader_instrtuctions)
    content = get_answer(prompt, model=model_name, temperature=temperature)
    content = clean_llm_json_output(content)
    parsed = pattern_parser_grader.parse(content)
    cleaned = clean_llm_json_output(content)
    try:
        parsed = pattern_parser_grader.parse(cleaned)
        return cleaned, parsed.model_dump()
    except Exception as e:
        print("Parsing failed. Raw output:")
        print(content)
        print("Cleaned output:")
        print(cleaned)
        print("Error:", e)
        return cleaned, {}
    
def create_tmp_svyinfo_dict(tmp_ky, top_ids, tmp_pre_res_dict):
    """         
    Create a temporary survey information dictionary for a given key.
    Args:
        tmp_ky (int): The index of the key in the top_ids list.
        top_ids (list): The list of top IDs.
        tmp_pre_res_dict (dict): The dictionary containing preprocessed results.
    Returns:

        dict: A dictionary containing the survey information for the specified key.
    """
    # Create a temporary survey information dictionary for a given key
    tmp_id_st = top_ids[tmp_ky]
    tmp_svyinfo_dict = {k.split('__')[1].upper(): v for k,v in tmp_pre_res_dict.items() if k.startswith(tmp_id_st)}
    tmp_svvinfo_st = ' '.join([f'{k}: {v}' for k,v in tmp_svyinfo_dict.items()])
    return tmp_svvinfo_st

def batch_process_expert_grader(user_query, top_ids, tmp_pre_res_dict, model_name , batch_size=8192):
    """
    Processes expert summaries in batches, saving checkpoints after each batch.

    Parameters:
        top_ids (list): List of variables to grade.
        tmp_pre_res_dict (dict): Dict with survey results.
        batch_size (int): Maximum token limit for each batch.

    Returns:
        dict: A dictionary of structured results.
    """


    # Prepare prompts and keys
    prompts = [
        create_prompt_grader(user_query,  
                             create_tmp_svyinfo_dict(tmp_ky, top_ids, 
                                                     tmp_pre_res_dict),
                                                     format_instructions=pattern_format_grader_instrtuctions)
        for tmp_ky in range(len(top_ids))
    ]
    keys = top_ids
    
    # Batch the documents
    batches = batch_documents(prompts, keys, max_tokens=batch_size, encoding_name="cl100k_base")
    
    # Initialize results dictionary
    structured_results = {}
    
    # Process each batch
    with tqdm.tqdm(total=len(keys), desc="Selecting and filtering questions") as pbar:
        for batch_docs, batch_keys in batches:
            for prompt, key in zip(batch_docs, batch_keys):
                try:
                    _, tmp_grade_dict = get_structured_summary_grader_p(prompt, model_name = model_name, temperature= 0.5)
                    #print(f'tmp_grade_dict: {tmp_grade_dict}')
                    structured_results[key] = tmp_grade_dict
                except Exception as e:
                    structured_results[key] = {'error': str(e)}
                pbar.update(1)
    
    return structured_results



def _database_selector(user_query: str, topic_id_st: str, llm: Any) -> List[str]:
    """
    Select relevant datasets based on the user's query.
    
    Args:
        user_query: The user's query about the datasets
        topic_id_st: String with topic information
        llm: Language model for reasoning
        
    Returns:
        A list of dataset names relevant to the query.
    """
    
    # Define Pydantic model for structured output
    class DatasetSelectionResponse(BaseModel):
        selected_datasets: List[str]
        reasoning: str = ""
        
    pattern_parser = PydanticOutputParser(pydantic_object=DatasetSelectionResponse)
    format_instructions = pattern_parser.get_format_instructions()
    
    # Use LLM to select relevant datasets
    prompt = f"""
    You will read the user query and select one or more of the datasets listed in the topic list. 
    If the user asks to use all datasets, you will return a list containing the string 'all'.
    Otherwise, from the list of available datasets below, you will select which ones most closely matches the user's query and return a list of their topic IDs.

    IMPORTANT: note that the topic list contains a list of elements with the following format: '* ABC|Topic description' where * marks the start of an element if the list, and ABC is the topic ID. 
    IMPORTANT: if the user request is not specific enough to select a dataset or you do not have enough information to choose a dataset, you should inform them that you cannot answer that question and suggest they ask about the available datasets.
    In this case, you should return 'all'.
    
    User query: "{user_query}"
    
    Available datasets:
    {tmp_topic_st}
    
    {format_instructions}
    """
    
    response = llm.invoke(prompt)
    
    try:
        parsed = pattern_parser.parse(response.content if hasattr(response, 'content') else str(response))
        return parsed.selected_datasets
    except Exception as e:
        print(f"Parsing failed in database_selector: {e}")
        return ["all"]


def retrieve_by_type_and_topics(db_f1, query_emb, topic_ids=None, type_lst=None, n_results=100):
    """
    Retrieves documents from db_f1 filtered by type and topic IDs.
    
    Args:
        db_f1: ChromaDB collection
        query_emb: Query embedding vector
        topic_ids: List of topic IDs (e.g., ['IDE', 'MED', 'POB']) or None for all topics
        type_lst: List of types (e.g., ["question", "summary", "implications"]) or None for all types
        n_results: Number of results to return per type
        
    Returns:
        dict: Dictionary with type as key and {ids: distances} as values
    """
    
    if type_lst is None:
        type_lst = ["question", "summary", "implications"]
    
    if topic_ids is None or topic_ids == ['all']:
        # Use all available topic IDs from rev_enc_nom_dict
        topic_ids = list(rev_topic_dict.keys())
    
    tmp_dist_dict = {}
    
    for doc_type in type_lst:
        print(f"Querying for type: {doc_type}")
        
        # Build the where clause
        if len(topic_ids) == 1:
            # Single topic ID - use simple contains
            where_clause = {
                "type": doc_type,
                "qid": {"$contains": f"|{topic_ids[0]}"}
            }
        else:
            # Multiple topic IDs - use $or with multiple $contains
            topic_conditions = [{"qid": {"$contains": f"|{topic_id}"}} for topic_id in topic_ids]
            where_clause = {
                "$and": [
                    {"type": doc_type},
                    {"$or": topic_conditions}
                ]
            }
        
        tmp_res_q = db_f1.query(
            query_embeddings=[query_emb],
            n_results=n_results,
            where=where_clause
        )
        
        [tmp_res_ids] = tmp_res_q['ids']
        [tmp_res_distances] = tmp_res_q['distances']
        
        tmp_dist_dict[doc_type] = dict(zip(tmp_res_ids, tmp_res_distances))
    
    return tmp_dist_dict

def _variable_selector(user_query, topic_id_st, mod_setting, top_vals=30):
    """
    Selects the top variables based on their relevance to the user query.
    Returns:
        dict: A dictionary of selected variables with their grades.
    """
    # Turn it into a vector
    print("Embedding the user query...")
     # embedding_fun_openai is defined above
    query_emb = embedding_fun_openai([user_query])[0]

    # tmp_dist_df contiene las distancias para los tres tipos/ facets, normalizadas entre 0 y 1

    # OJO: esto obviamente asume que los tres tipos de información tienen la misma importancia, lo cual no es inicialmente cierto.
    # Pero la mezcla de las tres calificaciones devuelve una variedad más amplia de resultados.  

    type_lst = [ "question", "summary", "implications"]
    tmp_dist_dict = {}

    topic_ids = _database_selector(user_query, topic_id_st, llm=mod_setting)

    # Use the enhanced retriever
    tmp_dist_dict = retrieve_by_type_and_topics(
        db_f1, 
        query_emb, 
        topic_ids=topic_ids,
        type_lst=["question", "summary", "implications"],
        n_results=100
    )


    # # TODO: agregar filtro where para filtrar por dataset si dataset != 'all'
    # # dataset != 'all' es una lista de uno o más 'ABC' para filtrar las llaves ... 
    # if dataset == 'all':
    #     for type in type_lst:
    #         print(f"Querying for type: {type}")
    #         tmp_res_q = db_f1.query(
    #             query_embeddings = [query_emb],
    #             n_results        = 100,  # devuelvo 100 resultados para cada tipo con distancias menores
    #             where            = {"type": type}
    #         )
    #         [tmp_res_ids] = tmp_res_q['ids']
    #         [tmp_res_distances] = tmp_res_q['distances']

    #         tmp_dist_dict[type]= dict(zip(tmp_res_ids, tmp_res_distances))
    # else:
    #     # If dataset is not 'all', filter by dataset
    #     for type in type_lst:
    #         print(f"Querying for type: {type} and dataset: {dataset}")
    #         tmp_res_q = db_f1.query(
    #             query_embeddings = [query_emb],
    #             n_results        = 100,  # devuelvo 100 resultados para cada tipo con distancias menores
    #             where            = {"type": type}# TODO: confirmar esta: {"type": type, "dataset": dataset}
    #         )
    #         [tmp_res_ids] = tmp_res_q['ids']
    #         [tmp_res_distances] = tmp_res_q['distances']

    #         tmp_dist_dict[type]= dict(zip(tmp_res_ids, tmp_res_distances))

    # remove the suffixes from the keys
    tmp_dist_dict = { outer_key: { k.split('__')[0]: v for k, v in inner_dict.items() }
        for outer_key, inner_dict in tmp_dist_dict.items() }

    # Create a DataFrame where keys in every subdict are the index and keys in tmp_dist_dict are columns
    tmp_dist_df = pd.DataFrame.from_dict(tmp_dist_dict)

    # Normalize each column so that max = 1 and min = 0
    tmp_dist_df = (tmp_dist_df - tmp_dist_df.min()) / (tmp_dist_df.max() - tmp_dist_df.min())


    tmp_dist_df['mean'] = tmp_dist_df.mean(axis=1)
    tmp_dist_df.sort_values(by='mean', ascending=True, inplace=True)

    top_ids = tmp_dist_df.head(top_vals).index.tolist()

    tmp_list = []

    for type in type_lst:
        for id in top_ids:
            tmp_list.append(id + f'__{type}')


    # Retrieve documents using the list of ids
    result_by_ids = db_f1.get(ids=tmp_list)

    tmp_pre_res_dict = dict(zip(result_by_ids['ids'], result_by_ids['documents']))

    ## generación del esquema de pydantic para la respuesta del evaluador de relevancia


    tst_res = batch_process_expert_grader(user_query, top_ids, tmp_pre_res_dict, mod_setting, batch_size=8192)
    tmp_grade_dict=  {k: v['GRADE_DICT'] for k, v in tst_res.items()}

    # Filtrar los elementos que tienen una calificación mayor a 1

    tmp_grade_dict= {k: v for k, v in tmp_grade_dict.items() if list(v.keys())[0] >1 }

    return topic_ids, tmp_pre_res_dict, tmp_grade_dict

