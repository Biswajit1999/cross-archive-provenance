"""Unit tests for the retry/status-classification logic in cli.py, using a
monkeypatched resolve_in_simbad -- no network needed to test the retry
behavior itself (the underlying function's real network behavior is
covered separately by the network-marked tests in test_data.py)."""
from provenance import cli
from provenance.data import SimbadQueryError


def test_resolve_with_retries_returns_resolved_on_first_success(monkeypatch):
    monkeypatch.setattr(cli, "resolve_in_simbad", lambda name: {"simbad_main_id": name})
    result, status = cli._resolve_with_retries("HD 209458", retries=2, backoff_seconds=0)
    assert status == "resolved"
    assert result == {"simbad_main_id": "HD 209458"}


def test_resolve_with_retries_returns_not_found_without_retrying(monkeypatch):
    calls = []

    def fake_resolve(name):
        calls.append(name)

    monkeypatch.setattr(cli, "resolve_in_simbad", fake_resolve)
    result, status = cli._resolve_with_retries("Not A Real Star", retries=2, backoff_seconds=0)
    assert status == "not_found"
    assert result is None
    assert len(calls) == 1  # a genuine "not found" is not retried


def test_resolve_with_retries_recovers_after_one_transient_failure(monkeypatch):
    """Regression test for the underlying fix: a query that fails once
    (network blip) and then succeeds should be reported as resolved, not
    silently miscounted as unresolved the way a bare `except Exception:
    return None` would have (an external review, Codex, caught that)."""
    attempts = {"n": 0}

    def flaky_resolve(name):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise SimbadQueryError("transient network error")
        return {"simbad_main_id": name}

    monkeypatch.setattr(cli, "resolve_in_simbad", flaky_resolve)
    result, status = cli._resolve_with_retries("HD 209458", retries=2, backoff_seconds=0)
    assert status == "resolved"
    assert result == {"simbad_main_id": "HD 209458"}
    assert attempts["n"] == 2


def test_resolve_with_retries_reports_query_failed_after_exhausting_retries(monkeypatch):
    def always_fails(name):
        raise SimbadQueryError("persistent failure")

    monkeypatch.setattr(cli, "resolve_in_simbad", always_fails)
    result, status = cli._resolve_with_retries("HD 209458", retries=2, backoff_seconds=0)
    assert status == "query_failed"
    assert result is None
