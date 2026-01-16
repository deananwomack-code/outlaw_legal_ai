"""
rate_limiter.py — Simple rate limiting middleware
-------------------------------------------------
Provides basic rate limiting to prevent API abuse and ensure fair usage.
"""

from fastapi import HTTPException, Request
from typing import Dict, Tuple
import time
import logging
from collections import defaultdict

logger = logging.getLogger("outlaw.ratelimit")

# ============================================================
# RATE LIMIT CONFIGURATION
# ============================================================

# Default: 100 requests per minute per IP
DEFAULT_RATE_LIMIT = 100
DEFAULT_WINDOW_SECONDS = 60


class RateLimiter:
    """
    Simple in-memory rate limiter based on sliding window algorithm.
    
    Tracks requests per IP address and enforces configurable limits.
    """
    
    def __init__(self, max_requests: int = DEFAULT_RATE_LIMIT, window_seconds: int = DEFAULT_WINDOW_SECONDS):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def _clean_old_requests(self, client_id: str, current_time: float):
        """Remove requests older than the window."""
        cutoff_time = current_time - self.window_seconds
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff_time
        ]
    
    def is_allowed(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Check if request is allowed for the client.
        
        Args:
            client_id: Unique identifier for the client (e.g., IP address)
        
        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(client_id, current_time)
        
        # Check if limit exceeded
        request_count = len(self.requests[client_id])
        
        if request_count >= self.max_requests:
            # Calculate when the oldest request will expire
            oldest_request = min(self.requests[client_id])
            retry_after = int(oldest_request + self.window_seconds - current_time) + 1
            return False, 0, retry_after
        
        # Record this request
        self.requests[client_id].append(current_time)
        
        remaining = self.max_requests - request_count - 1
        return True, remaining, 0
    
    def reset(self, client_id: str = None):
        """
        Reset rate limit for a specific client or all clients.
        
        Args:
            client_id: Client to reset, or None to reset all
        """
        if client_id:
            self.requests.pop(client_id, None)
        else:
            self.requests.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get rate limiter statistics."""
        return {
            "tracked_clients": len(self.requests),
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds
        }


# Global rate limiter instance
_global_rate_limiter = RateLimiter()


# ============================================================
# MIDDLEWARE HELPER
# ============================================================

async def check_rate_limit(request: Request):
    """
    Check rate limit for incoming request.
    
    Args:
        request: FastAPI request object
    
    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Get client identifier (IP address)
    client_host = request.client.host if request.client else "unknown"
    
    # Check rate limit
    is_allowed, remaining, retry_after = _global_rate_limiter.is_allowed(client_host)
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for {client_host}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
    
    # Add rate limit info to response headers (handled by caller)
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = _global_rate_limiter.max_requests


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _global_rate_limiter


def reset_rate_limit(client_id: str = None):
    """Reset rate limit for a client or all clients."""
    _global_rate_limiter.reset(client_id)
    if client_id:
        logger.info(f"Rate limit reset for {client_id}")
    else:
        logger.info("Rate limit reset for all clients")


def get_rate_limit_stats() -> Dict[str, int]:
    """Get rate limiter statistics."""
    return _global_rate_limiter.get_stats()
