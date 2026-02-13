"""Script-style test for preprocessing and summary generation pipeline.
Run directly: python test_process_summaries.py
"""
import pytest

pytestmark = pytest.mark.skip(reason="Script-style test with hardcoded paths, run directly with python")

if __name__ == '__main__':
    import os
    import subprocess
    import pickle
    import time
    import sys

    from workspace_module import ruta_enc

    preprocess_path = os.path.join(ruta_enc, 'preprocess_navegador.py')
    process_summaries_path = os.path.join(ruta_enc, 'process_summaries.py')

    print('Running preprocessing...')
    subprocess.run([sys.executable, preprocess_path], check=True, env=os.environ)

    time.sleep(2)

    print('Running process_summaries...')
    subprocess.run([sys.executable, process_summaries_path], check=True, env=os.environ)

    pickle_path = os.path.join(ruta_enc, 'db_f1.pkl')
    assert os.path.exists(pickle_path), 'Pickle file not created.'

    with open(pickle_path, 'rb') as f:
        db = pickle.load(f)

    assert ('summaries' in db and 'embeddings' in db and 'metadata' in db), 'db_f1 structure is incorrect.'
    print('Test passed.')
