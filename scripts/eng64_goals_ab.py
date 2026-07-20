"""ENG-64: métricas pooladas de matriz para o A/B da supressão do visitante (`away_pen`).

Computa, sob o **código corrente**, as métricas pareáveis do pool as-of das 5 Copas (mesmo
protocolo do ENG-56): Brier multiclasse do 1×2 (guarda de não-degradação), Brier binário do
over/under 2,5 e log-loss do placar exato (o que o bolão consome via `best_prediction`).
Comparar versões = rodar este script em dois commits (ex.: `daace91`, sem `away_pen`, vs o
commit do fix) — os números do veredito estão no BACKLOG (ENG-64) e no MODEL_CARD §7.
A calibração de gols/empate correspondente sai de `scripts/eng56_draw_pool.py` (sondas).

Uso: uv run python scripts/eng64_goals_ab.py [--years 2010 2014 2018 2022 2026]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from worldcup import backtest as bt
from worldcup.fetch_data import load_historical
from worldcup.scoring import outcome_probs_from_matrix
from worldcup.teams import canonical


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2010, 2014, 2018, 2022, 2026])
    years = tuple(ap.parse_args().years)

    df = load_historical()
    brier, brier_over, logloss = [], [], []
    for year in years:
        _m, cache, test = bt._prepare(year, df)
        for _, m in test.iterrows():
            mat = cache.matrix(canonical(m["home_team"]), canonical(m["away_team"]), bool(m["neutral"]))
            probs = outcome_probs_from_matrix(mat)
            hg, ag = int(m["home_score"]), int(m["away_score"])
            o = 0 if hg > ag else (1 if hg == ag else 2)
            brier.append(sum((probs[k] - (1.0 if k == o else 0.0)) ** 2 for k in range(3)))
            n = mat.shape[0]
            tot = np.add.outer(np.arange(n), np.arange(n))
            p_over = float(mat[tot >= 3].sum())
            brier_over.append((p_over - (1.0 if hg + ag >= 3 else 0.0)) ** 2)
            p_exact = float(mat[min(hg, n - 1), min(ag, n - 1)])
            logloss.append(-np.log(max(p_exact, 1e-12)))

    n_games = len(brier)
    print(f"📊 ENG-64 — métricas de matriz pooladas ({n_games} jogos, Copas {years}):")
    print(f"  Brier 1×2 (guarda)     : {np.mean(brier):.5f}")
    print(f"  Brier over/under 2,5   : {np.mean(brier_over):.5f}")
    print(f"  log-loss placar exato  : {np.mean(logloss):.5f}")
    print("(menor é melhor; compare entre commits com o mesmo historical_results.csv)")


if __name__ == "__main__":
    main()
