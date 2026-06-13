"""Testes dos helpers puros de sincronização de resultados."""

from __future__ import annotations

import pytest

from worldcup.sync import _result_for, _winner, write_fixtures_atomic


def test_result_for_handles_orientation():
    scores = {("Brazil", "Scotland"): [("2026-06-20", 2, 0)]}
    assert _result_for(scores, "Brazil", "Scotland") == (2, 0)
    # orientação invertida: placar é espelhado
    assert _result_for(scores, "Scotland", "Brazil") == (0, 2)
    assert _result_for(scores, "Brazil", "Japan") is None


def test_result_for_disambiguates_rematch_by_date():
    # mesmo par 2× na Copa (grupo + reencontro no mata-mata), mesma orientação na fonte
    scores = {("Brazil", "Argentina"): [("2026-06-20", 1, 1), ("2026-07-05", 2, 0)]}
    # cada jogo recebe o placar do SEU dia (sem o bug de colapsar no último)
    assert _result_for(scores, "Brazil", "Argentina", "2026-06-20") == (1, 1)
    assert _result_for(scores, "Brazil", "Argentina", "2026-07-05") == (2, 0)
    # orientação invertida continua espelhando, por data
    assert _result_for(scores, "Argentina", "Brazil", "2026-06-20") == (1, 1)
    assert _result_for(scores, "Argentina", "Brazil", "2026-07-05") == (0, 2)
    # ambíguo (2 jogos) e data que não casa nenhuma: não chuta
    assert _result_for(scores, "Brazil", "Argentina", "2026-06-30") is None
    assert _result_for(scores, "Brazil", "Argentina") is None


def test_result_for_single_game_ignores_date_mismatch():
    # com um único jogo registrado, devolve direto mesmo se a data não casar (robustez)
    scores = {("Brazil", "Scotland"): [("2026-06-20", 2, 0)]}
    assert _result_for(scores, "Brazil", "Scotland", "2026-06-21") == (2, 0)


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
    write_fixtures_atomic(path, rows)
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
    with pytest.raises(ValueError, match="fields not in fieldnames"):
        write_fixtures_atomic(path, bad_rows)
    # o original (spec versionada) fica intacto e o temporário é removido
    assert path.read_text() == original
    assert [p.name for p in path.parent.iterdir() if p.name.startswith(".fixtures-")] == []
