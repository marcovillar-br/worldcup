"""Testes da pontuação (Sistema I) e da escolha de palpite."""

from __future__ import annotations

import numpy as np

from worldcup.edition import ScoringConfig
from worldcup.scoring import Scorer


def _scorer(risk: float = 0.5) -> Scorer:
    return Scorer(ScoringConfig(system="sistema_i", risk=risk))


def test_wrong_result_scores_zero():
    s = _scorer()
    probs = (0.5, 0.3, 0.2)
    assert s.points((2, 0), (0, 1), probs) == 0.0


def test_exact_score_is_base_plus_five_only():
    # HIERÁRQUICO, não somado: o exato dá base + 5 (NÃO base + 5 + 3 + 2 + 1). Os níveis de placar
    # são mutuamente exclusivos; o exato não acumula gols do vencedor / saldo / gols do perdedor.
    s = _scorer()
    probs = (0.5, 0.3, 0.2)
    pts = s.points((2, 1), (2, 1), probs)
    base = 3.0  # curva fiel do app: p=0.50 -> 3 pts base
    assert abs(pts - (base + 5)) < 1e-6


def test_app_golden_points_per_game():
    """Casos de ouro das telas 'Pontos por Jogo' do app (rodada J55–J60, 25/06/2026).

    Travam a régua hierárquica contra o ground-truth do app. A base depende da probabilidade
    *do app* (que difere da nossa); aqui fixamos `probs` para isolar a estrutura do bônus.
    """
    s = _scorer()
    # Curaçao 0x2 C.Marfim, cravado (vitória do visitante, P≈0.81 → base 2): base + exato(5) = 7
    assert abs(s.points((0, 2), (0, 2), (0.10, 0.09, 0.81)) - (2 + 5)) < 1e-6
    # Paraguai 0x0 Austrália, empate cravado (P_empate=0.40 → base 4): base + exato(5) = 9
    assert abs(s.points((0, 0), (0, 0), (0.30, 0.40, 0.30)) - (4 + 5)) < 1e-6
    # Tunísia 0x3 / real 1x3: acertou só os gols do vencedor (3) — NÃO exato, NÃO saldo, NÃO perdedor
    # P_visitante=0.50 → base 3: base + gols_vencedor(3) = 6
    assert abs(s.points((0, 3), (1, 3), (0.25, 0.25, 0.50)) - (3 + 3)) < 1e-6


def test_placar_bonus_levels_are_exclusive():
    # cada nível decidido isolado, sem acumular com os outros (jogo decidido, P_mandante=0.50→base 3)
    s = _scorer()
    p = (0.50, 0.25, 0.25)
    assert abs(s.points((2, 0), (2, 1), p) - (3 + 3)) < 1e-6  # só gols do vencedor (+3): 2x0 vs 2x1
    assert abs(s.points((3, 1), (2, 0), p) - (3 + 2)) < 1e-6  # só saldo (+2): 3x1 vs 2x0
    assert abs(s.points((2, 1), (3, 1), p) - (3 + 1)) < 1e-6  # só gols do perdedor (+1): 2x1 vs 3x1


def test_underdog_correct_scores_more_than_favorite():
    s = _scorer()
    # mesmo placar exato, mas resultado raro (away com P=0.1) deve valer mais que favorito (P=0.7)
    fav = s.points((2, 1), (2, 1), (0.7, 0.2, 0.1))
    dog = s.points((1, 2), (1, 2), (0.7, 0.2, 0.1))
    assert dog > fav


def test_best_prediction_picks_favored_outcome():
    s = _scorer()
    # matriz claramente favorável ao mandante
    mat = np.zeros((7, 7))
    mat[2, 0] = 0.4
    mat[1, 0] = 0.3
    mat[1, 1] = 0.2
    mat[0, 1] = 0.1
    pred = s.best_prediction(mat)
    assert pred.home_goals > pred.away_goals  # prevê vitória do mandante
    assert pred.expected_points > 0


def test_base_points_reproduce_app_simulator():
    # curva base fiel ao Simulador do app (ENG-14): pontos observados nas telas de regras.
    s = _scorer()
    observed = {0.80: 2, 0.50: 3, 0.15: 7, 0.05: 11}
    for p, expected in observed.items():
        assert abs(s._base_points(p) - expected) <= 0.5, f"p={p}: {s._base_points(p)} != {expected}"
    # extremos clipados
    assert s._base_points(0.999) == 1.0  # favorito óbvio -> base_min
    assert s._base_points(0.001) == 13.0  # zebra extrema -> base_max


def test_base_points_independent_of_risk():
    # a régua de pontos do app é fixa; risk não deve alterá-la (só a escolha do palpite)
    assert _scorer(0.5)._base_points(0.5) == _scorer(0.9)._base_points(0.5)


def _picked_outcome_prob(pred) -> float:
    """Probabilidade do resultado (1x2) que o palpite escolheu."""
    if pred.home_goals > pred.away_goals:
        return pred.p_home
    if pred.home_goals == pred.away_goals:
        return pred.p_draw
    return pred.p_away


def test_higher_risk_favors_underdog_pick():
    # matriz equilibrada, mandante levemente favorito; risco alto tende a um resultado menos provável
    mat = np.array([[0.10, 0.18, 0.12], [0.14, 0.12, 0.06], [0.08, 0.05, 0.15]])
    mat = mat / mat.sum()
    cautious = _scorer(0.2).best_prediction(mat)
    bold = _scorer(0.9).best_prediction(mat)
    # o palpite ousado não escolhe um resultado mais provável que o cauteloso
    assert _picked_outcome_prob(bold) <= _picked_outcome_prob(cautious)


def test_so_vencedor_system():
    s = Scorer(ScoringConfig(system="so_vencedor"))
    probs = (0.5, 0.3, 0.2)
    assert s.points((3, 0), (1, 0), probs) == 1.0  # acertou o vencedor
    assert s.points((0, 1), (1, 0), probs) == 0.0  # errou


def test_goal_difference_bonus_on_draw():
    s = _scorer()
    probs = (0.3, 0.4, 0.3)
    # previu empate 1x1, saiu 2x2: acerta resultado (empate) + saldo, mas não o exato
    pts = s.points((1, 1), (2, 2), probs)
    base = 4.0  # curva fiel: p=0.40 -> 4 pts base
    assert abs(pts - (base + 2)) < 1e-6  # base + goal_diff


def test_knockout_bonus_extra_time_and_penalties():
    s = _scorer()
    # acertou que vai a pênaltis (+3) e o vencedor nos pênaltis (+3)
    assert s.knockout_bonus("penalties", "home", "penalties", "home") == 6.0
    # acertou só a ida a pênaltis, errou o vencedor (+3)
    assert s.knockout_bonus("penalties", "home", "penalties", "away") == 3.0
    # acertou que um lado vence na prorrogação (+3); sem pênaltis, sem bônus de pênaltis
    assert s.knockout_bonus("home", "home", "home", None) == 3.0
    # errou a prorrogação e não foi a pênaltis: zero
    assert s.knockout_bonus("home", "home", "penalties", "away") == 0.0


def test_knockout_bonus_only_for_sistema_i():
    s = Scorer(ScoringConfig(system="so_vencedor"))
    assert s.knockout_bonus("penalties", "home", "penalties", "home") == 0.0


def test_weighted_points_applies_phase_weight():
    # ENG-27: o app pontua a partida inteira (base + bônus) vezes o peso de fase.
    s = _scorer()
    probs = (0.25, 0.25, 0.50)
    base = s.points((0, 3), (1, 3), probs)  # base(0.50→3) + gols_vencedor(3) = 6
    assert base == 6.0
    assert s.weighted_points((0, 3), (1, 3), probs, 1.0) == base  # grupos ×1
    assert s.weighted_points((0, 3), (1, 3), probs, 2.0) == 2 * base  # R32–SF ×2
    assert s.weighted_points((0, 3), (1, 3), probs, 4.0) == 4 * base  # final ×4
    assert s.weighted_points((0, 3), (1, 3), probs) == base  # default = ×1
    # zerar o 1x2 zera mesmo ponderado (não inventa pontos)
    assert s.weighted_points((2, 0), (0, 1), probs, 4.0) == 0.0
