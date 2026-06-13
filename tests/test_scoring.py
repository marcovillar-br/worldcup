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
    base = 3.0  # curva fiel do app: p=0.50 -> 3 pts base
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


def test_base_points_reproduce_app_simulator():
    # curva base fiel ao Simulador do app (ENG-14): pontos observados nas telas de regras.
    s = _scorer()
    observed = {0.80: 2, 0.50: 3, 0.15: 7, 0.05: 11}
    for p, expected in observed.items():
        assert abs(s._base_points(p) - expected) <= 0.5, f"p={p}: {s._base_points(p)} != {expected}"
    # extremos clipados
    assert s._base_points(0.999) == 1.0  # favorito óbvio -> base_min
    assert s._base_points(0.001) == 13.0  # zebra extrema -> base_max


def test_base_points_independent_of_risk():
    # a régua de pontos do app é fixa; risk não deve alterá-la (só a escolha do palpite)
    assert _scorer(0.5)._base_points(0.5) == _scorer(0.9)._base_points(0.5)


def _picked_outcome_prob(pred) -> float:
    """Probabilidade do resultado (1x2) que o palpite escolheu."""
    if pred.home_goals > pred.away_goals:
        return pred.p_home
    if pred.home_goals == pred.away_goals:
        return pred.p_draw
    return pred.p_away


def test_higher_risk_favors_underdog_pick():
    # matriz equilibrada, mandante levemente favorito; risco alto tende a um resultado menos provável
    mat = np.array([[0.10, 0.18, 0.12], [0.14, 0.12, 0.06], [0.08, 0.05, 0.15]])
    mat = mat / mat.sum()
    cautious = _scorer(0.2).best_prediction(mat)
    bold = _scorer(0.9).best_prediction(mat)
    # o palpite ousado não escolhe um resultado mais provável que o cauteloso
    assert _picked_outcome_prob(bold) <= _picked_outcome_prob(cautious)


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
    base = 4.0  # curva fiel: p=0.40 -> 4 pts base
    assert abs(pts - (base + 2)) < 1e-6  # base + goal_diff


def test_knockout_bonus_extra_time_and_penalties():
    s = _scorer()
    # acertou que vai a pênaltis (+3) e o vencedor nos pênaltis (+3)
    assert s.knockout_bonus("penalties", "home", "penalties", "home") == 6.0
    # acertou só a ida a pênaltis, errou o vencedor (+3)
    assert s.knockout_bonus("penalties", "home", "penalties", "away") == 3.0
    # acertou que um lado vence na prorrogação (+3); sem pênaltis, sem bônus de pênaltis
    assert s.knockout_bonus("home", "home", "home", None) == 3.0
    # errou a prorrogação e não foi a pênaltis: zero
    assert s.knockout_bonus("home", "home", "penalties", "away") == 0.0


def test_knockout_bonus_only_for_sistema_i():
    s = Scorer(ScoringConfig(system="so_vencedor"))
    assert s.knockout_bonus("penalties", "home", "penalties", "home") == 0.0
