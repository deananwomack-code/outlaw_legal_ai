"""
Tests for rate_limiter.py
------------------------
Validates rate limiting functionality.
"""

import pytest
import time
from rate_limiter import RateLimiter


def test_rate_limiter_allows_within_limit():
    """Rate limiter should allow requests within the limit."""
    limiter = RateLimiter(max_requests=5, window_seconds=10)
    
    # Make 5 requests
    for i in range(5):
        is_allowed, remaining, retry_after = limiter.is_allowed("client1")
        assert is_allowed is True
        assert remaining >= 0


def test_rate_limiter_blocks_over_limit():
    """Rate limiter should block requests exceeding the limit."""
    limiter = RateLimiter(max_requests=3, window_seconds=10)
    
    # Make 3 requests (should succeed)
    for i in range(3):
        is_allowed, remaining, retry_after = limiter.is_allowed("client1")
        assert is_allowed is True
    
    # 4th request should be blocked
    is_allowed, remaining, retry_after = limiter.is_allowed("client1")
    assert is_allowed is False
    assert remaining == 0
    assert retry_after > 0


def test_rate_limiter_different_clients():
    """Rate limiter should track different clients independently."""
    limiter = RateLimiter(max_requests=2, window_seconds=10)
    
    # Client1 makes 2 requests
    limiter.is_allowed("client1")
    limiter.is_allowed("client1")
    
    # Client2 should still be able to make requests
    is_allowed, _, _ = limiter.is_allowed("client2")
    assert is_allowed is True


def test_rate_limiter_window_expiration():
    """Rate limiter should allow requests after window expires."""
    limiter = RateLimiter(max_requests=2, window_seconds=1)
    
    # Use up the limit
    limiter.is_allowed("client1")
    limiter.is_allowed("client1")
    
    # Should be blocked
    is_allowed, _, _ = limiter.is_allowed("client1")
    assert is_allowed is False
    
    # Wait for window to expire
    time.sleep(1.1)
    
    # Should be allowed again
    is_allowed, _, _ = limiter.is_allowed("client1")
    assert is_allowed is True


def test_rate_limiter_reset_specific_client():
    """Rate limiter should reset limits for specific client."""
    limiter = RateLimiter(max_requests=2, window_seconds=10)
    
    # Use up the limit
    limiter.is_allowed("client1")
    limiter.is_allowed("client1")
    
    # Should be blocked
    is_allowed, _, _ = limiter.is_allowed("client1")
    assert is_allowed is False
    
    # Reset the client
    limiter.reset("client1")
    
    # Should be allowed again
    is_allowed, _, _ = limiter.is_allowed("client1")
    assert is_allowed is True


def test_rate_limiter_reset_all():
    """Rate limiter should reset all clients."""
    limiter = RateLimiter(max_requests=1, window_seconds=10)
    
    # Multiple clients use up their limits
    limiter.is_allowed("client1")
    limiter.is_allowed("client2")
    
    # Both should be blocked
    assert limiter.is_allowed("client1")[0] is False
    assert limiter.is_allowed("client2")[0] is False
    
    # Reset all
    limiter.reset()
    
    # Both should be allowed again
    assert limiter.is_allowed("client1")[0] is True
    assert limiter.is_allowed("client2")[0] is True


def test_rate_limiter_stats():
    """Rate limiter should return correct statistics."""
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    
    limiter.is_allowed("client1")
    limiter.is_allowed("client2")
    
    stats = limiter.get_stats()
    
    assert stats["tracked_clients"] == 2
    assert stats["max_requests"] == 10
    assert stats["window_seconds"] == 60


def test_rate_limiter_remaining_count():
    """Rate limiter should return correct remaining count."""
    limiter = RateLimiter(max_requests=5, window_seconds=10)
    
    # First request
    is_allowed, remaining, _ = limiter.is_allowed("client1")
    assert is_allowed is True
    assert remaining == 4
    
    # Second request
    is_allowed, remaining, _ = limiter.is_allowed("client1")
    assert is_allowed is True
    assert remaining == 3


def test_rate_limiter_retry_after():
    """Rate limiter should calculate correct retry_after value."""
    limiter = RateLimiter(max_requests=2, window_seconds=10)
    
    # Use up the limit
    limiter.is_allowed("client1")
    limiter.is_allowed("client1")
    
    # Next request should be blocked with retry_after
    is_allowed, _, retry_after = limiter.is_allowed("client1")
    assert is_allowed is False
    assert retry_after > 0
    assert retry_after <= limiter.window_seconds + 1  # Should be within window + 1
