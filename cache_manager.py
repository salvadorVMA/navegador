"""
Cache management system for LLM responses and database queries.

This module provides caching functionality to reduce API costs and improve performance
by avoiding redundant LLM calls and database queries.
"""

import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Optional, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import sys

try:
    from config import get_config
    config = get_config()
except ImportError:
    config = None
    print("WARNING: config module not available, using default cache path", file=sys.stderr)


class CacheManager:
    """
    Manages caching for LLM responses and database queries.

    Features:
    - TTL (time-to-live) support
    - Hit/miss statistics
    - Multiple cache types (LLM, DB, etc.)
    - Automatic cleanup of expired entries
    - Cost savings tracking
    """

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl: int = 86400):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache storage. If None, uses project_root/.cache
            default_ttl: Default time-to-live in seconds (default: 86400 = 24 hours)
        """
        if cache_dir is None:
            if config:
                self.cache_dir = config.project_root / '.cache'
            else:
                self.cache_dir = Path.cwd() / '.cache'
        else:
            self.cache_dir = cache_dir

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

        # Statistics tracking
        self.stats = defaultdict(lambda: {'hits': 0, 'misses': 0, 'saves': 0})
        self.stats_file = self.cache_dir / 'cache_stats.json'
        self._load_stats()

    def _load_stats(self):
        """Load statistics from disk."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    loaded_stats = json.load(f)
                    for key, value in loaded_stats.items():
                        self.stats[key] = value
            except Exception as e:
                print(f"Warning: Could not load cache stats: {e}", file=sys.stderr)

    def _save_stats(self):
        """Save statistics to disk."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(dict(self.stats), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache stats: {e}", file=sys.stderr)

    def _generate_key(self, data: Any) -> str:
        """
        Generate a cache key from data.

        Args:
            data: Data to generate key from (will be JSON serialized)

        Returns:
            SHA256 hash of the data
        """
        # Convert to JSON string for consistent hashing
        if isinstance(data, str):
            key_str = data
        else:
            try:
                key_str = json.dumps(data, sort_keys=True)
            except (TypeError, ValueError):
                # Fall back to string representation
                key_str = str(data)

        return hashlib.sha256(key_str.encode()).hexdigest()

    def _get_cache_path(self, cache_type: str, key: str) -> Path:
        """
        Get path for cache file.

        Args:
            cache_type: Type of cache (e.g., 'llm', 'db', 'chromadb')
            key: Cache key

        Returns:
            Path to cache file
        """
        type_dir = self.cache_dir / cache_type
        type_dir.mkdir(parents=True, exist_ok=True)
        return type_dir / f"{key}.pkl"

    def _is_expired(self, cache_file: Path, ttl: int) -> bool:
        """
        Check if cache file is expired.

        Args:
            cache_file: Path to cache file
            ttl: Time-to-live in seconds

        Returns:
            True if expired or doesn't exist
        """
        if not cache_file.exists():
            return True

        file_time = cache_file.stat().st_mtime
        age = time.time() - file_time
        return age > ttl

    def get(self, cache_type: str, key_data: Any, ttl: Optional[int] = None) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            cache_type: Type of cache (e.g., 'llm', 'db')
            key_data: Data to generate cache key from
            ttl: Time-to-live in seconds (None = use default)

        Returns:
            Cached value or None if not found/expired
        """
        if ttl is None:
            ttl = self.default_ttl

        key = self._generate_key(key_data)
        cache_file = self._get_cache_path(cache_type, key)

        if self._is_expired(cache_file, ttl):
            self.stats[cache_type]['misses'] += 1
            self._save_stats()
            return None

        try:
            with open(cache_file, 'rb') as f:
                value = pickle.load(f)
                self.stats[cache_type]['hits'] += 1
                self._save_stats()
                return value
        except Exception as e:
            print(f"Warning: Could not load cache file {cache_file}: {e}", file=sys.stderr)
            self.stats[cache_type]['misses'] += 1
            self._save_stats()
            return None

    def set(self, cache_type: str, key_data: Any, value: Any) -> bool:
        """
        Store value in cache.

        Args:
            cache_type: Type of cache (e.g., 'llm', 'db')
            key_data: Data to generate cache key from
            value: Value to cache

        Returns:
            True if successful
        """
        key = self._generate_key(key_data)
        cache_file = self._get_cache_path(cache_type, key)

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
                self.stats[cache_type]['saves'] += 1
                self._save_stats()
                return True
        except Exception as e:
            print(f"Warning: Could not save to cache file {cache_file}: {e}", file=sys.stderr)
            return False

    def clear(self, cache_type: Optional[str] = None):
        """
        Clear cache.

        Args:
            cache_type: Type of cache to clear (None = clear all)
        """
        if cache_type:
            type_dir = self.cache_dir / cache_type
            if type_dir.exists():
                for cache_file in type_dir.glob('*.pkl'):
                    cache_file.unlink()
                self.stats[cache_type] = {'hits': 0, 'misses': 0, 'saves': 0}
        else:
            # Clear all caches
            for type_dir in self.cache_dir.iterdir():
                if type_dir.is_dir():
                    for cache_file in type_dir.glob('*.pkl'):
                        cache_file.unlink()
            self.stats.clear()

        self._save_stats()

    def cleanup_expired(self, cache_type: Optional[str] = None, ttl: Optional[int] = None):
        """
        Remove expired cache entries.

        Args:
            cache_type: Type of cache to clean (None = clean all)
            ttl: Time-to-live in seconds (None = use default)
        """
        if ttl is None:
            ttl = self.default_ttl

        if cache_type:
            type_dirs = [self.cache_dir / cache_type]
        else:
            type_dirs = [d for d in self.cache_dir.iterdir() if d.is_dir()]

        for type_dir in type_dirs:
            if not type_dir.exists():
                continue

            for cache_file in type_dir.glob('*.pkl'):
                if self._is_expired(cache_file, ttl):
                    cache_file.unlink()

    def get_stats(self, cache_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cache statistics.

        Args:
            cache_type: Type of cache (None = all types)

        Returns:
            Dictionary with statistics
        """
        if cache_type:
            stats_data = self.stats[cache_type].copy()
            total = stats_data['hits'] + stats_data['misses']
            stats_data['hit_rate'] = stats_data['hits'] / total if total > 0 else 0.0
            stats_data['total_requests'] = total
            return stats_data
        else:
            all_stats = {}
            for key, value in self.stats.items():
                total = value['hits'] + value['misses']
                all_stats[key] = {
                    **value,
                    'hit_rate': value['hits'] / total if total > 0 else 0.0,
                    'total_requests': total
                }
            return all_stats

    def estimate_savings(self, cache_type: str = 'llm', cost_per_call: float = 0.01) -> Dict[str, Any]:
        """
        Estimate cost savings from caching.

        Args:
            cache_type: Type of cache to analyze
            cost_per_call: Estimated cost per API call in USD

        Returns:
            Dictionary with savings estimates
        """
        stats = self.get_stats(cache_type)
        hits = stats.get('hits', 0)
        total = stats.get('total_requests', 0)

        savings = hits * cost_per_call
        potential_cost = total * cost_per_call
        actual_cost = (total - hits) * cost_per_call

        return {
            'cache_type': cache_type,
            'cache_hits': hits,
            'total_requests': total,
            'hit_rate': stats.get('hit_rate', 0.0),
            'cost_per_call': cost_per_call,
            'estimated_savings_usd': round(savings, 2),
            'actual_cost_usd': round(actual_cost, 2),
            'potential_cost_usd': round(potential_cost, 2),
            'savings_percentage': round((savings / potential_cost * 100) if potential_cost > 0 else 0, 1)
        }

    def get_cache_size(self, cache_type: Optional[str] = None) -> Dict[str, int]:
        """
        Get cache size in bytes.

        Args:
            cache_type: Type of cache (None = all types)

        Returns:
            Dictionary with size information
        """
        if cache_type:
            type_dirs = [self.cache_dir / cache_type]
        else:
            type_dirs = [d for d in self.cache_dir.iterdir() if d.is_dir()]

        sizes = {}
        for type_dir in type_dirs:
            if not type_dir.exists():
                continue

            total_size = sum(f.stat().st_size for f in type_dir.glob('*.pkl'))
            file_count = len(list(type_dir.glob('*.pkl')))
            sizes[type_dir.name] = {
                'bytes': total_size,
                'mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count
            }

        return sizes


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.

    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached_llm_call(func):
    """
    Decorator for caching LLM calls.

    Usage:
        @cached_llm_call
        def my_llm_function(prompt):
            return llm.invoke(prompt)
    """
    def wrapper(*args, **kwargs):
        cache = get_cache_manager()

        # Generate cache key from function name and arguments
        cache_key = {
            'function': func.__name__,
            'args': args,
            'kwargs': kwargs
        }

        # Try to get from cache
        result = cache.get('llm', cache_key)
        if result is not None:
            return result

        # Call function and cache result
        result = func(*args, **kwargs)
        cache.set('llm', cache_key, result)

        return result

    return wrapper
