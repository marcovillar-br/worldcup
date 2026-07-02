#!/usr/bin/env python3
"""ENG-36: bolão é jogo DIFERENCIAL — mede P(top-k) por política de palpite contra um pelotão sintético.

`best_prediction` maximiza E[pts] contra a verdade; mas ranking só muda quando o palpite diverge do
pelotão e a divergência acerta. Este script simula os jogos **restantes** da edição (placares pelo
modelo+blend atuais, mesmo caminho do `predict`), um pelotão de apostadores sintéticos (consenso /
ruidoso / caça-empate) ancorado nos pontos reais do bolão, e compara políticas para o usuário:

  fiel        — sempre o palpite do tool (predict_knockout: 90' sem empate + camadas ET/pên.)
  exato-alt   — mesmo lado do tool, mas o 2º melhor placar por E[pts] (descorrelação de placar)
  zebra-final — fiel até a final; na final (e 3º lugar), se atrás, lado zebra
  zebra-sf    — idem, a partir das semifinais
  zebra-qf    — idem, a partir das quartas, só em jogo apertado (P(favorito) < limiar)

Saída: P(#1), P(top-3), E[pontos finais] por política, nos cenários "atrás" (standing real) e
"na frente" (contrafactual). Reproduzível:

  uv run python scripts/eng36_pool_sim.py --edition 2026 --sims 3000 \
      --my-points 285 --leader 337 --pool-size 60

Premissas (documentadas no relatório): pontos dos adversários interpolados linearmente entre o líder
e o usuário (acima) e abaixo do usuário (desconhecidos — só líder/usuário são observados); pelotão
75% consenso, 15% ruidoso, 10% caça-empate (líder = caça-empate, perfil observado em 01/07);
placares "reais" amostrados das MESMAS matrizes usadas para palpitar (todas as políticas compartilham
o gerador — a comparação relativa é o que vale).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np

from worldcup.blend import blend_matrix_with_odds
from worldcup.edition import Edition, load_edition
from worldcup.fetch_data import load_historical
from worldcup.format_engine import MatrixCache
from worldcup.knockout import _expected_goals, _extra_time_probs, predict_knockout
from worldcup.model import DixonColesModel, FitConfig
from worldcup.pipeline import build_training_frame
from worldcup.scoring import Scorer, outcome_probs_from_matrix
from worldcup.sync import resolve_live_bracket

# ------------------------------------------------------------------ tipos

Pick = tuple[int, int, str, str]  # (gols_mandante, gols_visitante, camada_ET, camada_pênaltis)


@dataclass
class SimGame:
    """Um jogo restante: identidade + slots para resolver o confronto durante a simulação."""

    match_id: int
    stage: str
    date: str
    home_slot: str
    away_slot: str
    neutral: bool


# ------------------------------------------------------------------ picks por arquétipo


def _side_cells(n: int, side: str) -> list[tuple[int, int]]:
    if side == "home":
        return [(i, j) for i in range(n) for j in range(n) if i > j]
    return [(i, j) for i in range(n) for j in range(n) if i < j]


def _modal_cell(matrix: np.ndarray, cells: list[tuple[int, int]]) -> tuple[int, int]:
    return max(cells, key=lambda c: matrix[c])


def consensus_pick(matrix: np.ndarray) -> Pick:
    """Apostador de consenso: favorito vence com o placar MODAL do lado dele; ET/pên. no favorito."""
    ph, _pd, pa = outcome_probs_from_matrix(matrix)
    side = "home" if ph >= pa else "away"
    h, a = _modal_cell(matrix, _side_cells(matrix.shape[0], side))
    return (h, a, side, side)


def drawhunter_pick(matrix: np.ndarray) -> Pick:
    """Caça-empate (perfil do líder em 01/07): empate modal nos 90' + 'vai aos pênaltis' + favorito."""
    ph, _pd, pa = outcome_probs_from_matrix(matrix)
    fav = "home" if ph >= pa else "away"
    n = matrix.shape[0]
    d = max(range(n), key=lambda k: matrix[k, k])
    return (d, d, "penalties", fav)


def zebra_pick(matrix: np.ndarray, scorer: Scorer) -> Pick:
    """Lado ZEBRA com o melhor placar por E[pts] dentro do lado; camadas ET/pên. também na zebra."""
    ph, _pd, pa = outcome_probs_from_matrix(matrix)
    side = "away" if ph >= pa else "home"
    cells = _side_cells(matrix.shape[0], side)
    h, a = max(cells, key=lambda c: scorer.expected_points(c, matrix))
    return (h, a, side, side)


def tool_pick(home: str, away: str, matrix: np.ndarray, scorer: Scorer) -> Pick:
    kp = predict_knockout(home, away, matrix, scorer)
    return (kp.home_goals, kp.away_goals, kp.extra_time, kp.penalty_winner)


def exato_alt_pick(home: str, away: str, matrix: np.ndarray, scorer: Scorer) -> Pick:
    """Mesmo lado do tool, 2º melhor placar por E[pts] — descorrelaciona o exato sem trocar o 1×2."""
    h0, a0, et, pen = tool_pick(home, away, matrix, scorer)
    side = "home" if h0 > a0 else "away"
    cells = [c for c in _side_cells(matrix.shape[0], side) if c != (h0, a0)]
    h, a = max(cells, key=lambda c: scorer.expected_points(c, matrix))
    return (h, a, et, pen)


def noisy_pick(matrix: np.ndarray, scorer: Scorer, variant: int, rng: np.random.Generator) -> Pick:
    """Consenso com ruído: ~15% dos palpites viram zebra modal; senão, placar perturbado do consenso."""
    if rng.random() < 0.15:
        return zebra_pick(matrix, scorer)
    h, a, et, pen = consensus_pick(matrix)
    if variant % 2 == 1:  # metade dos ruidosos infla o placar do favorito (2x0 -> 3x0/2x1)
        if h > a:
            h = min(h + 1, matrix.shape[0] - 1)
        else:
            a = min(a + 1, matrix.shape[0] - 1)
    return (h, a, et, pen)


# ------------------------------------------------------------------ simulação de um jogo


def simulate_game(matrix: np.ndarray, rng: np.random.Generator) -> tuple[tuple[int, int], str | None, str | None, str]:
    """Amostra (placar 90', desfecho ET, vencedor pên., quem avança) da matriz.

    Desfecho ET ∈ {None (decidido nos 90'), 'home', 'away', 'penalties'}; vencedor de pênaltis só
    quando foi à disputa. ET amostrada do mesmo modelo de camada 2 do tool (Poisson 30').
    """
    n = matrix.shape[0]
    flat = matrix.ravel() / matrix.sum()
    idx = rng.choice(len(flat), p=flat)
    hg, ag = divmod(int(idx), n)
    if hg != ag:
        return (hg, ag), None, None, ("home" if hg > ag else "away")
    lam_h, lam_a = _expected_goals(matrix)
    p_et = np.array(_extra_time_probs(lam_h, lam_a))
    et = ["home", "penalties", "away"][int(rng.choice(3, p=p_et / p_et.sum()))]
    if et != "penalties":
        return (hg, ag), et, None, et
    ph, _pd, pa = outcome_probs_from_matrix(matrix)
    cond_home = ph / (ph + pa) if (ph + pa) > 0 else 0.5
    pen = "home" if rng.random() < cond_home else "away"
    return (hg, ag), "penalties", pen, pen


def score_pick(
    scorer: Scorer,
    pick: Pick,
    actual90: tuple[int, int],
    actual_et: str | None,
    actual_pen: str | None,
    probs: tuple[float, float, float],
    weight: float,
) -> float:
    """Pontos do Sistema I da partida inteira ×peso: 90' + bônus de ET/pên. quando foi além dos 90'."""
    pts = scorer.weighted_points(pick[:2], actual90, probs, weight)
    if actual_et is not None:  # o app só pontua as camadas quando o jogo passou dos 90'
        pts += scorer.knockout_bonus(pick[2], pick[3], actual_et, actual_pen) * weight
    return pts


# ------------------------------------------------------------------ pelotão sintético


def build_pool(my_points: float, leader: float, pool_size: int, my_rank: int) -> tuple[np.ndarray, list[str]]:
    """Pontos atuais + arquétipo de cada adversário (pool_size−1 adversários).

    Só (meus pontos, líder, minha posição) são observados; o resto é interpolação linear —
    premissa declarada no cabeçalho. Líder = caça-empate (perfil observado); demais 75/15/10.
    """
    n_above = my_rank - 1
    n_below = pool_size - my_rank
    above = np.linspace(leader, my_points + 2, n_above) if n_above else np.array([])
    below = np.linspace(my_points - 2, max(my_points - 105, 60.0), n_below) if n_below else np.array([])
    pts = np.concatenate([above, below])
    kinds: list[str] = []
    for i in range(len(pts)):
        if i == 0 and n_above:
            kinds.append("drawhunter")  # o líder
        elif i % 10 < 7:
            kinds.append("consensus")
        elif i % 10 < 9:
            kinds.append(f"noisy{i % 4}")
        else:
            kinds.append("drawhunter")
    return pts, kinds


# ------------------------------------------------------------------ torneio restante


def remaining_games(edition: Edition) -> list[SimGame]:
    return [
        SimGame(f.match_id, f.stage, f.date, f.home, f.away, f.neutral)
        for f in sorted(edition.fixtures, key=lambda x: (x.date, x.match_id))
        if not f.played
    ]


def seed_bracket(edition: Edition) -> tuple[dict[int, str], dict[int, str]]:
    """Vencedor/perdedor dos jogos de KO já disputados (para resolver slots W##/L##)."""
    winners: dict[int, str] = {}
    losers: dict[int, str] = {}
    for f in edition.fixtures:
        if f.is_group or not f.played:
            continue
        # times reais do confronto disputado: resolvidos pelo bracket vivo
        pair = resolve_live_bracket(edition).get(f.match_id)
        if pair is None:
            continue
        home, away = pair
        assert f.home_goals is not None
        assert f.away_goals is not None
        w = f.ko_outcome or (home if f.home_goals > f.away_goals else away)
        winners[f.match_id] = w
        losers[f.match_id] = away if w == home else home
    return winners, losers


class MatchupResolver:
    """Resolve (mandante, visitante) de um jogo restante durante a simulação."""

    def __init__(self, edition: Edition) -> None:
        self.live = resolve_live_bracket(edition)  # confrontos já determinados (ex.: R32 restante)
        self.base_winners, self.base_losers = seed_bracket(edition)

    def resolve(self, g: SimGame, winners: dict[int, str], losers: dict[int, str]) -> tuple[str, str]:
        if g.match_id in self.live:
            return self.live[g.match_id]

        def slot(s: str) -> str:
            if s.startswith("W"):
                return winners[int(s[1:])]
            if s.startswith("L"):
                return losers[int(s[1:])]
            raise ValueError(f"slot não resolvível na simulação: {s!r} (J{g.match_id})")

        return slot(g.home_slot), slot(g.away_slot)


# ------------------------------------------------------------------ main


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ENG-36: P(top-k) por política de palpite vs pelotão sintético")
    p.add_argument("--edition", type=int, default=2026)
    p.add_argument("--sims", type=int, default=3000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--my-points", type=float, default=285.0)
    p.add_argument("--leader", type=float, default=337.0)
    p.add_argument("--my-rank", type=int, default=21)
    p.add_argument("--pool-size", type=int, default=60)
    p.add_argument("--close-threshold", type=float, default=0.62, help="P(favorito) abaixo disso = jogo apertado")
    args = p.parse_args(argv)

    edition = load_edition(args.edition)
    scorer = Scorer(edition.scoring)
    print("⚙️  Ajustando o modelo (mesmo caminho do predict)...")
    model = DixonColesModel(FitConfig()).fit(build_training_frame(edition, load_historical()))
    cache = MatrixCache(model, edition.hosts)
    w = edition.scoring.blend_weight

    games = remaining_games(edition)
    resolver = MatchupResolver(edition)
    print(f"🎲 {len(games)} jogos restantes; {args.sims} torneios simulados; pool={args.pool_size}.")

    # memoização por confronto: matriz (com blend quando há odds) e picks por arquétipo
    mat_memo: dict[tuple[int, str, str], np.ndarray] = {}
    pick_memo: dict[tuple[str, tuple[int, str, str]], Pick] = {}

    def matrix_for(g: SimGame, home: str, away: str) -> np.ndarray:
        key = (g.match_id, home, away)
        if key not in mat_memo:
            mat = cache.matrix(home, away, g.neutral)
            odds = edition.odds.get(g.match_id)
            if odds is not None and w > 0:
                mat = blend_matrix_with_odds(mat, odds, w, totals=edition.totals.get(g.match_id))
            mat_memo[key] = mat
        return mat_memo[key]

    def memo_pick(kind: str, g: SimGame, home: str, away: str, mat: np.ndarray, rng: np.random.Generator) -> Pick:
        key = (kind, (g.match_id, home, away))
        if key not in pick_memo:
            if kind == "tool":
                pick_memo[key] = tool_pick(home, away, mat, scorer)
            elif kind == "exato_alt":
                pick_memo[key] = exato_alt_pick(home, away, mat, scorer)
            elif kind == "zebra":
                pick_memo[key] = zebra_pick(mat, scorer)
            elif kind == "consensus":
                pick_memo[key] = consensus_pick(mat)
            elif kind == "drawhunter":
                pick_memo[key] = drawhunter_pick(mat)
            elif kind.startswith("noisy"):
                pick_memo[key] = noisy_pick(mat, scorer, int(kind[-1]), rng)
            else:
                raise ValueError(kind)
        return pick_memo[key]

    scenarios = [
        ("ATRÁS (standing real)", args.my_points, args.leader, args.my_rank),
        ("NA FRENTE (contrafactual)", args.leader + 3, args.leader, 1),
    ]
    policies = ["fiel", "exato-alt", "zebra-final", "zebra-sf", "zebra-qf"]
    zebra_stages = {"zebra-final": {"final", "3rd_place"}, "zebra-sf": {"final", "3rd_place", "SF"}}
    zebra_stages["zebra-qf"] = zebra_stages["zebra-sf"] | {"QF"}

    for label, my_pts0, leader_pts, my_rank in scenarios:
        opp_pts0, opp_kinds = build_pool(my_pts0, leader_pts, args.pool_size, my_rank)
        rng = np.random.default_rng(args.seed)
        finals = {pol: np.zeros(args.sims) for pol in policies}
        ranks = {pol: np.zeros(args.sims, dtype=int) for pol in policies}

        for s in range(args.sims):
            winners = dict(resolver.base_winners)
            losers = dict(resolver.base_losers)
            opp = opp_pts0.copy()
            mine = dict.fromkeys(policies, my_pts0)
            for g in games:
                home, away = resolver.resolve(g, winners, losers)
                mat = matrix_for(g, home, away)
                probs = outcome_probs_from_matrix(mat)
                weight = edition.scoring.weight(g.stage)
                actual90, aet, apen, adv = simulate_game(mat, rng)
                winners[g.match_id] = home if adv == "home" else away
                losers[g.match_id] = away if adv == "home" else home
                # adversários
                for i, kind in enumerate(opp_kinds):
                    pk = memo_pick(kind, g, home, away, mat, rng)
                    opp[i] += score_pick(scorer, pk, actual90, aet, apen, probs, weight)
                # minhas políticas
                ph, _pd, pa = probs
                fav_prob = max(ph, pa) / (ph + pa) if (ph + pa) > 0 else 0.5
                for pol in policies:
                    behind = mine[pol] < opp.max()
                    use_zebra = (
                        pol in zebra_stages
                        and g.stage in zebra_stages[pol]
                        and behind
                        and (g.stage != "QF" or fav_prob < args.close_threshold)
                    )
                    kind = "zebra" if use_zebra else ("exato_alt" if pol == "exato-alt" else "tool")
                    pk = memo_pick(kind, g, home, away, mat, rng)
                    mine[pol] += score_pick(scorer, pk, actual90, aet, apen, probs, weight)
            for pol in policies:
                finals[pol][s] = mine[pol]
                ranks[pol][s] = 1 + int((opp > mine[pol]).sum())

        print(
            f"\n=== Cenário: {label} — eu {my_pts0:.0f} pts, líder {leader_pts:.0f}, "
            f"posição {my_rank}/{args.pool_size} ==="
        )
        print(f"{'política':<12} {'P(#1)':>7} {'P(top3)':>8} {'E[rank]':>8} {'E[pts finais]':>14}")
        for pol in policies:
            p1 = float((ranks[pol] == 1).mean())
            p3 = float((ranks[pol] <= 3).mean())
            print(f"{pol:<12} {100 * p1:6.1f}% {100 * p3:7.1f}% {ranks[pol].mean():8.2f} {finals[pol].mean():14.1f}")

    print(
        "\nLeitura: compare 'fiel' com as divergentes DENTRO de cada cenário (gerador compartilhado; "
        "diferenças são pareadas). Premissas do pelotão no cabeçalho do script."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
