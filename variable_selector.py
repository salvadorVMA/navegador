### Module for selecting relevant variables from datasets based on user queries

from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

import pandas as pd
import tqdm
from typing import List, Any

from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser

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
    GRADE: float
    EXPLANATION: str

pattern_parser_grader = PydanticOutputParser(pydantic_object=PatternItemGrader)
pattern_format_grader_instrtuctions = pattern_parser_grader.get_format_instructions()


def create_prompt_grader(user_query, tmp_svvinfo_st ,format_instructions=""):
    """
    prompt for grading items against a query
    """
    prompt = f"""
You are an expert in survey research and you are fluent in English and Spanish. You will reply in English only.  
Your task is to read SURVEY INFORMATION and a user QUERY, and grade the relevance of the survey to the query.

THE SURVEY INFORMATION has 3 parts:
- QUESTION: the question asked in the survey
- SUMMARY: a summary of the survey results  
- IMPLICATIONS: expert analysis of the importance and applications of the results

The GRADE is a number between 0 and 3:
- 0: Survey is completely unrelated to the query
- 1: Survey has some connection but is mostly unrelated
- 2: Survey is moderately relevant - covers related topics
- 3: Survey is highly relevant - directly addresses the query

Grade based on overall relevance, not requiring all three parts to match perfectly.
Focus on whether the survey provides useful information for answering the user's question.

Examples:
QUERY: "What do people think about education?"
SURVEY: "QUESTION: How do you rate education quality? SUMMARY: 60% say it's good. IMPLICATIONS: This shows public satisfaction with education."
GRADE: 3 (Directly relevant - about education opinions)

QUERY: "What do people think about education?" 
SURVEY: "QUESTION: Do you support education funding? SUMMARY: 70% support more funding. IMPLICATIONS: Shows willingness to invest in education."
GRADE: 2 (Moderately relevant - related to education but about funding, not opinions)

QUERY: "What do people think about education?"
SURVEY: "QUESTION: How often do you exercise? SUMMARY: 40% exercise daily. IMPLICATIONS: Regular exercise improves health."  
GRADE: 0 (Unrelated - about exercise, not education)

Return strict JSON format:
{{
  "GRADE": number,
  "EXPLANATION": "explanation text"
}}

QUERY: {user_query}
SURVEY_INFORMATION: {tmp_svvinfo_st}

{format_instructions}
"""
    return prompt

def get_structured_summary_grader_p(prompt, model_name: str = mod_alto, temperature: float = 0.9):
    # This function combines the prompt creation and LLM call,
    # then parses the response using the PydanticOutputParser.

    content = get_answer(prompt, model=model_name, temperature=temperature)
    cleaned = clean_llm_json_output(content)
    
    try:
        parsed = pattern_parser_grader.parse(cleaned)
        result = parsed.model_dump()
        # Convert to the expected GRADE_DICT format for backward compatibility
        if 'GRADE' in result and 'EXPLANATION' in result:
            result['GRADE_DICT'] = {result['GRADE']: result['EXPLANATION']}
        else:
            result['GRADE_DICT'] = {0.0: "Parsing failed"}
        return cleaned, result
    except Exception as e:
        print("Parsing failed. Raw output:")
        print(content)
        print("Cleaned output:")
        print(cleaned)
        print("Error:", e)
        # Return a fallback structure with GRADE_DICT
        return cleaned, {'GRADE_DICT': {0.0: f"Error: {str(e)}"}}
    
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
    
    # Safely split keys and handle cases where '__' separator might not be present
    tmp_svyinfo_dict = {}
    for k, v in tmp_pre_res_dict.items():
        if k.startswith(tmp_id_st):
            split_key = k.split('__')
            if len(split_key) >= 2:
                key_type = split_key[1].upper()
                tmp_svyinfo_dict[key_type] = v
            else:
                # Handle keys without type suffix
                tmp_svyinfo_dict['CONTENT'] = v
    
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
    # Track timings for performance monitoring
    import time
    from datetime import datetime
    
    start_time = time.time()

    def log_batch_progress(batch_num, batch_size, total, elapsed):
        """Log progress of batch processing with timestamp"""
        timestamp = datetime.now().isoformat()
        percent = min(100, int((batch_num * batch_size / total) * 100))
        print(f"🔄 [{timestamp}] Batch {batch_num}: {percent}% complete, elapsed: {elapsed:.2f}s")

    # Prepare prompts and keys
    print(f"Preparing prompts for {len(top_ids)} variables...")
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
    print(f"Created {len(batches)} batches for processing")
    
    # Initialize results dictionary
    structured_results = {}
    
    # Process each batch
    batch_count = 0
    with tqdm.tqdm(total=len(keys), desc="Selecting and filtering questions") as pbar:
        for batch_docs, batch_keys in batches:
            batch_count += 1
            batch_start = time.time()
            
            # Log batch start
            batch_elapsed = time.time() - start_time
            log_batch_progress(batch_count, len(batch_keys), len(keys), batch_elapsed)
            
            for i, (prompt, key) in enumerate(zip(batch_docs, batch_keys)):
                try:
                    _, tmp_grade_dict = get_structured_summary_grader_p(prompt, model_name = model_name, temperature= 0.5)
                    structured_results[key] = tmp_grade_dict
                    
                    # Update more frequently for UI responsiveness
                    if (i + 1) % max(1, len(batch_keys) // 10) == 0:
                        pbar.update((i + 1) % max(1, len(batch_keys) // 10))
                except Exception as e:
                    print(f"⚠️ Error grading variable {key}: {str(e)}")
                    structured_results[key] = {'error': str(e)}
                pbar.update(1)
                
            # Log batch completion
            batch_time = time.time() - batch_start
            print(f"✓ Batch {batch_count} completed in {batch_time:.2f}s")
    
    return structured_results



def _database_selector(user_query: str, topic_id_st: str, llm: Any) -> List[str]:
    """
    Select relevant datasets based on the user's query.
    
    Args:
        user_query: The user's query about the datasets
        topic_id_st: String with topic information
        llm: Language model for reasoning
        
    Returns:
        A list of dataset abbreviations (e.g., ['EDU', 'CUL']) relevant to the query.
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
    Otherwise, from the list of available datasets below, you will select which ones most closely matches the user's query and return a list of their topic names (not abbreviations).

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
        selected_topics = parsed.selected_datasets
        
        # If 'all' is selected, return all topic IDs
        if 'all' in selected_topics:
            return list(rev_topic_dict.keys())
        
        # Map the selected display names back to abbreviations
        mapped_topics = []
        for topic_name in selected_topics:
            # Find the abbreviation for this topic name
            for abbrev, display_name in rev_topic_dict.items():
                if topic_name.lower() in display_name.lower() or display_name.lower() in topic_name.lower():
                    mapped_topics.append(abbrev)
                    break
        
        # If no mappings found, return all topics
        if not mapped_topics:
            print(f"Warning: Could not map topics {selected_topics} to abbreviations, using all topics")
            return list(rev_topic_dict.keys())
        
        return mapped_topics
        
    except Exception as e:
        print(f"Parsing failed in database_selector: {e}")
        return list(rev_topic_dict.keys())  # Return all topics as fallback


def retrieve_all_types_simultaneously(db_f1, query_emb, topic_ids=None, type_lst=None, n_results=100):
    """
    Retrieves documents from db_f1 filtered by topic IDs, using a single query for all types.
    This is more efficient than separate queries but may be less balanced across types.
    
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
        # Use all available topic IDs from rev_topic_dict
        topic_ids = list(rev_topic_dict.keys())
    
    print(f"🔍 Querying all types simultaneously in a single ChromaDB query")
    print(f"📊 Filtering by topics: {topic_ids}")
    
    # Single query for all types
    tmp_res_q = db_f1.query(
        query_embeddings=[query_emb],
        n_results=n_results * len(type_lst) * 2,  # Get more results to ensure we have enough per type # TODO: is this necessary?
        where={"type": {"$in": type_lst}}
    )
    
    [tmp_res_ids] = tmp_res_q['ids']
    [tmp_res_distances] = tmp_res_q['distances']
    
    print(f"   📋 Total results retrieved: {len(tmp_res_ids)}")
    

    # TODO: remover el análisis por tipo: todas las respuestas deben ser procesadas al mismo tiempo - no por separado
    # -- pero esto es lo que hace esta función, pero no es necesario reportarlos por separado, o sí? 
    # Group results by type and filter by topic_ids
    tmp_dist_dict = {doc_type: {} for doc_type in type_lst}
    
    for i, doc_id in enumerate(tmp_res_ids):
        # Extract the type and QID from the document ID
        id_parts = doc_id.split('__')
        if len(id_parts) == 2:
            qid_part, doc_type = id_parts
            
            # Check if this type is in our list and if the topic matches
            if doc_type in type_lst:
                # Check if any of the topic_ids is in the QID part
                if any(f"|{topic_id}" in qid_part for topic_id in topic_ids):
                    # Only add if we haven't reached the limit for this type
                    if len(tmp_dist_dict[doc_type]) < n_results:
                        tmp_dist_dict[doc_type][doc_id] = tmp_res_distances[i]
    
    # Report results per type
    for doc_type in type_lst:
        results_count = len(tmp_dist_dict[doc_type])
        print(f"   📋 {doc_type}: {results_count} results after topic filtering")
        
        if tmp_dist_dict[doc_type]:
            sample_ids = list(tmp_dist_dict[doc_type].keys())[:3]
            sample_qids = [id.split('__')[0] for id in sample_ids]
            print(f"      📝 Sample QIDs: {sample_qids}")
    
    return tmp_dist_dict

def retrieve_by_type_and_topics(db_f1, query_emb, topic_ids=None, type_lst=None, n_results=100):
    """
    Retrieves documents from db_f1 filtered by type and topic IDs.
    Uses separate queries per type to ensure balanced results across all types.
    
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
        # Use all available topic IDs from rev_topic_dict
        topic_ids = list(rev_topic_dict.keys())
    
    print(f"🔍 Querying each type separately to ensure balanced results")
    print(f"📊 Filtering by topics: {topic_ids}")
    
    tmp_dist_dict = {}
    
    for doc_type in type_lst:
        print(f"   🔎 Querying type: {doc_type}")
        
        # Query each type separately to ensure balanced results
        tmp_res_q = db_f1.query(
            query_embeddings=[query_emb],
            n_results=n_results * 3,  # Get more results to filter from
            where={"type": {"$eq": doc_type}}
        )
        
        [tmp_res_ids] = tmp_res_q['ids']
        [tmp_res_distances] = tmp_res_q['distances']
        
        # Filter results by topic_ids
        filtered_results = {}
        
        for i, doc_id in enumerate(tmp_res_ids):
            # Extract the QID portion from the document ID
            id_parts = doc_id.split('__')
            if len(id_parts) == 2:
                qid_part = id_parts[0]
                # Check if any of the topic_ids is in the QID part
                if any(f"|{topic_id}" in qid_part for topic_id in topic_ids):
                    filtered_results[doc_id] = tmp_res_distances[i]
                    if len(filtered_results) >= n_results:
                        break
        
        tmp_dist_dict[doc_type] = filtered_results
        print(f"      📋 {len(filtered_results)} results after topic filtering")
        
        if filtered_results:
            sample_ids = list(filtered_results.keys())[:3]
            sample_qids = [id.split('__')[0] for id in sample_ids]
            print(f"      📝 Sample QIDs: {sample_qids}")
    
    return tmp_dist_dict

def _variable_selector(user_query, topic_id_st, mod_setting, top_vals=30, use_simultaneous_retrieval=True):
    """
    Selects the top variables based on their relevance to the user query.
    
    Args:
        user_query: The user's query
        topic_id_st: Topic string for database selection  
        mod_setting: Language model for processing (can be string or LangChain ChatOpenAI)
        top_vals: Number of top variables to return
        use_simultaneous_retrieval: If True, use single query for all types. If False, use separate queries per type.
        
    Returns:
        dict: A dictionary of selected variables with their grades.
    """
    # Track the start time for performance monitoring
    import time
    from datetime import datetime
    start_time = time.time()
    
    # Define a function for detailed progress logging
    def log_progress(stage, details):
        """Log progress of variable selection with timestamp"""
        timestamp = datetime.now().isoformat()
        elapsed = time.time() - start_time
        print(f"📊 [{timestamp}] [{elapsed:.2f}s] {stage}: {details}")
    
    log_progress("variable_selection_start", f"Query: {user_query}")
    
    # Handle LangChain ChatOpenAI objects by extracting the model name
    if hasattr(mod_setting, 'model_name'):
        model_name = mod_setting.model_name
    elif hasattr(mod_setting, 'model'):
        model_name = mod_setting.model
    else:
        # Assume it's already a string
        model_name = mod_setting
    
    log_progress("model_identified", f"Using model: {model_name}")
    
    # Turn it into a vector
    print("Embedding the user query...")
    
    if use_simultaneous_retrieval:
        # For simultaneous retrieval, use the original query for balanced results
        query_emb = embedding_fun_openai([user_query])[0]
    else:
        # For separate retrieval, use enriched query to target implications
        enriched_query = enrich_query_for_implications(user_query)
        query_emb = embedding_fun_openai([enriched_query])[0]

    # tmp_dist_df contiene las distancias para los tres tipos/ facets, normalizadas entre 0 y 1

    # OJO: esto obviamente asume que los tres tipos de información tienen la misma importancia, lo cual no es inicialmente cierto.
    # Pero la mezcla de las tres calificaciones devuelve una variedad más amplia de resultados.  

    type_lst = [ "question", "summary", "implications"]
    tmp_dist_dict = {}

    topic_ids = _database_selector(user_query, topic_id_st, llm=mod_setting)

    log_progress("database_selection", f"Selected topics: {topic_ids}")
    
    # Use the specified retrieval method
    if use_simultaneous_retrieval:
        print("📊 Using simultaneous retrieval for all types (balanced query)")
        log_progress("retrieval_start", "Starting simultaneous retrieval")
        tmp_dist_dict = retrieve_all_types_simultaneously(
            db_f1, 
            query_emb, 
            topic_ids=topic_ids,
            type_lst=["question", "summary", "implications"],
            n_results=100
        )
    else:
        print("📊 Using separate retrieval queries per type (enriched query for implications)")
        log_progress("retrieval_start", "Starting separate retrieval by type")
        tmp_dist_dict = retrieve_by_type_and_topics(
            db_f1, 
            query_emb, 
            topic_ids=topic_ids,
            type_lst=["question", "summary", "implications"],
            n_results=100
        )
    
    log_progress("retrieval_complete", f"Retrieved {sum([len(docs) for docs in tmp_dist_dict.values()])} documents")


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

    log_progress("processing_start", "Creating DataFrame and normalizing scores")
    
    # Create a DataFrame where keys in every subdict are the index and keys in tmp_dist_dict are columns
    tmp_dist_df = pd.DataFrame.from_dict(tmp_dist_dict)

    # Normalize each column so that max = 1 and min = 0
    tmp_dist_df = (tmp_dist_df - tmp_dist_df.min()) / (tmp_dist_df.max() - tmp_dist_df.min())

    tmp_dist_df['mean'] = tmp_dist_df.mean(axis=1)
    tmp_dist_df.sort_values(by='mean', ascending=True, inplace=True)

    top_ids = tmp_dist_df.head(top_vals).index.tolist()
    
    log_progress("ranking_complete", f"Selected top {len(top_ids)} variables")

    tmp_list = []

    for type in type_lst:
        for id in top_ids:
            tmp_list.append(id + f'__{type}')

    # Retrieve documents using the list of ids
    if not tmp_list:
        print("Warning: No IDs to retrieve from ChromaDB")
        return topic_ids, {}, {}
        
    result_by_ids = db_f1.get(ids=tmp_list)
    
    # Handle case where no results are found
    if not result_by_ids or not result_by_ids.get('ids') or not result_by_ids.get('documents'):
        print("Warning: No documents retrieved from ChromaDB")
        return topic_ids, {}, {}

    # Type assertion since we've verified these are not None
    ids = result_by_ids['ids']
    documents = result_by_ids['documents']
    if ids is None or documents is None:
        print("Warning: Unexpected None values in ChromaDB result")
        return topic_ids, {}, {}
    
    tmp_pre_res_dict = dict(zip(ids, documents))

    ## generación del esquema de pydantic para la respuesta del evaluador de relevancia

    log_progress("grading_start", f"Starting expert grading with model {model_name}")
    
    # Create a progress bar for the grading process
    total_items = len(top_ids)
    print(f"Selecting and filtering questions: 0% | 0/{total_items}")
    
    # Perform batch processing with expert grader
    tst_res = batch_process_expert_grader(user_query, top_ids, tmp_pre_res_dict, model_name, batch_size=8192)
    
    # Handle case where grading fails
    if not tst_res:
        log_progress("grading_error", "No grading results returned")
        print("Warning: No grading results returned")
        return topic_ids, tmp_pre_res_dict, {}
        
    tmp_grade_dict = {k: v.get('GRADE_DICT', {}) for k, v in tst_res.items() if 'GRADE_DICT' in v}

    # Filter elements with grade > 0 (instead of > 1) for less strict filtering
    tmp_grade_dict = {k: v for k, v in tmp_grade_dict.items() if v and list(v.keys())[0] > 0}
    
    # Log completion with elapsed time
    elapsed = time.time() - start_time
    filtered_count = len(tmp_grade_dict)
    log_progress("grading_complete", 
                f"Selected {filtered_count} variables after filtering. Total processing time: {elapsed:.2f}s")
    
    return topic_ids, tmp_pre_res_dict, tmp_grade_dict

def enrich_query_for_implications(user_query: str) -> str:
    """
    Enriches the user query with context that targets the implications field for expert relevance.
    This improves retrieval by focusing on expert insights and policy implications.
    
    Args:
        user_query: The original user query
        
    Returns:
        Enhanced query string with implications-focused context
    """
    implications_context = """
    Find expert insights, policy implications, research significance, 
    practical applications, and professional recommendations related to:
    """
    
    enriched_query = f"{implications_context} {user_query}"
    
    # Add specific implications-focused keywords to improve semantic matching
    enhanced_query = f"{enriched_query} expert analysis implications significance policy recommendations research insights"
    
    return enhanced_query

