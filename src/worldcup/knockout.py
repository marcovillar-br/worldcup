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

from dataclasses import dataclass

import numpy as np

from .scoring import Scorer, outcome_probs_from_matrix

# Limiar para palpitar que um lado vence a prorrogação (senão, palpita "vai pros pênaltis").
_ET_DECISIVE_THRESHOLD = 0.58


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


def predict_knockout(home: str, away: str, matrix: np.ndarray, scorer: Scorer) -> KnockoutPrediction:
    """Gera o palpite de mata-mata em 3 camadas a partir da matriz de placares."""
    p_home, p_draw, p_away = outcome_probs_from_matrix(matrix)

    # camada 1: melhor placar dos 90 min (mesma lógica de pontos esperados)
    pred90 = scorer.best_prediction(matrix)

    # probabilidade condicional de cada lado vencer um confronto decidido (ET/pênaltis)
    decisive = p_home + p_away
    cond_home = p_home / decisive if decisive > 0 else 0.5

    # P(mandante avança) = vence em 90 + empata e vence no desempate
    p_advance_home = p_home + p_draw * cond_home
    advancer = home if p_advance_home >= 0.5 else away

    # camada 2: prorrogação — palpita o lado claramente mais forte, senão "vai pros pênaltis"
    if cond_home >= _ET_DECISIVE_THRESHOLD:
        extra_time = "home"
    elif cond_home <= 1 - _ET_DECISIVE_THRESHOLD:
        extra_time = "away"
    else:
        extra_time = "penalties"

    # camada 3: pênaltis — quase moeda, leve vantagem ao mais forte
    penalty_winner = "home" if cond_home >= 0.5 else "away"

    return KnockoutPrediction(
        home=home,
        away=away,
        home_goals=pred90.home_goals,
        away_goals=pred90.away_goals,
        extra_time=extra_time,
        penalty_winner=penalty_winner,
        advancer=advancer,
        p_advance_home=p_advance_home,
    )
