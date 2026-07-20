"""ENG-56: o modelo subestima empate? Teste poolado de 5 Copas + sondas de mecanismo.

Protocolo (o mesmo do backtest, apples-to-apples entre Copas): para cada Copa, treina **só com
jogos anteriores ao início** (as-of), pontua P(empate nos 90') de cada jogo contra o empate real
dos 90' (`fetch_data.score_90`). Poolar as 5 Copas dá o poder que uma só não tem (EP ~5 pp por
Copa); o z é Poisson-binomial (`backtest.draw_regime_stats`), declarado a priori: |z| ≥ 2 ⇒ viés
real, senão ruído (hipótese a).

Sondas de mecanismo (só interpretáveis se o pooled acusar):
- **Estratos por equilíbrio** (pista de 12/07): favorito < 40% / 40–50% / ≥ 50%. Viés global mal
  calibrado apareceria em todo estrato; concentração no equilibrado aponta regime, não ruído.
- **Hipótese (c) — torneio travado:** total de gols observado (90') vs E[gols] da matriz, z pela
  variância prevista por jogo. Observado ≪ previsto ⇒ o λ está alto para jogo de Copa.
- **Hipótese (b) — rho sub-ajustado:** decompõe o déficit de empate em placares rho-sensíveis
  (0×0/1×1, que o termo Dixon–Coles governa) vs empates altos (2×2+). Déficit só nos baixos com
  total de gols calibrado ⇒ rho; total de gols inflado ⇒ (c).

Uso: uv run python scripts/eng56_draw_pool.py [--years 2010 2014 2018 2022 2026]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from worldcup import backtest as bt
from worldcup.fetch_data import load_historical
from worldcup.scoring import outcome_probs_from_matrix
from worldcup.teams import canonical

BUCKETS = (
    ("equilibrado (<40%)", 0.0, 0.40),
    ("intermediário (40–50%)", 0.40, 0.50),
    ("favorito claro (≥50%)", 0.50, 1.01),
)


@dataclass
class Game:
    year: int
    p_draw: float
    is_draw: bool
    fav: float  # prob do lado mais forte (1×2)
    pred_goals: float  # E[gols totais 90'] da matriz
    var_goals: float  # Var[gols totais] da matriz
    obs_goals: int
    p_low_draw: float  # P(0×0) + P(1×1)
    is_low_draw: bool  # empatou nos 90' em 0×0 ou 1×1


def collect(years: tuple[int, ...]) -> list[Game]:
    df = load_historical()
    games: list[Game] = []
    for year in years:
        _model, cache, test = bt._prepare(year, df)
        for _, m in test.iterrows():
            mat = cache.matrix(canonical(m["home_team"]), canonical(m["away_team"]), bool(m["neutral"]))
            ph, pd_, pa = outcome_probs_from_matrix(mat)
            n = mat.shape[0]
            totals = np.add.outer(np.arange(n), np.arange(n)).astype(float)
            e_goals = float((totals * mat).sum())
            var = float((totals**2 * mat).sum() - e_goals**2)
            hg, ag = int(m["home_score"]), int(m["away_score"])
            games.append(
                Game(
                    year=year,
                    p_draw=pd_,
                    is_draw=hg == ag,
                    fav=max(ph, pa),
                    pred_goals=e_goals,
                    var_goals=var,
                    obs_goals=hg + ag,
                    p_low_draw=float(mat[0, 0] + mat[1, 1]),
                    is_low_draw=hg == ag and hg <= 1,
                )
            )
    return games


def _draw_line(label: str, gs: list[Game]) -> None:
    dr = bt.draw_regime_stats([g.p_draw for g in gs], [g.is_draw for g in gs])
    obs_pct = 100 * dr.observed / dr.n if dr.n else 0.0
    exp_pct = 100 * dr.expected / dr.n if dr.n else 0.0
    print(
        f"  {label:<26} n={dr.n:>3}  obs {dr.observed:>3} ({obs_pct:4.1f}%)  "
        f"esp {dr.expected:6.1f} ({exp_pct:4.1f}%)  z={dr.z:+.2f}"
    )


def _goals_z(gs: list[Game]) -> tuple[float, float, float]:
    """(média observada, média prevista, z) do total de gols nos 90'."""
    obs = sum(g.obs_goals for g in gs)
    exp = sum(g.pred_goals for g in gs)
    var = sum(g.var_goals for g in gs)
    z = (obs - exp) / var**0.5 if var > 0 else 0.0
    return obs / len(gs), exp / len(gs), z


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2010, 2014, 2018, 2022, 2026])
    years = tuple(ap.parse_args().years)

    games = collect(years)
    print(f"📊 ENG-56 — empates de 90' poolados, {len(games)} jogos de {len(years)} Copas (as-of início de cada uma)\n")

    print("Por Copa:")
    for year in years:
        _draw_line(str(year), [g for g in games if g.year == year])
    print("\nPooled (veredito principal, gatilho |z| ≥ 2):")
    _draw_line("TODAS", games)
    dr = bt.draw_regime_stats([g.p_draw for g in games], [g.is_draw for g in games])
    var = sum(p * (1 - p) for p in (g.p_draw for g in games))
    mde = 2 * var**0.5 / len(games)
    print(f"  poder: com n={len(games)}, o teste detecta (2σ) um viés de ≥ {100 * mde:.1f} pp na taxa de empate")

    print("\nEstratos por equilíbrio (prob. do lado mais forte — pista de 12/07):")
    for label, lo, hi in BUCKETS:
        _draw_line(label, [g for g in games if lo <= g.fav < hi])

    print("\nSonda (c) — total de gols 90' (observado ≪ previsto ⇒ Copa mais travada que o λ):")
    for label, lo, hi in (("todos os jogos", 0.0, 1.01), *BUCKETS):
        gs = [g for g in games if lo <= g.fav < hi]
        o, e, z = _goals_z(gs)
        print(f"  {label:<26} n={len(gs):>3}  obs {o:.2f} gols/jogo  esp {e:.2f}  z={z:+.2f}")

    print("\nSonda (b) — decomposição do empate (0×0/1×1 é o território do rho):")
    low = bt.draw_regime_stats([g.p_low_draw for g in games], [g.is_low_draw for g in games])
    high = bt.draw_regime_stats(
        [g.p_draw - g.p_low_draw for g in games], [g.is_draw and not g.is_low_draw for g in games]
    )
    print(f"  0×0/1×1:  obs {low.observed:>3}  esp {low.expected:6.1f}  z={low.z:+.2f}")
    print(f"  2×2+:     obs {high.observed:>3}  esp {high.expected:6.1f}  z={high.z:+.2f}")

    verdict = (
        "VIÉS REAL (≥2σ): investigar (b)/(c) acima"
        if abs(dr.z) >= 2
        else "sem significância — compatível com ruído (hipótese a)"
    )
    print(f"\nVeredito automático: pooled z={dr.z:+.2f} → {verdict}")


if __name__ == "__main__":
    main()
