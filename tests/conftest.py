"""Utilitários compartilhados pelos testes."""

from __future__ import annotations

import numpy as np
import pandas as pd

from worldcup.edition import load_edition
from worldcup.model import DixonColesModel


def mini_historical(n_teams: int = 14) -> pd.DataFrame:
    """Histórico **sintético** mínimo para exercitar o pipeline real no CI (ENG-20).

    Round-robin ida/volta entre as `n_teams` primeiras seleções da edição 2026 (nomes canônicos
    reais), com o time mais forte (índice menor) sempre vencendo — cada uma joga ≥10 vezes
    (passa o `min_matches=10` do fit). As demais seleções caem no baseline. Não é realista (não é
    pra ser): serve para o `pipeline.run` rodar de ponta a ponta sem depender do
    `historical_results.csv` (gerado, gitignored, ausente no CI).
    """
    teams = load_edition(2026).teams[:n_teams]
    base = pd.Timestamp("2024-01-01")
    rows = []
    day = 0
    for i, h in enumerate(teams):
        for j, a in enumerate(teams):
            if i >= j:
                continue
            for home, away in ((h, a), (a, h)):
                strong_home = teams.index(home) < teams.index(away)
                hs, as_ = (2, 0) if strong_home else (0, 1)
                rows.append(
                    {
                        "date": base + pd.Timedelta(days=day),
                        "home_team": home,
                        "away_team": away,
                        "home_score": hs,
                        "away_score": as_,
                        # competitivo (peso ≥0.75 / "qualif") — senão o filtro do fit descarta tudo
                        "tournament": "FIFA World Cup qualification",
                        "neutral": True,
                    }
                )
                day += 1
    return pd.DataFrame(rows)


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
    m.attack = centered  # time forte marca mais
    m.defense = centered  # ...e defende melhor (defesa alta = sofre menos)
    m.home_adv = home_adv
    m.rho = 0.0
    m.base = base
    return m
