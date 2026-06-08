"""Testes dos helpers puros de sincronização de resultados."""

from __future__ import annotations

from worldcup.sync import _result_for, _winner


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
