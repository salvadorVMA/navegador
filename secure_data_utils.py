"""Secure alternatives to pickle for data serialization.

This module provides secure data serialization tools, including support for
pandas DataFrames, Series, and Python sets. All data is serialized to JSON
format which is both more secure and human-readable than pickle.

Features:
- Secure serialization and deserialization
- Support for pandas DataFrames and Series
- Support for Python sets
- Human-readable JSON format
- Type preservation
"""

from typing import Any, Dict, List, Set, Union
from pathlib import Path
import json
import pandas as pd

JsonSerializable = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
DataObject = Union[pd.DataFrame, pd.Series, Set[Any], Dict[str, Any], List[Any], JsonSerializable]
PathLike = Union[str, Path]

def load_json_with_types(filepath: PathLike) -> DataObject:
    """
    Load JSON data with type restoration.

    Handles pandas DataFrames, Series, and sets that were serialized
    with special type markers.

    Args:
        filepath: Path to the JSON file to load
        expected_type: Optional type annotation for better type checking

    Returns:
        The deserialized data with proper Python types restored
    """
    path = Path(filepath)
    with path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    def restore_types(obj: Any) -> DataObject:
        """Recursively restore types in deserialized JSON data."""
        if isinstance(obj, dict):
            # Handle pandas DataFrame
            if "__pandas_dataframe__" in obj:
                df_data = obj["data"]
                return pd.DataFrame(
                    data=df_data["data"],
                    index=df_data.get("index", None),
                    columns=df_data["columns"]
                )
            # Handle pandas Series
            elif "__pandas_series__" in obj:
                return pd.Series(obj["data"])
            # Handle sets
            elif "__set__" in obj:
                return set(obj["data"])
            # Recursively handle nested dictionaries
            else:
                return {str(k): restore_types(v) for k, v in obj.items()}
        # Handle lists
        elif isinstance(obj, list):
            return [restore_types(item) for item in obj]
        # Handle primitive types
        return obj

    return restore_types(data)

def save_json_with_types(data: DataObject, filepath: str) -> None:
    """
    Save data to JSON with type preservation.

    Handles pandas DataFrames, Series, and sets with special type markers.

    Args:
        data: The data to serialize
        filepath: Path where the JSON file should be saved
    """
    def convert_for_json(obj: Any) -> Dict[str, Any]:
        """Convert Python objects to JSON-serializable format with type information."""
        if isinstance(obj, pd.DataFrame):
            return {
                "__pandas_dataframe__": True,
                "data": obj.to_dict(orient='split')
            }
        elif isinstance(obj, pd.Series):
            return {
                "__pandas_series__": True,
                "data": obj.to_dict()
            }
        elif isinstance(obj, set):
            return {
                "__set__": True,
                "data": list(obj)
            }
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, default=convert_for_json, ensure_ascii=False, indent=2)
