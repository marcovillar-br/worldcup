"""Testes do blend com odds de mercado (ENG-19): des-vig, pool logarítmico e reescala da matriz."""

from __future__ import annotations

import math

import numpy as np
import pytest

from worldcup.blend import (
    blend_matrix_with_odds,
    devig,
    log_opinion_pool,
    rescale_matrix,
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
