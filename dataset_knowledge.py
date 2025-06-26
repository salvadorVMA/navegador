"""Module for managing dataset information and metadata"""

import pickle

# rutas a datos y recursos
ruta_enc= '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/'
ruta_rep= '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/reportes/'
ruta_tmp_images= '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/tmp_images/'

# pickle para cargar el diccionario de encuestas
with open(f'{ruta_enc}/los_mex_dict.pkl', 'rb') as f:
    los_mex_dict = pickle.load(f)
    print('los_mex_dict cargado --  leer readme_dict para info')

# enc_dict es el diccionario de encuestas
# Contiene información sobre las encuestas, , dataframes y metadata como 'variable_value_labels', 'column_names_to_labels'
enc_dict = los_mex_dict['enc_dict']

# enc_nom_dict es el diccionario de nombres de encuestas y sus identificadores
# Contiene los nombres de las encuestas y sus identificadores, que se usan para referenciar las encuestas en el sistema
# Ejemplo: {'IDENTIDAD_Y_VALORES': 'IDE'...}
enc_nom_dict = los_mex_dict['enc_nom_dict']
rev_enc_nom_dict = {v: k for k, v in enc_nom_dict.items()}

# Generar un string con los temas de las encuestas y sus identificadores
rev_topic_dict = {k: v.replace('_', ' ').lower() for k, v in rev_enc_nom_dict.items()}
topic_id_st = '\n'.join(['|'.join(['* ' + a, b]) for a, b in rev_topic_dict.items()])

# pregs_dict contiene códigos de identificación pregunta|encuesta y la pregunta completa
# ejemplo: p5_1|IDE': 'IDENTIDAD_Y_VALORES|¿Cuál de las siguientes emociones refleja mejor lo que siente sobre México?... }
pregs_dict = los_mex_dict['pregs_dict']

# pregs_dict contiene códigos de identificación pregunta|encuesta y la pregunta completa
# ejemplo: {'sd1|IDE': 'IDENTIDAD_Y_VALORES|Sexo:',
pregs_dict = los_mex_dict['pregs_dict']

# ses_dict contiene información sobre las la información socioeconómica de los encuestados -- aún no usada
# ejemplo: {'IDE': ['p5_1|IDE', 'p5_2|IDE'], ...}
ses_dict = los_mex_dict['ses_dict']

# mkdown_tables contiene tablas en formato markdown con las tablas de frecuencias de las encuestas
# 'p5_1|IDE': '| IDENTIDAD_Y_VALORES|¿Cuál de las siguientes emociones refleja mejor lo que siente sobre México?  1° MENCIÓN | % |\n| --- | --- |\n| Orgullo | 38.33 |\n...
mkdown_tables = los_mex_dict['mkdown_tables']

# df_tables contiene dataframes con las tablas de frecuencias de las encuestas
df_tables = los_mex_dict['df_tables']

# tmp_topic_lst es una lista de los temas de las encuestas
# ejemplo: dict_keys(['IDENTIDAD_Y_VALORES', 'MEDIO_AMBIENTE',... 
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

from typing import List, Any
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser

def _project_describer(user_query: str, tmp_data_describer_st: str, llm: Any) -> str:
    """
    Answer general questions about the project and datasets based on the user's query.
    
    Args:
        user_query: The user's query about the dataset
        tmp_data_describer_st: Predefined string with project and dataset information
        llm: Language model for reasoning
        
    Returns:
        A string with the relevant information about the project and datasets.
    """
    
    # Define Pydantic model for structured output
    class ProjectDescriptionResponse(BaseModel):
        answer: str
        redirect_needed: bool = False
        suggested_action: str = ""
    
    pattern_parser = PydanticOutputParser(pydantic_object=ProjectDescriptionResponse)
    format_instructions = pattern_parser.get_format_instructions()
        
    # Use LLM to select relevant variables
    prompt = f"""
    You are a helpful assistant who will answer general questions about a survey project. 
    Read the general description of the survey project and reply with the relevant information to the user's query. 
    IMPORTANT: If the user asks about specific variables or items from the datasets, you should redirect them to the QUERY VARIABLE_DATABASE action.
    IMPORTANT: If you do not have enough information to answer the user's query, you should inform them that you cannot answer that question and suggest they ask about the available datasets or specific variables.
    
    General description of the project and datasets:
    {tmp_data_describer_st} 
    
    User query: "{user_query}"
    
    {format_instructions}
    """
    
    response = llm.invoke(prompt)
    
    try:
        parsed = pattern_parser.parse(response.content if hasattr(response, 'content') else str(response))
        return parsed.answer
    except Exception as e:
        print(f"Parsing failed in project_describer: {e}")
        return str(response.content if hasattr(response, 'content') else response)
