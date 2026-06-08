"""Testes do motor de formato — incluindo uma edição sintética que prova a genericidade."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from conftest import make_model
from worldcup.edition import Edition, Fixture, GroupStageSpec, ScoringConfig, TournamentSpec
from worldcup.format_engine import (
    MatrixCache,
    _assign_thirds,
    deterministic_bracket,
    group_standings,
    monte_carlo,
)

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


def _synthetic_edition() -> tuple[Edition, object]:
    """Formato diferente do de 2026: 4 grupos de 4, sem melhores terceiros."""
    teams = [f"T{i}" for i in range(16)]
    groups = {g: teams[i * 4 : i * 4 + 4] for i, g in enumerate(["G1", "G2", "G3", "G4"])}

    fixtures: list[Fixture] = []
    mid = 1
    for g, ts in groups.items():
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                fixtures.append(Fixture(match_id=mid, stage="group", group=g, date="2030-06-01",
                                        home=ts[i], away=ts[j], neutral=True))
                mid += 1
    ko = [
        (25, "QF", "1G1", "2G2"), (26, "QF", "1G3", "2G4"),
        (27, "QF", "1G2", "2G1"), (28, "QF", "1G4", "2G3"),
        (29, "SF", "W25", "W26"), (30, "SF", "W27", "W28"),
        (31, "final", "W29", "W30"),
    ]
    for m, stage, h, a in ko:
        fixtures.append(Fixture(match_id=m, stage=stage, date="2030-07-01", home=h, away=a, neutral=True))

    spec = TournamentSpec(
        name="Copa Sintética", edition=2030, hosts=[],
        group_stage=GroupStageSpec(
            num_groups=4, group_size=4, advance_per_group=2, best_thirds=0,
            tiebreakers=TB, knockout_stages=["QF", "SF", "final"],
        ),
    )
    edition = Edition(spec=spec, groups=groups, fixtures=fixtures,
                      scoring=ScoringConfig(), directory=Path("/tmp"))
    # força crescente com o índice -> T15 é o mais forte
    model = make_model({t: i * 0.15 for i, t in enumerate(teams)})
    return edition, model


def test_synthetic_edition_runs_end_to_end():
    edition, model = _synthetic_edition()
    cache = MatrixCache(model)
    sim = monte_carlo(edition, model, cache, n_sims=300, seed=1)
    # probabilidades de título somam ~1 e o time mais forte é o favorito
    assert abs(sum(sim.champion_prob.values()) - 1.0) < 1e-6
    favorite = max(sim.champion_prob, key=sim.champion_prob.get)
    assert favorite in {"T15", "T14", "T13"}

    bracket = deterministic_bracket(edition, sim, cache)
    assert len(bracket) == 7  # 4 QF + 2 SF + 1 final
    final = [b for b in bracket if b.fixture.stage == "final"][0]
    assert final.home and final.away and final.home != final.away


def test_edition_2026_structure():
    from worldcup.edition import load_edition

    e = load_edition(2026)
    assert len(e.fixtures) == 104
    assert len(e.group_fixtures()) == 72
    assert len(e.knockout_fixtures()) == 32
    assert len(e.teams) == 48
