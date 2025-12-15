import asyncio

import pytest

import scriptname as sn


@pytest.fixture(autouse=True)
def clear_retry_state():
    sn._RETRY_URLS.clear()
    sn._LAST_STATUS.clear()
    yield
    sn._RETRY_URLS.clear()
    sn._LAST_STATUS.clear()


def test_url_scheduled_on_retry_status():
    sn._schedule_retry("https://example.com", 429)

    assert "https://example.com" in sn._RETRY_URLS
    assert sn._RETRY_URLS["https://example.com"]["retries"] == 0


@pytest.mark.asyncio
async def test_retry_wave_success_removes_entry(monkeypatch):
    sn._schedule_retry("https://example.com", 429)
    sn.RETRY_BACKOFF_BASE = 0.0

    async def fake_sleep(delay):
        return None

    async def fake_bounded(urls, run_id, rate, force=False):
        sn._LAST_STATUS[urls[0]] = 200
        return 1, [{"ok": True}]

    monkeypatch.setattr(sn.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(sn, "_bounded_process", fake_bounded)

    rate = sn._Rate(max_global=1, max_per_host=1)
    total, exhausted = await sn.process_retry_urls(run_id=1, rate=rate)

    assert total == 1
    assert exhausted == 0
    assert "https://example.com" not in sn._RETRY_URLS


@pytest.mark.asyncio
async def test_retry_wave_exhausts_budget(monkeypatch):
    sn._schedule_retry("https://example.com/fail", 429)
    sn.RETRY_MAX_PER_URL = 1
    sn.RETRY_BACKOFF_BASE = 0.0

    async def fake_sleep(delay):
        return None

    async def fake_bounded(urls, run_id, rate, force=False):
        sn._LAST_STATUS[urls[0]] = 429
        return 0, []

    monkeypatch.setattr(sn.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(sn, "_bounded_process", fake_bounded)

    rate = sn._Rate(max_global=1, max_per_host=1)
    total, exhausted = await sn.process_retry_urls(run_id=1, rate=rate)

    assert total == 1
    assert exhausted == 1
    assert not sn._RETRY_URLS
