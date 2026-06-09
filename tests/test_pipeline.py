"""Testes de utilitários do pipeline."""

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
