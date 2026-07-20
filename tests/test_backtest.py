"""Testes do backtest — mando do anfitrião (ENG-2) e calibração probabilística (ENG-18)."""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import make_model, mini_historical
from worldcup import backtest as bt
from worldcup.edition import load_edition
from worldcup.knockout import predict_knockout


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


# --------------------------------------------------------------- calibração (ENG-18)


def test_multiclass_brier_perfect_is_zero():
    # previsão determinística e correta em todo jogo -> Brier 0
    probs = [(1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)]
    outcomes = [0, 2, 1]
    assert bt.multiclass_brier(probs, outcomes) == pytest.approx(0.0)


def test_multiclass_brier_uniform_closed_form():
    # palpite uniforme (1/3,1/3,1/3): Σ_k (1/3 - 1{k=real})² = 4/9 + 1/9 + 1/9 = 2/3, qualquer real
    u = (1 / 3, 1 / 3, 1 / 3)
    assert bt.multiclass_brier([u, u, u], [0, 1, 2]) == pytest.approx(2 / 3)


def test_multiclass_brier_worst_case():
    # determinística e errada -> (1-0)²+(0-1)² = 2 por jogo
    assert bt.multiclass_brier([(1.0, 0.0, 0.0)], [2]) == pytest.approx(2.0)


def test_multiclass_brier_empty():
    assert bt.multiclass_brier([], []) == 0.0


def test_reliability_curve_bins_and_freq():
    # probs em 3 faixas distintas (n_bins=10): 0.05->[0,10%), 0.55->[50,60%), 0.95->[90,100%]
    # hits escolhidos para dar freq observada conhecida em cada faixa
    pred = [0.05, 0.05, 0.55, 0.95, 0.95]
    hits = [False, True, True, True, False]  # faixa0: 1/2=50%; faixa5: 1/1=100%; faixa9: 1/2=50%
    bins = bt.reliability_curve(pred, hits, n_bins=10)
    # só 3 faixas não-vazias, em ordem crescente
    assert [(round(b.lo, 1), b.count) for b in bins] == [(0.0, 2), (0.5, 1), (0.9, 2)]
    by_lo = {round(b.lo, 1): b for b in bins}
    assert by_lo[0.0].mean_pred == pytest.approx(0.05)
    assert by_lo[0.0].obs_freq == pytest.approx(0.5)
    assert by_lo[0.5].obs_freq == pytest.approx(1.0)
    assert by_lo[0.9].mean_pred == pytest.approx(0.95)
    assert by_lo[0.9].obs_freq == pytest.approx(0.5)


def test_reliability_curve_p_one_lands_in_last_bin():
    # p=1.0 não pode estourar o índice; cai na última faixa [90,100%]
    bins = bt.reliability_curve([1.0], [True], n_bins=10)
    assert len(bins) == 1
    assert bins[0].lo == pytest.approx(0.9)
    assert bins[0].count == 1


# --------------------------------------------------------- tracking prospectivo do blend (ENG-19)
def test_prospective_blend_empty_without_odds():
    # sem odds -> n=0 e nada a reportar (retorna antes de carregar histórico/ajustar)
    ed = load_edition(2026)
    ed.odds.clear()  # ignora o odds.csv versionado: o teste controla as odds
    res = bt.prospective_blend_report(ed)
    assert res.n == 0
    assert res.delta == 0.0


def test_prospective_blend_weight_zero_equals_model(monkeypatch):
    # w=0 => blend idêntico ao modelo => Brier igual (invariante de wiring); histórico sintético (CI)
    monkeypatch.setattr(bt, "load_historical", mini_historical)
    ed = load_edition(2026)
    ed.odds.clear()  # controla as odds do teste (ignora o odds.csv versionado)
    played = [f for f in ed.fixtures if f.is_group and f.played][:2]
    for f in played:
        ed.odds[f.match_id] = (2.0, 3.3, 3.7)
    res = bt.prospective_blend_report(ed, weight=0.0)
    assert res.n == len(played)
    assert res.brier_blend == pytest.approx(res.brier_model)
    assert res.delta == pytest.approx(0.0)


def test_blend_weight_sweep_shares_one_pass(monkeypatch):
    # ENG-38: a grade reusa a MESMA coleta as-of; w=0 reproduz o modelo-puro e o Brier do
    # modelo é idêntico em todos os pesos (só o blend varia).
    monkeypatch.setattr(bt, "load_historical", mini_historical)
    ed = load_edition(2026)
    ed.odds.clear()
    played = [f for f in ed.fixtures if f.is_group and f.played][:2]
    for f in played:
        ed.odds[f.match_id] = (2.0, 3.3, 3.7)
    results = bt.blend_weight_sweep(ed, [0.0, 0.5, 1.0])
    assert [r.weight for r in results] == [0.0, 0.5, 1.0]
    assert all(r.n == len(played) for r in results)
    assert results[0].brier_blend == pytest.approx(results[0].brier_model)
    assert len({round(r.brier_model, 12) for r in results}) == 1  # coleta compartilhada


def test_blend_weight_sweep_empty_without_odds():
    ed = load_edition(2026)
    ed.odds.clear()
    results = bt.blend_weight_sweep(ed, [0.0, 1.0])
    assert all(r.n == 0 for r in results)


# ------------------------------------------------ monitor de regime de empates (ENG-22)
def test_draw_regime_stats_known_z():
    # 20 jogos, P(empate)=0.25 cada, 8 empates: E=5, Var=20*0.25*0.75=3.75, z=3/sqrt(3.75)
    dr = bt.draw_regime_stats([0.25] * 20, [True] * 8 + [False] * 12)
    assert dr.n == 20
    assert dr.observed == 8
    assert dr.expected == pytest.approx(5.0)
    assert dr.z == pytest.approx(1.5492, abs=1e-3)
    assert not dr.significant  # ~1,5σ é variância


def test_draw_regime_stats_significant_above_2sigma():
    # muitos empates além do esperado -> |z| >= 2 dispara o gatilho
    dr = bt.draw_regime_stats([0.2] * 30, [True] * 15 + [False] * 15)
    assert dr.significant
    assert dr.z > 2.0


def test_draw_regime_stats_empty_is_safe():
    dr = bt.draw_regime_stats([], [])
    assert dr.n == 0
    assert dr.z == 0.0
    assert not dr.significant


def test_draw_regime_report_on_2026(monkeypatch):
    # observados = empates REAIS (independe do modelo); n = jogos de grupo disputados
    monkeypatch.setattr(bt, "load_historical", mini_historical)
    ed = load_edition(2026)
    played = [f for f in ed.fixtures if f.is_group and f.played]
    real_draws = sum(1 for f in played if f.home_goals == f.away_goals)
    dr = bt.draw_regime_report(ed)
    assert dr.n == len(played)
    assert dr.observed == real_draws
    assert 0.0 <= dr.expected <= dr.n
    assert isinstance(dr.z, float)


# --------------------------------------------------------------- bônus de mata-mata (ENG-12)


def _ko_row(home_score: int, away_score: int, minutes: list[tuple[str, int]], penalty_winner: str = ""):
    """Uma linha da base **como a produção a monta** (normalize → score_90), não fabricada à mão.

    Costura (ENG-48): quem decide o que é "prorrogação" é `fetch_data`; o teste do backtest tem de
    consumir essa decisão, não reimplementá-la. Foi um teste que fabricava a entrada que deixou o
    ENG-48 passar despercebido.
    """
    from worldcup.fetch_data import normalize, score_90

    games = pd.DataFrame(
        [
            {
                "date": "2022-12-09",
                "home_team": "Brazil",
                "away_team": "Argentina",
                "home_score": home_score,
                "away_score": away_score,
                "tournament": "FIFA World Cup",
                "neutral": True,
            }
        ]
    )
    goals = pd.DataFrame(
        [
            {"date": "2022-12-09", "home_team": "Brazil", "away_team": "Argentina", "team": t, "minute": m}
            for t, m in minutes
        ]
    )
    shootouts = (
        pd.DataFrame(
            [{"date": "2022-12-09", "home_team": "Brazil", "away_team": "Argentina", "winner": penalty_winner}]
        )
        if penalty_winner
        else None
    )
    base = normalize(games, cutoff="2006-01-01", shootouts=shootouts, goalscorers=goals)
    return score_90(base).iloc[0]


def _poisson_matrix(lam_home: float, lam_away: float, n: int = 8):
    import math

    import numpy as np

    ph = np.array([math.exp(-lam_home) * lam_home**k / math.factorial(k) for k in range(n)])
    pa = np.array([math.exp(-lam_away) * lam_away**k / math.factorial(k) for k in range(n)])
    m = np.outer(ph, pa)
    return m / m.sum()


def test_knockout_bonus_awarded_on_penalty_shootout():
    """Jogo decidido nos pênaltis recebe os bônus de KO; decidido nos 90', zero."""
    import numpy as np

    award = bt._award_scorer()
    mat = np.zeros((7, 7))
    mat[1, 0] = mat[0, 1] = 0.3  # vitória do mandante / do visitante simétricas
    mat[0, 0] = mat[1, 1] = 0.2  # empates → jogo "vai aos pênaltis", vencedor previsto = mandante

    # 1×1 nos 90', foi a pênaltis: acertou a ida à disputa (+3) e o vencedor = mandante (+3)
    pens_home = _ko_row(1, 1, [("Brazil", 30), ("Argentina", 70)], penalty_winner="Brazil")
    assert bt._knockout_bonus_for(pens_home, mat, award) == 6.0
    # vencedor real = visitante → só o bônus de ida aos pênaltis (+3)
    pens_away = _ko_row(1, 1, [("Brazil", 30), ("Argentina", 70)], penalty_winner="Argentina")
    assert bt._knockout_bonus_for(pens_away, mat, award) == 3.0
    # decidido nos 90' → sem slot de prorrogação, sem bônus
    in_90 = _ko_row(2, 1, [("Brazil", 30), ("Brazil", 55), ("Argentina", 70)])
    assert bt._knockout_bonus_for(in_90, mat, award) == 0.0


def test_knockout_bonus_awarded_on_a_goal_in_extra_time():
    """ENG-54: jogo decidido por **gol na prorrogação** também rende o bônus do slot de ET.

    Antes, esses jogos eram invisíveis para o backtest (a fonte não traz fase nem flag de ET) e
    **nunca** eram creditados — o teto do backtest saía subestimado justamente no mata-mata.
    """
    award = bt._award_scorer()
    mat = _poisson_matrix(2.8, 0.6)  # favorito claro ⇒ o modelo prevê que o mandante vence na ET
    assert predict_knockout("Brazil", "Argentina", mat, award).extra_time == "home"  # premissa do caso

    # 1×1 nos 90' (gols aos 30' e 70'), decidido por gol do mandante aos 113' ⇒ consolidado 2×1
    et_home = _ko_row(2, 1, [("Brazil", 30), ("Argentina", 70), ("Brazil", 113)])
    assert et_home["et_outcome"] == "home"
    assert bt._knockout_bonus_for(et_home, mat, award) == 3.0  # acertou o slot de prorrogação

    # mesmo jogo, mas quem vence na ET é o visitante ⇒ o palpite ("home") erra o slot
    et_away = _ko_row(1, 2, [("Brazil", 30), ("Argentina", 70), ("Argentina", 113)])
    assert et_away["et_outcome"] == "away"
    assert bt._knockout_bonus_for(et_away, mat, award) == 0.0


def test_world_cup_registry_includes_2026():
    # ENG-56: com a 2026 encerrada e ingerida na fonte, ela entra no protocolo as-of do backtest
    # (pool de calibração, `backtest --edition 2026`) — anfitriões tratados como em produção.
    assert bt._WORLD_CUP_START[2026] == "2026-06-11"
    assert set(bt._WORLD_CUP_HOSTS[2026]) == {"United States", "Canada", "Mexico"}
