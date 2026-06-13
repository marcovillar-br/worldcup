"""Testes da edição (carregamento e transformações)."""

from __future__ import annotations

from worldcup.edition import load_edition


def test_as_of_clears_results_from_cutoff_onward():
    ed = load_edition(2026)
    # 2026-06-12: jogos de 11/06 permanecem; os de 12/06 (inclusive) são descartados
    view = ed.as_of("2026-06-12")
    for f in view.fixtures:
        if f.date >= "2026-06-12":
            assert not f.played  # zerado: ainda não acontecera naquela manhã
        elif f.date < "2026-06-12":
            # o que era conhecido antes do corte continua intacto
            orig = next(o for o in ed.fixtures if o.match_id == f.match_id)
            assert f.played == orig.played


def test_as_of_does_not_mutate_original():
    ed = load_edition(2026)
    played_before = [f.match_id for f in ed.fixtures if f.played]
    ed.as_of("2026-06-11")  # zera tudo na cópia
    played_after = [f.match_id for f in ed.fixtures if f.played]
    assert played_before == played_after  # original inalterado
