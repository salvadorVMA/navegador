"""Test utilities for creating sample data."""

import pandas as pd
import numpy as np
from secure_data_utils import save_json_with_types
import os

def create_test_data(ruta_enc):
    """Create test data for process_summaries tests."""
    # Create sample survey data
    survey_data = pd.DataFrame({
        'p1_1': ['A', 'B', 'C', 'A', 'B'] * 20,
        'peso': [1.0, 1.2, 0.8, 1.1, 0.9] * 20
    })
    
    # Create sample pregs_dict
    pregs_dict = {
        'p1_1|1': 'survey1|¿Cómo calificaría su experiencia?'
    }
    
    # Create sample enc_dict
    enc_dict = {
        'survey1': survey_data
    }
    
    # Save test data
    save_json_with_types(pregs_dict, os.path.join(ruta_enc, 'pregs_dict.json'))
    save_json_with_types(enc_dict, os.path.join(ruta_enc, 'enc_dict.json'))
