import pytest

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
    # Patch asyncio.sleep to be async but fast
    async def fake_sleep(*args, **kwargs):
        pass
    monkeypatch.setattr(sn.asyncio, "sleep", fake_sleep)


@pytest.mark.asyncio
async def test_daterestrict_is_forwarded(monkeypatch):
    sn.QUERIES = ["dummy"]
    calls = {"google": None, "ddg": None}

    async def fake_google(q, max_results=60, date_restrict=None):
        calls["google"] = date_restrict
        return [], False

    async def fake_ddg(q, max_results=30, date_restrict=None):
        calls["ddg"] = date_restrict
        return []

    async def fake_pplx(q):
        return []

    async def fake_ka(q, max_results=10):
        return []

    async def fake_bounded(urls, run_id, rate, force=False):
        return 0, []

    monkeypatch.setattr(sn, "google_cse_search_async", fake_google)
    monkeypatch.setattr(sn, "duckduckgo_search_async", fake_ddg)
    monkeypatch.setattr(sn, "search_perplexity_async", fake_pplx)
    monkeypatch.setattr(sn, "kleinanzeigen_search_async", fake_ka)
    monkeypatch.setattr(sn, "_bounded_process", fake_bounded)

    await sn.run_scrape_once_async(run_flag={"running": True}, force=True, date_restrict="d7")

    assert calls["google"] == "d7"
    assert calls["ddg"] == "d7"


@pytest.mark.asyncio
async def test_no_daterestrict_when_not_set(monkeypatch):
    sn.QUERIES = ["dummy"]
    calls = {"google": "set", "ddg": "set"}

    async def fake_google(q, max_results=60, date_restrict=None):
        calls["google"] = date_restrict
        return [], False

    async def fake_ddg(q, max_results=30, date_restrict=None):
        calls["ddg"] = date_restrict
        return []

    async def fake_pplx(q):
        return []

    async def fake_ka(q, max_results=10):
        return []

    async def fake_bounded(urls, run_id, rate, force=False):
        return 0, []

    monkeypatch.setattr(sn, "google_cse_search_async", fake_google)
    monkeypatch.setattr(sn, "duckduckgo_search_async", fake_ddg)
    monkeypatch.setattr(sn, "search_perplexity_async", fake_pplx)
    monkeypatch.setattr(sn, "kleinanzeigen_search_async", fake_ka)
    monkeypatch.setattr(sn, "_bounded_process", fake_bounded)

    await sn.run_scrape_once_async(run_flag={"running": True}, force=True, date_restrict=None)

    assert calls["google"] is None
    assert calls["ddg"] is None
