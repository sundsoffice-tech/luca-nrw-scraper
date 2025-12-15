import pytest

import scriptname as sn


@pytest.fixture(autouse=True)
def clear_state():
    sn._reset_metrics()
    sn._RETRY_URLS.clear()
    yield
    sn._reset_metrics()
    sn._RETRY_URLS.clear()


def test_record_drop_updates_metrics():
    sn._record_drop("portal_host")
    sn._record_drop("impressum_no_contact")
    sn._record_drop("pdf_without_cv_hint")

    assert sn.RUN_METRICS["removed_by_dropper"] == 3
    assert sn.RUN_METRICS["portal_dropped"] == 1
    assert sn.RUN_METRICS["impressum_dropped"] == 1
    assert sn.RUN_METRICS["pdf_dropped"] == 1


def test_schedule_retry_counts_and_status():
    sn._schedule_retry("https://example.com", 429)
    sn._schedule_retry("https://example.com/again", 503)
    sn._schedule_retry("https://example.com/forbidden", 403)

    assert sn.RUN_METRICS["retry_count"] == 3
    assert sn.RUN_METRICS["status_429"] == 1
    assert sn.RUN_METRICS["status_403"] == 1
    assert sn.RUN_METRICS["status_5xx"] == 1


def test_finish_run_logs_metrics(monkeypatch, capsys):
    calls = []

    def fake_log(level, msg, **ctx):
        calls.append((level, msg, ctx))

    class DummyCursor:
        def execute(self, *a, **k):
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

    monkeypatch.setattr(sn, "log", fake_log)
    monkeypatch.setattr(sn, "db", lambda: DummyDB())

    metrics = {
        "removed_by_dropper": 2,
        "portal_dropped": 1,
        "impressum_dropped": 0,
        "pdf_dropped": 1,
        "retry_count": 3,
        "status_429": 1,
        "status_403": 0,
        "status_5xx": 2,
    }

    sn.finish_run(1, 5, 2, status="ok", metrics=metrics)

    assert any(msg == "Run metrics" and ctx == metrics for _, msg, ctx in calls)
