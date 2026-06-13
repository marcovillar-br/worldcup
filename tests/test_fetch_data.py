"""Testes do tratamento de erro de rede no download da base."""

from __future__ import annotations

import urllib.error

import pytest

from worldcup import fetch_data
from worldcup.fetch_data import DataSourceError, NetworkError, _download_text


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
