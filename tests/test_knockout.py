"""Testes do palpite de mata-mata (ENG-29): desfecho da prorrogação por E[pts], não por limiar."""

from __future__ import annotations

import math

import numpy as np

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


def test_layer1_never_predicts_a_draw_in_knockout():
    # ENG-32: num confronto equilibrado e baixo o E[pts]-ótimo livre é um empate (ex.: 0×0), que
    # zeraria se o jogo fosse decidido nos 90'. A camada 1 do KO usa forbid_draw ⇒ placar com
    # vencedor. As camadas de prorrogação/pênaltis/avanço (2–3) seguem inalteradas.
    m = _poisson_matrix(1.0, 1.0)
    assert _scorer().best_prediction(m).home_goals == _scorer().best_prediction(m).away_goals  # livre = empate
    kp = predict_knockout("H", "A", m, _scorer())
    assert kp.home_goals != kp.away_goals  # camada 1 nunca empata no KO
    assert kp.extra_time == "penalties"  # equilíbrio ⇒ pênaltis (camada 2 inalterada)
