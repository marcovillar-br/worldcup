"""Pipeline: do histórico aos 104 palpites de uma edição.

Orquestra: ajustar o modelo (com realimentação dos jogos já disputados da Copa) → simular
(Monte Carlo + chaveamento determinístico) → gerar o palpite de cada jogo (placar para a fase de
grupos; 3 camadas para o mata-mata). Retorna linhas prontas para CSV e a tabela em Markdown.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pandas as pd

from .blend import blend_matrix_with_odds
from .fetch_data import load_historical
from .format_engine import MatrixCache, deterministic_bracket, monte_carlo
from .knockout import predict_knockout
from .model import DixonColesModel, FitConfig
from .scoring import Scorer
from .teams import display

if TYPE_CHECKING:
    import numpy as np

    from .edition import Edition

logger = logging.getLogger(__name__)

# Peso extra dado aos jogos já disputados da própria Copa (realimentação).
CURRENT_EDITION_BOOST = 6.0


def _pct_round(*probs: float) -> list[int]:
    """Arredonda probabilidades (0..1) para inteiros que somam exatamente 100.

    Método do maior resto (Hamilton): evita que mandante/empate/visitante somem 99 ou 101
    por arredondamentos independentes.
    """
    total = sum(probs) or 1.0
    scaled = [p / total * 100 for p in probs]  # normaliza (matriz truncada pode não somar 1)
    floors = [int(x) for x in scaled]
    remainder = 100 - sum(floors)
    # distribui as unidades que faltam para as maiores partes fracionárias
    order = sorted(range(len(scaled)), key=lambda i: scaled[i] - floors[i], reverse=True)
    for i in order[:remainder]:
        floors[i] += 1
    return floors


def build_training_frame(edition: Edition, historical: pd.DataFrame) -> pd.DataFrame:
    """Histórico + jogos já disputados da edição (com peso alto) para o ajuste do modelo."""
    rows = []
    for f in edition.fixtures:
        if f.played:
            rows.append(
                {
                    "date": pd.Timestamp(f.date),
                    "home_team": f.home,
                    "away_team": f.away,
                    "home_score": f.home_goals,
                    "away_score": f.away_goals,
                    "tournament": "FIFA World Cup",
                    "neutral": f.neutral,
                    "weight_mult": CURRENT_EDITION_BOOST,
                }
            )
    if not rows:
        return historical
    extra = pd.DataFrame(rows)
    # só faz sentido somar jogos de grupo (times reais); KO com nomes reais também vale
    extra = extra[extra["home_team"].isin(edition.teams) & extra["away_team"].isin(edition.teams)]
    base = historical.copy()
    base["weight_mult"] = 1.0
    return pd.concat([base, extra], ignore_index=True)


@dataclass
class PredictionRun:
    rows: list[dict]
    champion_prob: dict[str, float]
    advance_prob: dict[str, float]
    edition: Edition


def _ko_layer_text(kp, edition_home: str, edition_away: str) -> tuple[str, str]:
    """Texto dos palpites de prorrogação e pênaltis."""
    et = {"home": edition_home, "away": edition_away, "penalties": "Vai aos pênaltis"}[kp.extra_time]
    pen = edition_home if kp.penalty_winner == "home" else edition_away
    return et, pen


def _final_ko_layers(f, shootouts: dict[int, str]) -> tuple[str, str, str]:
    """(prorrogação, pênaltis, avança) de um jogo de KO **já disputado**, dos resultados reais (ENG-30).

    `avança` vem sempre do `ko_outcome` (classificado real). O desfecho prorrogação/pênaltis: placar dos
    90' decidido ⇒ "—"; empate nos 90' + shootout conhecido (fonte ou `shootouts.csv`) ⇒ "Vai aos
    pênaltis" + vencedor; empate nos 90' sem shootout conhecido ⇒ vazio (não afirmar prorrogação sob
    incerteza/latência da fonte).
    """
    avanca = display(f.ko_outcome) if f.ko_outcome else ""
    if f.home_goals is None or f.away_goals is None:
        return "", "", avanca
    if f.home_goals != f.away_goals:
        return "—", "—", avanca  # decidido nos 90'
    pen_winner = shootouts.get(f.match_id)
    if pen_winner:
        return "Vai aos pênaltis", display(pen_winner), avanca
    return "", "", avanca  # empate nos 90', desfecho ET/pênaltis ainda não capturado


def run(edition: Edition, n_sims: int = 5000, seed: int = 12345) -> PredictionRun:
    """Executa o pipeline completo e devolve as linhas de palpite dos 104 jogos."""
    historical = load_historical()
    train = build_training_frame(edition, historical)
    model = DixonColesModel(FitConfig()).fit(train)
    scorer = Scorer(edition.scoring)
    cache = MatrixCache(model, edition.hosts)

    sim = monte_carlo(edition, model, cache, n_sims=n_sims, seed=seed)
    bracket = {rm.fixture.match_id: rm for rm in deterministic_bracket(edition, sim, cache)}

    # Blend com odds de mercado (ENG-19): aplicado só na geração do palpite dos jogos que têm odds;
    # a simulação de campeão/avanço segue só com o modelo (odds em geral só existem para a rodada
    # iminente). weight=0 ou sem odds ⇒ matriz do modelo intacta.
    blend_weight = edition.scoring.blend_weight
    blended_games = 0

    def _matrix(home: str, away: str, fixture) -> np.ndarray:
        nonlocal blended_games
        mat = cache.matrix(home, away, fixture.neutral)
        odds = edition.odds.get(fixture.match_id)
        if odds is not None and blend_weight > 0.0:
            blended_games += 1
            return blend_matrix_with_odds(mat, odds, blend_weight)
        return mat

    rows: list[dict] = []
    for f in sorted(edition.fixtures, key=lambda x: x.match_id):
        home: str | None
        away: str | None
        if f.is_group:
            home, away = f.home, f.away
        else:
            rm = bracket[f.match_id]
            home, away = rm.home, rm.away

        row = {
            "jogo": f.match_id,
            "data": f.date,
            "fase": f.stage,
            "grupo": f.group or "",
            "mandante": display(home) if home else "?",
            "visitante": display(away) if away else "?",
            "palpite": "",
            "P_mandante": "",
            "P_empate": "",
            "P_visitante": "",
            "ousado": "",
            "mais_provavel": "",
            "prorrogacao": "",
            "penaltis": "",
            "avanca": "",
            "status": "PREVISTO",
            "placar_real": "",
        }

        if f.played:
            row["status"] = "FINAL"
            row["placar_real"] = f"{f.home_goals}x{f.away_goals}"
            row["palpite"] = f"{f.home_goals}x{f.away_goals}"
            if not f.is_group:  # KO disputado: mostra prorrogação/pênaltis/quem avançou reais (ENG-30)
                row["prorrogacao"], row["penaltis"], row["avanca"] = _final_ko_layers(f, edition.shootouts)

        if home and away and not f.played:
            mat = _matrix(home, away, f)
            if f.is_group:
                p = scorer.best_prediction(mat)
                ph, pd_, pa = _pct_round(p.p_home, p.p_draw, p.p_away)
                row.update(
                    palpite=p.scoreline,
                    P_mandante=f"{ph}%",
                    P_empate=f"{pd_}%",
                    P_visitante=f"{pa}%",
                    ousado="⚡" if p.is_upset else "",
                    mais_provavel=p.modal_scoreline,
                )
            else:
                kp = predict_knockout(home, away, mat, scorer)
                et, pen = _ko_layer_text(kp, display(home), display(away))
                row.update(
                    palpite=kp.scoreline,
                    P_mandante=f"{kp.p_advance_home * 100:.0f}%",  # P(mandante avança)
                    prorrogacao=et,
                    penaltis=pen,
                    avanca=display(kp.advancer),
                )
        rows.append(row)

    if blend_weight > 0.0:
        logger.info("blend com odds (peso %.2f) aplicado a %d jogo(s)", blend_weight, blended_games)

    return PredictionRun(
        rows=rows,
        champion_prob=sim.champion_prob,
        advance_prob=sim.advance_prob,
        edition=edition,
    )
