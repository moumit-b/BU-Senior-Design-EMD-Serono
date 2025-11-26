"""
Multi-Level Cache System

Implements 3-level caching:
- L1: Query results (60s TTL) - Fast, short-term
- L2: Tool compositions (10min TTL) - Medium-term
- L3: Research session data (persistent) - Long-term
"""

import time
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict


class CacheEntry:
    """Single cache entry with expiration."""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl  # seconds
        self.hits = 0

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl

    def get_value(self) -> Any:
        self.hits += 1
        return self.value


class MultiLevelCache:
    """
    Multi-level cache with different TTLs for different data types.

    Level 1: Short-term query results
    Level 2: Medium-term composed tools
    Level 3: Long-term session data
    """

    def __init__(self):
        self.l1_cache: Dict[str, CacheEntry] = {}  # 60s TTL
        self.l2_cache: Dict[str, CacheEntry] = {}  # 600s TTL (10min)
        self.l3_cache: Dict[str, CacheEntry] = {}  # No expiration

        # Statistics
        self.stats = {
            'l1': {'hits': 0, 'misses': 0, 'evictions': 0},
            'l2': {'hits': 0, 'misses': 0, 'evictions': 0},
            'l3': {'hits': 0, 'misses': 0, 'evictions': 0},
        }

    def get(self, key: str, level: int = 1) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            level: Cache level (1, 2, or 3)

        Returns:
            Cached value or None if not found/expired
        """
        cache = self._get_cache_for_level(level)
        stats_key = f'l{level}'

        if key not in cache:
            self.stats[stats_key]['misses'] += 1
            return None

        entry = cache[key]

        if entry.is_expired():
            del cache[key]
            self.stats[stats_key]['misses'] += 1
            self.stats[stats_key]['evictions'] += 1
            return None

        self.stats[stats_key]['hits'] += 1
        return entry.get_value()

    def set(self, key: str, value: Any, level: int = 1, ttl: Optional[int] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            level: Cache level (1, 2, or 3)
            ttl: Optional custom TTL (overrides defaults)
        """
        cache = self._get_cache_for_level(level)

        # Default TTLs per level
        if ttl is None:
            if level == 1:
                ttl = 60  # 1 minute
            elif level == 2:
                ttl = 600  # 10 minutes
            else:  # level 3
                ttl = 86400 * 7  # 1 week

        cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str, level: int = 1):
        """Delete entry from cache."""
        cache = self._get_cache_for_level(level)
        if key in cache:
            del cache[key]

    def clear(self, level: Optional[int] = None):
        """Clear cache (all levels or specific level)."""
        if level is None:
            self.l1_cache.clear()
            self.l2_cache.clear()
            self.l3_cache.clear()
        else:
            cache = self._get_cache_for_level(level)
            cache.clear()

    def _get_cache_for_level(self, level: int) -> Dict[str, CacheEntry]:
        """Get the cache dict for a specific level."""
        if level == 1:
            return self.l1_cache
        elif level == 2:
            return self.l2_cache
        elif level == 3:
            return self.l3_cache
        else:
            raise ValueError(f"Invalid cache level: {level}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {}
        for level in [1, 2, 3]:
            key = f'l{level}'
            hits = self.stats[key]['hits']
            misses = self.stats[key]['misses']
            total = hits + misses
            hit_rate = hits / total if total > 0 else 0

            stats[f'level_{level}'] = {
                'hits': hits,
                'misses': misses,
                'hit_rate': hit_rate,
                'size': len(self._get_cache_for_level(level)),
                'evictions': self.stats[key]['evictions']
            }

        return stats

    def cleanup_expired(self):
        """Remove all expired entries from all levels."""
        for level in [1, 2, 3]:
            cache = self._get_cache_for_level(level)
            expired_keys = [
                key for key, entry in cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del cache[key]
                self.stats[f'l{level}']['evictions'] += 1
