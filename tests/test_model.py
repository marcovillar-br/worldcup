"""Testes do modelo Dixon-Coles."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
import pytest

from worldcup.model import DixonColesModel, FitConfig, tournament_weight
from worldcup.scoring import outcome_probs_from_matrix


def _synthetic_matches() -> pd.DataFrame:
    """Liga sintética: A (forte) > B (médio) > C (fraco), repetida várias vezes.

    Os mandantes marcam consistentemente mais que os visitantes (jogos com mando,
    `neutral=False`), de modo que o fit convergido estima `home_adv > 0` — sem esse sinal,
    o ótimo verdadeiro tem mando ~0 e os testes de mando ficariam no fio da navalha (ENG-16)."""
    rows = []
    base = pd.Timestamp("2024-01-01")
    scripted = [
        ("A", "B", 3, 0),  # mandante marca mais nas duas orientações de cada confronto
        ("A", "C", 4, 0),
        ("B", "C", 3, 0),
        ("B", "A", 1, 2),
        ("C", "A", 1, 3),
        ("C", "B", 1, 1),
    ]
    for k in range(12):
        for i, (h, a, hs, as_) in enumerate(scripted):
            rows.append(
                {
                    "date": base + pd.Timedelta(days=k * 30 + i),
                    "home_team": h,
                    "away_team": a,
                    "home_score": hs,
                    "away_score": as_,
                    "tournament": "FIFA World Cup qualification",
                    "neutral": False,
                }
            )
    return pd.DataFrame(rows)


def test_fit_logs_dropped_low_match_teams(caplog):
    # uma seleção com poucos jogos é descartada por min_matches — antes era silencioso (ENG-4)
    df = _synthetic_matches()
    rare = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2024-02-01"),
                "home_team": "A",
                "away_team": "Rarea",
                "home_score": 5,
                "away_score": 0,
                "tournament": "FIFA World Cup qualification",
                "neutral": False,
            }
        ]
    )
    df = pd.concat([df, rare], ignore_index=True)
    with caplog.at_level(logging.INFO, logger="worldcup.model"):
        DixonColesModel().fit(df)
    assert any("descartou" in r.message for r in caplog.records)
    assert "Rarea" in caplog.text


def test_fit_warns_when_optimizer_does_not_converge(caplog):
    # maxiter=1 força o L-BFGS-B a parar antes de convergir -> deve avisar (ENG-3)
    with caplog.at_level(logging.WARNING, logger="worldcup.model"):
        model = DixonColesModel(FitConfig(maxiter=1)).fit(_synthetic_matches())
    assert any("não convergiu" in r.message for r in caplog.records)
    # mesmo sem convergir, devolve um modelo utilizável (res.x), sem quebrar a saída
    mat = model.score_matrix("A", "C", neutral=True)
    assert abs(mat.sum() - 1.0) < 1e-9


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


def test_unknown_team_raises_instead_of_average_fallback():
    # ENG-57: nome fora do ajuste (typo, slot `L101` não resolvido) levantava a matriz do
    # "time médio" em silêncio — previsão plausível e errada. Agora é erro explícito.
    m = DixonColesModel().fit(_synthetic_matches())
    with pytest.raises(KeyError, match="__desconhecido__"):
        m.score_matrix("A", "__desconhecido__", neutral=True)
    with pytest.raises(KeyError, match="L101"):
        m.expected_goals("L101", "A", neutral=True)


def test_tournament_weight_ordering():
    assert tournament_weight("FIFA World Cup") > tournament_weight("Friendly")
    assert tournament_weight("FIFA World Cup qualification") > tournament_weight("Friendly")


def test_fitconfig_calibrated_defaults():
    # ENG-17: defaults tunados via backtest leave-one-World-Cup-out (+9,2% de pontos do bolão
    # sobre os antigos 2.5/0.05, config vencedora nas 4 dobras). Trava a calibração escolhida —
    # mudá-la deve ser deliberado (re-rodar o LOO-CV), não acidental.
    cfg = FitConfig()
    assert cfg.halflife_years == 2.0
    assert cfg.ridge == 0.10


def _low_score_matches() -> pd.DataFrame:
    """Liga sintética só com placares baixos — exercita todos os ramos da correção
    Dixon-Coles (tau): 0x0, 1x0, 0x1 e 1x1, cujas derivadas o gradiente analítico precisa cobrir."""
    rows = []
    base = pd.Timestamp("2024-01-01")
    scripted = [
        ("A", "B", 1, 0),  # m10
        ("A", "C", 1, 1),  # m11
        ("B", "C", 0, 0),  # m00
        ("B", "A", 0, 1),  # m01
        ("C", "A", 1, 2),
        ("C", "B", 2, 1),
        ("A", "B", 2, 1),
        ("B", "C", 1, 0),  # m10
        ("C", "A", 0, 0),  # m00
        ("A", "C", 0, 1),  # m01
    ]
    for k in range(4):
        for i, (h, a, hs, as_) in enumerate(scripted):
            rows.append(
                {
                    "date": base + pd.Timedelta(days=k * 30 + i),
                    "home_team": h,
                    "away_team": a,
                    "home_score": hs,
                    "away_score": as_,
                    "tournament": "FIFA World Cup qualification",
                    "neutral": False,
                }
            )
    return pd.DataFrame(rows)


def _central_grad(fun, x, h=1e-5):
    """Gradiente por diferenças centrais (truncamento O(h²)) — referência p/ checar o analítico."""
    g = np.zeros_like(x)
    for i in range(len(x)):
        xp, xm = x.copy(), x.copy()
        xp[i] += h
        xm[i] -= h
        g[i] = (fun(xp) - fun(xm)) / (2 * h)
    return g


def test_fit_uses_analytic_gradient_matching_numeric(monkeypatch):
    # Regressão ENG-16: o fit deve passar um jac analítico ao otimizador, e esse gradiente
    # deve casar com o numérico — senão o L-BFGS-B converge para o ótimo errado (ou esgota o
    # maxfun do scipy estimando o gradiente por diferenças finitas e nem converge).
    import worldcup.model as model_mod

    captured: dict[str, Any] = {}
    real_minimize = model_mod.minimize

    def spy(fun, x0, jac=None, **kwargs):
        assert jac is not None, "fit deve passar um gradiente analítico (jac) ao minimize"
        errs = [
            float(np.max(np.abs(jac(x0 + delta) - _central_grad(fun, x0 + delta))))
            for delta in (0.0, 0.2, -0.25)  # x0 e pontos perturbados (rho != 0 ativa o tau)
        ]
        captured["max_err"] = max(errs)
        res = real_minimize(fun, x0, jac=jac, **kwargs)
        captured["success"] = bool(res.success)
        return res

    monkeypatch.setattr(model_mod, "minimize", spy)
    DixonColesModel().fit(_low_score_matches())

    assert captured["max_err"] < 1e-5  # analítico == numérico
    assert captured["success"]  # com o jac correto, o fit converge dentro do maxiter
