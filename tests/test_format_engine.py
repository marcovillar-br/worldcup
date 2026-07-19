"""Testes do motor de formato — incluindo uma edição sintética que prova a genericidade."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from conftest import make_model
from worldcup.edition import Edition, Fixture, GroupStageSpec, ScoringConfig, TournamentSpec
from worldcup.format_engine import (
    MatrixCache,
    _assign_thirds,
    deterministic_bracket,
    group_standings,
    mc_ci95,
    monte_carlo,
)

if TYPE_CHECKING:
    from worldcup.model import DixonColesModel

RNG = np.random.default_rng(0)
TB = ["points", "goal_difference", "goals_for", "random"]


def test_group_standings_orders_by_points_then_gd():
    teams = ["X", "Y", "Z"]
    results = {("X", "Y"): (3, 0), ("X", "Z"): (1, 0), ("Y", "Z"): (2, 2)}
    table = group_standings(teams, results, TB, RNG)
    assert table[0].team == "X"  # 6 pts
    assert {table[1].team, table[2].team} == {"Y", "Z"}


def test_assign_thirds_respects_allowed_groups():
    slots = [(74, ["A", "B"]), (77, ["C", "D"])]
    assign = _assign_thirds(slots, ["A", "D"])
    assert assign[74] == "A"
    assert assign[77] == "D"


def test_assign_thirds_official_override_overrides_backtracking():
    """Quando o override (tabela Annex C) descreve a combinação realizada, ele manda — mesmo que o
    backtracking encontrasse outro emparelhamento válido."""
    # Ambos os grupos são permitidos nos dois slots ⇒ o backtracking sozinho casaria 74->A, 77->B.
    slots = [(74, ["A", "B"]), (77, ["A", "B"])]
    override = {74: "B", 77: "A"}
    assign = _assign_thirds(slots, ["A", "B"], override)
    assert assign == {74: "B", 77: "A"}


def test_assign_thirds_override_ignored_when_combination_differs():
    """Se os terceiros classificados não batem com o conjunto do override, ignora-o e casa por restrição."""
    slots = [(74, ["A", "B"]), (77, ["C", "D"])]
    override = {74: "B", 77: "A"}  # descreve {A,B}, mas a combinação real é {A,D}
    assign = _assign_thirds(slots, ["A", "D"], override)
    assert assign == {74: "A", 77: "D"}


def _synthetic_edition() -> tuple[Edition, DixonColesModel]:
    """Formato diferente do de 2026: 4 grupos de 4, sem melhores terceiros."""
    teams = [f"T{i}" for i in range(16)]
    groups = {g: teams[i * 4 : i * 4 + 4] for i, g in enumerate(["G1", "G2", "G3", "G4"])}

    fixtures: list[Fixture] = []
    mid = 1
    for g, ts in groups.items():
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                fixtures.append(
                    Fixture(
                        match_id=mid, stage="group", group=g, date="2030-06-01", home=ts[i], away=ts[j], neutral=True
                    )
                )
                mid += 1
    ko = [
        (25, "QF", "1G1", "2G2"),
        (26, "QF", "1G3", "2G4"),
        (27, "QF", "1G2", "2G1"),
        (28, "QF", "1G4", "2G3"),
        (29, "SF", "W25", "W26"),
        (30, "SF", "W27", "W28"),
        (31, "final", "W29", "W30"),
    ]
    for m, stage, h, a in ko:
        fixtures.append(Fixture(match_id=m, stage=stage, date="2030-07-01", home=h, away=a, neutral=True))

    spec = TournamentSpec(
        name="Copa Sintética",
        edition=2030,
        hosts=[],
        group_stage=GroupStageSpec(
            num_groups=4,
            group_size=4,
            advance_per_group=2,
            best_thirds=0,
            tiebreakers=TB,
            knockout_stages=["QF", "SF", "final"],
        ),
    )
    edition = Edition(spec=spec, groups=groups, fixtures=fixtures, scoring=ScoringConfig(), directory=Path("/tmp"))
    # força crescente com o índice -> T15 é o mais forte
    model = make_model({t: i * 0.15 for i, t in enumerate(teams)})
    return edition, model


def test_synthetic_edition_runs_end_to_end():
    edition, model = _synthetic_edition()
    cache = MatrixCache(model)
    sim = monte_carlo(edition, model, cache, n_sims=300, seed=1)
    # probabilidades de título somam ~1 e o time mais forte é o favorito
    assert abs(sum(sim.champion_prob.values()) - 1.0) < 1e-6
    favorite = max(sim.champion_prob, key=lambda t: sim.champion_prob[t])
    assert favorite in {"T15", "T14", "T13"}

    bracket = deterministic_bracket(edition, sim, cache)
    assert len(bracket) == 7  # 4 QF + 2 SF + 1 final
    final = next(b for b in bracket if b.fixture.stage == "final")
    assert final.home
    assert final.away
    assert final.home != final.away


def test_edition_2026_structure():
    from worldcup.edition import load_edition

    e = load_edition(2026)
    assert len(e.fixtures) == 104
    assert len(e.group_fixtures()) == 72
    assert len(e.knockout_fixtures()) == 32
    assert len(e.teams) == 48


# ── ENG-51: bracket e palpite decidem quem avança com a MESMA matriz ────────────────────────────


def _one_sided_matrix(away_wins: bool) -> np.ndarray:
    """Matriz de placar degenerada: toda a massa num placar que faz o lado escolhido vencer."""
    mat = np.zeros((6, 6))
    mat[(0, 3)] = 1.0 if away_wins else 0.0  # 0×3 → visitante vence
    mat[(3, 0)] = 0.0 if away_wins else 1.0  # 3×0 → mandante vence
    return mat


def _ko_determined_edition() -> tuple[Edition, DixonColesModel]:
    """4 grupos de 3, fase de grupos **toda disputada** ⇒ semifinalistas determinados.

    KO: 2 SF (1A×1B, 1C×1D) + final. Sem aleatoriedade de grupo, os confrontos de KO são fixos —
    base para exercitar `matrix_fn`/`ko_blend` sem depender do `historical_results.csv` (ausente no CI).
    Grupos de 3 (não 2) porque o `deterministic_bracket` sempre calcula o 3º colocado do grupo.
    """
    teams = [f"S{i}" for i in range(12)]
    groups = {g: teams[i * 3 : i * 3 + 3] for i, g in enumerate(["A", "B", "C", "D"])}
    fixtures: list[Fixture] = []
    mid = 1
    for g, ts in groups.items():
        # placares determinísticos: ts[0] 1º (6 pts), ts[1] 2º (3), ts[2] 3º (0)
        for (h, a), (hg, ag) in {(ts[0], ts[1]): (1, 0), (ts[0], ts[2]): (1, 0), (ts[1], ts[2]): (1, 0)}.items():
            fixtures.append(
                Fixture(
                    match_id=mid,
                    stage="group",
                    group=g,
                    date="2030-06-01",
                    home=h,
                    away=a,
                    neutral=True,
                    home_goals=hg,
                    away_goals=ag,
                )
            )
            mid += 1
    ko = [(31, "SF", "1A", "1B"), (32, "SF", "1C", "1D"), (33, "final", "W31", "W32")]
    for m, stage, h, a in ko:
        fixtures.append(Fixture(match_id=m, stage=stage, date="2030-07-01", home=h, away=a, neutral=True))
    spec = TournamentSpec(
        name="KO determinado",
        edition=2030,
        hosts=[],
        group_stage=GroupStageSpec(
            num_groups=4,
            group_size=3,
            advance_per_group=1,
            best_thirds=0,
            tiebreakers=TB,
            knockout_stages=["SF", "final"],
        ),
    )
    edition = Edition(spec=spec, groups=groups, fixtures=fixtures, scoring=ScoringConfig(), directory=Path("/tmp"))
    model = make_model(dict.fromkeys(teams, 0.1))  # forças iguais: quem decide é a matriz injetada
    return edition, model


def test_deterministic_bracket_matrix_fn_flips_advancer():
    # o vencedor propagado ao downstream vem da matriz de `matrix_fn`, não do modelo puro (ENG-51)
    edition, model = _ko_determined_edition()
    cache = MatrixCache(model)
    sim = monte_carlo(edition, model, cache, n_sims=50, seed=1)

    home_wins = {
        rm.fixture.match_id: rm
        for rm in deterministic_bracket(
            edition, sim, cache, matrix_fn=lambda h, a, f: _one_sided_matrix(away_wins=False)
        )
    }
    away_wins = {
        rm.fixture.match_id: rm
        for rm in deterministic_bracket(
            edition, sim, cache, matrix_fn=lambda h, a, f: _one_sided_matrix(away_wins=True)
        )
    }

    # SF31 = 1A×1B = S0×S3: com mando vencendo → S0 à final; com visitante vencendo → S3
    assert home_wins[33].home == "S0"  # vencedor do SF31 (mandante 1A)
    assert away_wins[33].home == "S3"  # vencedor do SF31 (visitante 1B)
    assert home_wins[33].home != away_wins[33].home


def test_bracket_advancer_matches_predict_knockout_under_same_matrix():
    # invariante do ENG-51: dada a MESMA matriz, o vencedor do bracket == o avanço do palpite
    from worldcup.knockout import predict_knockout
    from worldcup.scoring import Scorer

    edition, model = _ko_determined_edition()
    cache = MatrixCache(model)
    sim = monte_carlo(edition, model, cache, n_sims=50, seed=1)
    mat = _one_sided_matrix(away_wins=True)
    bracket = {
        rm.fixture.match_id: rm for rm in deterministic_bracket(edition, sim, cache, matrix_fn=lambda h, a, f: mat)
    }

    sf = bracket[31]
    assert sf.home is not None
    assert sf.away is not None
    kp = predict_knockout(sf.home, sf.away, mat, Scorer(edition.scoring))
    # o palpite avança o visitante (matriz o favorece); o bracket propaga o mesmo time à final
    assert kp.advancer == sf.away
    assert bracket[33].home == sf.away


def test_monte_carlo_ko_blend_shifts_champion():
    # ENG-51: blendar um confronto determinado desloca o campeão para o lado que a matriz favorece
    edition, model = _ko_determined_edition()
    cache = MatrixCache(model)
    base = monte_carlo(edition, model, cache, n_sims=400, seed=3).champion_prob
    # blenda a SF31 (S0×S3, confronto fixo) para o visitante S3 sempre vencer → chega mais à final
    blend = {("S0", "S3", True): _one_sided_matrix(away_wins=True)}
    tilted = monte_carlo(edition, model, cache, n_sims=400, seed=3, ko_blend=blend).champion_prob
    assert tilted.get("S3", 0) > base.get("S3", 0)


def test_mc_ci95_is_the_binomial_half_width():
    # ENG-62: 1,96·√(p(1−p)/n) — em 5000 sims, p=0,5 carrega ±~1,4 p.p.
    assert abs(mc_ci95(0.5, 5000) - 0.01386) < 1e-4
    assert mc_ci95(0.0, 5000) == 0.0  # p degenerado: sem variância
    assert mc_ci95(0.5, 0) == 0.0  # sims desconhecidas → sem barra (compat)
