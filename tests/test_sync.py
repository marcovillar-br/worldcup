"""Testes dos helpers puros de sincronização de resultados."""

from __future__ import annotations

import pytest

from worldcup.sync import _result_for, _winner, _write_fixtures_atomic


def test_result_for_handles_orientation():
    scores = {("Brazil", "Scotland"): (2, 0)}
    assert _result_for(scores, "Brazil", "Scotland") == (2, 0)
    # orientação invertida: placar é espelhado
    assert _result_for(scores, "Scotland", "Brazil") == (0, 2)
    assert _result_for(scores, "Brazil", "Japan") is None


def test_winner_decisive():
    assert _winner("Brazil", "Scotland", 2, 0, {}) == "Brazil"
    assert _winner("Brazil", "Scotland", 0, 1, {}) == "Scotland"


def test_winner_on_penalties_uses_shootouts():
    shootouts = {frozenset({"Argentina", "France"}): "Argentina"}
    assert _winner("Argentina", "France", 3, 3, shootouts) == "Argentina"
    # empate sem registro de pênaltis -> indefinido
    assert _winner("Argentina", "France", 3, 3, {}) is None


def test_write_fixtures_atomic_roundtrip(tmp_path):
    path = tmp_path / "fixtures.csv"
    rows = [{"match_id": "1", "home": "Brazil"}, {"match_id": "2", "home": "France"}]
    _write_fixtures_atomic(path, rows)
    text = path.read_text()
    assert text.splitlines() == ["match_id,home", "1,Brazil", "2,France"]
    # nenhum temporário deixado pra trás
    assert [p.name for p in path.parent.iterdir() if p.name.startswith(".fixtures-")] == []


def test_write_fixtures_atomic_preserves_original_on_failure(tmp_path):
    path = tmp_path / "fixtures.csv"
    original = "match_id,home\n1,Brazil\n"
    path.write_text(original)
    # 2ª linha tem coluna extra -> DictWriter levanta no meio da escrita (após o header já no temp)
    bad_rows = [{"match_id": "1"}, {"match_id": "2", "EXTRA": "x"}]
    with pytest.raises(ValueError):
        _write_fixtures_atomic(path, bad_rows)
    # o original (spec versionada) fica intacto e o temporário é removido
    assert path.read_text() == original
    assert [p.name for p in path.parent.iterdir() if p.name.startswith(".fixtures-")] == []
