"""Modelo Dixon–Coles ponderado para prever placares de futebol.

Cada seleção tem força de **ataque** e **defesa**; há um termo de **mando** (só quando o jogo
não é em campo neutro) e a correção **Dixon–Coles** (rho) para placares baixos. A verossimilhança
é ponderada por **decaimento temporal** (jogos antigos pesam menos) e pela **importância do
torneio** (Copa > eliminatórias > amistoso). Uma regularização (ridge) funciona como prior fraco:
seleções com poucos jogos regridem à média, evitando estimativas absurdas para estreantes.

A saída principal é `score_matrix(home, away, neutral)`: a matriz de probabilidade de cada placar.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

from .teams import canonical

logger = logging.getLogger(__name__)

# Peso por tipo de torneio (importância na estimativa de força).
_TOURNAMENT_WEIGHTS = {
    "FIFA World Cup": 1.0,
    "Copa América": 0.85,
    "UEFA Euro": 0.85,
    "African Cup of Nations": 0.8,
    "AFC Asian Cup": 0.8,
    "Gold Cup": 0.7,
    "UEFA Nations League": 0.75,
    "Confederations Cup": 0.8,
    "Friendly": 0.5,
}
_DEFAULT_TOURNAMENT_WEIGHT = 0.7


def tournament_weight(name: str) -> float:
    """Peso de importância de um torneio (eliminatórias herdam ~0.8 da competição-mãe)."""
    if name in _TOURNAMENT_WEIGHTS:
        return _TOURNAMENT_WEIGHTS[name]
    if "qualification" in name.lower() or "qualifier" in name.lower():
        return 0.8
    return _DEFAULT_TOURNAMENT_WEIGHT


@dataclass
class FitConfig:
    halflife_years: float = 2.5  # meia-vida do decaimento temporal
    ridge: float = 0.05  # força do prior (shrinkage à média)
    max_goals: int = 10  # alcance da matriz de placares
    max_xg: float = 6.0  # teto de gols esperados por time (estabilidade numérica)
    min_matches: int = 10  # ignora seleções com menos jogos no período (ruído não-FIFA)
    maxiter: int = 500  # teto de iterações do otimizador (L-BFGS-B)


class DixonColesModel:
    """Modelo de força de seleções estimado por máxima verossimilhança ponderada."""

    def __init__(self, config: FitConfig | None = None) -> None:
        self.config = config or FitConfig()
        self.teams: list[str] = []
        self._idx: dict[str, int] = {}
        self.attack: np.ndarray = np.array([])
        self.defense: np.ndarray = np.array([])
        self.home_adv: float = 0.0
        self.rho: float = 0.0
        self.base: float = 0.0  # intercepto (média de gols em escala log)

    # ------------------------------------------------------------------ fit
    def fit(self, matches: pd.DataFrame, ref_date: pd.Timestamp | None = None) -> DixonColesModel:
        """Ajusta o modelo a partir de um DataFrame de jogos disputados.

        Colunas esperadas: date, home_team, away_team, home_score, away_score, tournament,
        neutral. Coluna opcional `weight_mult` multiplica o peso de jogos específicos
        (usada na realimentação para dar peso alto aos jogos já disputados da Copa).
        """
        df = matches.copy()
        df["home_team"] = df["home_team"].map(canonical)
        df["away_team"] = df["away_team"].map(canonical)
        if ref_date is None:
            ref_date = pd.to_datetime(df["date"]).max()

        # mantém só seleções que disputam competições oficiais (eliminatórias/continentais/Copa).
        # Isso remove microsseleções e times não-FIFA (CONIFA, ilhas) que jogam circuitos isolados
        # e poluiriam a estimativa de força.
        is_major = df["tournament"].map(lambda n: tournament_weight(n) >= 0.75 or "qualif" in n.lower())
        competitive = set(df.loc[is_major, "home_team"]) | set(df.loc[is_major, "away_team"])
        counts = pd.concat([df["home_team"], df["away_team"]]).value_counts()
        keep = competitive & set(counts[counts >= self.config.min_matches].index)
        all_teams = set(df["home_team"]) | set(df["away_team"])
        dropped = all_teams - keep
        if dropped:
            logger.info(
                "min_matches=%d/filtro de competitividade descartou %d seleções: %s",
                self.config.min_matches,
                len(dropped),
                ", ".join(sorted(dropped)[:15]) + (" …" if len(dropped) > 15 else ""),
            )
        df = df[df["home_team"].isin(keep) & df["away_team"].isin(keep)].reset_index(drop=True)

        teams = sorted(set(df["home_team"]) | set(df["away_team"]))
        self.teams = teams
        self._idx = {t: i for i, t in enumerate(teams)}
        n = len(teams)

        hi = df["home_team"].map(self._idx).to_numpy()
        ai = df["away_team"].map(self._idx).to_numpy()
        hg = df["home_score"].to_numpy(dtype=float)
        ag = df["away_score"].to_numpy(dtype=float)
        home_flag = (~df["neutral"].to_numpy(dtype=bool)).astype(float)  # 1 = tem mando

        age_years = (ref_date - pd.to_datetime(df["date"])).dt.days.to_numpy() / 365.25
        decay = 0.5 ** (age_years / self.config.halflife_years)
        timp = df["tournament"].map(tournament_weight).to_numpy(dtype=float)
        wmult = df["weight_mult"].to_numpy(dtype=float) if "weight_mult" in df else np.ones(len(df))
        weights = decay * timp * wmult

        base0 = float(np.log(max(df[["home_score", "away_score"]].to_numpy().mean(), 0.3)))

        # vetor de parâmetros: [attack(n), defense(n), home_adv, rho, base]
        x0 = np.concatenate([np.zeros(n), np.zeros(n), [0.25, 0.0, base0]])
        ridge = self.config.ridge

        def neg_ll(x: np.ndarray) -> float:
            att = x[:n]
            dfn = x[n : 2 * n]
            home_adv, rho, base = x[2 * n], x[2 * n + 1], x[2 * n + 2]
            lam = np.exp(np.clip(base + att[hi] - dfn[ai] + home_adv * home_flag, -3, np.log(self.config.max_xg)))
            mu = np.exp(np.clip(base + att[ai] - dfn[hi], -3, np.log(self.config.max_xg)))
            ll = hg * np.log(lam) - lam + ag * np.log(mu) - mu
            tau = _tau(hg, ag, lam, mu, rho)
            ll = ll + np.log(np.clip(tau, 1e-9, None))
            penalty = ridge * (np.sum(att**2) + np.sum(dfn**2))
            return -np.sum(weights * ll) + penalty

        bounds = [(-3, 3)] * (2 * n) + [(-1.0, 1.0), (-0.2, 0.2), (-2.0, 2.0)]
        res = minimize(neg_ll, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": self.config.maxiter})

        if not res.success:
            # fit não-convergido gera forças ruins sem sinal; avisa (não interrompe — res.x é o
            # melhor ponto alcançado). Considerar subir maxiter quando a base crescer.
            logger.warning("ajuste do modelo não convergiu (maxiter=%d): %s", self.config.maxiter, res.message)
        if not np.all(np.isfinite(res.x)):
            logger.warning("ajuste do modelo produziu parâmetros não-finitos; previsões podem ser inválidas")

        x = res.x
        att = x[:n]
        att = att - att.mean()  # centra o ataque (identificabilidade)
        self.attack = att
        self.defense = x[n : 2 * n] - x[n : 2 * n].mean()
        self.home_adv = float(x[2 * n])
        self.rho = float(x[2 * n + 1])
        self.base = float(x[2 * n + 2]) + x[:n].mean() - x[n : 2 * n].mean()
        return self

    # --------------------------------------------------------------- predição
    def _strength(self, team: str) -> tuple[float, float]:
        i = self._idx.get(canonical(team))
        if i is None:  # seleção sem histórico no período -> média
            return 0.0, 0.0
        return float(self.attack[i]), float(self.defense[i])

    def expected_goals(
        self, home: str, away: str, neutral: bool = True, host_away: bool = False
    ) -> tuple[float, float]:
        ah, dh = self._strength(home)
        aa, da = self._strength(away)
        adv = 0.0 if neutral else self.home_adv
        # mando vai para o mandante, salvo `host_away`: o visitante (anfitrião) joga em casa.
        home_adv, away_adv = (0.0, adv) if host_away else (adv, 0.0)
        lam = float(np.exp(np.clip(self.base + ah - da + home_adv, -3, np.log(self.config.max_xg))))
        mu = float(np.exp(np.clip(self.base + aa - dh + away_adv, -3, np.log(self.config.max_xg))))
        return lam, mu

    def score_matrix(
        self, home: str, away: str, neutral: bool = True, max_goals: int | None = None, host_away: bool = False
    ) -> np.ndarray:
        """Matriz P[i, j] = probabilidade de placar i (mandante) x j (visitante)."""
        mg = max_goals or self.config.max_goals
        lam, mu = self.expected_goals(home, away, neutral, host_away)
        gh = poisson.pmf(np.arange(mg + 1), lam)
        ga = poisson.pmf(np.arange(mg + 1), mu)
        mat = np.outer(gh, ga)
        # correção Dixon–Coles nos placares baixos
        mat[0, 0] *= 1 - lam * mu * self.rho
        mat[0, 1] *= 1 + lam * self.rho
        mat[1, 0] *= 1 + mu * self.rho
        mat[1, 1] *= 1 - self.rho
        mat = np.clip(mat, 0, None)
        return mat / mat.sum()

    def outcome_probs(
        self, home: str, away: str, neutral: bool = True, host_away: bool = False
    ) -> tuple[float, float, float]:
        """(P(vitória mandante), P(empate), P(vitória visitante))."""
        m = self.score_matrix(home, away, neutral, host_away=host_away)
        p_home = float(np.tril(m, -1).sum())
        p_draw = float(np.trace(m))
        p_away = float(np.triu(m, 1).sum())
        return p_home, p_draw, p_away


def _tau(x: np.ndarray, y: np.ndarray, lam: np.ndarray, mu: np.ndarray, rho: float) -> np.ndarray:
    """Correção Dixon–Coles para dependência em placares baixos (vetorizada)."""
    t = np.ones_like(lam, dtype=float)
    m00 = (x == 0) & (y == 0)
    m01 = (x == 0) & (y == 1)
    m10 = (x == 1) & (y == 0)
    m11 = (x == 1) & (y == 1)
    t = np.where(m00, 1 - lam * mu * rho, t)
    t = np.where(m01, 1 + lam * rho, t)
    t = np.where(m10, 1 + mu * rho, t)
    return np.where(m11, 1 - rho, t)
