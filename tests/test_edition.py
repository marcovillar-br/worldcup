"""Testes da edição (carregamento e transformações)."""

from __future__ import annotations

from worldcup.edition import _load_odds, _load_regulation, _load_shootouts, _load_totals, load_edition


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


def test_load_totals_parses_optional_columns(tmp_path):
    # ENG-35: colunas total_line/over/under no MESMO odds.csv; em branco ou ausentes ⇒ sem totals
    path = tmp_path / "odds.csv"
    path.write_text(
        "match_id,home,draw,away,total_line,over,under\n"
        "21,1.90,3.40,4.20,2.5,1.85,1.95\n"
        "22,2.10,3.30,3.60,,,\n",  # jogo com 1×2 mas sem totals: blend degrada para só-1×2
        encoding="utf-8",
    )
    totals = _load_totals(path)
    assert totals == {21: (2.5, 1.85, 1.95)}
    assert set(_load_odds(path)) == {21, 22}  # o 1×2 não é afetado pelas colunas novas


def test_load_totals_legacy_file_and_missing(tmp_path):
    legacy = tmp_path / "odds.csv"
    legacy.write_text("match_id,home,draw,away\n21,1.90,3.40,4.20\n", encoding="utf-8")
    assert _load_totals(legacy) == {}  # arquivo pré-ENG-35 segue válido
    assert _load_totals(tmp_path / "nope.csv") == {}


def test_load_shootouts(tmp_path):
    # ENG-30: match_id,winner (canônico); linhas sem vencedor ignoradas; ausente ⇒ vazio
    path = tmp_path / "shootouts.csv"
    path.write_text("match_id,winner\n74,Paraguay\n75,Morocco\n88,\n")
    winners, scores = _load_shootouts(path)
    assert winners == {74: "Paraguay", 75: "Morocco"}  # 88 (sem vencedor) ignorado
    assert scores == {}  # arquivo antigo, sem as colunas de placar, segue válido
    assert _load_shootouts(tmp_path / "nope.csv") == ({}, {})


def test_load_shootouts_penalty_scores(tmp_path):
    # ENG-59: pen_home/pen_away são OPCIONAIS e ortogonais ao vencedor (a fonte não publica o placar)
    path = tmp_path / "shootouts.csv"
    path.write_text("match_id,winner,pen_home,pen_away\n74,Paraguay,3,4\n88,Egypt,,\n96,Switzerland,4,3\n")
    winners, scores = _load_shootouts(path)
    assert winners == {74: "Paraguay", 88: "Egypt", 96: "Switzerland"}  # vencedor sem placar é válido
    assert scores == {74: (3, 4), 96: (4, 3)}  # 88 (sem placar) fica de fora, sem perder o vencedor


def test_load_regulation(tmp_path):
    # ENG-45: match_id,reg_home,reg_away (placar dos 90'); linhas sem os dois placares ignoradas
    path = tmp_path / "regulation.csv"
    path.write_text("match_id,reg_home,reg_away\n82,2,2\n99,,\n")
    reg = _load_regulation(path)
    assert reg == {82: (2, 2)}  # 99 (placar incompleto) ignorado
    assert _load_regulation(tmp_path / "nope.csv") == {}


def test_as_of_drops_future_regulation():
    # ENG-45: o placar de 90' de um jogo a partir do corte some (ainda não acontecera na manhã)
    ed = load_edition(2026).model_copy(update={"regulation": {82: (2, 2)}})
    f82 = next(f for f in ed.fixtures if f.match_id == 82)
    view = ed.as_of(f82.date)  # corte no próprio dia do J82 ⇒ deve descartá-lo
    assert 82 not in view.regulation
    assert ed.regulation == {82: (2, 2)}  # original intacto


def test_2026_blend_weight_prior():
    # w=0.8 deliberado (ENG-38, 2026-07-02): `blend-track --sweep` em 49 jogos deu Brier
    # monotônico decrescente em w (mercado > modelo); 0.8 captura o grosso sem abraçar o extremo
    # w*=1.0 em amostra pequena. Prior original do ENG-19 era 0.6. Travado: mudar é deliberado.
    assert load_edition(2026).scoring.blend_weight == 0.8


def test_2026_phase_weights():
    # ENG-27: peso de fase do app (Equilíbrio gradual) — grupos ×1, eliminatórias ×2, final ×4.
    # Travado porque é consumido na contabilidade de pontos/teto (efficiency.py); mudar é deliberado.
    cfg = load_edition(2026).scoring
    assert cfg.weight("group") == 1.0
    assert cfg.weight("R32") == 2.0
    assert cfg.weight("R16") == 2.0
    assert cfg.weight("QF") == 2.0
    assert cfg.weight("SF") == 2.0
    assert cfg.weight("final") == 4.0
    assert cfg.weight("fase_inexistente") == 1.0  # default seguro
