"""Testes do tratamento de erro de rede no download da base."""

from __future__ import annotations

import urllib.error

import pytest

from worldcup import fetch_data
from worldcup.fetch_data import DataSourceError, NetworkError, _download_text, download_from_urls


class _FakeResp:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *exc) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_download_text_raises_networkerror_after_retries(monkeypatch):
    calls = []

    def boom(req, timeout):
        calls.append(1)
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(fetch_data.urllib.request, "urlopen", boom)
    monkeypatch.setattr(fetch_data.time, "sleep", lambda _s: None)  # não espera no teste

    with pytest.raises(NetworkError):
        _download_text("https://example.test/x", timeout=1, retries=2)
    assert len(calls) == 3  # tentativa inicial + 2 retries


def test_download_text_retries_then_succeeds(monkeypatch):
    state = {"n": 0}

    def flaky(req, timeout):
        state["n"] += 1
        if state["n"] == 1:
            raise TimeoutError("blip")
        return _FakeResp(b"ok,data\n1,2\n")

    monkeypatch.setattr(fetch_data.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(fetch_data.time, "sleep", lambda _s: None)

    assert _download_text("https://example.test/x", timeout=1, retries=1) == "ok,data\n1,2\n"
    assert state["n"] == 2  # falhou uma vez, sucesso na segunda


def test_download_raw_rejects_unexpected_schema(monkeypatch):
    # a fonte respondeu, mas faltam colunas -> erro explícito e cedo (ENG-5), não KeyError adiante
    csv_sem_colunas = "date,home_team,away_team\n2026-06-11,Mexico,South Africa\n"
    monkeypatch.setattr(fetch_data, "_download_text", lambda url, timeout: csv_sem_colunas)
    with pytest.raises(DataSourceError, match="home_score"):
        fetch_data.download_raw()


def test_download_shootouts_rejects_unexpected_schema(monkeypatch):
    csv_sem_winner = "date,home_team,away_team\n2026-06-11,Mexico,South Africa\n"
    monkeypatch.setattr(fetch_data, "_download_text", lambda url, timeout: csv_sem_winner)
    with pytest.raises(DataSourceError, match="winner"):
        fetch_data.download_shootouts()


_VALID_CSV = (
    "date,home_team,away_team,home_score,away_score,tournament,neutral\n"
    "2026-06-11,Mexico,South Africa,2,0,FIFA World Cup,False\n"
)

_PRIMARY = "https://primary.test/r.csv"
_FALLBACK = "https://fallback.test/r.csv"


def _make_fake_raw(valid_csv: str):
    from io import StringIO

    import pandas as pd

    def _fake(url: str, timeout: int = 60) -> pd.DataFrame:
        return pd.read_csv(StringIO(valid_csv))

    return _fake


def test_download_from_urls_falls_back_on_network_error(monkeypatch):
    """Primeira URL com NetworkError → usa a segunda."""
    called = []
    good = _make_fake_raw(_VALID_CSV)

    def fake_download_raw(url: str, timeout: int = 60):
        called.append(url)
        if url == _PRIMARY:
            raise NetworkError("offline")
        return good(url, timeout)

    monkeypatch.setattr(fetch_data, "download_raw", fake_download_raw)
    df = download_from_urls([_PRIMARY, _FALLBACK])
    assert called == [_PRIMARY, _FALLBACK]
    assert len(df) == 1


def test_download_from_urls_falls_back_on_schema_error(monkeypatch):
    """Primeira URL com DataSourceError → usa a segunda."""
    called = []
    good = _make_fake_raw(_VALID_CSV)

    def fake_download_raw(url: str, timeout: int = 60):
        called.append(url)
        if url == _PRIMARY:
            raise DataSourceError("schema mudou")
        return good(url, timeout)

    monkeypatch.setattr(fetch_data, "download_raw", fake_download_raw)
    df = download_from_urls([_PRIMARY, _FALLBACK])
    assert called == [_PRIMARY, _FALLBACK]
    assert len(df) == 1


def test_download_from_urls_raises_when_all_fail(monkeypatch):
    """Todas as URLs falham → relança o último erro."""

    def fake_download_raw(url: str, timeout: int = 60):
        raise NetworkError(f"offline: {url}")

    monkeypatch.setattr(fetch_data, "download_raw", fake_download_raw)
    with pytest.raises(NetworkError, match="offline"):
        download_from_urls([_PRIMARY, _FALLBACK])
