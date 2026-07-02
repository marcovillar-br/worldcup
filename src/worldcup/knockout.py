"""Palpites de mata-mata em 3 camadas (90 min, prorrogação, pênaltis) e quem avança.

No app, cada jogo eliminatório tem 3 palpites independentes, avaliados conforme até onde o jogo
real chegar:
  1. **Placar dos 90 min** — placar do tempo normal (pode ser empate);
  2. **Prorrogação** — vitória do mandante / vai pros pênaltis / vitória do visitante;
  3. **Pênaltis** — quem vence a disputa.

Tudo é derivado da matriz de placares do modelo. Para montar o chaveamento, também expomos quem
o modelo aponta como classificado (`advancer`) e a probabilidade de avanço.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .scoring import Scorer, outcome_probs_from_matrix

# Prorrogação são 30 min ≈ 1/3 do tempo regular — escala as taxas de gol da ET (ENG-29).
_ET_FRACTION = 30.0 / 90.0


def _expected_goals(matrix: np.ndarray) -> tuple[float, float]:
    """Gols esperados (mandante, visitante) nos 90' a partir da matriz de placares."""
    idx = np.arange(matrix.shape[0])
    lam_home = float((matrix.sum(axis=1) * idx).sum())
    lam_away = float((matrix.sum(axis=0) * idx).sum())
    return lam_home, lam_away


def _extra_time_probs(lam_home: float, lam_away: float) -> tuple[float, float, float]:
    """P(mandante vence / empate→pênaltis / visitante vence) na **prorrogação**.

    Aproxima a ET (30 min) por Poisson **independente** com taxa = taxa de 90' × 30/90 por lado. A
    correção Dixon-Coles (baixos placares) é ignorada: é de 2ª ordem para o split vitória/empate/
    derrota, e o que importa é capturar que a ET, sendo curta, **empata com frequência** (→ pênaltis)
    — efeito que o limiar fixo antigo ignorava. Empate na ET = "vai aos pênaltis".
    """
    mu_h, mu_a = lam_home * _ET_FRACTION, lam_away * _ET_FRACTION
    k_max = 12
    ph = [math.exp(-mu_h) * mu_h**k / math.factorial(k) for k in range(k_max + 1)]
    pa = [math.exp(-mu_a) * mu_a**k / math.factorial(k) for k in range(k_max + 1)]
    p_home = p_draw = p_away = 0.0
    for i in range(k_max + 1):
        for j in range(k_max + 1):
            p = ph[i] * pa[j]
            if i > j:
                p_home += p
            elif i == j:
                p_draw += p
            else:
                p_away += p
    return p_home, p_draw, p_away


@dataclass
class KnockoutPrediction:
    home: str
    away: str
    # camada 1: placar dos 90 minutos
    home_goals: int
    away_goals: int
    # camada 2: prorrogação ("home" | "penalties" | "away")
    extra_time: str
    # camada 3: vencedor nos pênaltis ("home" | "away")
    penalty_winner: str
    # avanço (para montar o chaveamento)
    advancer: str
    p_advance_home: float

    @property
    def scoreline(self) -> str:
        return f"{self.home_goals}x{self.away_goals}"


def _zebra_prediction(matrix: np.ndarray, scorer: Scorer) -> tuple[int, int]:
    """Melhor placar por E[pts] DENTRO do lado azarão (modo bolão-atrás, ENG-36).

    Num bolão, ranking só muda quando o palpite diverge do pelotão (que aglomera no favorito) e a
    divergência acerta. Restringe a escolha às células de vitória do lado com MENOR P(vitória) e
    maximiza E[pts] dentro delas — descorrelação máxima ao menor custo de E[pts] dentro do lado.
    """
    p_home, _p_draw, p_away = outcome_probs_from_matrix(matrix)
    zebra_home = p_home < p_away
    n = matrix.shape[0]
    cells = [(i, j) for i in range(n) for j in range(n) if (i > j) == zebra_home and i != j]
    return max(cells, key=lambda c: scorer.expected_points(c, matrix))


def _empate_prediction(matrix: np.ndarray, scorer: Scorer) -> tuple[int, int]:
    """Melhor placar de EMPATE por E[pts] (diagonal) — modo bolão-atrás `empate` (ENG-39/40).

    A arma do líder, cirúrgica: em final apertada, P(empate 90') real supera a precificada pela
    base do app (5 das 8 finais desde 1994 empataram nos 90' vs ~28% no modelo), e o palpite de
    empate descorrelaciona do pelotão (que aglomera no favorito) exatamente no peso ×4.
    """
    n = matrix.shape[0]
    d = max(range(n), key=lambda k: scorer.expected_points((k, k), matrix))
    return d, d


def predict_knockout(
    home: str, away: str, matrix: np.ndarray, scorer: Scorer, *, pool_behind: str | None = None
) -> KnockoutPrediction:
    """Gera o palpite de mata-mata em 3 camadas a partir da matriz de placares.

    `pool_behind` (modo endgame de bolão; use SÓ nos jogos de peso máximo e SÓ atrás no ranking):
      - `"empate"` (ENG-39/40, política dominante): 90' no melhor placar de **empate** por E[pts];
        camadas ET/pênaltis e avanço seguem o cálculo fiel. Domina a zebra em todos os geradores
        testados (P(top-3) 8,4% vs 5,5% no baseline; 14,3% vs 3,8% no gerador histórico de finais).
      - `"zebra"` (ENG-36, superada — mantida para a reavaliação da véspera): lado azarão nas
        3 camadas, 90' pelo melhor E[pts] dentro dele.
      - `None`: palpite fiel.
    """
    if pool_behind not in (None, "empate", "zebra"):
        raise ValueError(f"pool_behind inválido: {pool_behind!r} (use None, 'empate' ou 'zebra')")

    p_home, p_draw, p_away = outcome_probs_from_matrix(matrix)

    if pool_behind == "zebra":
        zh, za = _zebra_prediction(matrix, scorer)
        zebra_side = "home" if zh > za else "away"
        return KnockoutPrediction(
            home=home,
            away=away,
            home_goals=zh,
            away_goals=za,
            extra_time=zebra_side,
            penalty_winner=zebra_side,
            advancer=home if zebra_side == "home" else away,
            p_advance_home=p_home + p_draw * (p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0.5),
        )

    # camada 1: melhor placar dos 90 min. No KO proíbe empate (ENG-32): um palpite de empate zera
    # sempre que o jogo é decidido no tempo normal, e seu ganho de E[pts] é marginal e apoiado numa
    # leve super-estimação de empate no KO. Exceção deliberada: modo `empate` (ENG-39) força a
    # diagonal — na final, a frequência real de empate supera a do modelo E a precificada pelo app.
    # O desfecho real (ET/pênaltis/avanço) segue nas camadas 2–3.
    if pool_behind == "empate":
        eh, ea = _empate_prediction(matrix, scorer)
        pred90 = None
    else:
        pred90 = scorer.best_prediction(matrix, forbid_draw=True)

    # probabilidade condicional de cada lado vencer um confronto decidido (ET/pênaltis)
    decisive = p_home + p_away
    cond_home = p_home / decisive if decisive > 0 else 0.5

    # P(mandante avança) = vence em 90 + empata e vence no desempate
    p_advance_home = p_home + p_draw * cond_home
    advancer = home if p_advance_home >= 0.5 else away

    # camada 2: desfecho da prorrogação por E[pts] — escolhe o desfecho MAIS PROVÁVEL da ET (o bônus
    # é fixo, então maximizar E[pts] = maximizar P(acerto)). Modela P(empate na ET → pênaltis), que o
    # limiar antigo ignorava: a ET tem 1/3 do tempo ⇒ muitos 0×0, então "vai aos pênaltis" costuma ser
    # o modal mesmo com um favorito moderado (ENG-29).
    lam_home, lam_away = _expected_goals(matrix)
    et_home, et_draw, et_away = _extra_time_probs(lam_home, lam_away)
    extra_time = max((("home", et_home), ("penalties", et_draw), ("away", et_away)), key=lambda kv: kv[1])[0]

    # camada 3: pênaltis — quase moeda, leve vantagem ao mais forte (argmax = lado mais provável)
    penalty_winner = "home" if cond_home >= 0.5 else "away"

    return KnockoutPrediction(
        home=home,
        away=away,
        home_goals=eh if pred90 is None else pred90.home_goals,
        away_goals=ea if pred90 is None else pred90.away_goals,
        extra_time=extra_time,
        penalty_winner=penalty_winner,
        advancer=advancer,
        p_advance_home=p_advance_home,
    )
