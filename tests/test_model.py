"""Testes do modelo Dixon-Coles."""

from __future__ import annotations

import numpy as np
import pandas as pd

from worldcup.model import DixonColesModel, tournament_weight
from worldcup.scoring import outcome_probs_from_matrix


def _synthetic_matches() -> pd.DataFrame:
    """Liga sintética: A (forte) > B (médio) > C (fraco), repetida várias vezes."""
    rows = []
    base = pd.Timestamp("2024-01-01")
    scripted = [
        ("A", "B", 2, 0), ("A", "C", 3, 0), ("B", "C", 2, 1),
        ("B", "A", 0, 2), ("C", "A", 0, 3), ("C", "B", 1, 2),
    ]
    for k in range(12):
        for i, (h, a, hs, as_) in enumerate(scripted):
            rows.append({
                "date": base + pd.Timedelta(days=k * 30 + i),
                "home_team": h, "away_team": a,
                "home_score": hs, "away_score": as_,
                "tournament": "FIFA World Cup qualification", "neutral": False,
            })
    return pd.DataFrame(rows)


def test_score_matrix_is_a_distribution():
    m = DixonColesModel().fit(_synthetic_matches())
    mat = m.score_matrix("A", "C", neutral=True)
    assert mat.shape[0] == mat.shape[1]
    assert abs(mat.sum() - 1.0) < 1e-9
    assert (mat >= 0).all()


def test_stronger_team_more_likely_to_win():
    m = DixonColesModel().fit(_synthetic_matches())
    p_home, _, p_away = outcome_probs_from_matrix(m.score_matrix("A", "C", neutral=True))
    assert p_home > p_away
    # A é claramente favorito sobre C
    assert p_home > 0.6


def test_home_advantage_increases_win_prob():
    m = DixonColesModel().fit(_synthetic_matches())
    p_neutral, *_ = outcome_probs_from_matrix(m.score_matrix("B", "C", neutral=True))
    p_home, *_ = outcome_probs_from_matrix(m.score_matrix("B", "C", neutral=False))
    assert p_home >= p_neutral


def test_host_away_gives_mando_to_visitor():
    # anfitrião listado como visitante (ex.: Suíça x Canadá em Vancouver): o mando segue o
    # visitante. Dar mando a C como visitante == jogo normal de C em casa, espelhado.
    m = DixonColesModel().fit(_synthetic_matches())
    mat_host_away = m.score_matrix("B", "C", neutral=False, host_away=True)
    mat_mirror = m.score_matrix("C", "B", neutral=False).T
    assert np.allclose(mat_host_away, mat_mirror)
    # e o mando do visitante aumenta a chance dele vs. campo neutro
    _, _, pa_neutral = outcome_probs_from_matrix(m.score_matrix("B", "C", neutral=True))
    _, _, pa_host_away = outcome_probs_from_matrix(mat_host_away)
    assert pa_host_away >= pa_neutral


def test_unknown_team_falls_back_to_average():
    m = DixonColesModel().fit(_synthetic_matches())
    lam, mu = m.expected_goals("A", "__desconhecido__", neutral=True)
    assert lam > 0 and mu > 0  # não quebra com time fora do treino


def test_tournament_weight_ordering():
    assert tournament_weight("FIFA World Cup") > tournament_weight("Friendly")
    assert tournament_weight("FIFA World Cup qualification") > tournament_weight("Friendly")
