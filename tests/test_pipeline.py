"""Testes de utilitários do pipeline."""

from conftest import mini_historical
from worldcup import pipeline
from worldcup.edition import load_edition
from worldcup.pipeline import _pct_round


def test_pct_round_sums_to_100():
    # caso que arredondado independentemente daria 73+19+9 = 101
    assert sum(_pct_round(0.726, 0.194, 0.089)) == 100
    # caso que daria 50+26+23 = 99
    assert sum(_pct_round(0.504, 0.263, 0.233)) == 100


def test_pct_round_preserves_order():
    ph, pd_, pa = _pct_round(0.726, 0.194, 0.089)
    assert ph > pd_ > pa


def test_pct_round_exact_values_unchanged():
    assert _pct_round(0.5, 0.3, 0.2) == [50, 30, 20]


def test_pct_round_extra_unit_goes_to_largest_remainder():
    # 33.4 / 33.3 / 33.3  -> resto sobra 1, vai para a maior fração (a primeira)
    assert _pct_round(0.334, 0.333, 0.333) == [34, 33, 33]


# ------------------------------------------------- e2e do pipeline real no CI (ENG-20)
def test_pipeline_run_e2e_invariants(monkeypatch):
    """Roda `pipeline.run` de ponta a ponta com histórico sintético e afirma invariantes
    estruturais — fecha o ponto cego de o CI nunca exercitar fit→sim→bracket→predict."""
    monkeypatch.setattr(pipeline, "load_historical", mini_historical)
    ed = load_edition(2026).as_of("2026-06-11")  # pré-torneio: 104 jogos não disputados
    result = pipeline.run(ed, n_sims=100, seed=1)

    assert len(result.rows) == len(ed.fixtures) == 104
    assert all(r["status"] == "PREVISTO" for r in result.rows)  # nada disputado no pré-torneio

    group_rows = [r for r in result.rows if r["fase"] == "group"]
    assert len(group_rows) == 72
    for r in group_rows:
        ph, pdr, pa = (int(r[k].rstrip("%")) for k in ("P_mandante", "P_empate", "P_visitante"))
        assert ph + pdr + pa == 100  # Hamilton (_pct_round) garante soma exata
        assert "x" in r["palpite"]  # todo jogo previsto tem placar

    ko_rows = [r for r in result.rows if r["fase"] != "group"]
    assert len(ko_rows) == 32
    for r in ko_rows:
        assert r["mandante"] != "?"  # chaveamento resolvido
        assert r["avanca"]  # quem avança preenchido

    assert abs(sum(result.champion_prob.values()) - 1.0) < 0.02  # probabilidades de título normalizadas


def test_final_ko_layers_real_outcomes():
    # ENG-30: jogo de KO já disputado mostra prorrogação/pênaltis/quem avançou reais.
    from worldcup.edition import Fixture
    from worldcup.pipeline import _final_ko_layers

    def ko(match_id, home, away, hg, ag, winner):
        return Fixture(
            match_id=match_id,
            stage="R32",
            date="2026-06-29",
            home=home,
            away=away,
            home_goals=hg,
            away_goals=ag,
            ko_outcome=winner,
        )

    # decidido nos 90' → "—"/"—", avança o vencedor real
    assert _final_ko_layers(ko(76, "Brazil", "Japan", 2, 1, "Brazil"), {}) == ("—", "—", "Brasil")
    # empate nos 90' + shootout capturado → "Vai aos pênaltis" + vencedor
    pen = ko(74, "Germany", "Paraguay", 1, 1, "Paraguay")
    assert _final_ko_layers(pen, {74: "Paraguay"}) == ("Vai aos pênaltis", "Paraguai", "Paraguai")
    # empate nos 90' SEM shootout conhecido → prorrogação/pênaltis vazios, mas avança conhecido
    assert _final_ko_layers(ko(75, "Netherlands", "Morocco", 1, 1, "Morocco"), {}) == ("", "", "Marrocos")


def test_edition_loads_shootouts():
    from worldcup.edition import load_edition

    sh = load_edition(2026).shootouts
    # capturado de fontes verificadas: J74 Paraguai, J75 Marrocos, J88 Egito a pênaltis
    assert sh.get(74) == "Paraguay"
    assert sh.get(75) == "Morocco"
    assert sh.get(88) == "Egypt"


def test_build_training_frame_no_double_count():
    """Jogos da edição presentes na base histórica (fetch-data no meio da Copa) não são contados em
    dobro: entram uma vez só, com o boost — não também a peso 1.0 pela base."""
    import pandas as pd

    from worldcup.pipeline import CURRENT_EDITION_BOOST, build_training_frame

    ed = load_edition(2026).as_of("2026-06-20")  # alguns jogos de grupo já disputados
    played = next(f for f in ed.fixtures if f.played and f.home in ed.teams and f.away in ed.teams)

    # base histórica que JÁ contém o jogo da edição (mesmo par/dia) + uma linha de enchimento
    historical = pd.DataFrame(
        [
            {
                "date": pd.Timestamp(played.date),
                "home_team": played.home,
                "away_team": played.away,
                "home_score": 9,  # placar "errado" na base: deve ser descartado em favor do fixture
                "away_score": 9,
                "tournament": "FIFA World Cup",
                "neutral": played.neutral,
            },
            {
                "date": pd.Timestamp("2000-01-01"),
                "home_team": played.home,
                "away_team": played.away,
                "home_score": 0,
                "away_score": 0,
                "tournament": "Friendly",
                "neutral": True,
            },
        ]
    )
    train = build_training_frame(ed, historical)

    key = train.apply(lambda r: (str(r["date"])[:10], frozenset((r["home_team"], r["away_team"]))), axis=1)
    match_key = (str(played.date)[:10], frozenset((played.home, played.away)))
    matches = train[key == match_key]
    assert len(matches) == 1  # uma única cópia, não duas
    assert matches.iloc[0]["weight_mult"] == CURRENT_EDITION_BOOST  # a do fixture (boost), não a base
    assert matches.iloc[0]["home_score"] == played.home_goals  # placar autoritativo é o do fixture
    # a linha de enchimento (dia diferente) permanece intacta
    assert (train["tournament"] == "Friendly").sum() == 1


def test_build_training_frame_feeds_knockout_with_boost():
    """ENG-42: jogo de KO disputado (fixture guarda slot `W##`/`2D`) entra no treino com os nomes
    reais das seleções e o boost — não fica preso à base histórica a peso 1.0."""
    import pandas as pd

    from worldcup.pipeline import CURRENT_EDITION_BOOST, build_training_frame
    from worldcup.sync import resolve_live_bracket

    ed = load_edition(2026).as_of("2026-07-04")  # mata-mata em andamento (16-avos disputados)
    ko = resolve_live_bracket(ed)
    played_ko = next(f for f in ed.fixtures if f.played and not f.is_group and f.match_id in ko)
    home, away = ko[played_ko.match_id]
    assert played_ko.home not in ed.teams  # o fixture guarda slot (`W##`/`2D`), não a seleção real
    assert home in ed.teams  # ...que resolve_live_bracket resolve para a seleção real

    train = build_training_frame(ed, pd.DataFrame(columns=["date", "home_team", "away_team"]))
    key = train.apply(lambda r: (str(r["date"])[:10], frozenset((r["home_team"], r["away_team"]))), axis=1)
    match = train[key == (str(played_ko.date)[:10], frozenset((home, away)))]
    assert len(match) == 1  # entra pelos nomes reais, uma vez
    assert match.iloc[0]["weight_mult"] == CURRENT_EDITION_BOOST  # com boost, não a peso 1.0 da base
