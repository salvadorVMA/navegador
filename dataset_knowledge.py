"""Module for managing dataset information and metadata"""

import pickle

ruta_enc= '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/'
ruta_rep= '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/reportes/'
ruta_tmp_images= '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/tmp_images/'

with open(f'{ruta_enc}/los_mex_dict.pkl', 'rb') as f:
    los_mex_dict = pickle.load(f)
    print('los_mex_dict cargado --  leer readme_dict para info')


enc_dict = los_mex_dict['enc_dict']
enc_nom_dict = los_mex_dict['enc_nom_dict']
rev_enc_nom_dict = {v: k for k, v in enc_nom_dict.items()}

# Generar un string con los temas de las encuestas y sus identificadores
rev_topic_dict = {k: v.replace('_', ' ').lower() for k, v in rev_enc_nom_dict.items()}
topic_id_st = '\n'.join(['|'.join(['* ' + a, b]) for a, b in rev_topic_dict.items()])

pregs_dict = los_mex_dict['pregs_dict']
ses_dict = los_mex_dict['ses_dict']
mkdown_tables = los_mex_dict['mkdown_tables']
df_tables = los_mex_dict['df_tables']


tmp_topic_lst = enc_nom_dict.keys()

tmp_topic_st= ', '.join([st.replace('_', ' ').title() for st in tmp_topic_lst])

# prompt para descripción
tmp_data_describer_st = f"""
    General information about the project: 
    -Name: "Los mexicanos vistos por sí mismos"
    -Description: This project is a group of {len(tmp_topic_st)} public opinion surveys conducted in Mexico between 2014 and 2015,
    -Topics: {tmp_topic_st}.
    -Objective: To understand the Mexican population's opinions on various topics, including politics, society, culture, and economics.
    -Team: Mtra. Julia Flores coordinated the team at the "Unidad de Investigación en Opinión Pública" and a group of experts in each of the topics, who designed the questionnaires, analyzed the data and wrote a book for each topic.
    -Repository: Datasets and the books written with the results of each survey are available at http://www.losmexicanos.unam.mx/
    -Sponsor: "Universidad Nacional Autónoma de México" (UNAM)
    -Samples: All samples are have a size of 1000 and are representative of the Mexican population, with a margin of error of 3% and a confidence level of 95%."""

# TODO: extraerá un sólo string con la descripción de los datasets y el proyecto, para que el LLM pueda responder preguntas generales sobre el proyecto y los datasets.
from typing import List, Any

def project_describer(user_query: str, tmp_data_describer_st: str, llm: Any) -> List[str]:
    """
    Answer general questions about the project and datasets based on the user's query.
    
    Args:
        user_query: The user's query about the dataset
        tmp_data_describer_st: Predefined string with project and dataset information
        llm: Language model for reasoning
        
    Returns:
        A string with the relevant information about the project and datasets.
    """
        
    # Use LLM to select relevant variables
    prompt = f"""
    You are a helpful assistant who will answer general questions about a survey project. 
    Read the general description of the survey project and reply with the relevant information to the user's query. 
    IMPORTANT: If the user asks about specific variables or items from the datasets, you should redirect them to the QUERY VARIABLE_DATABASE action.
    IMPORTANT: If you do not have enough information to answer the user's query, you should inform them that you cannot answer that question and suggest they ask about the available datasets or specific variables.
    
    General description of the project and datasets:
    {tmp_data_describer_st} 
    
    User query: "{user_query}"
    """
    
    response = llm.invoke(prompt)
    
    # TODO: agrgar parser, etc. 
        
    return parsed_response


# TODO: crear módulo para hacer query inicial o modificar la lista de variables a petición del usuario

def database_selector(user_query: str, topic_id_st: str, llm: Any) -> List[str]:
    """
    Select relevant datasets based on the user's query.
    
    Args:
        user_query: The user's query about the datasets
        llm: Language model for reasoning
        
    Returns:
        A list of dataset names relevant to the query.
    """
    
    # Use LLM to select relevant datasets
    prompt = f"""
    You will read the user query and select one or more of the datasets listed in the topic list.
    IMPORTANT: note that the topic list contains a list of elements with the following format: '* ABC|Topic description' where * marks the start of an element if the list, and ABC is the topic ID. 
    You will make  your selection based on the topic descriptions, but will return a list with the topic IDs (eg. ['ABC', 'DEF']) only. Make sure to return one topic ID for each topic description you choose.

    IMPORTANT: if the user request is not specific enough to select a dataset or you do not have enough information to choose a dataset, you should inform them that you cannot answer that question and suggest they ask about the available datasets.
    In this case, you should return an empty list.
    
    User query: "{user_query}"
    
    Available datasets:
    {tmp_topic_st}
    
    """
    
    response = llm.invoke(prompt)

    # TODO: agrgar parser, etc.

    return parsed_response
