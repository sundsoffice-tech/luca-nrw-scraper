"""
Tests for asynchronous query processing with task pool and dynamic query loading.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import scriptname as sn


class DummyCursor:
    def execute(self, *args, **kwargs):
        return self
    
    def fetchall(self):
        return []
    
    def fetchone(self):
        return [0]


class DummyDB:
    def cursor(self):
        return DummyCursor()
    
    def commit(self):
        return None
    
    def close(self):
        return None


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    """Patch database and basic functions for all tests."""
    monkeypatch.setattr(sn, "init_db", lambda: None)
    monkeypatch.setattr(sn, "db", lambda: DummyDB())
    monkeypatch.setattr(sn, "start_run", lambda: 1)
    monkeypatch.setattr(sn, "finish_run", lambda *a, **k: None)
    monkeypatch.setattr(sn, "mark_query_done", lambda *a, **k: None)
    monkeypatch.setattr(sn, "append_csv", lambda *a, **k: None)
    monkeypatch.setattr(sn, "append_xlsx", lambda *a, **k: None)
    monkeypatch.setattr(sn, "insert_leads", lambda *a, **k: [])
    monkeypatch.setattr(sn, "url_seen", lambda *a, **k: False)
    monkeypatch.setattr(sn, "is_denied", lambda *a, **k: False)
    monkeypatch.setattr(sn, "path_ok", lambda *a, **k: True)
    monkeypatch.setattr(sn, "_url_seen_fast", lambda *a, **k: False)
    monkeypatch.setattr(sn, "is_query_done", lambda *a, **k: False)
    # Patch asyncio.sleep to be async but fast
    async def fake_sleep(*args, **kwargs):
        pass
    monkeypatch.setattr(sn.asyncio, "sleep", fake_sleep)


@pytest.mark.asyncio
async def test_get_dynamic_queries_with_openai(monkeypatch):
    """Test get_dynamic_queries generates queries using OpenAI."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    # Mock generate_smart_dorks to return test queries
    async def fake_smart_dorks(industry, count=5):
        return [f"smart_query_{i}_{industry}" for i in range(count)]
    
    monkeypatch.setattr(sn, "generate_smart_dorks", fake_smart_dorks)
    
    queries = await sn.get_dynamic_queries("candidates", count=3)
    
    assert len(queries) == 3
    assert all("smart_query" in q for q in queries)
    assert all("candidates" in q for q in queries)


@pytest.mark.asyncio
async def test_get_dynamic_queries_with_learning(monkeypatch):
    """Test get_dynamic_queries uses learning engine when available."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    # Mock learning engine
    mock_learning = MagicMock()
    mock_learning.get_best_dorks = MagicMock(return_value=["learning_query_1", "learning_query_2"])
    
    queries = await sn.get_dynamic_queries("vertrieb", count=4, learning_engine=mock_learning)
    
    assert len(queries) >= 2
    assert "learning_query_1" in queries
    assert "learning_query_2" in queries


@pytest.mark.asyncio
async def test_get_dynamic_queries_fallback(monkeypatch):
    """Test get_dynamic_queries falls back to extended dorks."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    # Mock get_smart_dorks_extended
    def fake_extended(industry, count=20):
        return [f"extended_query_{i}" for i in range(count)]
    
    monkeypatch.setattr(sn, "get_smart_dorks_extended", fake_extended)
    
    queries = await sn.get_dynamic_queries("handelsvertreter", count=5, learning_engine=None)
    
    assert len(queries) == 5
    assert all("extended_query" in q for q in queries)


@pytest.mark.asyncio
async def test_process_query_async_basic(monkeypatch):
    """Test process_query_async processes a single query."""
    query = "test query"
    run_id = 1
    rate = sn._Rate(max_global=10, max_per_host=2)
    
    # Mock search functions
    async def fake_google(q, max_results=60, date_restrict=None):
        return [{"url": f"http://example{i}.com", "title": f"Title {i}"} for i in range(3)], False
    
    async def fake_ddg(q, max_results=30, date_restrict=None):
        return []
    
    async def fake_pplx(q):
        return []
    
    async def fake_ka(q, max_results=10):
        return []
    
    async def fake_bounded(urls, run_id, rate, force=False):
        # Return some dummy leads
        leads = [{"email": f"test{i}@example.com", "score": 80} for i in range(len(urls))]
        return len(urls), leads
    
    monkeypatch.setattr(sn, "google_cse_search_async", fake_google)
    monkeypatch.setattr(sn, "duckduckgo_search_async", fake_ddg)
    monkeypatch.setattr(sn, "search_perplexity_async", fake_pplx)
    monkeypatch.setattr(sn, "kleinanzeigen_search_async", fake_ka)
    monkeypatch.setattr(sn, "_bounded_process", fake_bounded)
    monkeypatch.setattr(sn, "domain_pivot_queries", lambda dom: [])
    monkeypatch.setattr(sn, "try_sitemaps_async", lambda base: [])
    
    links_checked, leads = await sn.process_query_async(query, run_id, rate)
    
    assert links_checked > 0
    assert len(leads) > 0


@pytest.mark.asyncio
async def test_process_query_async_skip_done(monkeypatch):
    """Test process_query_async skips already done queries."""
    query = "already done query"
    run_id = 1
    rate = sn._Rate(max_global=10, max_per_host=2)
    
    # Mock is_query_done to return True
    monkeypatch.setattr(sn, "is_query_done", lambda q: True)
    
    links_checked, leads = await sn.process_query_async(query, run_id, rate, force=False)
    
    assert links_checked == 0
    assert len(leads) == 0


@pytest.mark.asyncio
async def test_process_query_async_respects_stop_flag(monkeypatch):
    """Test process_query_async respects run_flag stop signal."""
    query = "test query"
    run_id = 1
    rate = sn._Rate(max_global=10, max_per_host=2)
    run_flag = {"running": False}
    
    links_checked, leads = await sn.process_query_async(query, run_id, rate, run_flag=run_flag)
    
    assert links_checked == 0
    assert len(leads) == 0


@pytest.mark.asyncio
async def test_parallel_query_processing(monkeypatch):
    """Test that multiple queries are processed in parallel using asyncio.gather."""
    monkeypatch.setenv("MAX_CONCURRENT_QUERIES", "2")
    sn.QUERIES = ["query1", "query2", "query3"]
    
    processed_queries = []
    
    async def fake_process_query(q, run_id, rate, run_flag=None, force=False, date_restrict=None):
        processed_queries.append(q)
        await asyncio.sleep(0.01)  # Simulate some work
        return (1, [])
    
    # Mock all search functions
    async def fake_google(q, max_results=60, date_restrict=None):
        return [], False
    
    async def fake_ddg(q, max_results=30, date_restrict=None):
        return []
    
    async def fake_pplx(q):
        return []
    
    async def fake_ka(q, max_results=10):
        return []
    
    async def fake_bounded(urls, run_id, rate, force=False):
        return 0, []
    
    async def fake_enrich(leads):
        return leads
    
    monkeypatch.setattr(sn, "process_query_async", fake_process_query)
    monkeypatch.setattr(sn, "google_cse_search_async", fake_google)
    monkeypatch.setattr(sn, "duckduckgo_search_async", fake_ddg)
    monkeypatch.setattr(sn, "search_perplexity_async", fake_pplx)
    monkeypatch.setattr(sn, "kleinanzeigen_search_async", fake_ka)
    monkeypatch.setattr(sn, "_bounded_process", fake_bounded)
    monkeypatch.setattr(sn, "enrich_leads_with_telefonbuch", fake_enrich)
    monkeypatch.setattr(sn, "crawl_portals_smart", AsyncMock(return_value=[]))
    
    await sn.run_scrape_once_async(run_flag={"running": True}, force=True)
    
    # All queries should be processed
    assert len(processed_queries) >= 3
    assert "query1" in processed_queries
    assert "query2" in processed_queries
    assert "query3" in processed_queries


@pytest.mark.asyncio
async def test_dynamic_query_loading(monkeypatch):
    """Test that new dynamic queries are loaded during execution."""
    monkeypatch.setenv("MAX_CONCURRENT_QUERIES", "2")
    monkeypatch.setenv("DYNAMIC_QUERY_INTERVAL", "2")
    sn.QUERIES = ["query1", "query2"]
    
    dynamic_queries_generated = []
    
    async def fake_get_dynamic_queries(industry, count=5, learning_engine=None):
        new_queries = [f"dynamic_query_{len(dynamic_queries_generated)}_{i}" for i in range(count)]
        dynamic_queries_generated.extend(new_queries)
        return new_queries
    
    async def fake_process_query(q, run_id, rate, run_flag=None, force=False, date_restrict=None):
        await asyncio.sleep(0.01)
        return (1, [])
    
    async def fake_enrich(leads):
        return leads
    
    monkeypatch.setattr(sn, "get_dynamic_queries", fake_get_dynamic_queries)
    monkeypatch.setattr(sn, "process_query_async", fake_process_query)
    monkeypatch.setattr(sn, "enrich_leads_with_telefonbuch", fake_enrich)
    monkeypatch.setattr(sn, "crawl_portals_smart", AsyncMock(return_value=[]))
    
    await sn.run_scrape_once_async(run_flag={"running": True}, force=True)
    
    # Dynamic queries should have been generated
    assert len(dynamic_queries_generated) > 0


@pytest.mark.asyncio
async def test_asyncio_gather_for_pivot_queries(monkeypatch):
    """Test that pivot queries use asyncio.gather for parallel execution."""
    query = "test query"
    run_id = 1
    rate = sn._Rate(max_global=10, max_per_host=2)
    
    gather_called = []
    
    # Store original asyncio.gather
    original_gather = asyncio.gather
    
    async def tracking_gather(*tasks, **kwargs):
        gather_called.append(len(tasks))
        return await original_gather(*tasks, **kwargs)
    
    # Mock search functions to return domains for pivot queries
    async def fake_google(q, max_results=60, date_restrict=None):
        if "domain:" in q or "site:" in q:
            # Pivot query
            return [{"url": "http://pivot.com/page"}], False
        return [{"url": "http://example.com/page"}], False
    
    async def fake_ddg(q, max_results=30, date_restrict=None):
        return []
    
    async def fake_pplx(q):
        return []
    
    async def fake_ka(q, max_results=10):
        return []
    
    async def fake_bounded(urls, run_id, rate, force=False):
        return len(urls), []
    
    def fake_domain_pivot(dom):
        return [f"site:{dom} contact", f"site:{dom} team"]
    
    monkeypatch.setattr(asyncio, "gather", tracking_gather)
    monkeypatch.setattr(sn, "google_cse_search_async", fake_google)
    monkeypatch.setattr(sn, "duckduckgo_search_async", fake_ddg)
    monkeypatch.setattr(sn, "search_perplexity_async", fake_pplx)
    monkeypatch.setattr(sn, "kleinanzeigen_search_async", fake_ka)
    monkeypatch.setattr(sn, "_bounded_process", fake_bounded)
    monkeypatch.setattr(sn, "domain_pivot_queries", fake_domain_pivot)
    monkeypatch.setattr(sn, "try_sitemaps_async", lambda base: [])
    
    await sn.process_query_async(query, run_id, rate)
    
    # asyncio.gather should have been called for pivot queries
    assert len(gather_called) > 0
    # Should have multiple tasks in gather (pivot queries)
    assert any(count > 1 for count in gather_called)


@pytest.mark.asyncio
async def test_query_deduplication_in_dynamic_loading(monkeypatch):
    """Test that dynamic queries don't duplicate already processed queries."""
    monkeypatch.setenv("MAX_CONCURRENT_QUERIES", "1")
    monkeypatch.setenv("DYNAMIC_QUERY_INTERVAL", "1")
    sn.QUERIES = ["query1"]
    
    async def fake_get_dynamic_queries(industry, count=5, learning_engine=None):
        # Return mix of new and duplicate queries
        return ["query1", "new_query_2", "new_query_3"]
    
    processed_queries = []
    
    async def fake_process_query(q, run_id, rate, run_flag=None, force=False, date_restrict=None):
        processed_queries.append(q)
        await asyncio.sleep(0.01)
        return (1, [])
    
    async def fake_enrich(leads):
        return leads
    
    monkeypatch.setattr(sn, "get_dynamic_queries", fake_get_dynamic_queries)
    monkeypatch.setattr(sn, "process_query_async", fake_process_query)
    monkeypatch.setattr(sn, "enrich_leads_with_telefonbuch", fake_enrich)
    monkeypatch.setattr(sn, "crawl_portals_smart", AsyncMock(return_value=[]))
    
    await sn.run_scrape_once_async(run_flag={"running": True}, force=True)
    
    # query1 should only be processed once (no duplicates)
    assert processed_queries.count("query1") == 1
    # new queries should be processed
    assert "new_query_2" in processed_queries
    assert "new_query_3" in processed_queries
