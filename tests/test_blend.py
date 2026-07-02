"""Testes do blend com odds de mercado (ENG-19): des-vig, pool logarítmico e reescala da matriz."""

from __future__ import annotations

import math

import numpy as np
import pytest

from worldcup.blend import (
    blend_matrix_with_odds,
    devig,
    devig_pair,
    expected_total_goals,
    implied_total_rate,
    log_opinion_pool,
    prob_total_over,
    rescale_matrix,
    tilt_matrix_to_total,
)
from worldcup.scoring import outcome_probs_from_matrix


def _toy_matrix() -> np.ndarray:
    """Matriz de placares 4x4 assimétrica e normalizada (mandante levemente favorito)."""
    m = np.array(
        [
            [0.10, 0.06, 0.03, 0.01],
            [0.12, 0.08, 0.04, 0.01],
            [0.09, 0.07, 0.05, 0.02],
            [0.05, 0.04, 0.02, 0.04],
        ],
        dtype=float,
    )
    return m / m.sum()


# --------------------------------------------------------------------------- devig
def test_devig_fair_odds_no_margin():
    # odds "justas" (sem margem): 1/o já soma 1 -> probabilidades = 1/o exatas
    probs = devig((2.0, 4.0, 4.0))
    assert probs == pytest.approx((0.5, 0.25, 0.25))


def test_devig_removes_margin_and_sums_to_one():
    probs = devig((1.90, 3.40, 4.20))
    assert sum(probs) == pytest.approx(1.0)
    # overround real > 1 -> cada prob fica abaixo do 1/o bruto
    assert probs[0] < 1 / 1.90


def test_devig_rejects_nonsense_odds():
    with pytest.raises(ValueError, match="odds decimais"):
        devig((1.0, 3.0, 4.0))  # odd <= 1.0 é inválida


# ------------------------------------------------------------------ log_opinion_pool
def test_pool_weight_zero_is_model():
    model = (0.5, 0.3, 0.2)
    assert log_opinion_pool(model, (0.1, 0.2, 0.7), 0.0) == pytest.approx(model)


def test_pool_weight_one_is_market():
    market = (0.1, 0.2, 0.7)
    assert log_opinion_pool((0.5, 0.3, 0.2), market, 1.0) == pytest.approx(market)


def test_pool_half_is_normalized_geometric_mean():
    model = (0.5, 0.3, 0.2)
    market = (0.2, 0.3, 0.5)
    out = log_opinion_pool(model, market, 0.5)
    geo = [math.sqrt(m * q) for m, q in zip(model, market, strict=True)]
    geo = [g / sum(geo) for g in geo]
    assert out == pytest.approx(tuple(geo))
    assert sum(out) == pytest.approx(1.0)


def test_pool_rejects_weight_out_of_range():
    with pytest.raises(ValueError, match="weight"):
        log_opinion_pool((0.5, 0.3, 0.2), (0.3, 0.3, 0.4), 1.5)


# ------------------------------------------------------------------- rescale_matrix
def test_rescale_hits_target_outcome_probs():
    m = _toy_matrix()
    target = (0.6, 0.25, 0.15)
    out = rescale_matrix(m, target)
    assert outcome_probs_from_matrix(out) == pytest.approx(target, abs=1e-9)


def test_rescale_preserves_total_mass():
    m = _toy_matrix()
    out = rescale_matrix(m, (0.6, 0.25, 0.15))
    assert out.sum() == pytest.approx(m.sum())


def test_rescale_preserves_conditional_shape_within_class():
    # a razão entre dois placares da MESMA classe (ambos vitória do mandante) não muda
    m = _toy_matrix()
    out = rescale_matrix(m, (0.6, 0.25, 0.15))
    # (1,0) e (2,0) são vitórias do mandante (linha > coluna)
    assert out[1, 0] / out[2, 0] == pytest.approx(m[1, 0] / m[2, 0])


# ------------------------------------------------------------- blend_matrix_with_odds
def test_blend_weight_zero_returns_model_matrix():
    m = _toy_matrix()
    out = blend_matrix_with_odds(m, (1.90, 3.40, 4.20), 0.0)
    assert np.array_equal(out, m)


def test_blend_weight_one_matches_devigged_odds():
    m = _toy_matrix()
    odds = (1.90, 3.40, 4.20)
    out = blend_matrix_with_odds(m, odds, 1.0)
    assert outcome_probs_from_matrix(out) == pytest.approx(devig(odds), abs=1e-9)


def test_blend_partial_moves_toward_market():
    m = _toy_matrix()
    # mercado discorda do modelo: dá mais ao visitante
    odds = (5.0, 4.0, 1.6)
    model_probs = outcome_probs_from_matrix(m)
    market_probs = devig(odds)
    blended = outcome_probs_from_matrix(blend_matrix_with_odds(m, odds, 0.5))
    # P(visitante) do blend fica entre o modelo e o mercado, mais alta que a do modelo
    assert model_probs[2] < blended[2] < market_probs[2]


# ----------------------------------------------------------- totals (ENG-35)
def _poisson_matrix(lam_home: float, lam_away: float, n: int = 9) -> np.ndarray:
    """Produto de Poissons truncado (sem correção DC) — matriz sintética com λ conhecidos."""
    from scipy.stats import poisson

    ph = poisson.pmf(np.arange(n), lam_home)
    pa = poisson.pmf(np.arange(n), lam_away)
    m = np.outer(ph, pa)
    return m / m.sum()


def test_devig_pair_fair_odds():
    assert devig_pair(2.0, 2.0) == pytest.approx((0.5, 0.5))


def test_devig_pair_removes_margin():
    p_over, p_under = devig_pair(1.85, 1.95)
    assert p_over + p_under == pytest.approx(1.0)
    assert p_over < 1 / 1.85  # margem removida


def test_devig_pair_rejects_nonsense_odds():
    with pytest.raises(ValueError, match="odds decimais"):
        devig_pair(1.0, 2.0)


def test_implied_total_rate_inverts_poisson():
    # p_over exato de uma Poisson(2.7) na linha 2.5 -> recupera λ=2.7
    from scipy.stats import poisson

    lam = 2.7
    p_over = float(poisson.sf(2, lam))  # P(T > 2.5) = P(T >= 3)
    assert implied_total_rate(2.5, p_over) == pytest.approx(lam, rel=1e-4)


def test_implied_total_rate_rejects_degenerate_prob():
    with pytest.raises(ValueError, match="p_over"):
        implied_total_rate(2.5, 1.0)


def test_expected_total_goals_of_poisson_product():
    m = _poisson_matrix(1.5, 1.0)
    # truncado em 8 gols por lado, o E[total] fica ~λh+λa
    assert expected_total_goals(m) == pytest.approx(2.5, rel=1e-3)


def test_tilt_hits_target_total_and_preserves_home_share():
    # grade folgada (15): a invariância do share sob tilting é exata no produto de Poissons
    # NÃO-truncado; com grade curta o rabo truncado desloca a fração em ~1e-4
    m = _poisson_matrix(1.5, 1.0, n=15)
    out = tilt_matrix_to_total(m, 3.5)
    assert expected_total_goals(out) == pytest.approx(3.5, rel=1e-6)
    assert out.sum() == pytest.approx(m.sum())  # massa preservada
    # tilting c^(i+j) escala as duas taxas por c -> a fração do mandante no total não muda
    n = m.shape[0]
    goals = np.arange(n, dtype=float)
    home_share_before = float((m.sum(axis=1) * goals).sum()) / expected_total_goals(m)
    home_share_after = float((out.sum(axis=1) * goals).sum()) / expected_total_goals(out)
    assert home_share_after == pytest.approx(home_share_before, rel=1e-6)


def test_prob_total_over_counts_mass_above_line():
    m = _poisson_matrix(1.5, 1.0)
    n = m.shape[0]
    totals = np.arange(n)[:, None] + np.arange(n)[None, :]
    assert prob_total_over(m, 2.5) == pytest.approx(float(m[totals >= 3].sum()))


def test_blend_with_totals_hits_pooled_targets():
    m = _poisson_matrix(1.5, 1.0)  # λ_model = 2.5
    odds = (2.1, 3.3, 3.8)
    w = 0.6
    # mercado com odds "justas" na linha 2.5 implicando λ conhecido (3.2)
    from scipy.stats import poisson

    lam_market = 3.2
    p_over = float(poisson.sf(2, lam_market))
    totals = (2.5, 1.0 / p_over, 1.0 / (1.0 - p_over))
    out = blend_matrix_with_odds(m, odds, w, totals=totals)
    # 1×2 bate o pool exatamente (rescale é o último passo)
    target_1x2 = log_opinion_pool(outcome_probs_from_matrix(m), devig(odds), w)
    assert outcome_probs_from_matrix(out) == pytest.approx(target_1x2, abs=1e-9)
    # taxa total converge ao pool geométrico dos λ (tolerância da interação tilt↔rescale)
    lam_target = 2.5 ** (1 - w) * lam_market**w
    assert expected_total_goals(out) == pytest.approx(lam_target, rel=1e-2)


def test_blend_without_totals_is_pre_eng35_path():
    # sem totals, o resultado é EXATAMENTE o caminho antigo (pool de 1×2 + rescale)
    m = _toy_matrix()
    odds = (1.90, 3.40, 4.20)
    w = 0.6
    old = rescale_matrix(m, log_opinion_pool(outcome_probs_from_matrix(m), devig(odds), w))
    assert np.array_equal(blend_matrix_with_odds(m, odds, w), old)
    assert np.array_equal(blend_matrix_with_odds(m, odds, w, totals=None), old)
