"""Testes de utilitários do pipeline."""

from conftest import mini_historical
from worldcup import pipeline
from worldcup.edition import load_edition
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


# ------------------------------------------------- e2e do pipeline real no CI (ENG-20)
def test_pipeline_run_e2e_invariants(monkeypatch):
    """Roda `pipeline.run` de ponta a ponta com histórico sintético e afirma invariantes
    estruturais — fecha o ponto cego de o CI nunca exercitar fit→sim→bracket→predict."""
    monkeypatch.setattr(pipeline, "load_historical", mini_historical)
    ed = load_edition(2026).as_of("2026-06-11")  # pré-torneio: 104 jogos não disputados
    result = pipeline.run(ed, n_sims=100, seed=1)

    assert len(result.rows) == len(ed.fixtures) == 104
    assert all(r["status"] == "PREVISTO" for r in result.rows)  # nada disputado no pré-torneio

    group_rows = [r for r in result.rows if r["fase"] == "group"]
    assert len(group_rows) == 72
    for r in group_rows:
        ph, pdr, pa = (int(r[k].rstrip("%")) for k in ("P_mandante", "P_empate", "P_visitante"))
        assert ph + pdr + pa == 100  # Hamilton (_pct_round) garante soma exata
        assert "x" in r["palpite"]  # todo jogo previsto tem placar

    ko_rows = [r for r in result.rows if r["fase"] != "group"]
    assert len(ko_rows) == 32
    for r in ko_rows:
        assert r["mandante"] != "?"  # chaveamento resolvido
        assert r["avanca"]  # quem avança preenchido

    assert abs(sum(result.champion_prob.values()) - 1.0) < 0.02  # probabilidades de título normalizadas
