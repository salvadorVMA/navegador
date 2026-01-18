"""
Performance Optimization Module for Navegador Project

This module implements caching, batching, and other performance optimizations
to reduce LLM call latency and improve overall response times.
"""

import os
import json
import hashlib
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Cache implementation
class LLMCache:
    """In-memory cache for LLM responses with optional file persistence."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600, persist_file: Optional[str] = None):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.persist_file = persist_file
        self.lock = threading.Lock()
        
        # Load cache from file if it exists
        if persist_file and os.path.exists(persist_file):
            self.load_cache()
    
    def _generate_key(self, prompt: str, model: str, temperature: float) -> str:
        """Generate a hash key for the cache."""
        content = f"{prompt}|{model}|{temperature}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        return time.time() - entry['timestamp'] > self.ttl_seconds
    
    def get(self, prompt: str, model: str, temperature: float) -> Optional[str]:
        """Get cached response if available and not expired."""
        key = self._generate_key(prompt, model, temperature)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not self._is_expired(entry):
                    entry['hits'] = entry.get('hits', 0) + 1
                    return entry['response']
                else:
                    # Remove expired entry
                    del self.cache[key]
        
        return None
    
    def set(self, prompt: str, model: str, temperature: float, response: str) -> None:
        """Cache a response."""
        key = self._generate_key(prompt, model, temperature)
        
        with self.lock:
            # Implement simple LRU eviction if cache is full
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]
            
            self.cache[key] = {
                'response': response,
                'timestamp': time.time(),
                'hits': 0
            }
        
        # Persist cache if file is specified
        if self.persist_file:
            self.save_cache()
    
    def save_cache(self) -> None:
        """Save cache to file."""
        if not self.persist_file:
            return
        
        try:
            with open(self.persist_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache to {self.persist_file}: {e}")
    
    def load_cache(self) -> None:
        """Load cache from file."""
        if not self.persist_file or not os.path.exists(self.persist_file):
            return
        
        try:
            with open(self.persist_file, 'r') as f:
                self.cache = json.load(f)
            print(f"Loaded {len(self.cache)} entries from cache file")
        except Exception as e:
            print(f"Warning: Could not load cache from {self.persist_file}: {e}")
            self.cache = {}
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_hits = sum(entry.get('hits', 0) for entry in self.cache.values())
            return {
                'total_entries': len(self.cache),
                'total_hits': total_hits,
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds
            }


# Performance monitoring
class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'llm_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time': 0,
            'analysis_times': [],
            'total_tokens': 0,
            'prompt_tokens': 0,
            'completion_tokens': 0
        }
    
    def record_llm_call(self, cached: bool = False):
        """Record an LLM call."""
        self.metrics['llm_calls'] += 1
        if cached:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
    
    def record_analysis_time(self, analysis_type: str, duration: float):
        """Record analysis duration."""
        self.metrics['analysis_times'].append({
            'type': analysis_type,
            'duration': duration,
            'timestamp': time.time()
        })
        self.metrics['total_time'] += duration
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        cache_hit_rate = (self.metrics['cache_hits'] / max(1, self.metrics['llm_calls'])) * 100
        
        # Calculate average times by analysis type
        type_times = {}
        for entry in self.metrics['analysis_times']:
            analysis_type = entry['type']
            if analysis_type not in type_times:
                type_times[analysis_type] = []
            type_times[analysis_type].append(entry['duration'])
        
        avg_times = {
            analysis_type: sum(times) / len(times)
            for analysis_type, times in type_times.items()
        }
        
        return {
            'llm_calls': self.metrics['llm_calls'],
            'cache_hit_rate': round(cache_hit_rate, 2),
            'total_analysis_time': round(self.metrics['total_time'], 2),
            'average_times_by_type': {k: round(v, 2) for k, v in avg_times.items()},
            'cache_stats': _llm_cache.stats()
        }
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = {
            'llm_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time': 0,
            'analysis_times': [],
            'total_tokens': 0,
            'prompt_tokens': 0,
            'completion_tokens': 0
        }


# Global performance monitor
performance_monitor = PerformanceMonitor()


# Global cache instance
_llm_cache = LLMCache(
    max_size=2000,  # Increased from 1000 to store more responses
    ttl_seconds=86400,  # 24 hour TTL (increased from 1 hour for better cache hit rate)
    persist_file=os.path.join(os.path.dirname(__file__), "llm_cache.json")
)


def cached_llm_call(func):
    """Decorator to add caching to LLM calls."""
    @wraps(func)
    def wrapper(prompt: str, system_prompt=None, model: str = 'gpt-4o-mini-2024-07-18', temperature: float = 0.9, **kwargs):
        # Include system_prompt in cache key generation for more accurate caching
        cache_key_str = f"{prompt}|{system_prompt}|{model}|{temperature}"

        # Check cache first using combined key
        cached_response = _llm_cache.get(cache_key_str, model, temperature)
        if cached_response is not None:
            print(f"✓ Cache hit for prompt hash: {hashlib.md5(prompt.encode()).hexdigest()[:8]}")
            # Record cache hit in performance monitor
            performance_monitor.record_llm_call(cached=True)
            return cached_response

        # Call original function
        print(f"✗ Cache miss, calling LLM for prompt hash: {hashlib.md5(prompt.encode()).hexdigest()[:8]}")
        response = func(prompt, system_prompt=system_prompt, model=model, temperature=temperature, **kwargs)

        # Record cache miss in performance monitor
        performance_monitor.record_llm_call(cached=False)

        # Cache the response
        if response:
            _llm_cache.set(cache_key_str, model, temperature, response)

        return response
    return wrapper


# Batch processing for LLM calls
class LLMBatchProcessor:
    """Batch processor for parallel LLM calls."""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
    
    def process_batch(self, llm_requests: List[Dict[str, Any]], llm_function) -> List[Dict[str, Any]]:
        """
        Process multiple LLM requests in parallel.
        
        Args:
            llm_requests: List of dicts with 'prompt', 'model', 'temperature', 'key' fields
            llm_function: Function to call for each request
            
        Returns:
            List of results with same order as input
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all requests
            future_to_key = {}
            for request in llm_requests:
                future = executor.submit(
                    llm_function,
                    prompt=request['prompt'],
                    model=request.get('model', 'gpt-4o-mini-2024-07-18'),
                    temperature=request.get('temperature', 0.9)
                )
                future_to_key[future] = request['key']
            
            # Collect results
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    result = future.result()
                    results[key] = {'success': True, 'result': result}
                except Exception as e:
                    print(f"Error in batch processing for key {key}: {e}")
                    results[key] = {'success': False, 'error': str(e)}
        
        # Return results in original order
        return [results.get(req['key'], {'success': False, 'error': 'Not processed'}) 
                for req in llm_requests]


# Singleton database client
class DatabaseManager:
    """Singleton manager for database connections."""
    
    _instance = None
    _client = None
    _db_f1 = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self):
        """Get or create database client."""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    print("Initializing database client (singleton)...")
                    from utility_functions import environment_setup, embedding_fun_openai
                    self._client, self._db_f1 = environment_setup(embedding_fun_openai)
                    print("Database client initialized successfully")
        
        return self._client, self._db_f1
    
    def reset(self):
        """Reset the database connection (for testing)."""
        with self._lock:
            self._client = None
            self._db_f1 = None



def performance_timer(analysis_type: str):
    """Decorator to time analysis functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = end_time - start_time
                performance_monitor.record_analysis_time(analysis_type, duration)
                print(f"{analysis_type} completed in {duration:.2f} seconds")
        return wrapper
    return decorator


# Utility functions for performance optimization
def get_cache_stats() -> Dict[str, Any]:
    """Get current cache statistics."""
    return performance_monitor.get_stats()


def clear_cache() -> None:
    """Clear the LLM cache."""
    _llm_cache.clear()
    print("Cache cleared")


def reset_performance_metrics() -> None:
    """Reset performance monitoring metrics."""
    performance_monitor.reset()
    print("Performance metrics reset")


# ChromaDB Query Caching
class ChromaDBCache:
    """Cache for ChromaDB query results."""

    def __init__(self, max_size: int = 500, ttl_seconds: int = 86400):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
        self.stats = {'hits': 0, 'misses': 0}

    def _generate_key(self, query_embeddings: List, n_results: int, where: Optional[Dict] = None) -> str:
        """Generate cache key for ChromaDB query."""
        # Convert embeddings to string (first few digits only for key)
        emb_str = str(query_embeddings[0][:5]) if query_embeddings else ""
        where_str = json.dumps(where, sort_keys=True) if where else ""
        key_content = f"{emb_str}|{n_results}|{where_str}"
        return hashlib.md5(key_content.encode()).hexdigest()

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        return time.time() - entry['timestamp'] > self.ttl_seconds

    def get(self, query_embeddings: List, n_results: int, where: Optional[Dict] = None) -> Optional[Any]:
        """Get cached query result."""
        key = self._generate_key(query_embeddings, n_results, where)

        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not self._is_expired(entry):
                    self.stats['hits'] += 1
                    return entry['result']
                else:
                    del self.cache[key]

            self.stats['misses'] += 1
        return None

    def set(self, query_embeddings: List, n_results: int, where: Optional[Dict], result: Any) -> None:
        """Cache query result."""
        key = self._generate_key(query_embeddings, n_results, where)

        with self.lock:
            # Simple LRU eviction
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]

            self.cache[key] = {
                'result': result,
                'timestamp': time.time()
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
            return {
                'total_entries': len(self.cache),
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'ttl_seconds': self.ttl_seconds
            }

    def clear(self) -> None:
        """Clear cache."""
        with self.lock:
            self.cache.clear()
            self.stats = {'hits': 0, 'misses': 0}


# Global ChromaDB cache
_chromadb_cache = ChromaDBCache(max_size=500, ttl_seconds=86400)


def cached_chromadb_query(db_collection, query_embeddings: List, n_results: int, where: Optional[Dict] = None):
    """
    Cached wrapper for ChromaDB queries.

    Usage:
        from performance_optimization import cached_chromadb_query
        result = cached_chromadb_query(db_f1, [query_emb], n_results=10, where={"type": "question"})
    """
    # Check cache
    cached_result = _chromadb_cache.get(query_embeddings, n_results, where)
    if cached_result is not None:
        print(f"✓ ChromaDB cache hit")
        return cached_result

    # Query database
    print(f"✗ ChromaDB cache miss, querying database")
    result = db_collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        where=where
    )

    # Cache result
    _chromadb_cache.set(query_embeddings, n_results, where, result)

    return result


def get_chromadb_cache_stats() -> Dict[str, Any]:
    """Get ChromaDB cache statistics."""
    return _chromadb_cache.get_stats()


def clear_chromadb_cache() -> None:
    """Clear ChromaDB cache."""
    _chromadb_cache.clear()
    print("ChromaDB cache cleared")


# Optimized prompt templates to reduce token usage
class OptimizedPrompts:
    """Collection of optimized prompt templates."""
    
    @staticmethod
    def create_short_summary_prompt(data: str, query: str) -> str:
        """Create a concise summary prompt to reduce tokens."""
        return f"""Analyze this data for: {query}

Data: {data[:2000]}...

Provide:
1. Top 3 key findings
2. Brief answer to query

Keep response under 200 words."""
    
    @staticmethod
    def create_batch_expert_prompt(patterns: List[Dict], db_implications: str) -> str:
        """Create a batched prompt for multiple expert summaries."""
        pattern_text = "\n".join([
            f"Pattern {i+1}: {p['TITLE_SUMMARY']} - {p['DESCRIPTION'][:200]}..."
            for i, p in enumerate(patterns)
        ])
        
        return f"""Analyze these patterns with expert context:

Patterns:
{pattern_text}

Expert Context: {db_implications[:1000]}...

For each pattern, provide a 2-sentence expert analysis.
Format: Pattern X: [analysis]"""
