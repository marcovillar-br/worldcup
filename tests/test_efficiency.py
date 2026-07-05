"""Testes da lógica pura do scripts/efficiency.py (desfecho de KO + bônus ponderado; ENG-27 parte 2)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

from worldcup.edition import Fixture, ScoringConfig
from worldcup.scoring import Scorer

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "efficiency.py"
_spec = importlib.util.spec_from_file_location("efficiency", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
efficiency = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(efficiency)


def _pens(date: str, home: str, away: str, winner: str) -> dict:
    return {(date, frozenset({home, away})): winner}


def test_actual_ko_outcome_regulation():
    # placar dos 90' decidido → não houve prorrogação/pênaltis
    assert efficiency._actual_ko_outcome(2, 1, "2026-06-29", "Brazil", "Brazil", "Japan", {}) == (None, None)


def test_actual_ko_outcome_penalties():
    # 90' empate + na fonte com vencedor de pênaltis → ("penalties", lado do vencedor)
    pens = _pens("2026-06-29", "Germany", "Paraguay", "Paraguay")
    assert efficiency._actual_ko_outcome(1, 1, "2026-06-29", "Paraguay", "Germany", "Paraguay", pens) == (
        "penalties",
        "away",
    )


def test_actual_ko_outcome_extra_time():
    # 90' empate + na fonte SEM shootout → decidido na prorrogação; vencedor = quem avançou
    pens = {("2026-06-29", frozenset({"Netherlands", "Morocco"})): ""}
    assert efficiency._actual_ko_outcome(1, 1, "2026-06-29", "Morocco", "Netherlands", "Morocco", pens) == (
        "away",
        None,
    )


def test_actual_ko_outcome_latency_skips():
    # 90' empate mas o jogo ainda NÃO está na fonte (chave ausente) → não inferir (latência)
    assert efficiency._actual_ko_outcome(1, 1, "2026-06-29", "Morocco", "Netherlands", "Morocco", {}) == (
        None,
        None,
    )


def _fx(mid: int, hg: int | None, ag: int | None) -> Fixture:
    return Fixture(match_id=mid, stage="R32", date="2026-07-01", home="1G", away="3rd", home_goals=hg, away_goals=ag)


def test_regulation_90_prefers_reg_score_for_et_goal():
    # ENG-45: KO decidido por gol na ET → o gravado (3x2) inclui a prorrogação; o slot de 90' usa o 90' (2x2)
    ed = SimpleNamespace(regulation={82: (2, 2)})
    assert efficiency.regulation_90(ed, _fx(82, 3, 2)) == (2, 2)


def test_regulation_90_falls_back_to_recorded():
    ed = SimpleNamespace(regulation={})
    assert efficiency.regulation_90(ed, _fx(76, 2, 1)) == (2, 1)  # sem entrada ⇒ o gravado É o 90'
    assert efficiency.regulation_90(ed, _fx(91, None, None)) is None  # não disputado


def test_eng45_et_goal_scored_against_90_and_gets_bonus():
    # Regressão ENG-45: o placar de 90' (2x2) faz o jogo cair no caminho de ET (empate nos 90'),
    # resolvendo o bônus; com o placar GRAVADO (3x2) a lógica antiga o tratava como decidido nos 90'.
    reg90 = efficiency.regulation_90(SimpleNamespace(regulation={82: (2, 2)}), _fx(82, 3, 2))
    pens = {("2026-07-01", frozenset({"Belgium", "Senegal"})): ""}  # na fonte, sem shootout ⇒ ET
    assert efficiency._actual_ko_outcome(reg90[0], reg90[1], "2026-07-01", "Belgium", "Belgium", "Senegal", pens) == (
        "home",
        None,
    )
    # contraste (o bug): usar o gravado 3x2 ⇒ "decidido nos 90'", nenhum bônus de ET e slot pontuado errado
    assert efficiency._actual_ko_outcome(3, 2, "2026-07-01", "Belgium", "Belgium", "Senegal", pens) == (None, None)


def test_weighted_ko_bonus_is_doubled_in_r32():
    # o bônus de KO também leva o peso de fase: pênaltis acertados = +3/+3 unit → ×2 = +12 no R32
    s = Scorer(ScoringConfig(system="sistema_i", risk=0.5))
    w = 2.0
    assert s.knockout_bonus("penalties", "home", "penalties", "home") * w == 12.0
    # só a ida aos pênaltis certa (errou o vencedor): +3 unit ×2 = 6
    assert s.knockout_bonus("penalties", "home", "penalties", "away") * w == 6.0
