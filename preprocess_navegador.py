import os
import pickle
import re
import sys
import subprocess

# Add environment debug info before importing numpy/pandas
print("Python interpreter path:", sys.executable)
print("Python version:", sys.version)

# Get conda environment information
conda_prefix = os.environ.get('CONDA_PREFIX')
print("Conda environment:", conda_prefix)

# Try with different import strategies if the standard one fails
try:
    import numpy as np
    import pandas as pd
    print("numpy version:", np.__version__)
    print("pandas version:", pd.__version__)
except ValueError as e:
    if "numpy.dtype size changed" in str(e):
        print("Detected numpy/pandas version incompatibility. Trying conda reinstall...")
        # Use conda to reinstall numpy - this is appropriate for conda environments
        try:
            # Use the conda from the active environment
            conda_executable = os.path.join(conda_prefix, 'bin', 'conda') if conda_prefix else 'conda'
            # Run conda install with -y to automatically answer yes to prompts
            subprocess.run([conda_executable, "install", "-y", "numpy"], check=True)
            # After reinstallation, try importing again
            import numpy as np
            import pandas as pd
            print("After reinstall - numpy version:", np.__version__)
            print("After reinstall - pandas version:", pd.__version__)
        except subprocess.CalledProcessError as conda_err:
            print(f"Conda reinstall failed: {conda_err}")
            raise
    else:
        raise

# Load environment variables from .env if available
from dotenv import load_dotenv
load_dotenv()

########## Helper Functions ##########
def replace_latin_characters(text):
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    for latin_char, ascii_char in replacements.items():
        text = text.replace(latin_char, ascii_char)
    return text

def calculate_weighted_proportion(df, categorical_var, weight_var='ponderador', normalize=True):
    df = df.copy()
    df[weight_var] = df[weight_var].astype(float).fillna(0)
    if normalize:
        df[weight_var] = df[weight_var] / df[weight_var].sum()
    weighted_counts = df.groupby(categorical_var)[weight_var].sum()
    return weighted_counts.to_frame(name='proportion')

def dataframe_to_markdown(df):
    headers = df.columns.tolist()
    index_name = df.index.name if df.index.name is not None else ""
    header_row = "| " + str(index_name) + " | " + " | ".join(str(col) for col in headers) + " |"
    separator_row = "| --- | " + " | ".join(["---" for _ in headers]) + " |"
    data_rows = []
    for idx, row in df.iterrows():
        formatted_values = [f"{val:.2f}" if isinstance(val, float) else str(val) for val in row]
        data_rows.append("| " + str(idx) + " | " + " | ".join(formatted_values) + " |")
    return "\n".join([header_row, separator_row] + data_rows)

def create_prompt_sum(md_str):
    return f"Summarize the following table:\n{md_str}"

def get_answer(prompt, system_prompt=None, model='gpt-4o-mini-2024-07-18'):
    from openai import OpenAI
    client_local = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    response = client_local.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content

########## Preprocessing Objects ##########
# Load survey data from pickle to create enc_dict
ruta_enc_pickle = '/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas'
with open(os.path.join(ruta_enc_pickle, 'encs.pkl'), 'rb') as f:
    enc_dict = pickle.load(f)
    print('Pickle file loaded successfully')
enc_dict = {replace_latin_characters(k.upper()): v for k, v in enc_dict.items()}

# Define enc_nom_dict mapping survey codes to survey names
enc_nom_dict = {
    "IDE": "Identidad y Valores",
    "MED": "Medio Ambiente",
    "POB": "Pobreza",
    "CUL": "Cultura Política",
    "REL": "Religión, Secularización y Laicidad",
    "SEG": "Seguridad Pública",
    "SAL": "Salud",
    "IND": "Indígenas",
    "SOC": "Sociedad de la Información",
    "ENV": "Envejecimiento",
    "DER": "Derechos Humanos, Discriminación y Grupos Vulnerables",
    "COR": "Corrupción y Cultura de la Legalidad",
    "HAB": "La Condición de Habitabilidad de Vivienda en México",
    "GLO": "Globalización",
    "JUS": "Justicia",
    "JUE": "Juegos de Azar",
    "MIG": "Migración",
    "FED": "Federalismo",
    "GEN": "Género",
    "CON": "Cultura Constitucional",
    "DEP": "Cultura, Lectura y Deporte",
    "ECO": "Economía y Empleo",
    "NIN": "Niños, Adolescentes y Jóvenes",
    "FAM": "Familia",
    "CIE": "Ciencia y Tecnología",
    "EDU": "Educación"
}
enc_nom_dict = {k: replace_latin_characters(v.upper()) for k, v in enc_nom_dict.items()}
enc_nom_dict = {k: v.replace(' ', '_').replace(',', '') for k, v in enc_nom_dict.items()}
enc_nom_dict = {v: k for k, v in enc_nom_dict.items()}

# Process survey question metadata to create pregs_dict
pregs_agg_dict = {}
for ky in enc_dict.keys():
    tmp_pregs = enc_dict[ky]['metadata']['column_names_to_labels']
    tmp_pregs = {k: v for k, v in tmp_pregs.items() if k.startswith('p') or k.startswith('sd')}
    rgx_st = r'^\s*\d+\.*\s'
    for k, v in tmp_pregs.items():
        if isinstance(v, str) and re.match(rgx_st, v):
            tmp_pregs[k] = re.sub(rgx_st, '', v).strip()
    tmp_pregs = {'|'.join([k, enc_nom_dict[ky]]): '|'.join([ky, v]) for k, v in tmp_pregs.items()}
    pregs_agg_dict.update(tmp_pregs)

ses_dict = {k: v for k, v in pregs_agg_dict.items() if k.startswith('sd')}
pregs_dict = {k: v for k, v in pregs_agg_dict.items() if k.startswith('p')}
pregs_dict = {k: v for k, v in pregs_dict.items() if not ('a' in k or 'a_1' in k or '2°' in v or '3°' in v or '2 menc' in v or '3 menc' in v)}

########## Initialize LLM Client ##########
from openai import OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

########## Expose for Imports ##########
__all__ = [
    "enc_dict", "pregs_dict", "calculate_weighted_proportion",
    "dataframe_to_markdown", "create_prompt_sum", "get_answer", "client"
]

if __name__ == '__main__':
    print('Preprocessing complete.')