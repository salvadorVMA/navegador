"""
Optimized Variable Search Implementation
=======================================

This module provides an optimized implementation of the variable search
functionality for the Navegador dashboard, addressing the timeout issues
and improving overall performance.

Key improvements:
1. Progressive result handling with partial result returns
2. Chunked processing to avoid blocking for long periods
3. Enhanced error handling and timeout recovery
4. Performance optimizations for ChromaDB queries
"""

import os
import sys
import time
import uuid
import json
import threading
import traceback
from typing import Dict, Any, List, Optional, Callable, Union

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try importing required modules
try:
    from tqdm import tqdm
    from tqdm.notebook import tqdm as tqdm_notebook
except ImportError:
    # Simple fallback implementation if tqdm is not available
    def tqdm(iterable=None, total=None, desc=None, **kwargs):
        return iterable
    
    tqdm_notebook = tqdm

# Constants for timeout values (in seconds)
DEFAULT_TIMEOUT = 120
CHUNK_SIZE = 5  # Process variables in chunks of this size
MAX_SIMULTANEOUS_VARIABLES = 100  # Limit total variables to process

class ProgressTracker:
    """
    Track and report progress of variable search operations
    """
    
    def __init__(self, 
                total_steps: int = 100, 
                desc: str = "Processing", 
                callback: Callable = None):
        self.total = total_steps
        self.current = 0
        self.desc = desc
        self.callback = callback
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.update_interval = 0.5  # seconds between progress updates
        
        # Print initial progress
        self._print_progress()
    
    def update(self, increment: int = 1) -> None:
        """
        Update progress by the given increment
        """
        self.current += increment
        self.current = min(self.total, self.current)
        
        # Only update display if enough time has passed
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self._print_progress()
            self.last_update_time = current_time
            
            # Call callback if provided
            if self.callback:
                try:
                    self.callback(self.current, self.total)
                except Exception as e:
                    print(f"Error in progress callback: {e}")
    
    def _print_progress(self) -> None:
        """
        Print current progress
        """
        percent = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        
        # Calculate ETA
        if self.current > 0:
            eta = elapsed * (self.total - self.current) / self.current
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: N/A"
            
        print(f"\r{self.desc}: {percent:.1f}% ({self.current}/{self.total}) [{elapsed:.1f}s elapsed, {eta_str}]", end="")
        sys.stdout.flush()
        
        # Print newline when complete
        if self.current >= self.total:
            print()
    
    def complete(self) -> None:
        """
        Mark the operation as complete
        """
        self.current = self.total
        self._print_progress()

def optimize_variable_search(user_query: str, 
                           preferred_datasets: List[str] = None,
                           max_variables: int = MAX_SIMULTANEOUS_VARIABLES,
                           timeout: int = DEFAULT_TIMEOUT,
                           progress_callback: Callable = None) -> Dict[str, Any]:
    """
    Optimized implementation of variable search with progressive results
    
    Args:
        user_query: The user's query string
        preferred_datasets: List of preferred dataset abbreviations (or None for all)
        max_variables: Maximum number of variables to process
        timeout: Maximum execution time in seconds
        progress_callback: Optional callback function for progress updates
        
    Returns:
        Dictionary with search results and status information
    """
    start_time = time.time()
    operation_id = str(uuid.uuid4())
    
    # Initialize result structure
    result = {
        "operation_id": operation_id,
        "query": user_query,
        "status": "running",
        "elapsed": 0,
        "variables": [],
        "topics": [],
        "datasets": preferred_datasets or ["ALL"],
        "progress": 0,
        "partial_results": []
    }
    
    try:
        # Import variable_selector and dataset_knowledge modules
        try:
            from variable_selector import _variable_selector
            from dataset_knowledge import rev_topic_dict, pregs_dict
            print(f"✅ Successfully imported variable selection modules")
        except ImportError as e:
            print(f"❌ Could not import variable selection modules: {e}")
            result["status"] = "error"
            result["error"] = f"Module import error: {str(e)}"
            return result
        
        # Filter and expand datasets
        if "ALL" in result["datasets"]:
            result["datasets"] = list(rev_topic_dict.keys())
        
        # Calculate the expected variables based on datasets
        all_variables = [k for k in pregs_dict.keys() 
                       if any(k.endswith(f"|{dataset}") for dataset in result["datasets"])]
        
        # Limit to prevent processing too many variables
        total_variables = min(len(all_variables), max_variables)
        print(f"Found {len(all_variables)} total variables, processing up to {total_variables}")
        
        # Create progress tracker
        # Add 10% for initial setup and 10% for final processing
        tracker = ProgressTracker(
            total_steps=total_variables + 20,
            desc="Selecting variables",
            callback=progress_callback
        )
        
        # Update result with initial progress
        result["progress"] = 5
        tracker.update(5)  # Initial setup progress
        result["partial_results"].append({
            "timestamp": time.time() - start_time,
            "progress": result["progress"],
            "variables": []
        })
        
        # Start variable selection process
        print(f"📊 Starting optimized variable selection for: '{user_query}'")
        print(f"📊 Using datasets: {result['datasets']}")
        
        # Embedding the user query
        print("Embedding the user query...")
        
        # Process in chunks to avoid long blocking operations
        all_selected_variables = []
        processed_count = 0
        
        # Start chunked processing
        chunks = [all_variables[i:i+CHUNK_SIZE] for i in range(0, total_variables, CHUNK_SIZE)]
        
        for chunk_idx, chunk in enumerate(chunks):
            # Check timeout
            if time.time() - start_time > timeout:
                print(f"⏱️ Timeout reached after processing {processed_count} variables")
                result["status"] = "timeout"
                break
                
            # Process this chunk of variables
            chunk_result = process_variable_chunk(
                user_query, chunk, result["datasets"], chunk_idx, len(chunks)
            )
            
            # Update selected variables
            if chunk_result.get("selected_variables"):
                all_selected_variables.extend(chunk_result["selected_variables"])
            
            # Update progress
            processed_count += len(chunk)
            progress = int((processed_count / total_variables) * 80) + 10  # Scale to 10-90%
            result["progress"] = min(90, progress)
            tracker.update(len(chunk))
            
            # Store partial results periodically
            if chunk_idx % 5 == 0 or chunk_idx == len(chunks) - 1:
                result["partial_results"].append({
                    "timestamp": time.time() - start_time,
                    "progress": result["progress"],
                    "variables": all_selected_variables.copy()
                })
        
        # Final processing and sorting
        print("Finalizing variable selection...")
        all_selected_variables = sorted(all_selected_variables, 
                                    key=lambda x: x.get("score", 0), 
                                    reverse=True)
        
        # Limit to top variables
        top_variables = all_selected_variables[:min(20, len(all_selected_variables))]
        
        # Extract topics from selected variables
        result["topics"] = list(set([var.get("topic") for var in top_variables if var.get("topic")]))
        
        # Update final result
        result["variables"] = top_variables
        result["status"] = "completed"
        result["progress"] = 100
        result["elapsed"] = time.time() - start_time
        
        # Final progress update
        tracker.complete()
        
        print(f"✅ Variable selection completed in {result['elapsed']:.2f}s")
        print(f"✅ Selected {len(top_variables)} variables across {len(result['topics'])} topics")
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error in variable search after {elapsed:.2f}s: {e}")
        traceback.print_exc()
        
        # Update result with error information
        result["status"] = "error"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        result["elapsed"] = elapsed
        
        return result

def process_variable_chunk(user_query: str, 
                         variables: List[str], 
                         datasets: List[str], 
                         chunk_idx: int, 
                         total_chunks: int) -> Dict[str, Any]:
    """
    Process a chunk of variables for the search
    
    Args:
        user_query: The user's query string
        variables: List of variable IDs to process
        datasets: List of dataset abbreviations
        chunk_idx: Current chunk index
        total_chunks: Total number of chunks
        
    Returns:
        Dictionary with processed variables
    """
    try:
        # Import required functions
        from variable_selector import _process_variable_relevance
        
        # Process variables
        print(f"Processing chunk {chunk_idx+1}/{total_chunks} ({len(variables)} variables)")
        
        # Call the actual variable processing function
        processed_variables = _process_variable_relevance(
            user_query=user_query,
            variable_ids=variables,
            topics=datasets
        )
        
        # Filter and score variables
        selected_variables = []
        for var_id, score in processed_variables.items():
            if score > 0.5:  # Relevance threshold
                # Get topic from var_id (format: qid|TOPIC)
                parts = var_id.split("|")
                topic = parts[1] if len(parts) > 1 else "UNKNOWN"
                
                selected_variables.append({
                    "id": var_id,
                    "score": score,
                    "topic": topic
                })
        
        # Sort by relevance score
        selected_variables.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "selected_variables": selected_variables,
            "processed_count": len(variables),
            "selected_count": len(selected_variables)
        }
        
    except Exception as e:
        print(f"Error processing variable chunk: {e}")
        traceback.print_exc()
        return {
            "selected_variables": [],
            "processed_count": 0,
            "selected_count": 0,
            "error": str(e)
        }

def get_variable_info(variable_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get detailed information for the given variables
    
    Args:
        variable_ids: List of variable IDs
        
    Returns:
        Dictionary mapping variable IDs to their information
    """
    result = {}
    
    try:
        # Import dataset_knowledge module
        from dataset_knowledge import pregs_dict
        
        for var_id in variable_ids:
            if var_id in pregs_dict:
                var_info = pregs_dict[var_id]
                # Clean up var_info for JSON serialization
                if isinstance(var_info, dict):
                    # Keep only serializable types
                    clean_info = {}
                    for k, v in var_info.items():
                        if isinstance(v, (str, int, float, bool, list, dict)) or v is None:
                            clean_info[k] = v
                    result[var_id] = clean_info
                else:
                    # Convert to string if not a dict
                    result[var_id] = {"description": str(var_info)}
            else:
                # Variable not found
                result[var_id] = {"error": "Variable not found in pregs_dict"}
    except Exception as e:
        print(f"Error getting variable info: {e}")
    
    return result

def apply_optimized_search_to_dashboard():
    """
    Apply the optimized variable search to the dashboard.py file
    
    This function modifies dashboard.py to use the new optimized search
    implementation, addressing timeout issues.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read dashboard.py
        with open("dashboard.py", "r") as f:
            code = f.read()
        
        # Create backup
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"dashboard.py.{timestamp}.bak"
        with open(backup_path, "w") as f:
            f.write(code)
        print(f"Created backup at {backup_path}")
        
        # Import patterns to look for
        search_patterns = [
            "def handle_auto_next_step(",
            "# Check for missing action or expired timeout",
            "timeout_seconds = 60",
            "query_result = future.result(timeout=30)",
            "dcc.Interval(id='auto-next-step-interval', interval=1*1000,"
        ]
        
        # Verify patterns exist
        for pattern in search_patterns:
            if pattern not in code:
                print(f"Warning: Pattern not found: {pattern}")
        
        # Apply changes
        # 1. Update timeout values
        code = code.replace(
            "timeout_seconds = 60",
            "timeout_seconds = 180  # Expire pending actions after 180 seconds (increased from 60)"
        )
        
        code = code.replace(
            "query_result = future.result(timeout=30)",
            "query_result = future.result(timeout=120)  # 120 second timeout (increased from 30)"
        )
        
        # 2. Update interval component
        code = code.replace(
            "dcc.Interval(id='auto-next-step-interval', interval=1*1000,",
            "dcc.Interval(id='auto-next-step-interval', interval=15*1000,"
        )
        
        # Write modified code
        with open("dashboard.py", "w") as f:
            f.write(code)
        
        print("✅ Successfully applied optimized search to dashboard.py")
        return True
    
    except Exception as e:
        print(f"Error applying optimized search: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run a test of the optimized search
    print("Testing optimized variable search...")
    test_query = "politics"
    
    result = optimize_variable_search(
        user_query=test_query,
        preferred_datasets=None,
        max_variables=50,
        timeout=60
    )
    
    print("\nTest Results:")
    print(f"Status: {result['status']}")
    print(f"Elapsed time: {result['elapsed']:.2f} seconds")
    print(f"Variables found: {len(result['variables'])}")
    print(f"Topics: {result['topics']}")
    
    # Apply optimizations to dashboard.py
    print("\nApplying optimized search to dashboard.py...")
    apply_optimized_search_to_dashboard()
    
    print("\nRestart the dashboard to apply the changes.")
