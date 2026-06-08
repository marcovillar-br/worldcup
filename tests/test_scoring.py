"""Testes da pontuação (Sistema I) e da escolha de palpite."""

from __future__ import annotations

import numpy as np

from worldcup.edition import ScoringConfig
from worldcup.scoring import Scorer


def _scorer(risk: float = 0.5) -> Scorer:
    return Scorer(ScoringConfig(system="sistema_i", risk=risk))


def test_wrong_result_scores_zero():
    s = _scorer()
    probs = (0.5, 0.3, 0.2)
    assert s.points((2, 0), (0, 1), probs) == 0.0


def test_exact_score_gets_all_bonuses():
    s = _scorer()
    probs = (0.5, 0.3, 0.2)
    # placar exato 2x1: base + exact(5) + winner_goals(3) + goal_diff(2) + loser_goals(1)
    pts = s.points((2, 1), (2, 1), probs)
    base = 1.0 / 0.5  # risk 0.5 -> gamma 1 -> 1/p
    assert abs(pts - (base + 5 + 3 + 2 + 1)) < 1e-6


def test_underdog_correct_scores_more_than_favorite():
    s = _scorer()
    # mesmo placar exato, mas resultado raro (away com P=0.1) deve valer mais que favorito (P=0.7)
    fav = s.points((2, 1), (2, 1), (0.7, 0.2, 0.1))
    dog = s.points((1, 2), (1, 2), (0.7, 0.2, 0.1))
    assert dog > fav


def test_best_prediction_picks_favored_outcome():
    s = _scorer()
    # matriz claramente favorável ao mandante
    mat = np.zeros((7, 7))
    mat[2, 0] = 0.4
    mat[1, 0] = 0.3
    mat[1, 1] = 0.2
    mat[0, 1] = 0.1
    pred = s.best_prediction(mat)
    assert pred.home_goals > pred.away_goals  # prevê vitória do mandante
    assert pred.expected_points > 0


def test_so_vencedor_system():
    s = Scorer(ScoringConfig(system="so_vencedor"))
    probs = (0.5, 0.3, 0.2)
    assert s.points((3, 0), (1, 0), probs) == 1.0  # acertou o vencedor
    assert s.points((0, 1), (1, 0), probs) == 0.0  # errou


def test_goal_difference_bonus_on_draw():
    s = _scorer()
    probs = (0.3, 0.4, 0.3)
    # previu empate 1x1, saiu 2x2: acerta resultado (empate) + saldo, mas não o exato
    pts = s.points((1, 1), (2, 2), probs)
    base = 1.0 / 0.4
    assert abs(pts - (base + 2)) < 1e-6  # base + goal_diff
