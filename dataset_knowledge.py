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

pregs_dict = los_mex_dict['pregs_dict']
ses_dict = los_mex_dict['ses_dict']
mkdown_tables = los_mex_dict['mkdown_tables']
df_tables = los_mex_dict['df_tables']


DATASETS = enc_nom_dict.keys()

tmp_topic_st= ', '.join([st.replace('_', ' ').title() for st in DATASETS])

# prompt para descripción
"""    If the user wants you to ANSWER GENERAL QUESTIONS, then you can provide information about the topics of the available datasets, general questions about the project that created these datasets.
    Any specific questions about available questions from these datasets will lead to action QUERY VARIABLE_DATABASE.
    Available topics for the available survey datasets: {tmp_topic_st})
    General information about the project: 
    -Name: "Los mexicanos vistos por sí mismos"
    -Description: This project is a group of {len(tmp_topic_st)} public opinion surveys conducted in Mexico between 2014 and 2015,
    -Team: Mtra. Julia Flores coordinated the team at the "Unidad de Investigación en Opinión Pública" and a group of experts in each of the topics, who designed the questionnaires, analyzed the data and wrote a book for each topic.
    -Repository: Datasets and the books written with the results of each survey are available at http://www.losmexicanos.unam.mx/
       sponored by the "Uniniversidad Nacional Autónoma de México" (UNAM).
    -Sponsor: "Universidad Nacional Autónoma de México" (UNAM)
    -Samples: All samples are have a size of 1000 and are representative of the Mexican population, with a margin of error of 3% and a confidence level of 95%."""



# # Example dataset information - in a real implementation, this could come from a database
# DATASETS = {
#     "customer_data": {
#         "description": "Customer demographic and transaction data",
#         "variables": [
#             "customer_id", "age", "gender", "income", "location", 
#             "purchase_history", "purchase_amount", "purchase_date"
#         ],
#         "size": "1.2M records",
#         "last_updated": "2025-03-15"
#     },
#     "product_data": {
#         "description": "Product catalog with specifications and reviews",
#         "variables": [
#             "product_id", "name", "category", "price", "cost", 
#             "supplier", "stock_level", "review_score", "review_count"
#         ],
#         "size": "50K records",
#         "last_updated": "2025-04-01"
#     },
#     "marketing_campaigns": {
#         "description": "Marketing campaign performance data",
#         "variables": [
#             "campaign_id", "channel", "start_date", "end_date", 
#             "budget", "spend", "impressions", "clicks", "conversions",
#             "roi", "target_audience"
#         ],
#         "size": "500 campaigns",
#         "last_updated": "2025-03-28"
#     }
# }

def list_datasets() -> str:
    """Return a formatted list of all available datasets"""
    result = []
    
    for name, info in DATASETS.items():
        result.append(f"- {name}: {info['description']}")
        
    return "\n".join(result)

def get_dataset_info(dataset_name: str) -> str:
    """Get detailed information about a specific dataset"""
    if dataset_name.lower() not in DATASETS:
        return f"Dataset '{dataset_name}' not found in the system."
    
    dataset = DATASETS[dataset_name.lower()]
    
    info = [
        f"Dataset: {dataset_name}",
        f"Description: {dataset['description']}",
        f"Size: {dataset['size']}",
        f"Last Updated: {dataset['last_updated']}",
        "\nVariables:",
    ]
    
    for var in dataset['variables']:
        info.append(f"- {var}")
    
    return "\n".join(info)

def get_variables(dataset_name: str) -> list:
    """Return the list of variables for a specific dataset"""
    if dataset_name.lower() not in DATASETS:
        return []
    
    return DATASETS[dataset_name.lower()]['variables']
