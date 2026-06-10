"""Motor de simulação genérico: classificação de grupos, melhores terceiros e chaveamento.

Lê a spec da edição (qualquer formato) e resolve quem avança, montando o chaveamento do
mata-mata. Faz duas coisas:
  - **Monte Carlo** da Copa inteira → probabilidades (classificação, título);
  - **Chaveamento determinístico** (cenário mais provável) → o bracket concreto que vira palpite.

Resultados reais já conhecidos (`fixtures.csv` preenchido) são respeitados em vez de simulados.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from .scoring import outcome_probs_from_matrix

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .edition import Edition, Fixture
    from .model import DixonColesModel


class MatrixCache:
    """Memoiza matrizes de placar do modelo e permite amostrar placares."""

    def __init__(self, model: DixonColesModel, hosts: Iterable[str] = ()) -> None:
        self.model = model
        self.hosts = frozenset(hosts)
        self._cache: dict[tuple[str, str, bool], np.ndarray] = {}
        self._cdf: dict[tuple[str, str, bool], tuple[np.ndarray, int]] = {}

    def _host_away(self, home: str, away: str, neutral: bool) -> bool:
        """Jogo não-neutro em que o anfitrião é o visitante oficial (joga em casa mesmo assim)."""
        return not neutral and away in self.hosts and home not in self.hosts

    def matrix(self, home: str, away: str, neutral: bool) -> np.ndarray:
        key = (home, away, neutral)
        if key not in self._cache:
            host_away = self._host_away(home, away, neutral)
            self._cache[key] = self.model.score_matrix(home, away, neutral, host_away=host_away)
        return self._cache[key]

    def sample(self, home: str, away: str, neutral: bool, rng: np.random.Generator) -> tuple[int, int]:
        key = (home, away, neutral)
        if key not in self._cdf:
            mat = self.matrix(home, away, neutral)
            self._cdf[key] = (np.cumsum(mat.ravel()), mat.shape[1])
        cdf, n = self._cdf[key]
        idx = int(np.searchsorted(cdf, rng.random() * cdf[-1]))
        return divmod(idx, n)


@dataclass
class TeamStats:
    team: str
    points: int = 0
    gf: int = 0
    ga: int = 0
    played: int = 0

    @property
    def gd(self) -> int:
        return self.gf - self.ga

    def add(self, scored: int, conceded: int) -> None:
        self.played += 1
        self.gf += scored
        self.ga += conceded
        if scored > conceded:
            self.points += 3
        elif scored == conceded:
            self.points += 1


def _sort_key(stats: TeamStats, tiebreakers: list[str], rng: np.random.Generator) -> tuple:
    parts: list[float] = []
    for tb in tiebreakers:
        if tb == "points":
            parts.append(stats.points)
        elif tb == "goal_difference":
            parts.append(stats.gd)
        elif tb == "goals_for":
            parts.append(stats.gf)
        elif tb == "random":
            parts.append(float(rng.random()))
    return tuple(-p for p in parts)  # ordem decrescente


def group_standings(
    teams: list[str],
    results: dict[tuple[str, str], tuple[int, int]],
    tiebreakers: list[str],
    rng: np.random.Generator,
) -> list[TeamStats]:
    """Classificação de um grupo dado os placares de seus jogos."""
    stats = {t: TeamStats(t) for t in teams}
    for (h, a), (hg, ag) in results.items():
        stats[h].add(hg, ag)
        stats[a].add(ag, hg)
    return sorted(stats.values(), key=lambda s: _sort_key(s, tiebreakers, rng))


# --------------------------------------------------------------------- slots
def _assign_thirds(slots: list[tuple[int, list[str]]], qualified_groups: list[str]) -> dict[int, str]:
    """Casa cada grupo de terceiro classificado a um slot permitido (matching por backtracking)."""
    assignment: dict[int, str] = {}
    used: set[str] = set()

    def backtrack(i: int) -> bool:
        if i == len(slots):
            return True
        match_id, allowed = slots[i]
        for g in qualified_groups:
            if g in used or g not in allowed:
                continue
            used.add(g)
            assignment[match_id] = g
            if backtrack(i + 1):
                return True
            used.remove(g)
            del assignment[match_id]
        return False

    backtrack(0)
    return assignment


# --------------------------------------------------------------- Monte Carlo
@dataclass
class SimulationResult:
    champion_prob: dict[str, float] = field(default_factory=dict)
    advance_prob: dict[str, float] = field(default_factory=dict)  # P(passar da fase de grupos)
    rank_counts: dict[str, dict[str, Counter]] = field(default_factory=dict)  # grupo->team->rank Counter
    third_qualify: Counter = field(default_factory=Counter)


def _played_group_results(edition: Edition) -> dict[str, dict[tuple[str, str], tuple[int, int]]]:
    """Placares reais já registrados, por grupo."""
    out: dict[str, dict[tuple[str, str], tuple[int, int]]] = defaultdict(dict)
    for f in edition.group_fixtures():
        if f.home_goals is None or f.away_goals is None or f.group is None:
            continue
        out[f.group][(f.home, f.away)] = (f.home_goals, f.away_goals)
    return out


def monte_carlo(
    edition: Edition,
    model: DixonColesModel,
    cache: MatrixCache,
    n_sims: int = 8000,
    seed: int = 12345,
) -> SimulationResult:
    """Simula a Copa inteira N vezes para estimar probabilidades."""
    rng = np.random.default_rng(seed)
    spec = edition.spec.group_stage
    tb = spec.tiebreakers
    group_games = edition.group_fixtures()
    ko = edition.knockout_fixtures()
    third_slots = [(f.match_id, f.third_groups) for f in ko if f.away == "3rd"]
    played = _played_group_results(edition)

    champ: Counter[str] = Counter()
    advanced: Counter[str] = Counter()
    rank_counts: dict[str, dict[str, Counter]] = {g: defaultdict(Counter) for g in edition.groups}
    third_q: Counter[str] = Counter()

    for _ in range(n_sims):
        # 1) fase de grupos
        results_by_group: dict[str, dict] = {g: dict(played.get(g, {})) for g in edition.groups}
        for f in group_games:
            if f.played or f.group is None:
                continue
            results_by_group[f.group][(f.home, f.away)] = cache.sample(f.home, f.away, f.neutral, rng)

        winners, runners, thirds = {}, {}, []
        for g, teams in edition.groups.items():
            st = group_standings(teams, results_by_group[g], tb, rng)
            for pos, s in enumerate(st, 1):
                rank_counts[g][s.team][pos] += 1
            winners[g] = st[0].team
            runners[g] = st[1].team
            for s in st[:2]:
                advanced[s.team] += 1
            if spec.best_thirds and len(st) >= 3:
                thirds.append((g, st[2]))

        # melhores terceiros
        thirds.sort(key=lambda x: (-x[1].points, -x[1].gd, -x[1].gf, rng.random()))
        qual_thirds = thirds[: spec.best_thirds]
        for _, s in qual_thirds:
            third_q[s.team] += 1
        third_assign = _assign_thirds(third_slots, [g for g, _ in qual_thirds])
        third_team = {mid: {g: s.team for g, s in qual_thirds}[g] for mid, g in third_assign.items()}

        # 2) mata-mata
        champ_team = _simulate_knockout(ko, winners, runners, third_team, cache, rng)
        if champ_team:
            champ[champ_team] += 1

    total = float(n_sims)
    return SimulationResult(
        champion_prob={t: c / total for t, c in champ.items()},
        advance_prob={t: c / total for t, c in advanced.items()},
        rank_counts=rank_counts,
        third_qualify=third_q,
    )


def _resolve_slot(slot: str, winners, runners, third_team, ko_winner, ko_loser) -> str | None:
    if slot.startswith("W"):
        return ko_winner.get(int(slot[1:]))
    if slot.startswith("L"):
        return ko_loser.get(int(slot[1:]))
    if slot == "3rd":
        return None  # resolvido por match_id à parte
    pos, g = slot[0], slot[1:]
    return winners.get(g) if pos == "1" else runners.get(g)


def _resolve_pair(f, winners, runners, third_team, ko_winner, ko_loser) -> tuple[str | None, str | None]:
    """Resolve as duas seleções de um jogo de mata-mata a partir dos slots do fixture."""

    def one(slot: str) -> str | None:
        if slot == "3rd":
            return third_team.get(f.match_id)
        return _resolve_slot(slot, winners, runners, third_team, ko_winner, ko_loser)

    return one(f.home), one(f.away)


def _simulate_knockout(ko, winners, runners, third_team, cache, rng) -> str | None:
    ko_winner: dict[int, str] = {}
    ko_loser: dict[int, str] = {}
    champion = None
    for f in sorted(ko, key=lambda x: x.match_id):
        home, away = _resolve_pair(f, winners, runners, third_team, ko_winner, ko_loser)
        if home is None or away is None:
            continue
        hg, ag = f.home_goals, f.away_goals
        if hg is not None and ag is not None:  # resultado real
            if hg > ag:
                w, loser = home, away
            elif ag > hg:
                w, loser = away, home
            else:  # empate -> vencedor real do confronto (pênaltis)
                w = f.ko_outcome or home
                loser = away if w == home else home
        else:
            hg, ag = cache.sample(home, away, f.neutral, rng)
            if hg > ag:
                w, loser = home, away
            elif ag > hg:
                w, loser = away, home
            else:  # empate -> decide por probabilidade condicional
                ph, _, pa = outcome_probs_from_matrix(cache.matrix(home, away, f.neutral))
                cond = ph / (ph + pa) if (ph + pa) > 0 else 0.5
                w, loser = (home, away) if rng.random() < cond else (away, home)
        ko_winner[f.match_id] = w
        ko_loser[f.match_id] = loser
        if f.stage == "final":
            champion = w
    return champion


# ----------------------------------------------------- chaveamento determinístico
@dataclass
class ResolvedMatch:
    fixture: Fixture
    home: str | None  # None enquanto o slot não resolve (ex.: mata-mata ainda sem times)
    away: str | None


def deterministic_bracket(
    edition: Edition,
    sim: SimulationResult,
    cache: MatrixCache,
) -> list[ResolvedMatch]:
    """Monta o chaveamento do cenário mais provável a partir das contagens do Monte Carlo."""
    spec = edition.spec.group_stage
    # 1º/2º/3º mais prováveis de cada grupo (sem repetir time)
    winners, runners, thirds = {}, {}, {}
    for g, teams in edition.groups.items():
        rc = sim.rank_counts[g]
        winner = max(teams, key=lambda t: rc[t][1])
        runner = max((t for t in teams if t != winner), key=lambda t: rc[t][2])
        third = max((t for t in teams if t not in {winner, runner}), key=lambda t: rc[t][3])
        winners[g], runners[g], thirds[g] = winner, runner, third

    # 8 melhores terceiros pela frequência de classificação no Monte Carlo
    third_groups_ranked = sorted(edition.groups, key=lambda g: -sim.third_qualify.get(thirds[g], 0))[: spec.best_thirds]
    ko = edition.knockout_fixtures()
    third_slots = [(f.match_id, f.third_groups) for f in ko if f.away == "3rd"]
    third_assign = _assign_thirds(third_slots, third_groups_ranked)
    third_team = {mid: thirds[g] for mid, g in third_assign.items()}

    # resolve cada jogo do mata-mata na ordem, propagando vencedores previstos
    ko_winner: dict[int, str] = {}
    ko_loser: dict[int, str] = {}
    resolved: list[ResolvedMatch] = []
    for f in sorted(ko, key=lambda x: x.match_id):
        home, away = _resolve_pair(f, winners, runners, third_team, ko_winner, ko_loser)
        resolved.append(ResolvedMatch(fixture=f, home=home, away=away))
        # determina o avanço previsto (resultado real tem prioridade)
        if f.home_goals is not None and f.away_goals is not None:  # resultado real
            if f.home_goals > f.away_goals:
                w, loser = home, away
            elif f.away_goals > f.home_goals:
                w, loser = away, home
            else:
                w = f.ko_outcome or home
                loser = away if w == home else home
        elif home and away:
            mat = cache.matrix(home, away, f.neutral)
            ph, _, pa = outcome_probs_from_matrix(mat)
            cond = ph / (ph + pa) if (ph + pa) > 0 else 0.5
            p_adv_home = ph + outcome_probs_from_matrix(mat)[1] * cond
            w, loser = (home, away) if p_adv_home >= 0.5 else (away, home)
        else:
            w = loser = None
        if w is not None:
            ko_winner[f.match_id] = w
        if loser is not None:
            ko_loser[f.match_id] = loser
    return resolved
