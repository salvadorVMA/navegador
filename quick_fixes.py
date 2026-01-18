"""
Quick reliability fixes for navegador dashboard.

This module contains infrastructure for critical reliability improvements:
1. Request locking to prevent race conditions
2. Persistent thread pool for better resource management
3. Centralized error handling with logging

Usage:
    from quick_fixes import RequestManager, get_thread_pool, ErrorHandler

Apply these fixes to dashboard.py to improve reliability.
"""

import threading
import uuid
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import copy

# =============================================================================
# 1. REQUEST MANAGEMENT (Prevents Race Conditions)
# =============================================================================

class RequestManager:
    """
    Thread-safe request manager to prevent race conditions in callbacks.

    Features:
    - Tracks active requests by unique ID
    - Prevents duplicate request processing
    - Automatic cleanup of completed requests
    - Thread-safe operations
    """

    def __init__(self):
        self._active_requests: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_request(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """
        Create a new request and return its unique ID.

        Args:
            user_message: The user's query
            context: Additional context for the request

        Returns:
            Unique request ID
        """
        request_id = str(uuid.uuid4())

        with self._lock:
            self._active_requests[request_id] = {
                'user_message': user_message,
                'context': context or {},
                'created_at': time.time(),
                'status': 'pending'
            }

        return request_id

    def is_active(self, request_id: str) -> bool:
        """Check if request is still active."""
        with self._lock:
            return request_id in self._active_requests

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get request details."""
        with self._lock:
            return self._active_requests.get(request_id)

    def mark_processing(self, request_id: str) -> bool:
        """
        Mark request as being processed.

        Returns:
            True if successfully marked, False if already processing
        """
        with self._lock:
            if request_id not in self._active_requests:
                return False

            request = self._active_requests[request_id]
            if request['status'] == 'processing':
                return False  # Already being processed

            request['status'] = 'processing'
            request['processing_started'] = time.time()
            return True

    def complete_request(self, request_id: str, result: Any = None, error: Optional[Exception] = None):
        """Mark request as completed and clean up."""
        with self._lock:
            if request_id in self._active_requests:
                request = self._active_requests[request_id]
                request['status'] = 'completed'
                request['completed_at'] = time.time()
                request['result'] = result
                request['error'] = error

                # Remove from active requests after a short delay (for debugging)
                # In production, remove immediately
                del self._active_requests[request_id]

    def cleanup_old_requests(self, max_age_seconds: int = 300):
        """Remove requests older than specified age."""
        current_time = time.time()

        with self._lock:
            expired = [
                req_id for req_id, req in self._active_requests.items()
                if current_time - req['created_at'] > max_age_seconds
            ]

            for req_id in expired:
                del self._active_requests[req_id]

        return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about active requests."""
        with self._lock:
            total = len(self._active_requests)
            by_status = {}
            for req in self._active_requests.values():
                status = req['status']
                by_status[status] = by_status.get(status, 0) + 1

            return {
                'total_active': total,
                'by_status': by_status
            }


# Global request manager instance
_request_manager = RequestManager()


def get_request_manager() -> RequestManager:
    """Get the global request manager instance."""
    return _request_manager


# =============================================================================
# 2. THREAD POOL MANAGEMENT (Better Resource Management)
# =============================================================================

class ManagedThreadPool:
    """
    Singleton thread pool manager for dashboard operations.

    Benefits:
    - Reuses threads instead of creating new ones
    - Configurable worker count
    - Graceful shutdown
    - Statistics tracking
    """

    _instance: Optional['ManagedThreadPool'] = None
    _lock = threading.Lock()

    def __new__(cls, max_workers: int = 4):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_workers: int = 4):
        if self._initialized:
            return

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._max_workers = max_workers
        self._task_count = 0
        self._completed_count = 0
        self._initialized = True

    def submit(self, fn: Callable, *args, **kwargs):
        """Submit a task to the thread pool."""
        self._task_count += 1
        future = self._executor.submit(fn, *args, **kwargs)

        # Add callback to track completion
        future.add_done_callback(lambda f: self._on_task_complete())

        return future

    def _on_task_complete(self):
        """Track completed tasks."""
        self._completed_count += 1

    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool."""
        self._executor.shutdown(wait=wait)

    def get_stats(self) -> Dict[str, Any]:
        """Get thread pool statistics."""
        return {
            'max_workers': self._max_workers,
            'total_submitted': self._task_count,
            'total_completed': self._completed_count,
            'active_tasks': self._task_count - self._completed_count
        }


# Global thread pool instance
_thread_pool = ManagedThreadPool(max_workers=4)


def get_thread_pool() -> ManagedThreadPool:
    """Get the global thread pool instance."""
    return _thread_pool


# =============================================================================
# 3. ERROR HANDLING (Centralized Logging)
# =============================================================================

class ErrorHandler:
    """
    Centralized error handler with logging and user-friendly messages.

    Features:
    - Persistent logging to file
    - User-friendly error messages
    - Error categorization
    - Error rate tracking
    """

    def __init__(self, log_file: str = 'dashboard_errors.log'):
        self.logger = logging.getLogger('dashboard_errors')
        self.logger.setLevel(logging.ERROR)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Error tracking
        self._error_count = 0
        self._errors_by_type = {}

    def handle_error(
        self,
        error: Exception,
        context: str,
        user_message: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle an error with logging and user-friendly message.

        Args:
            error: The exception that occurred
            context: Description of where/when error occurred
            user_message: Optional user-friendly message
            request_id: Optional request ID for tracking

        Returns:
            Dict with error info suitable for dashboard display
        """
        # Log detailed error
        self.logger.error(
            f"[{context}] {type(error).__name__}: {error}",
            exc_info=True,
            extra={'request_id': request_id}
        )

        # Track error
        self._error_count += 1
        error_type = type(error).__name__
        self._errors_by_type[error_type] = self._errors_by_type.get(error_type, 0) + 1

        # Generate user-friendly message
        if user_message is None:
            user_message = self._get_user_friendly_message(error)

        return {
            'type': 'assistant',
            'content': f"⚠️ {user_message}",
            'timestamp': datetime.now().strftime("%H:%M"),
            'is_error': True,
            'error_context': context
        }

    def _get_user_friendly_message(self, error: Exception) -> str:
        """Generate user-friendly error message based on error type."""
        error_messages = {
            'TimeoutError': "The operation took too long. Please try again with a simpler query.",
            'ConnectionError': "Could not connect to the service. Please check your connection and try again.",
            'ValueError': "Invalid input received. Please check your query and try again.",
            'KeyError': "Required information is missing. Please try again.",
            'FileNotFoundError': "Required data file not found. Please contact support.",
        }

        error_type = type(error).__name__
        return error_messages.get(
            error_type,
            "An unexpected error occurred. Please try again or contact support if the problem persists."
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            'total_errors': self._error_count,
            'by_type': dict(self._errors_by_type)
        }


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return _error_handler


# =============================================================================
# 4. UTILITY FUNCTIONS
# =============================================================================

def deep_copy_session_data(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a deep copy of session data to prevent modification issues.

    Args:
        session_data: Session data dictionary

    Returns:
        Deep copy of session data
    """
    if session_data is None:
        return {}

    try:
        return copy.deepcopy(session_data)
    except Exception as e:
        print(f"Warning: Could not deep copy session data: {e}")
        # Fallback to shallow copy
        return session_data.copy() if session_data else {}


def create_timeout_message(seconds: int, context: str = "operation") -> str:
    """
    Create a user-friendly timeout message.

    Args:
        seconds: Timeout duration
        context: What operation timed out

    Returns:
        User-friendly message
    """
    return (
        f"The {context} is taking longer than expected ({seconds}s timeout). "
        f"Please try again or simplify your query. "
        f"If this persists, contact support."
    )


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("Quick Fixes Module - Usage Examples")
    print("=" * 80)

    # Example 1: Request Management
    print("\n1. Request Management:")
    rm = get_request_manager()
    req_id = rm.create_request("Sample query", {"key": "value"})
    print(f"   Created request: {req_id}")
    print(f"   Is active: {rm.is_active(req_id)}")
    rm.complete_request(req_id)
    print(f"   After completion: {rm.is_active(req_id)}")

    # Example 2: Thread Pool
    print("\n2. Thread Pool:")
    pool = get_thread_pool()
    def sample_task():
        time.sleep(0.1)
        return "Done"

    future = pool.submit(sample_task)
    result = future.result()
    print(f"   Task result: {result}")
    print(f"   Pool stats: {pool.get_stats()}")

    # Example 3: Error Handling
    print("\n3. Error Handling:")
    eh = get_error_handler()
    try:
        raise ValueError("Sample error")
    except Exception as e:
        error_msg = eh.handle_error(e, "testing", request_id="test-123")
        print(f"   Error message: {error_msg['content']}")
        print(f"   Error stats: {eh.get_stats()}")

    print("\n" + "=" * 80)
    print("All examples completed successfully!")
