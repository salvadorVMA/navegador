import os
import subprocess
import time
import sys  # Import sys to get the current interpreter
from workspace_module import ruta_enc  # ruta_enc is set in workspace_module
from secure_data_utils import load_json_with_types  # Use secure JSON instead of pickle

# Define paths for the required files
preprocess_path = os.path.join(ruta_enc, 'preprocess_navegador.py')
process_summaries_path = os.path.join(ruta_enc, 'process_summaries.py')

# Run the preprocessing script using the current Python interpreter and current environment
print('Running preprocessing...')
subprocess.run([sys.executable, preprocess_path], check=True, env=os.environ)

# Allow a short delay to ensure preprocessing completes
time.sleep(2)

# Run the process_summaries script using the current Python interpreter and current environment
print('Running process_summaries...')
subprocess.run([sys.executable, process_summaries_path], check=True, env=os.environ)

# Validate that the pickle file has been created and has the correct structure
pickle_path = os.path.join(ruta_enc, 'db_f1.pkl')
# Check for JSON file instead of pickle
json_path = pickle_path.replace('.pkl', '.json')
assert os.path.exists(json_path), 'JSON file not created.'

# Load data using secure JSON
db = load_json_with_types(json_path)
assert isinstance(db, dict), 'Loaded data is not a dictionary'

# Verify expected structure
assert ('summaries' in db and 'embeddings' in db and 'metadata' in db), 'db_f1 structure is incorrect.'
print('Test passed.')
