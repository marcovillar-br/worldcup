"""Validação do modelo numa Copa passada (backtest).

Treina o modelo só com jogos **anteriores** ao início da Copa-alvo e "palpita" todos os jogos
daquela Copa, somando os pontos do bolão (Sistema I) que o app teria feito. Compara estratégias
de risco diferentes — a seleção do placar usa o risco testado, mas os pontos são sempre concedidos
pela fórmula fiel (risk=0.5), como o app faria.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .edition import ScoringConfig
from .fetch_data import load_historical
from .format_engine import MatrixCache
from .model import DixonColesModel, FitConfig
from .scoring import Scorer, outcome_probs_from_matrix
from .teams import canonical

# Início aproximado de cada Copa (para cortar o treino antes do torneio).
_WORLD_CUP_START = {2010: "2010-06-11", 2014: "2014-06-12", 2018: "2018-06-14", 2022: "2022-11-20"}

# Anfitrião de cada Copa (nome canônico). O mando é aplicado como na produção, via MatrixCache:
# jogos não-neutros do país-sede recebem vantagem, mesmo quando a fonte lista o anfitrião como
# visitante. Sem isso, o backtest pontuava esses jogos diferente do caminho real do app.
_WORLD_CUP_HOSTS = {2010: ("South Africa",), 2014: ("Brazil",), 2018: ("Russia",), 2022: ("Qatar",)}


@dataclass
class BacktestResult:
    year: int
    n_matches: int
    by_risk: dict[float, dict[str, float]]


def _award_scorer() -> Scorer:
    """Pontuação fiel (risk=0.5) usada para conceder pontos, independente da estratégia."""
    cfg = ScoringConfig(system="sistema_i", risk=0.5)
    return Scorer(cfg)


def run_backtest(year: int = 2022, risks: tuple[float, ...] = (0.0, 0.5, 1.0), n_sims: int = 0) -> BacktestResult:
    if year not in _WORLD_CUP_START:
        raise ValueError(f"Sem data de início cadastrada para {year}. Opções: {sorted(_WORLD_CUP_START)}")
    start = _WORLD_CUP_START[year]
    df = load_historical()

    train = df[df["date"] < pd.Timestamp(start)].copy()
    test = df[(df["tournament"] == "FIFA World Cup") & (df["date"].dt.year == year)].copy()
    if test.empty:
        raise ValueError(f"Nenhum jogo da Copa {year} no histórico (rode fetch-data?).")

    model = DixonColesModel(FitConfig()).fit(train, ref_date=pd.Timestamp(start))
    award = _award_scorer()
    # mesma lógica de mando da produção (anfitrião joga em casa mesmo listado como visitante).
    cache = MatrixCache(model, _WORLD_CUP_HOSTS.get(year, ()))

    by_risk: dict[float, dict[str, float]] = {}
    for risk in risks:
        cfg = ScoringConfig(system="sistema_i", risk=risk)
        selector = Scorer(cfg)
        total = exact = correct = 0.0
        for _, m in test.iterrows():
            mat = cache.matrix(canonical(m["home_team"]), canonical(m["away_team"]), bool(m["neutral"]))
            pred = selector.best_prediction(mat)
            actual = (int(m["home_score"]), int(m["away_score"]))
            probs = outcome_probs_from_matrix(mat)
            pts = award.points((pred.home_goals, pred.away_goals), actual, probs)
            total += pts
            if (pred.home_goals, pred.away_goals) == actual:
                exact += 1
            ar = (actual[0] > actual[1]) - (actual[0] < actual[1])
            pr = (pred.home_goals > pred.away_goals) - (pred.home_goals < pred.away_goals)
            if ar == pr:
                correct += 1
        n = len(test)
        by_risk[risk] = {
            "total": total,
            "avg": total / n,
            "exact_pct": 100 * exact / n,
            "result_pct": 100 * correct / n,
        }

    result = BacktestResult(year=year, n_matches=len(test), by_risk=by_risk)
    _print_report(result)
    return result


def _print_report(r: BacktestResult) -> None:
    print(f"\n📊 Backtest Copa {r.year} — {r.n_matches} jogos (treino só com jogos anteriores)")
    print(f"{'risco':>6} | {'pts totais':>10} | {'média/jogo':>10} | {'% resultado':>11} | {'% placar exato':>14}")
    print("-" * 64)
    for risk, s in r.by_risk.items():
        print(
            f"{risk:>6.1f} | {s['total']:>10.1f} | {s['avg']:>10.2f} | "
            f"{s['result_pct']:>10.1f}% | {s['exact_pct']:>13.1f}%"
        )
    print("\n(% resultado = acertou vencedor/empate; % placar exato = cravou o placar.)")
