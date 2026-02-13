"""
Rate Limiter

Per-user and per-MCP rate limiting to prevent abuse.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict


class RateLimiter:
    """
    Rate limiting for MCP tool calls.
    
    Tracks:
    - Per-user rate limits
    - Per-MCP server limits
    - Burst protection
    """

    def __init__(self, default_limit: int = 100):
        """
        Initialize rate limiter.
        
        Args:
            default_limit: Default requests per hour
        """
        self.default_limit = default_limit
        self.user_requests = defaultdict(list)  # user_id -> [(timestamp, server)]
        self.server_requests = defaultdict(list)  # server -> [timestamp]

    def check_rate_limit(self, user_id: str, server: str) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            user_id: User identifier
            server: MCP server name
            
        Returns:
            True if within limits, False otherwise
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Clean old requests
        self.user_requests[user_id] = [
            (ts, srv) for ts, srv in self.user_requests[user_id]
            if ts > hour_ago
        ]

        # Check user limit
        if len(self.user_requests[user_id]) >= self.default_limit:
            return False

        # Record request
        self.user_requests[user_id].append((now, server))
        self.server_requests[server].append(now)

        return True

    def get_usage_stats(self, user_id: str) -> Dict[str, int]:
        """Get usage statistics for a user."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        recent_requests = [
            (ts, srv) for ts, srv in self.user_requests[user_id]
            if ts > hour_ago
        ]

        return {
            "total_requests": len(recent_requests),
            "limit": self.default_limit,
            "remaining": max(0, self.default_limit - len(recent_requests))
        }
