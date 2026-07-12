"""Testes do palpite de mata-mata (ENG-29): desfecho da prorrogação por E[pts], não por limiar."""

from __future__ import annotations

import math

import numpy as np
import pytest

from worldcup.edition import ScoringConfig
from worldcup.knockout import _expected_goals, _extra_time_probs, predict_knockout
from worldcup.scoring import Scorer, outcome_probs_from_matrix


def _scorer() -> Scorer:
    return Scorer(ScoringConfig(system="sistema_i", risk=0.5))


def _poisson_matrix(lam_home: float, lam_away: float, n: int = 8) -> np.ndarray:
    ph = np.array([math.exp(-lam_home) * lam_home**k / math.factorial(k) for k in range(n)])
    pa = np.array([math.exp(-lam_away) * lam_away**k / math.factorial(k) for k in range(n)])
    m = np.outer(ph, pa)
    return m / m.sum()


def test_expected_goals_recovers_lambdas():
    m = _poisson_matrix(1.7, 0.9)
    lh, la = _expected_goals(m)
    assert abs(lh - 1.7) < 1e-2  # matriz truncada/renormalizada → recupera a média dela (~1.697)
    assert abs(la - 0.9) < 1e-2


def test_extra_time_probs_symmetric_and_normalized():
    p_home, p_draw, p_away = _extra_time_probs(1.2, 1.2)
    assert abs((p_home + p_draw + p_away) - 1.0) < 1e-6
    assert abs(p_home - p_away) < 1e-9  # simétrico
    assert p_draw > p_home  # ET curta e equilibrada → empate (pênaltis) é o modal


def test_extra_time_probs_low_scoring_favours_penalties():
    # a ET tem 1/3 do tempo: mesmo um favorito moderado raramente decide nela
    p_home, p_draw, p_away = _extra_time_probs(1.3, 1.0)
    assert p_draw > p_home > p_away


def test_layer2_moderate_favourite_picks_penalties_not_the_favourite():
    # caso que o LIMIAR antigo errava: cond_home≈0.60 (≥0.58) → cravava "home";
    # o E[pts] correto é "penalties" (P(ET empatada) domina). ENG-29.
    m = _poisson_matrix(1.3, 1.0)
    p_home, _p_draw, p_away = outcome_probs_from_matrix(m)
    cond_home = p_home / (p_home + p_away)
    assert cond_home >= 0.58  # o limiar antigo teria escolhido "home" aqui
    assert predict_knockout("H", "A", m, _scorer()).extra_time == "penalties"


def test_layer2_strong_favourite_picks_that_side():
    m = _poisson_matrix(2.8, 0.6)
    assert predict_knockout("H", "A", m, _scorer()).extra_time == "home"


def test_layer2_balanced_picks_penalties():
    m = _poisson_matrix(1.1, 1.1)
    assert predict_knockout("H", "A", m, _scorer()).extra_time == "penalties"


def test_penalty_winner_and_advancer_follow_the_stronger_side():
    m = _poisson_matrix(2.8, 0.6)  # mandante claramente mais forte
    kp = predict_knockout("H", "A", m, _scorer())
    assert kp.penalty_winner == "home"  # camada 3: argmax (lado mais provável) — inalterado
    assert kp.advancer == "H"  # avanço segue a lógica condicional existente (inalterado)


def test_layer1_follows_expected_points_and_may_draw_in_a_balanced_knockout():
    # ENG-53 (revoga o ENG-32): a camada 1 é E[pts]-fiel, empate incluído. Num KO equilibrado o
    # empate é o E[pts]-máximo — e é o que o bolão pontua, porque o slot de 90' é medido contra o
    # tempo normal (um 1×1 decidido na prorrogação pontua o empate cheio).
    m = _poisson_matrix(1.0, 1.0)
    free = _scorer().best_prediction(m)
    assert free.home_goals == free.away_goals  # premissa do caso: o E[pts]-ótimo livre é um empate
    kp = predict_knockout("H", "A", m, _scorer())
    assert (kp.home_goals, kp.away_goals) == (free.home_goals, free.away_goals)  # camada 1 = E[pts]-fiel
    assert kp.extra_time == "penalties"  # equilíbrio ⇒ pênaltis (camada 2 inalterada)


def test_layer1_still_picks_a_winner_when_there_is_a_clear_favourite():
    # O contrapeso do ENG-53: liberar o empate NÃO faz o tool espalhar 1×1. Com favorito claro o
    # maximizador de E[pts] escolhe o placar decisivo sozinho — o antigo ban era inócuo aqui.
    m = _poisson_matrix(2.8, 0.6)
    kp = predict_knockout("H", "A", m, _scorer())
    assert kp.home_goals > kp.away_goals


def test_pool_behind_zebra_picks_the_underdog_side_with_all_layers():
    # ENG-36: modo bolão-atrás 'zebra' — 90' no lado ZEBRA (melhor E[pts] dentro dele), camadas
    # ET/pên. e avanço também na zebra (descorrelação máxima do pelotão, que aglomera no favorito).
    m = _poisson_matrix(2.8, 0.6)  # mandante claramente favorito -> zebra = visitante
    kp = predict_knockout("H", "A", m, _scorer(), pool_behind="zebra")
    assert kp.away_goals > kp.home_goals  # lado zebra
    assert kp.extra_time == "away"
    assert kp.penalty_winner == "away"
    assert kp.advancer == "A"


def test_pool_behind_zebra_score_is_expected_points_optimal_within_side():
    m = _poisson_matrix(2.8, 0.6)
    kp = predict_knockout("H", "A", m, _scorer(), pool_behind="zebra")
    sc = _scorer()
    n = m.shape[0]
    away_cells = [(i, j) for i in range(n) for j in range(n) if j > i]
    best = max(away_cells, key=lambda c: sc.expected_points(c, m))
    assert (kp.home_goals, kp.away_goals) == best


def test_pool_behind_empate_forces_best_draw_by_expected_points():
    # ENG-39/40: modo 'empate' — 90' no melhor placar de EMPATE por E[pts] (diagonal), mesmo com
    # favorito claro; a política dominante do endgame (finais empatam ~60% nos 90' historicamente).
    m = _poisson_matrix(2.8, 0.6)
    kp = predict_knockout("H", "A", m, _scorer(), pool_behind="empate")
    assert kp.home_goals == kp.away_goals  # diagonal
    sc = _scorer()
    best_d = max(range(m.shape[0]), key=lambda k: sc.expected_points((k, k), m))
    assert kp.home_goals == best_d


def test_pool_behind_empate_keeps_fiel_layers_and_advancer():
    # As camadas 2–3 e o avanço NÃO mudam no modo 'empate': só o placar dos 90' diverge do fiel
    # (a descorrelação mora no resultado, não em trocar o classificado).
    m = _poisson_matrix(2.8, 0.6)
    fiel = predict_knockout("H", "A", m, _scorer())
    emp = predict_knockout("H", "A", m, _scorer(), pool_behind="empate")
    assert emp.extra_time == fiel.extra_time
    assert emp.penalty_winner == fiel.penalty_winner
    assert emp.advancer == fiel.advancer
    assert emp.p_advance_home == fiel.p_advance_home
    assert (emp.home_goals, emp.away_goals) != (fiel.home_goals, fiel.away_goals)  # fiel nunca empata


def test_pool_behind_none_is_unchanged():
    m = _poisson_matrix(2.8, 0.6)
    assert predict_knockout("H", "A", m, _scorer()) == predict_knockout("H", "A", m, _scorer(), pool_behind=None)


def test_pool_behind_invalid_value_raises():
    m = _poisson_matrix(2.8, 0.6)
    with pytest.raises(ValueError, match="pool_behind"):
        predict_knockout("H", "A", m, _scorer(), pool_behind="zebra-final")
