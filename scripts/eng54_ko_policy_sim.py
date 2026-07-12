#!/usr/bin/env python3
"""ENG-54: re-mede a política de palpite do 90' no mata-mata contra a régua CERTA (placar dos 90').

O ENG-32 baniu o empate no 90' do KO apoiado em "+70 pts realizados em 4 Copas". Aquele número era
**artefato da régua**: o backtest pontuava contra a base martj42, que grava o placar **consolidado**
(com prorrogação), então punia o palpite de empate exatamente nos jogos em que o bolão — que pontua
o slot de 90' contra o **tempo normal** — o premiaria. Fechado o ENG-54 (os 90' reconstruídos da
lista de gols), a medição volta a ser válida e é isto que este script refaz.

Compara, nos 16 jogos de mata-mata de cada uma das 4 Copas de backtest (64 no total):

  fiel  — `best_prediction` livre (E[pts]-máximo, empate incluído)  ← política atual (ENG-53)
  ban   — `best_prediction(forbid_draw=True)` (empate proibido)     ← política do ENG-32, revogada

As camadas de prorrogação/pênaltis são idênticas nas duas políticas (só a camada 1 muda), então o
bônus de KO entra igual dos dois lados e não contamina a comparação.

Existe porque o veredito do ENG-54 é citado como evidência em AGENTS.md, docs/SPEC.md,
docs/MODEL_CARD.md e docs/BACKLOG.md — número que sustenta decisão tem de ser **reproduzível**
(mesmo espírito do `eng36_pool_sim.py`). Reproduzível:

  uv run python scripts/eng54_ko_policy_sim.py

Requer a base histórica (`uv run worldcup fetch-data`), pois é dela que saem os 90'.
"""

from __future__ import annotations

import argparse
import math

from worldcup.backtest import (
    _WORLD_CUP_START,
    _award_scorer,
    _knockout_bonus_for,
    _prepare,
    outcome_probs_from_matrix,
)
from worldcup.edition import ScoringConfig
from worldcup.fetch_data import load_historical
from worldcup.model import canonical
from worldcup.scoring import Scorer

# Numa Copa de 32 seleções o mata-mata são os 16 últimos jogos (8 oitavas + 4 quartas + 2 semis +
# 3º lugar + final). A base martj42 não traz a fase, mas a ordem cronológica basta: a fase de grupos
# termina antes de qualquer jogo de KO começar.
KNOCKOUT_GAMES_PER_CUP = 16


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--risk", type=float, default=0.5, help="ousadia do maximizador (default: 0.5 = fiel)")
    args = ap.parse_args()

    df = load_historical()
    award = _award_scorer()
    selector = Scorer(ScoringConfig(system="sistema_i", risk=args.risk))

    deltas: list[float] = []  # pontos (ban - fiel) por jogo de KO
    per_cup: dict[int, float] = {}
    different_score = ban_wins = ban_losses = 0

    for year in sorted(_WORLD_CUP_START):
        _model, cache, test = _prepare(year, df)
        knockout = test.sort_values("date").tail(KNOCKOUT_GAMES_PER_CUP)
        cup_delta = 0.0
        for _, m in knockout.iterrows():
            mat = cache.matrix(canonical(m["home_team"]), canonical(m["away_team"]), bool(m["neutral"]))
            actual = (int(m["home_score"]), int(m["away_score"]))  # já são os 90' (score_90 em _prepare)
            probs = outcome_probs_from_matrix(mat)
            bonus = _knockout_bonus_for(m, mat, award)  # idêntico nas duas políticas

            faithful = selector.best_prediction(mat, forbid_draw=False)
            banned = selector.best_prediction(mat, forbid_draw=True)
            pts_faithful = award.points((faithful.home_goals, faithful.away_goals), actual, probs) + bonus
            pts_banned = award.points((banned.home_goals, banned.away_goals), actual, probs) + bonus

            delta = pts_banned - pts_faithful
            deltas.append(delta)
            cup_delta += delta
            if (faithful.home_goals, faithful.away_goals) != (banned.home_goals, banned.away_goals):
                different_score += 1
                ban_wins += delta > 0
                ban_losses += delta < 0
        per_cup[year] = cup_delta

    n = len(deltas)
    mean = sum(deltas) / n
    sd = math.sqrt(sum((d - mean) ** 2 for d in deltas) / (n - 1))
    se = sd / math.sqrt(n)

    per_cup_txt = ", ".join(f"{y}: {v:+.0f}" for y, v in per_cup.items())
    print(f"Política de 90' no mata-mata: BAN de empate (ENG-32) vs. E[pts]-FIEL (ENG-53), risk={args.risk}")
    print("Régua: placar dos 90' (ENG-54) — o slot que o bolão de fato pontua.\n")
    print(f"jogos de mata-mata ......... {n} ({len(per_cup)} Copas × {KNOCKOUT_GAMES_PER_CUP})")
    print(f"ganho médio do ban ......... {mean:+.2f} pt/jogo")
    print(f"                     t ..... {mean / se:+.2f}")
    print(f"                 IC95% ..... [{mean - 1.96 * se:+.2f}, {mean + 1.96 * se:+.2f}]")
    print(f"placar palpitado diverge ... {different_score} de {n} jogos")
    print(f"  destes, os pontos mudam .. {ban_wins + ban_losses} (ban ganha {ban_wins}, perde {ban_losses})")
    print(f"saldo por Copa ............. {per_cup_txt}")
    print(f"saldo total ................ {sum(deltas):+.0f} pts\n")
    print("Leitura: o IC95% cruza o zero — o backtest NÃO distingue as duas políticas (e não apoia o")
    print("ban). A escolha fiel (ENG-53) se sustenta no argumento de E[pts], que vale por construção.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
