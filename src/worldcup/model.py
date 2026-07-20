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
    halflife_years: float = 2.0  # meia-vida do decaimento temporal (tunado via backtest LOO, ENG-17)
    ridge: float = 0.10  # força do prior (shrinkage à média; tunado via backtest LOO, ENG-17)
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
        self.away_pen: float = 0.0  # supressão do visitante em jogo com mando (ENG-64)
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

        # vetor de parâmetros: [attack(n), defense(n), home_adv, away_pen, rho, base].
        # `away_pen` (ENG-64): o mando não só infla o mandante — suprime o visitante. Sem ele, o
        # modelo forçava o total dos jogos com mando para cima e o `base` compensava para baixo no
        # ajuste (dominado por jogos com mando), deprimindo o λ dos jogos neutros — quase toda a
        # Copa (residual +0,17 gol/jogo no neutro, -0,17 no mando; z=+6,3/-9,0 na janela 2014+).
        x0 = np.concatenate([np.zeros(n), np.zeros(n), [0.25, 0.1, 0.0, base0]])
        ridge = self.config.ridge
        logmx = np.log(self.config.max_xg)
        # máscaras de placar baixo usadas na correção Dixon–Coles (tau) e na sua derivada
        m00 = (hg == 0) & (ag == 0)
        m01 = (hg == 0) & (ag == 1)
        m10 = (hg == 1) & (ag == 0)
        m11 = (hg == 1) & (ag == 1)

        def _rates(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
            """λ/μ (pós-clip) e as máscaras da região não-clipada (onde dλ/dη = λ)."""
            att, dfn = x[:n], x[n : 2 * n]
            home_adv, away_pen, base = x[2 * n], x[2 * n + 1], x[2 * n + 3]
            eta_l = base + att[hi] - dfn[ai] + home_adv * home_flag
            eta_m = base + att[ai] - dfn[hi] - away_pen * home_flag
            lam = np.exp(np.clip(eta_l, -3, logmx))
            mu = np.exp(np.clip(eta_m, -3, logmx))
            unclipped_l = (eta_l > -3) & (eta_l < logmx)
            unclipped_m = (eta_m > -3) & (eta_m < logmx)
            return lam, mu, unclipped_l, unclipped_m

        def neg_ll(x: np.ndarray) -> float:
            att, dfn = x[:n], x[n : 2 * n]
            rho = x[2 * n + 2]
            lam, mu, _, _ = _rates(x)
            ll = hg * np.log(lam) - lam + ag * np.log(mu) - mu
            tau = _tau(hg, ag, lam, mu, rho)
            ll = ll + np.log(np.clip(tau, 1e-9, None))
            penalty = ridge * (np.sum(att**2) + np.sum(dfn**2))
            return -np.sum(weights * ll) + penalty

        def grad(x: np.ndarray) -> np.ndarray:
            """Gradiente analítico de neg_ll. Sem ele, o gradiente numérico custa ~2n
            avaliações por iteração e esgota o maxfun do scipy antes de convergir (ENG-16)."""
            att, dfn = x[:n], x[n : 2 * n]
            rho = x[2 * n + 2]
            lam, mu, unclipped_l, unclipped_m = _rates(x)
            tau = np.clip(_tau(hg, ag, lam, mu, rho), 1e-9, None)
            # derivadas de tau (não-nulas só nos placares baixos)
            dtau_dlam = np.where(m00, -mu * rho, np.where(m01, rho, 0.0))
            dtau_dmu = np.where(m00, -lam * rho, np.where(m10, rho, 0.0))
            dtau_drho = np.where(m00, -lam * mu, np.where(m01, lam, np.where(m10, mu, np.where(m11, -1.0, 0.0))))
            # d(ll)/d(eta) por jogo, já ponderado e mascarado na região clipada (onde dλ/dη = 0)
            g_l = weights * unclipped_l * ((hg - lam) + (lam / tau) * dtau_dlam)
            g_m = weights * unclipped_m * ((ag - mu) + (mu / tau) * dtau_dmu)
            g_rho = weights * (1.0 / tau) * dtau_drho
            g = np.zeros_like(x)
            np.add.at(g[:n], hi, -g_l)  # att entra em λ via mandante, em μ via visitante
            np.add.at(g[:n], ai, -g_m)
            np.add.at(g[n : 2 * n], ai, g_l)  # dfn entra com sinal negativo em λ/μ
            np.add.at(g[n : 2 * n], hi, g_m)
            g[2 * n] = -np.sum(g_l * home_flag)  # home_adv
            g[2 * n + 1] = np.sum(g_m * home_flag)  # away_pen (entra com sinal negativo em η_μ)
            g[2 * n + 2] = -np.sum(g_rho)  # rho
            g[2 * n + 3] = -np.sum(g_l + g_m)  # base
            g[:n] += 2 * ridge * att  # derivada do ridge
            g[n : 2 * n] += 2 * ridge * dfn
            return g

        bounds = [(-3, 3)] * (2 * n) + [(-1.0, 1.0), (-1.0, 1.0), (-0.2, 0.2), (-2.0, 2.0)]
        res = minimize(neg_ll, x0, jac=grad, method="L-BFGS-B", bounds=bounds, options={"maxiter": self.config.maxiter})

        if not res.success:
            # fit não-convergido gera forças ruins sem sinal; avisa (não interrompe — res.x é o
            # melhor ponto alcançado). Com o gradiente analítico (jac=grad) o fit converge bem
            # dentro de maxiter; um aviso aqui agora indica um problema real a investigar.
            logger.warning("ajuste do modelo não convergiu (maxiter=%d): %s", self.config.maxiter, res.message)
        if not np.all(np.isfinite(res.x)):
            logger.warning("ajuste do modelo produziu parâmetros não-finitos; previsões podem ser inválidas")

        x = res.x
        att = x[:n]
        att = att - att.mean()  # centra o ataque (identificabilidade)
        self.attack = att
        self.defense = x[n : 2 * n] - x[n : 2 * n].mean()
        self.home_adv = float(x[2 * n])
        self.away_pen = float(x[2 * n + 1])
        self.rho = float(x[2 * n + 2])
        self.base = float(x[2 * n + 3]) + x[:n].mean() - x[n : 2 * n].mean()
        return self

    # --------------------------------------------------------------- predição
    def _strength(self, team: str) -> tuple[float, float]:
        # Nome fora do ajuste levanta em vez de cair no "time médio" (ENG-57): a fallback
        # silenciosa transformava slot não resolvido (`L101`) ou typo em previsão plausível
        # e errada — a mesma classe de falha do ENG-48 (valor plausível, chamada silenciosa).
        i = self._idx.get(canonical(team))
        if i is None:
            raise KeyError(
                f"seleção desconhecida para o modelo: {team!r} não está em `model.teams` "
                "(slot de bracket não resolvido? typo no nome canônico? filtrada no ajuste?)"
            )
        return float(self.attack[i]), float(self.defense[i])

    def expected_goals(
        self, home: str, away: str, neutral: bool = True, host_away: bool = False
    ) -> tuple[float, float]:
        ah, dh = self._strength(home)
        aa, da = self._strength(away)
        adv = 0.0 if neutral else self.home_adv
        pen = 0.0 if neutral else self.away_pen
        # mando vai para o mandante (e a supressão ao visitante), salvo `host_away`: o visitante
        # (anfitrião) joga em casa — bônus e penalidade trocam de lado juntos (ENG-64).
        home_adj, away_adj = (-pen, adv) if host_away else (adv, -pen)
        lam = float(np.exp(np.clip(self.base + ah - da + home_adj, -3, np.log(self.config.max_xg))))
        mu = float(np.exp(np.clip(self.base + aa - dh + away_adj, -3, np.log(self.config.max_xg))))
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
