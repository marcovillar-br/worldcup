"""Testes do backtest — mando do anfitrião (ENG-2) e calibração probabilística (ENG-18)."""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import make_model, mini_historical
from worldcup import backtest as bt
from worldcup.edition import load_edition


def test_world_cup_hosts_cover_all_backtest_years():
    # toda Copa com data de início cadastrada precisa ter anfitrião, senão o mando some em silêncio
    assert set(bt._WORLD_CUP_START) <= set(bt._WORLD_CUP_HOSTS)


def test_backtest_applies_host_advantage(monkeypatch):
    """O jogo do anfitrião (listado como visitante) deve ser pontuado com host_away=True,
    igual à produção — não como jogo neutro."""
    model = make_model({"Brazil": 0.6, "Croatia": 0.0})

    # Brasil (anfitrião 2014) listado como VISITANTE num jogo não-neutro: caso host-away.
    test_df = pd.DataFrame(
        [
            {
                "tournament": "FIFA World Cup",
                "date": pd.Timestamp("2014-06-12"),
                "home_team": "Croatia",
                "away_team": "Brazil",
                "home_score": 1,
                "away_score": 3,
                "neutral": False,
            }
        ]
    )
    monkeypatch.setattr(bt, "load_historical", lambda: test_df)
    monkeypatch.setattr(bt.DixonColesModel, "fit", lambda self, *a, **k: model)

    seen: dict[str, bool] = {}
    original = model.score_matrix

    def spy(home, away, neutral=True, max_goals=None, host_away=False):
        seen["host_away"] = host_away
        return original(home, away, neutral, max_goals, host_away)

    monkeypatch.setattr(model, "score_matrix", spy)

    bt.run_backtest(2014, risks=(0.5,))

    # o anfitrião como visitante recebe o mando (host_away), como no caminho real do app
    assert seen["host_away"] is True


# --------------------------------------------------------------- calibração (ENG-18)


def test_multiclass_brier_perfect_is_zero():
    # previsão determinística e correta em todo jogo -> Brier 0
    probs = [(1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)]
    outcomes = [0, 2, 1]
    assert bt.multiclass_brier(probs, outcomes) == pytest.approx(0.0)


def test_multiclass_brier_uniform_closed_form():
    # palpite uniforme (1/3,1/3,1/3): Σ_k (1/3 - 1{k=real})² = 4/9 + 1/9 + 1/9 = 2/3, qualquer real
    u = (1 / 3, 1 / 3, 1 / 3)
    assert bt.multiclass_brier([u, u, u], [0, 1, 2]) == pytest.approx(2 / 3)


def test_multiclass_brier_worst_case():
    # determinística e errada -> (1-0)²+(0-1)² = 2 por jogo
    assert bt.multiclass_brier([(1.0, 0.0, 0.0)], [2]) == pytest.approx(2.0)


def test_multiclass_brier_empty():
    assert bt.multiclass_brier([], []) == 0.0


def test_reliability_curve_bins_and_freq():
    # probs em 3 faixas distintas (n_bins=10): 0.05->[0,10%), 0.55->[50,60%), 0.95->[90,100%]
    # hits escolhidos para dar freq observada conhecida em cada faixa
    pred = [0.05, 0.05, 0.55, 0.95, 0.95]
    hits = [False, True, True, True, False]  # faixa0: 1/2=50%; faixa5: 1/1=100%; faixa9: 1/2=50%
    bins = bt.reliability_curve(pred, hits, n_bins=10)
    # só 3 faixas não-vazias, em ordem crescente
    assert [(round(b.lo, 1), b.count) for b in bins] == [(0.0, 2), (0.5, 1), (0.9, 2)]
    by_lo = {round(b.lo, 1): b for b in bins}
    assert by_lo[0.0].mean_pred == pytest.approx(0.05)
    assert by_lo[0.0].obs_freq == pytest.approx(0.5)
    assert by_lo[0.5].obs_freq == pytest.approx(1.0)
    assert by_lo[0.9].mean_pred == pytest.approx(0.95)
    assert by_lo[0.9].obs_freq == pytest.approx(0.5)


def test_reliability_curve_p_one_lands_in_last_bin():
    # p=1.0 não pode estourar o índice; cai na última faixa [90,100%]
    bins = bt.reliability_curve([1.0], [True], n_bins=10)
    assert len(bins) == 1
    assert bins[0].lo == pytest.approx(0.9)
    assert bins[0].count == 1


# --------------------------------------------------------- tracking prospectivo do blend (ENG-19)
def test_prospective_blend_empty_without_odds():
    # sem odds -> n=0 e nada a reportar (retorna antes de carregar histórico/ajustar)
    ed = load_edition(2026)
    ed.odds.clear()  # ignora o odds.csv versionado: o teste controla as odds
    res = bt.prospective_blend_report(ed)
    assert res.n == 0
    assert res.delta == 0.0


def test_prospective_blend_weight_zero_equals_model(monkeypatch):
    # w=0 => blend idêntico ao modelo => Brier igual (invariante de wiring); histórico sintético (CI)
    monkeypatch.setattr(bt, "load_historical", mini_historical)
    ed = load_edition(2026)
    ed.odds.clear()  # controla as odds do teste (ignora o odds.csv versionado)
    played = [f for f in ed.fixtures if f.is_group and f.played][:2]
    for f in played:
        ed.odds[f.match_id] = (2.0, 3.3, 3.7)
    res = bt.prospective_blend_report(ed, weight=0.0)
    assert res.n == len(played)
    assert res.brier_blend == pytest.approx(res.brier_model)
    assert res.delta == pytest.approx(0.0)
