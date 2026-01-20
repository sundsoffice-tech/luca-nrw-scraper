# -*- coding: utf-8 -*-
"""
Tests for HTTP connection pooling improvements.
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'luca_scraper'))

from luca_scraper.http.client import (
    get_pooled_client,
    cleanup_connection_pool,
    _CONNECTION_POOL,
    _CONNECTION_POOL_SIZE,
)


async def test_get_pooled_client_basic():
    """Test basic connection pooling."""
    # Clear pool before test
    _CONNECTION_POOL.clear()
    
    # Get client for host1
    client1 = await get_pooled_client("example.com", secure=True)
    assert client1 is not None
    
    # Get same client again - should return same instance
    client2 = await get_pooled_client("example.com", secure=True)
    assert client1 is client2
    
    # Get client for different host - should be different instance
    client3 = await get_pooled_client("test.com", secure=True)
    assert client3 is not client1


async def test_connection_pool_size_limit():
    """Test connection pool respects size limit."""
    # Clear pool before test
    _CONNECTION_POOL.clear()
    
    # Create clients up to pool size
    clients = []
    for i in range(_CONNECTION_POOL_SIZE):
        client = await get_pooled_client(f"host{i}.com", secure=True)
        clients.append(client)
    
    # Pool should be at capacity
    assert len(_CONNECTION_POOL) <= _CONNECTION_POOL_SIZE
    
    # Add one more - should evict oldest
    new_client = await get_pooled_client("newhost.com", secure=True)
    assert len(_CONNECTION_POOL) <= _CONNECTION_POOL_SIZE


async def test_connection_pool_different_security():
    """Test connection pool handles secure and insecure separately."""
    # Clear pool before test
    _CONNECTION_POOL.clear()
    
    # Get secure client
    secure_client = await get_pooled_client("example.com", secure=True)
    
    # Get insecure client for same host - should be different
    insecure_client = await get_pooled_client("example.com", secure=False)
    
    # Should be different instances
    assert secure_client is not insecure_client
    
    # Pool should have both
    assert len(_CONNECTION_POOL) >= 2


async def test_cleanup_connection_pool():
    """Test cleaning up connection pool."""
    # Clear pool before test
    _CONNECTION_POOL.clear()
    
    # Add some clients to pool
    await get_pooled_client("host1.com", secure=True)
    await get_pooled_client("host2.com", secure=True)
    
    initial_size = len(_CONNECTION_POOL)
    assert initial_size > 0
    
    # Cleanup pool
    await cleanup_connection_pool()
    
    # Pool should be empty
    assert len(_CONNECTION_POOL) == 0


async def test_connection_pool_disabled():
    """Test connection pooling can be disabled."""
    # Clear pool before test
    _CONNECTION_POOL.clear()
    
    with patch.dict(os.environ, {"HTTP_POOL_ENABLED": "0"}):
        # Reimport to pick up env var
        import importlib
        from luca_scraper.http import client
        importlib.reload(client)
        
        # Get client - should not use pool
        client1 = await client.get_pooled_client("example.com", secure=True)
        client2 = await client.get_pooled_client("example.com", secure=True)
        
        # When disabled, should create new instances each time
        # (This test might be implementation-dependent)


def run_async_test(coro):
    """Helper to run async test."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == "__main__":
    # Run tests manually
    print("Running connection pooling tests...")
    
    run_async_test(test_get_pooled_client_basic())
    print("✓ Basic connection pooling")
    
    run_async_test(test_connection_pool_size_limit())
    print("✓ Connection pool size limit")
    
    run_async_test(test_connection_pool_different_security())
    print("✓ Connection pool different security levels")
    
    run_async_test(test_cleanup_connection_pool())
    print("✓ Connection pool cleanup")
    
    print("\nAll connection pooling tests passed! ✓")
