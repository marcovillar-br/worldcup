"""Pontuação do bolão e escolha do palpite que maximiza os pontos esperados.

Suporta os sistemas configuráveis no app:
  - "sistema_i"     probabilístico: pontos crescem com a raridade do resultado (zebra vale mais);
  - "simplificado"  pontos fixos com bônus por placar exato e saldo;
  - "so_vencedor"   só importa acertar vencedor/empate.

A estratégia escolhe o placar `(h, a)` que maximiza `E[pontos] = Σ P(real)·pontos(palpite, real)`.
O **nível de risco** (`risk`) controla o quanto inclinar para zebras de valor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .edition import ScoringConfig


def outcome_probs_from_matrix(matrix: np.ndarray) -> tuple[float, float, float]:
    """(P(mandante), P(empate), P(visitante)) a partir da matriz de placares."""
    p_home = float(np.tril(matrix, -1).sum())
    p_draw = float(np.trace(matrix))
    p_away = float(np.triu(matrix, 1).sum())
    return p_home, p_draw, p_away


def _result(h: int, a: int) -> int:
    """1 = vitória mandante, 0 = empate, -1 = vitória visitante."""
    return (h > a) - (h < a)


@dataclass
class Prediction:
    home_goals: int
    away_goals: int
    expected_points: float
    p_home: float
    p_draw: float
    p_away: float
    is_upset: bool  # palpite contraria o favorito do modelo (aposta ousada)
    modal_home: int  # placar mais provável (referência)
    modal_away: int

    @property
    def scoreline(self) -> str:
        return f"{self.home_goals}x{self.away_goals}"

    @property
    def modal_scoreline(self) -> str:
        return f"{self.modal_home}x{self.modal_away}"


class Scorer:
    """Calcula pontos e escolhe o melhor palpite conforme o sistema/risco configurados."""

    def __init__(self, config: ScoringConfig) -> None:
        self.cfg = config
        self.system = config.system
        self.risk = config.risk
        sysparams = config.sistema_i or {}
        self.max_goals = int(sysparams.get("max_goals", 6))

    # ----------------------------------------------------------- pontos
    def _base_points(self, p_outcome: float) -> float:
        """Pontos base do Sistema I: variam com a probabilidade do resultado (base_min..base_max).

        O `risk` ajusta a ousadia: 0.5 = fiel (base ~ 1/p), >0.5 valoriza mais a zebra,
        <0.5 achata a curva em direção ao placar mais provável.
        """
        c = self.cfg.sistema_i
        lo = float(c.get("base_min", 1.0))
        hi = float(c.get("base_max", 13.0))
        gamma = 2.0 * self.risk  # risk=0.5 -> gamma=1 (fiel a 1/p)
        raw = (1.0 / max(p_outcome, 1e-6)) ** gamma
        return float(min(hi, max(lo, raw)))

    def points(
        self,
        pred: tuple[int, int],
        actual: tuple[int, int],
        probs: tuple[float, float, float],
    ) -> float:
        """Pontos ganhos ao palpitar `pred` quando o real foi `actual` (resultado dos 90 min)."""
        ph, pa = pred
        ah, aa = actual
        rp, ra = _result(ph, pa), _result(ah, aa)
        if self.system == "so_vencedor":
            return 1.0 if rp == ra else 0.0
        if rp != ra:  # errou o resultado (1x2) -> zero em todos os sistemas
            return 0.0

        if self.system == "simplificado":
            c = self.cfg.simplificado
            if (ph, pa) == (ah, aa):
                return float(c.get("exact", 18.0))
            if (ph - pa) == (ah - aa):
                return float(c.get("winner", 10.0)) + float(c.get("diff_bonus", 3.0))
            return float(c.get("winner", 10.0))

        # sistema_i: base por probabilidade + bônus cumulativos
        c = self.cfg.sistema_i
        p_out = probs[0] if ra > 0 else probs[1] if ra == 0 else probs[2]
        pts = self._base_points(p_out)
        exact = (ph, pa) == (ah, aa)
        if exact:
            pts += float(c.get("exact", 5.0))
        if (ph - pa) == (ah - aa):  # diferença de gols (vale também para empates)
            pts += float(c.get("goal_diff", 2.0))
        if ra != 0:  # jogo decidido: bônus de gols do vencedor / do perdedor
            win_pred = ph if rp > 0 else pa
            win_act = ah if ra > 0 else aa
            lose_pred = pa if rp > 0 else ph
            lose_act = aa if ra > 0 else ah
            if win_pred == win_act:
                pts += float(c.get("winner_goals", 3.0))
            if lose_pred == lose_act:
                pts += float(c.get("loser_goals", 1.0))
            if exact and abs(ah - aa) >= 3:  # goleada acertada
                pts += float(c.get("goleada", 1.0))
        return pts

    # ----------------------------------------------------------- escolha
    def expected_points(self, pred: tuple[int, int], matrix: np.ndarray) -> float:
        """E[pontos] do palpite `pred` integrando sobre a matriz de placares."""
        probs = outcome_probs_from_matrix(matrix)
        n = matrix.shape[0]
        total = 0.0
        for ah in range(n):
            row = matrix[ah]
            for aa in range(n):
                p = row[aa]
                if p <= 0:
                    continue
                total += p * self.points(pred, (ah, aa), probs)
        return total

    def best_prediction(self, matrix: np.ndarray) -> Prediction:
        """Escolhe o placar que maximiza os pontos esperados."""
        probs = outcome_probs_from_matrix(matrix)
        favorite = int(np.argmax(probs))  # 0=mandante,1=empate,2=visitante
        mg = min(self.max_goals, matrix.shape[0] - 1)
        modal = np.unravel_index(int(np.argmax(matrix)), matrix.shape)

        best, best_ep = (0, 0), -1.0
        for h in range(mg + 1):
            for a in range(mg + 1):
                ep = self.expected_points((h, a), matrix)
                if ep > best_ep:
                    best_ep, best = ep, (h, a)
        pred_outcome = 0 if best[0] > best[1] else 1 if best[0] == best[1] else 2
        return Prediction(
            home_goals=best[0],
            away_goals=best[1],
            expected_points=best_ep,
            p_home=probs[0],
            p_draw=probs[1],
            p_away=probs[2],
            is_upset=(pred_outcome != favorite),
            modal_home=int(modal[0]),
            modal_away=int(modal[1]),
        )
