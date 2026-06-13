"""Pontuação do bolão e escolha do palpite que maximiza os pontos esperados.

Suporta os sistemas configuráveis no app:
  - "sistema_i"     probabilístico: pontos crescem com a raridade do resultado (zebra vale mais);
  - "simplificado"  pontos fixos com bônus por placar exato e saldo;
  - "so_vencedor"   só importa acertar vencedor/empate.

A estratégia escolhe o placar `(h, a)` que maximiza `E[pontos] = Σ P(real)·pontos(palpite, real)`.
O **nível de risco** (`risk`) controla o quanto inclinar para zebras de valor.
"""

from __future__ import annotations

import math
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
        """Pontos base do app: crescem com a raridade do resultado, de `base_min` a `base_max`.

        Forma **logarítmica** `base = 1 + a·log10(1/p)`, calibrada ao Simulador de Pontos do app
        (ex.: 80%→2, 50%→3, 15%→7, 5%→11; `a≈7,55`), arredondada e limitada a [base_min, base_max].
        É a pontuação **fiel** do app, independente de `risk` — o risco mora na *escolha* do palpite
        (`best_prediction`), não na régua de pontos.
        """
        c = self.cfg.sistema_i
        lo = float(c.get("base_min", 1.0))
        hi = float(c.get("base_max", 13.0))
        a = float(c.get("base_log_coeff", 7.55))
        raw = 1.0 + a * math.log10(1.0 / max(p_outcome, 1e-6))
        return float(min(hi, max(lo, math.floor(raw + 0.5))))

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

    def knockout_bonus(
        self,
        pred_extra_time: str,
        pred_penalty_winner: str,
        actual_extra_time: str,
        actual_penalty_winner: str | None,
    ) -> float:
        """Bônus de mata-mata do Sistema I (camadas 2 e 3), independentes do placar de 90'.

        - `extra_time` (+3): acertar o desfecho da prorrogação — `"home"`/`"away"` (um lado
          vence na prorrogação) ou `"penalties"` (foi à disputa).
        - `penalties` (+3): acertar o vencedor nos pênaltis (só quando o jogo foi a pênaltis).

        Os valores vêm do `scoring.toml` (`extra_time`/`penalties`). Só o Sistema I tem essas camadas.
        """
        if self.system != "sistema_i":
            return 0.0
        c = self.cfg.sistema_i
        bonus = 0.0
        if pred_extra_time == actual_extra_time:
            bonus += float(c.get("extra_time", 3.0))
        went_to_pens = actual_extra_time == "penalties" and actual_penalty_winner is not None
        if went_to_pens and pred_penalty_winner == actual_penalty_winner:
            bonus += float(c.get("penalties", 3.0))
        return bonus

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
        """Escolhe o placar maximizando os pontos esperados, com tilt de risco.

        Objetivo = `E[pontos] · (1/P(resultado))^(2·risk − 1)`. Em `risk=0.5` o expoente é 0
        (fator 1) → **maximiza E[pontos] puro** (fiel). `>0.5` favorece resultados raros (zebra);
        `<0.5` puxa para o favorito. O `expected_points` reportado é sempre o E[pontos] **real**.
        """
        probs = outcome_probs_from_matrix(matrix)
        favorite = int(np.argmax(probs))  # 0=mandante,1=empate,2=visitante
        mg = min(self.max_goals, matrix.shape[0] - 1)
        modal = np.unravel_index(int(np.argmax(matrix)), matrix.shape)
        tilt = 2.0 * self.risk - 1.0  # 0 em risk=0.5 (E-max puro); >0 ousa mais; <0 conservador

        best, best_obj, best_ep = (0, 0), -1.0, 0.0
        for h in range(mg + 1):
            for a in range(mg + 1):
                ep = self.expected_points((h, a), matrix)
                outcome = 0 if h > a else 1 if h == a else 2
                p_o = max(probs[outcome], 1e-6)
                obj = ep * (1.0 / p_o) ** tilt
                if obj > best_obj:
                    best_obj, best, best_ep = obj, (h, a), ep
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
