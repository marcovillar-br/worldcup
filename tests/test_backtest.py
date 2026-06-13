"""Testes do backtest — foco no mando do anfitrião (ENG-2)."""

from __future__ import annotations

import pandas as pd

from conftest import make_model
from worldcup import backtest as bt


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
