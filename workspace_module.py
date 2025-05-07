import pandas as pd
import numpy as np
import os
import sys

# Set the ruta_enc as used throughout the project.
ruta_enc = '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador'

# Import objects and functions from the preprocessing module later, to avoid circular imports
def import_preprocess_modules():
    # Add debugging
    print("Python interpreter path:", sys.executable)
    print("Python version:", sys.version)
    conda_prefix = os.environ.get('CONDA_PREFIX')
    print("Conda environment:", conda_prefix)
    
    try:
        import numpy as np
        import pandas as pd
        print("numpy version:", np.__version__)
        print("pandas version:", pd.__version__)
        
        # Direct import from preprocess_navegador
        from preprocess_navegador import (
            enc_dict as imported_enc_dict,
            pregs_dict as imported_pregs_dict,
            calculate_weighted_proportion as imported_calculate_weighted_proportion,
            dataframe_to_markdown as imported_dataframe_to_markdown,
            create_prompt_sum as imported_create_prompt_sum,
            get_answer as imported_get_answer,
            client as imported_client
        )
        print('Pickle file loaded successfully')
        
        # Return imported objects
        return (
            imported_enc_dict, 
            imported_pregs_dict, 
            imported_calculate_weighted_proportion, 
            imported_dataframe_to_markdown, 
            imported_create_prompt_sum, 
            imported_get_answer, 
            imported_client
        )
    except ImportError as e:
        raise ImportError("Ensure that preprocess_navegador.py is accessible and run before importing. " + str(e))

# These will be populated when needed
enc_dict = None
pregs_dict = None
calculate_weighted_proportion = None
dataframe_to_markdown = None
create_prompt_sum = None
get_answer = None
client = None

# Function to ensure all modules are loaded and return them
def ensure_modules_loaded():
    global enc_dict, pregs_dict, calculate_weighted_proportion, dataframe_to_markdown, create_prompt_sum, get_answer, client
    
    if pregs_dict is None:
        # Import modules and explicitly assign to globals
        loaded_modules = import_preprocess_modules()
        enc_dict = loaded_modules[0]
        pregs_dict = loaded_modules[1]
        calculate_weighted_proportion = loaded_modules[2]
        dataframe_to_markdown = loaded_modules[3]
        create_prompt_sum = loaded_modules[4]
        get_answer = loaded_modules[5]
        client = loaded_modules[6]
        
        # Verify
        if pregs_dict is None:
            raise ValueError("Failed to initialize pregs_dict")
            
    return enc_dict, pregs_dict, calculate_weighted_proportion, dataframe_to_markdown, create_prompt_sum, get_answer, client

# Define llm_request() as a wrapper that delegates to get_answer()
def llm_request(prompt, model='gpt-4o-mini-2025-04-14'):
    global get_answer
    if get_answer is None:
        # Import modules on first use
        _, _, _, _, _, get_answer, _ = ensure_modules_loaded()
    return get_answer(prompt=prompt, model=model)

# Define embedding_function() to use the client's embeddings capability.
def embedding_function(text):
    global client
    if client is None:
        # Import modules on first use
        _, _, _, _, _, _, client = ensure_modules_loaded()
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text,
            encoding_format="float"
        )
        # Return the first embedding vector.
        return response.embeddings[0].values
    except Exception as e:
        raise RuntimeError("Failed to compute embedding: " + str(e))