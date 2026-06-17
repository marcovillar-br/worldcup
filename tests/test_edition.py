"""Testes da edição (carregamento e transformações)."""

from __future__ import annotations

from worldcup.edition import _load_odds, load_edition


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


def test_2026_odds_well_formed():
    # odds.csv (se presente) carrega como {match_id válido: (home,draw,away)} de odds decimais > 1.0;
    # robusto a quais jogos/valores e à ausência do arquivo (dict vazio passa trivialmente)
    ed = load_edition(2026)
    valid_ids = {f.match_id for f in ed.fixtures}
    for mid, odds in ed.odds.items():
        assert mid in valid_ids
        assert len(odds) == 3
        assert all(o > 1.0 for o in odds)


def test_load_odds_parses_and_skips_blanks(tmp_path):
    path = tmp_path / "odds.csv"
    path.write_text(
        "match_id,home,draw,away\n"
        "21,1.90,3.40,4.20\n"
        "22,,,\n"  # linha em branco: ignorada (jogo sem odds ainda)
        "23,2.10,3.30,3.60\n",
        encoding="utf-8",
    )
    odds = _load_odds(path)
    assert set(odds) == {21, 23}
    assert odds[21] == (1.90, 3.40, 4.20)


def test_load_odds_missing_file_is_empty(tmp_path):
    assert _load_odds(tmp_path / "nope.csv") == {}


def test_2026_blend_weight_prior():
    # prior de princípio do ENG-19 (Gate 2): w≈0.6 travado — mudar deve ser deliberado
    assert load_edition(2026).scoring.blend_weight == 0.6
