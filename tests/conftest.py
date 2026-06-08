"""Utilitários compartilhados pelos testes."""

from __future__ import annotations

import numpy as np

from worldcup.model import DixonColesModel


def make_model(strengths: dict[str, float], home_adv: float = 0.3, base: float = 0.1) -> DixonColesModel:
    """Cria um modelo determinístico com forças dadas (attack=força, defense=força).

    Times mais fortes têm `strength` maior -> marcam mais e sofrem menos.
    """
    m = DixonColesModel()
    teams = sorted(strengths)
    m.teams = teams
    m._idx = {t: i for i, t in enumerate(teams)}
    vals = np.array([strengths[t] for t in teams], dtype=float)
    centered = vals - vals.mean()
    m.attack = centered            # time forte marca mais
    m.defense = centered           # ...e defende melhor (defesa alta = sofre menos)
    m.home_adv = home_adv
    m.rho = 0.0
    m.base = base
    return m
