"""Sincroniza resultados reais da internet para o fixtures.csv da edição.

Usa o mesmo dataset público (`martj42/international_results`, atualizado poucas horas após cada
jogo) como feed de resultados — mais confiável de parsear que a página da FIFA (renderizada em
JavaScript). Preenche automaticamente os placares dos jogos já disputados:

  - **Fase de grupos**: casa por par de seleções (mesma orientação do dataset que gerou o fixture).
  - **Mata-mata**: resolve o chaveamento só com os resultados reais (sem modelo), grupo a grupo, e
    casa cada confronto; empate nos 90'/prorrogação é decidido pelo vencedor em `shootouts.csv`.

Depois é só rodar `predict` para repalpitar os jogos restantes.
"""

from __future__ import annotations

import csv
import os
import tempfile
from contextlib import suppress
from pathlib import Path

import numpy as np

from .edition import EDITIONS_DIR, Edition, load_edition
from .fetch_data import download_raw, download_shootouts
from .format_engine import group_standings
from .teams import canonical


def _edition_results(year: int) -> tuple[dict[tuple[str, str], list[tuple[str, int, int]]], dict[frozenset[str], str]]:
    """Resultados reais (jogos por par) e vencedores de pênaltis da Copa do ano dado.

    Cada par mapeia para uma **lista** de `(data, gols_casa, gols_fora)`: numa mesma Copa o
    mesmo par pode jogar 2× (adversários de grupo que se reencontram no mata-mata — possível no
    formato 2026). Guardar lista + data evita que a segunda partida sobrescreva a primeira.
    """
    raw = download_raw()
    wc = raw[(raw["tournament"] == "FIFA World Cup") & (raw["date"].astype(str).str.startswith(str(year)))].copy()
    wc = wc.dropna(subset=["home_score", "away_score"])
    scores: dict[tuple[str, str], list[tuple[str, int, int]]] = {}
    for _, r in wc.iterrows():
        h, a = canonical(r["home_team"]), canonical(r["away_team"])
        scores.setdefault((h, a), []).append((str(r["date"]), int(r["home_score"]), int(r["away_score"])))

    so = download_shootouts()
    so = so[so["date"].astype(str).str.startswith(str(year))]
    shootouts: dict[frozenset[str], str] = {}
    for _, r in so.iterrows():
        shootouts[frozenset({canonical(r["home_team"]), canonical(r["away_team"])})] = canonical(r["winner"])
    return scores, shootouts


def _result_for(scores, home: str, away: str, date: str | None = None) -> tuple[int, int] | None:
    """Placar do confronto na orientação (home, away), independente da ordem na fonte.

    `scores` mapeia cada par a uma **lista** de jogos. Com um único jogo registrado, devolve-o
    direto (robusto a divergência de data entre fixture e fonte). Com mais de um (o mesmo par 2×
    na Copa), desambigua por `date`; sem casar a data, devolve `None` em vez de chutar.
    """
    candidates: list[tuple[str, int, int]] = []
    for d, hg, ag in scores.get((home, away), []):
        candidates.append((d, hg, ag))
    for d, hg, ag in scores.get((away, home), []):
        candidates.append((d, ag, hg))  # orientação invertida na fonte -> placar espelhado
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0][1], candidates[0][2]
    if date is not None:
        for d, hg, ag in candidates:
            if d == date:
                return hg, ag
    return None  # par jogou 2× e a data não casou: não dá pra desambiguar com segurança


def _winner(home: str, away: str, hg: int, ag: int, shootouts) -> str | None:
    if hg > ag:
        return home
    if ag > hg:
        return away
    return shootouts.get(frozenset({home, away}))  # empate -> pênaltis


def _resolve_real_bracket(edition: Edition, scores, shootouts) -> dict[int, tuple[str, str]]:
    """Resolve os confrontos do mata-mata usando só resultados reais (None onde ainda indefinido)."""
    spec = edition.spec.group_stage
    rng = np.random.default_rng(0)  # tiebreak determinístico (raro empatar em tudo)

    # standings só de grupos completos
    winners, runners, thirds_by_group = {}, {}, {}
    all_groups_complete = True
    for g, teams in edition.groups.items():
        games = {}
        for f in edition.group_fixtures():
            if f.group != g:
                continue
            res = _result_for(scores, f.home, f.away, f.date)
            if res is None:
                all_groups_complete = False
                break
            games[(f.home, f.away)] = res
        else:
            st = group_standings(teams, games, spec.tiebreakers, rng)
            winners[g], runners[g], thirds_by_group[g] = st[0].team, st[1].team, st[2]
            continue
        # grupo incompleto

    # melhores terceiros só quando todos os grupos terminaram
    third_team_by_match: dict[int, str] = {}
    if all_groups_complete and spec.best_thirds:
        from .format_engine import _assign_thirds

        ranked = sorted(thirds_by_group.items(), key=lambda kv: (-kv[1].points, -kv[1].gd, -kv[1].gf))[
            : spec.best_thirds
        ]
        ko = edition.knockout_fixtures()
        slots = [(f.match_id, f.third_groups) for f in ko if f.away == "3rd"]
        assign = _assign_thirds(slots, [g for g, _ in ranked])
        third_team_by_match = {mid: thirds_by_group[g].team for mid, g in assign.items()}

    # caminha o mata-mata propagando vencedores reais
    ko_winner: dict[int, str] = {}
    resolved: dict[int, tuple[str, str]] = {}

    def slot_team(slot: str, match_id: int) -> str | None:
        if slot == "3rd":
            return third_team_by_match.get(match_id)
        if slot.startswith("W"):
            return ko_winner.get(int(slot[1:]))
        if slot.startswith("L"):
            return None  # disputa de 3º: tratada à parte abaixo
        pos, g = slot[0], slot[1:]
        return winners.get(g) if pos == "1" else runners.get(g)

    losers: dict[int, str] = {}
    for f in sorted(edition.knockout_fixtures(), key=lambda x: x.match_id):
        if f.home.startswith("L") or f.away.startswith("L"):
            home = ko_winner.get(int(f.home[1:])) if f.home.startswith("W") else losers.get(int(f.home[1:]))
            away = ko_winner.get(int(f.away[1:])) if f.away.startswith("W") else losers.get(int(f.away[1:]))
        else:
            home = slot_team(f.home, f.match_id)
            away = slot_team(f.away, f.match_id)
        if not home or not away:
            continue
        resolved[f.match_id] = (home, away)
        res = _result_for(scores, home, away, f.date)
        if res is None:
            continue
        hg, ag = res
        w = _winner(home, away, hg, ag, shootouts)
        if w:
            ko_winner[f.match_id] = w
            losers[f.match_id] = away if w == home else home
    return resolved


def sync_results(year: int = 2026, base_dir: Path = EDITIONS_DIR) -> dict[str, int]:
    """Baixa resultados e preenche fixtures.csv. Retorna contagem de jogos preenchidos."""
    edition = load_edition(year, base_dir)
    scores, shootouts = _edition_results(year)

    path = base_dir / str(year) / "fixtures.csv"
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    bracket = _resolve_real_bracket(edition, scores, shootouts)
    filled_group = filled_ko = 0

    for r in rows:
        if r["home_goals"].strip():  # já preenchido (manual ou sync anterior)
            continue
        mid = int(r["match_id"])
        if r["stage"] == "group":
            res = _result_for(scores, r["home"], r["away"], r["date"])
            if res:
                r["home_goals"], r["away_goals"] = str(res[0]), str(res[1])
                filled_group += 1
        elif mid in bracket:
            home, away = bracket[mid]
            res = _result_for(scores, home, away, r["date"])
            if res:
                hg, ag = res
                r["home_goals"], r["away_goals"] = str(hg), str(ag)
                w = _winner(home, away, hg, ag, shootouts)
                if w:
                    r["ko_outcome"] = w
                filled_ko += 1

    write_fixtures_atomic(path, rows)

    total_played = sum(len(v) for v in scores.values())
    return {"group": filled_group, "knockout": filled_ko, "total_played_in_source": total_played}


def write_fixtures_atomic(path: Path, rows: list[dict]) -> None:
    """Reescreve o fixtures.csv (spec versionada) de forma atômica.

    Grava num temporário no mesmo diretório e faz um rename atômico (`Path.replace`): uma falha
    no meio da escrita nunca deixa o arquivo original truncado/corrompido.
    """
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".fixtures-", suffix=".csv.tmp")
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
            fh.flush()
            os.fsync(fh.fileno())
        tmp_path.replace(path)
    except BaseException:
        with suppress(OSError):
            tmp_path.unlink()
        raise
