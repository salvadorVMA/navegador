"""
Enhanced auto-next-step module to handle variable search with progressive timeouts.

This module improves the handling of long-running operations in the dashboard
by implementing a progressive timeout approach and better state management.
"""

import time
import json
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, List, Optional

class ProgressiveTimeout:
    """
    Manages progressive timeouts for long-running operations.
    Increases the timeout for each attempt, providing better feedback.
    """
    
    def __init__(self, 
                 initial_timeout: int = 15, 
                 max_timeout: int = 60,
                 increment: int = 15):
        """
        Initialize the progressive timeout manager.
        
        Args:
            initial_timeout: Initial timeout in seconds
            max_timeout: Maximum timeout in seconds
            increment: Increment in seconds for each retry
        """
        self.initial_timeout = initial_timeout
        self.max_timeout = max_timeout
        self.increment = increment
        self.attempts = 0
        self.start_time = None
        self.last_attempt_time = None
    
    def start(self):
        """Start the timeout tracking"""
        self.start_time = time.time()
        self.attempts = 0
        return self
    
    def next_attempt(self) -> int:
        """
        Record a new attempt and return the timeout for this attempt.
        
        Returns:
            Timeout in seconds for this attempt
        """
        self.attempts += 1
        self.last_attempt_time = time.time()
        
        # Calculate timeout for this attempt
        timeout = min(self.initial_timeout + (self.attempts - 1) * self.increment, 
                      self.max_timeout)
        
        return timeout
    
    def get_total_elapsed(self) -> float:
        """Get the total elapsed time since start"""
        if self.start_time is None:
            return 0
        return time.time() - self.start_time
    
    def get_attempt_elapsed(self) -> float:
        """Get the elapsed time since the last attempt"""
        if self.last_attempt_time is None:
            return 0
        return time.time() - self.last_attempt_time
    
    def get_status_message(self) -> str:
        """Get a user-friendly status message about the current state"""
        if self.start_time is None:
            return "Operation not started"
        
        total_elapsed = self.get_total_elapsed()
        
        if self.attempts == 0:
            return f"Starting operation (0.0s elapsed)"
        
        return f"Attempt {self.attempts} in progress ({total_elapsed:.1f}s total elapsed)"

def handle_variable_search_with_timeout(agent, state, config, 
                                      progressive_timeout: Optional[ProgressiveTimeout] = None) -> Dict[str, Any]:
    """
    Execute a variable search with progressive timeouts.
    
    Args:
        agent: The agent to invoke
        state: The agent state
        config: The agent configuration
        progressive_timeout: Optional ProgressiveTimeout instance to use
        
    Returns:
        A dict with the results or error information
    """
    if progressive_timeout is None:
        progressive_timeout = ProgressiveTimeout().start()
    
    # Get the timeout for this attempt
    timeout = progressive_timeout.next_attempt()
    attempt = progressive_timeout.attempts
    
    print(f"🔄 Variable search attempt {attempt} with {timeout}s timeout")
    start_time = time.time()
    
    try:
        # Execute with timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(agent.invoke, state, config=config)
            result = future.result(timeout=timeout)
        
        # Success!
        elapsed_time = time.time() - start_time
        print(f"✅ Variable search successful after {elapsed_time:.2f}s (within {timeout}s timeout)")
        
        return {
            "success": True,
            "result": result,
            "elapsed": elapsed_time,
            "attempts": attempt
        }
        
    except concurrent.futures.TimeoutError:
        elapsed_time = time.time() - start_time
        print(f"⌛ Attempt {attempt} timed out after {elapsed_time:.2f}s (hit {timeout}s limit)")
        
        # Check if we should try again with a longer timeout
        if progressive_timeout.attempts < 3:  # Limit to 3 attempts
            print(f"🔄 Trying again with a longer timeout...")
            return handle_variable_search_with_timeout(agent, state, config, progressive_timeout)
        else:
            print(f"⚠️ Giving up after {progressive_timeout.attempts} attempts and {progressive_timeout.get_total_elapsed():.2f}s")
            return {
                "success": False,
                "error": "timeout",
                "elapsed": progressive_timeout.get_total_elapsed(),
                "attempts": progressive_timeout.attempts
            }
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Variable search failed with error after {elapsed_time:.2f}s: {e}")
        return {
            "success": False,
            "error": str(e),
            "elapsed": elapsed_time,
            "attempts": attempt
        }
