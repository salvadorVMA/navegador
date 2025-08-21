from pathlib import Path
from secure_data_utils import load_json_with_types

# Load the real data
RUTA_BASE = Path('/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador')
ruta_enc = RUTA_BASE / 'encuestas'
los_mex_dict = load_json_with_types(str(ruta_enc / 'los_mex_dict.json'))

print(f"los_mex_dict cargado: {los_mex_dict.keys()}")