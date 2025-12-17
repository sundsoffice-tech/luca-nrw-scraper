"""Test that _bounded_process always returns a tuple."""
import asyncio
import pytest

import scriptname as sn


@pytest.mark.asyncio
async def test_bounded_process_empty_urls_returns_tuple(monkeypatch):
    """Test that _bounded_process returns (0, []) when given empty URLs."""
    # Mock rate limiter
    rate = sn._Rate(max_global=1, max_per_host=1)
    
    # Test with empty list
    result = await sn._bounded_process([], run_id=1, rate=rate, force=False)
    
    assert isinstance(result, tuple), "Expected tuple return type"
    assert len(result) == 2, "Expected tuple of length 2"
    assert isinstance(result[0], int), "First element should be int (links_checked)"
    assert isinstance(result[1], list), "Second element should be list (collected)"
    assert result == (0, []), "Empty URLs should return (0, [])"


@pytest.mark.asyncio
async def test_bounded_process_none_urls_returns_tuple(monkeypatch):
    """Test that _bounded_process returns a tuple when given URLs that resolve to nothing."""
    # Mock rate limiter
    rate = sn._Rate(max_global=1, max_per_host=1)
    
    # Mock process_link_async to avoid actual HTTP calls
    async def fake_process_link(item, run_id, force=False):
        return 0, []
    
    monkeypatch.setattr(sn, "process_link_async", fake_process_link)
    
    # Test with URLs that will be filtered out
    urls_with_none = [None, "", {}]
    result = await sn._bounded_process(urls_with_none, run_id=1, rate=rate, force=False)
    
    assert isinstance(result, tuple), "Expected tuple return type"
    assert len(result) == 2, "Expected tuple of length 2"
    assert isinstance(result[0], int), "First element should be int (links_checked)"
    assert isinstance(result[1], list), "Second element should be list (collected)"


@pytest.mark.asyncio
async def test_bounded_process_valid_urls_returns_tuple(monkeypatch):
    """Test that _bounded_process returns a proper tuple when processing valid URLs."""
    # Mock rate limiter
    rate = sn._Rate(max_global=1, max_per_host=1)
    
    # Mock process_link_async to simulate successful processing
    async def fake_process_link(item, run_id, force=False):
        return 1, [{"name": "Test", "email": "test@example.com"}]
    
    # Mock prioritize_urls to avoid URL processing complexity
    def fake_prioritize(urls):
        return urls
    
    monkeypatch.setattr(sn, "process_link_async", fake_process_link)
    monkeypatch.setattr(sn, "prioritize_urls", fake_prioritize)
    
    # Test with a valid URL
    urls = ["https://example.com"]
    result = await sn._bounded_process(urls, run_id=1, rate=rate, force=False)
    
    assert isinstance(result, tuple), "Expected tuple return type"
    assert len(result) == 2, "Expected tuple of length 2"
    assert isinstance(result[0], int), "First element should be int (links_checked)"
    assert isinstance(result[1], list), "Second element should be list (collected)"
    assert result[0] >= 0, "links_checked should be non-negative"


@pytest.mark.asyncio
async def test_bounded_process_exception_in_gather(monkeypatch):
    """Test that exceptions in asyncio.gather don't cause return type issues."""
    # Mock rate limiter
    rate = sn._Rate(max_global=1, max_per_host=1)
    
    # Mock process_link_async to raise an exception
    async def fake_process_link_error(item, run_id, force=False):
        raise Exception("Simulated processing error")
    
    # Mock prioritize_urls
    def fake_prioritize(urls):
        return urls
    
    monkeypatch.setattr(sn, "process_link_async", fake_process_link_error)
    monkeypatch.setattr(sn, "prioritize_urls", fake_prioritize)
    
    # Test that exception propagates (doesn't return None)
    urls = ["https://example.com"]
    
    with pytest.raises(Exception, match="Simulated processing error"):
        await sn._bounded_process(urls, run_id=1, rate=rate, force=False)
