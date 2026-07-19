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
from .consistency import check_prediction_consistency
from .fetch_data import load_historical
from .format_engine import MatrixCache, deterministic_bracket, monte_carlo
from .knockout import predict_knockout
from .model import DixonColesModel, FitConfig
from .scoring import Scorer, outcome_probs_from_matrix
from .teams import display

if TYPE_CHECKING:
    import numpy as np

    from .edition import Edition, Fixture

logger = logging.getLogger(__name__)


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


def build_training_frame(edition: Edition, historical: pd.DataFrame, boost: float | None = None) -> pd.DataFrame:
    """Histórico + jogos já disputados da edição (com peso alto) para o ajuste do modelo.

    `boost` é o peso dado a cada jogo disputado da edição; `None` (default) usa
    `edition.scoring.edition_boost` (ENG-42/44 — calibrado por `blend-track --boost-sweep`; a 2026
    usa 1.0, sem boost, após o sweep mostrar Brier crescente em boost). Passa-se explícito só no
    próprio sweep.

    Os jogos da edição corrente entram **uma única vez**, com `boost`. Se a base
    histórica já contém esses mesmos jogos (acontece quando `fetch-data` é rodado no meio da Copa —
    martj42 traz o torneio em andamento), eles são **removidos da base** antes do append, senão
    seriam contados em dobro (peso 1.0 na base + boost via fixtures → 7.0 efetivo), inflando o peso
    dos resultados recentes e distorcendo o ajuste. A chave de casamento é (data, {mandante,
    visitante}) — o resultado real da edição é sempre o do `fixtures.csv`.

    Os jogos de mata-mata guardam **slots** (`W73`, `2D`) em `home`/`away`, não seleções — então
    são resolvidos para os nomes reais via `resolve_live_bracket` (só resultados reais) antes de
    entrar. Sem isso escapariam do filtro `.isin(edition.teams)` e o KO só chegaria ao modelo pela
    base histórica (peso 1.0, refém da atualidade dela) — a subponderação do ENG-42.

    O placar que entra é o dos **90'** — dos **dois lados** da união. Da edição, via
    `Edition.score_90` (ENG-55); da base histórica, via `fetch_data.score_90` (ENG-54), que
    reconstrói o tempo normal a partir da lista de gols do martj42. Nos dois casos o consolidado
    inclui a prorrogação (J82 = `3×2`, mas `2×2` nos 90'; a final de 2022 = `3×3`, mas `2×2`), e o
    modelo estima taxas de gol de **90'** — a camada de ET do `knockout` reescala λ por 30/90, o que
    só é válido se λ for a taxa de 90'. Treinar com o consolidado infla o λ e, pior, **apaga
    empates** (um 1×1 decidido na ET vira "vitória"), suprimindo a taxa de empate que o modelo
    aprende.
    """
    from .fetch_data import score_90
    from .sync import resolve_live_bracket

    historical = score_90(historical)  # a base grava o consolidado; o ajuste treina nos 90' (ENG-54)
    b = edition.scoring.edition_boost if boost is None else boost
    ko_matchups = resolve_live_bracket(edition)  # {match_id: (mandante, visitante)} real dos KO disputados
    rows = []
    for f in edition.fixtures:
        score = edition.score_90(f)
        if score is not None:
            home, away = ko_matchups.get(f.match_id, (f.home, f.away))
            rows.append(
                {
                    "date": pd.Timestamp(f.date),
                    "home_team": home,
                    "away_team": away,
                    "home_score": score[0],
                    "away_score": score[1],
                    "tournament": "FIFA World Cup",
                    "neutral": f.neutral,
                    "weight_mult": b,
                }
            )
    if not rows:
        return historical
    extra = pd.DataFrame(rows)
    # grupo já vem com times reais; KO agora também (resolvido acima) — o filtro barra só slots órfãos
    extra = extra[extra["home_team"].isin(edition.teams) & extra["away_team"].isin(edition.teams)]
    base = _drop_edition_games(historical, extra)
    base["weight_mult"] = 1.0
    return pd.concat([base, extra], ignore_index=True)


def _drop_edition_games(historical: pd.DataFrame, edition_games: pd.DataFrame) -> pd.DataFrame:
    """Remove de `historical` os jogos que já entram via fixtures (evita double-count — ver acima).

    Casa por (data, par não-ordenado de seleções); o resultado autoritativo da edição é o do fixture.
    """
    if historical.empty or edition_games.empty:
        return historical.copy()

    def _key(dates: pd.Series, home: pd.Series, away: pd.Series) -> pd.Series:
        d = pd.to_datetime(dates).dt.strftime("%Y-%m-%d")
        pair = [frozenset((h, a)) for h, a in zip(home, away, strict=True)]
        return pd.Series(list(zip(d, pair, strict=True)), index=dates.index)

    edition_keys = set(_key(edition_games["date"], edition_games["home_team"], edition_games["away_team"]))
    base_keys = _key(historical["date"], historical["home_team"], historical["away_team"])
    return historical[~base_keys.isin(edition_keys)].copy()


def ingestion_gaps(edition: Edition) -> list[int]:
    """`match_id`s de jogos **disputados** que NÃO entram no ajuste do modelo (ENG-43).

    Um jogo disputado só alimenta o fit se, após resolver os slots de KO (`resolve_live_bracket`),
    **ambos** os times estão em `edition.teams` — o **mesmo critério** do filtro `.isin(edition.teams)`
    em `build_training_frame`. Se um KO disputado não resolve (slot órfão), ele é descartado do ajuste
    **em silêncio** — a staleness que motivou ENG-41/42 (o caminho de grupo funcionava, mascarando o
    de KO quebrado, por semanas). Vazio = base em dia. Barato: só resultados reais, sem histórico.
    """
    from .sync import resolve_live_bracket

    ko = resolve_live_bracket(edition)
    teams = set(edition.teams)
    return [
        f.match_id
        for f in edition.fixtures
        if f.played and not all(t in teams for t in ko.get(f.match_id, (f.home, f.away)))
    ]


@dataclass
class PredictionRun:
    rows: list[dict]
    champion_prob: dict[str, float]
    advance_prob: dict[str, float]
    edition: Edition
    n_sims: int = 0  # sims que geraram champion_prob — dimensiona o ±IC95 exibido (ENG-62)


def _ko_layer_text(kp, edition_home: str, edition_away: str) -> tuple[str, str]:
    """Texto dos palpites de prorrogação e pênaltis."""
    et = {"home": edition_home, "away": edition_away, "penalties": "Vai aos pênaltis"}[kp.extra_time]
    pen = edition_home if kp.penalty_winner == "home" else edition_away
    return et, pen


def _final_ko_layers(edition: Edition, f: Fixture, home: str | None, away: str | None) -> tuple[str, str, str]:
    """(prorrogação, pênaltis, avança) de um jogo de KO **já disputado**, dos resultados reais (ENG-30).

    `home`/`away` são os nomes reais (canônicos) das seleções, resolvidos pelo bracket — necessários
    porque o `fixture` guarda slots.

    O `fixtures.csv` grava o placar **consolidado** (com prorrogação); os 90' vêm de
    `Edition.score_90` — **fonte única** (ENG-55). Ler `home_goals`/`away_goals` cru aqui fazia um KO
    decidido por gol na ET (J82: `2×2` nos 90', `3×2` no consolidado) parecer decidido no tempo
    normal, e as camadas saíam `—`/`—` (ENG-58).

    Camadas: 90' decidido ⇒ `—`/`—`; empate nos 90' com gol na ET ⇒ vencedor da prorrogação (+ placar
    de 120'), pênaltis `—`; empate também aos 120' ⇒ "Vai aos pênaltis" + vencedor da disputa
    (`shootouts.csv`, ou o `ko_outcome` — quem avançou de um 120' empatado **é** quem venceu nos
    pênaltis), com o **placar da disputa** entre parênteses quando capturado (ENG-59; a fonte não o
    publica, então ele pode faltar — vencedor sem placar é válido). Sem nenhum dos dois ⇒ vazio (não
    afirmar desfecho sob latência da fonte). Todo placar sai na ordem **mandante × visitante**.

    `avança`: `ko_outcome` quando a fonte o traz; senão, quem fez mais gols (a fonte preenche
    `ko_outcome` de forma inconsistente em jogo de 90' — o bracket já deriva do placar, o display
    precisa fazer igual).
    """
    reg = edition.score_90(f)
    if reg is None or f.home_goals is None or f.away_goals is None:
        return "", "", display(f.ko_outcome) if f.ko_outcome else ""
    reg_home, reg_away = reg
    if reg_home != reg_away:
        winner = f.ko_outcome or (home if reg_home > reg_away else away)  # 90' decide
        return "—", "—", display(winner) if winner else ""
    # empate nos 90'
    avanca = display(f.ko_outcome) if f.ko_outcome else ""
    if (f.home_goals, f.away_goals) != (reg_home, reg_away):  # gol na prorrogação decidiu
        winner = f.ko_outcome or (home if f.home_goals > f.away_goals else away)
        et = f"{display(winner)} ({f.home_goals}x{f.away_goals})" if winner else ""
        return et, "—", avanca or (display(winner) if winner else "")
    pen_winner = edition.shootouts.get(f.match_id) or f.ko_outcome  # 120' empatado ⇒ pênaltis
    if pen_winner:
        pen = edition.shootout_scores.get(f.match_id)  # placar da disputa: opcional (ENG-59)
        pen_txt = f"{display(pen_winner)} ({pen[0]}x{pen[1]})" if pen else display(pen_winner)
        return "Vai aos pênaltis", pen_txt, avanca or display(pen_winner)
    return "", "", avanca  # desfecho ainda não capturado


def _max_ko_weight(edition: Edition) -> float:
    """Maior peso de fase entre os estágios de mata-mata da edição (alvo do modo pool_behind)."""
    stages = edition.spec.group_stage.knockout_stages
    return max((edition.scoring.weight(s) for s in stages), default=1.0)


def run(edition: Edition, n_sims: int = 5000, seed: int = 12345, pool_behind: str | None = None) -> PredictionRun:
    """Executa o pipeline completo e devolve as linhas de palpite dos 104 jogos.

    `pool_behind` (ENG-36/40): modo endgame de bolão — nos jogos de KO de peso **máximo** da
    edição (a final, no Equilíbrio gradual), o palpite diverge do pelotão: `"empate"` (default do
    flag; política dominante, ENG-39) empata os 90' com o melhor placar por E[pts]; `"zebra"`
    (ENG-36, superada) palpita o lado azarão nas 3 camadas. Nos demais jogos, nada muda. Use só
    quando estiver atrás no ranking (na frente o modo custa P(#1): `scripts/eng36_pool_sim.py`).
    """
    historical = load_historical()
    train = build_training_frame(edition, historical)
    model = DixonColesModel(FitConfig()).fit(train)
    scorer = Scorer(edition.scoring)
    cache = MatrixCache(model, edition.hosts)

    # Blend com odds de mercado (ENG-19): matriz do modelo × mercado nos jogos que têm odds. weight=0
    # ou sem odds ⇒ matriz do modelo intacta. Com totals no odds.csv, a taxa total de gols também é
    # ancorada no mercado (ENG-35); sem totals, blend só de 1×2.
    blend_weight = edition.scoring.blend_weight

    def _blend(home: str, away: str, fixture) -> np.ndarray:
        mat = cache.matrix(home, away, fixture.neutral)
        odds = edition.odds.get(fixture.match_id)
        if odds is not None and blend_weight > 0.0:
            return blend_matrix_with_odds(mat, odds, blend_weight, totals=edition.totals.get(fixture.match_id))
        return mat

    # ENG-51: as probabilidades de campeão (Monte Carlo) blendam os confrontos de KO **totalmente
    # determinados** que têm odds (via resolve_live_bracket) — a mesma estimativa do palpite. Jogos de
    # rodadas futuras variam de time a cada simulação e não têm como ancorar a odd ⇒ seguem no modelo.
    ko_blend: dict[tuple[str, str, bool], np.ndarray] = {}
    if blend_weight > 0.0:
        from .sync import resolve_live_bracket

        ko_by_id = {f.match_id: f for f in edition.knockout_fixtures()}
        for mid, (h, a) in resolve_live_bracket(edition).items():
            f = ko_by_id.get(mid)
            if f is not None and not f.played and edition.odds.get(mid) is not None:
                ko_blend[(h, a, f.neutral)] = _blend(h, a, f)

    sim = monte_carlo(edition, model, cache, n_sims=n_sims, seed=seed, ko_blend=ko_blend)

    # O **chaveamento** decide quem avança com a MESMA matriz blendada do palpite exibido (ENG-51):
    # senão o bracket (modelo puro) e o palpite (blend) podem escolher vencedores diferentes no mesmo
    # jogo, e o bracket se autocontradiz ("X avança a semi" mas "Y joga a final").
    bracket = {rm.fixture.match_id: rm for rm in deterministic_bracket(edition, sim, cache, matrix_fn=_blend)}

    blended_games = 0

    def _matrix(home: str, away: str, fixture) -> np.ndarray:
        nonlocal blended_games
        odds = edition.odds.get(fixture.match_id)
        if odds is not None and blend_weight > 0.0:
            blended_games += 1
        return _blend(home, away, fixture)

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
            # A coluna de placar é o slot de **90'** (é o que o bolão pontua): num KO decidido na ET,
            # o consolidado do `fixtures.csv` não serve — vem de `Edition.score_90` (ENG-55/58).
            real = edition.score_90(f) or (f.home_goals, f.away_goals)
            row["status"] = "FINAL"
            row["placar_real"] = f"{real[0]}x{real[1]}"
            row["palpite"] = row["placar_real"]
            if not f.is_group:  # KO disputado: mostra prorrogação/pênaltis/quem avançou reais (ENG-30)
                row["prorrogacao"], row["penaltis"], row["avanca"] = _final_ko_layers(edition, f, home, away)

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
                # ENG-36/40: divergência só no(s) estágio(s) de peso máximo (final) quando pool_behind
                max_weight = edition.scoring.weight(f.stage) >= _max_ko_weight(edition)
                mode = pool_behind if pool_behind and max_weight else None
                kp = predict_knockout(home, away, mat, scorer, pool_behind=mode)
                et, pen = _ko_layer_text(kp, display(home), display(away))
                # P_* = 1×2 do **90'** (como nos grupos), não mais P(avança) — uniformiza a semântica
                # e deixa o snapshot carregar o 1×2 do 90' que o `efficiency.py` precisa p/ pontuar a
                # base do palpite de 90' do KO a partir do snapshot real (ENG-46). O avanço fica em
                # `avanca` (nome). Colunas P_* de KO são CSV-only (não exibidas nem lidas no ramo KO).
                ph, pd_, pa = _pct_round(*outcome_probs_from_matrix(mat))
                row.update(
                    palpite=kp.scoreline,
                    P_mandante=f"{ph}%",
                    P_empate=f"{pd_}%",
                    P_visitante=f"{pa}%",
                    prorrogacao=et,
                    penaltis=pen,
                    avanca=display(kp.advancer),
                )
        rows.append(row)

    if blend_weight > 0.0:
        logger.info("blend com odds (peso %.2f) aplicado a %d jogo(s)", blend_weight, blended_games)

    # ENG-52: recusa emitir uma tabela auto-contraditória (ex.: bracket que diz "X avança a semi" mas
    # "Y joga a final"). É um bug de derivação, não um palpite — deve falhar alto, não sair no CSV.
    violations = check_prediction_consistency(edition, rows)
    if violations:
        raise ValueError("palpite incoerente (ENG-52):\n  " + "\n  ".join(violations))

    return PredictionRun(
        rows=rows,
        champion_prob=sim.champion_prob,
        advance_prob=sim.advance_prob,
        edition=edition,
        n_sims=sim.n_sims,
    )
