"""Validação do modelo numa Copa passada (backtest).

Treina o modelo só com jogos **anteriores** ao início da Copa-alvo e "palpita" todos os jogos
daquela Copa, somando os pontos do bolão (Sistema I) que o app teria feito. Compara estratégias
de risco diferentes — a seleção do placar usa o risco testado, mas os pontos são sempre concedidos
pela fórmula fiel (risk=0.5), como o app faria.

Além dos pontos e do **acerto de 1×2** (métricas de classificação, via argmax), mede a
**calibração probabilística** do modelo (ENG-18): se P(mandante)/P(empate)/P(visitante) batem com
as frequências reais. São coisas independentes — dá para acertar muito 1×2 com P(empate)
sistematicamente baixa. Métricas: **Brier multiclasse** (calibração+resolução num número) e
**curva de confiabilidade** da classe empate (a suspeita levantada na Copa 2026). A calibração é
propriedade do modelo, não da estratégia — independe de `risk`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pandas as pd

from .edition import ScoringConfig
from .fetch_data import load_historical
from .format_engine import MatrixCache
from .knockout import predict_knockout
from .model import DixonColesModel, FitConfig
from .scoring import Scorer, outcome_probs_from_matrix
from .teams import canonical

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np

    from .edition import Edition, Fixture

# Início aproximado de cada Copa (para cortar o treino antes do torneio).
_WORLD_CUP_START = {2010: "2010-06-11", 2014: "2014-06-12", 2018: "2018-06-14", 2022: "2022-11-20"}

# Anfitrião de cada Copa (nome canônico). O mando é aplicado como na produção, via MatrixCache:
# jogos não-neutros do país-sede recebem vantagem, mesmo quando a fonte lista o anfitrião como
# visitante. Sem isso, o backtest pontuava esses jogos diferente do caminho real do app.
_WORLD_CUP_HOSTS = {2010: ("South Africa",), 2014: ("Brazil",), 2018: ("Russia",), 2022: ("Qatar",)}


@dataclass
class ReliabilityBin:
    """Uma faixa da curva de confiabilidade: prob prevista média vs. frequência observada."""

    lo: float
    hi: float
    count: int
    mean_pred: float
    obs_freq: float


@dataclass
class BacktestResult:
    year: int
    n_matches: int
    by_risk: dict[float, dict[str, float]]
    # calibração (risk-independente): Brier multiclasse e confiabilidade da classe empate
    brier: float = 0.0
    reliability_draw: list[ReliabilityBin] = field(default_factory=list)
    n_penalty_shootouts: int = 0  # jogos de KO decididos nos pênaltis (bônus de KO computado — ENG-12)


def _outcome_index(home_score: int, away_score: int) -> int:
    """0 = vitória mandante, 1 = empate, 2 = vitória visitante (mesma ordem de `outcome_probs`)."""
    r = (home_score > away_score) - (home_score < away_score)
    return 0 if r > 0 else 1 if r == 0 else 2


def multiclass_brier(probs: Sequence[tuple[float, float, float]], outcomes: Sequence[int]) -> float:
    """Brier multiclasse médio: `mean_jogos Σ_k (p_k − 1{real==k})²` sobre (mandante, empate, visitante).

    0 = previsão determinística e correta; 2/3 ≈ 0,667 = palpite uniforme (1/3,1/3,1/3); 2 = pior
    caso (determinística e errada). Mais baixo é melhor.
    """
    if not probs:
        return 0.0
    total = 0.0
    for p, o in zip(probs, outcomes, strict=True):
        total += sum((p[k] - (1.0 if k == o else 0.0)) ** 2 for k in range(3))
    return total / len(probs)


def reliability_curve(pred_probs: Sequence[float], hits: Sequence[bool], n_bins: int = 10) -> list[ReliabilityBin]:
    """Curva de confiabilidade de uma classe: agrupa os jogos por prob prevista em `n_bins` faixas
    iguais de [0,1] e devolve só as faixas **não-vazias** com (prob média prevista, freq observada).

    Bem calibrado ⇒ `mean_pred ≈ obs_freq` em toda faixa. `hits[i]` é True quando aquela classe foi
    o resultado real do jogo `i`.
    """
    sums = [0.0] * n_bins  # soma das probs previstas na faixa
    obs = [0] * n_bins  # quantos jogos da faixa tiveram a classe como resultado
    cnt = [0] * n_bins
    for p, hit in zip(pred_probs, hits, strict=True):
        b = min(n_bins - 1, int(p * n_bins))  # p=1.0 cai na última faixa
        sums[b] += p
        obs[b] += 1 if hit else 0
        cnt[b] += 1
    out: list[ReliabilityBin] = []
    for b in range(n_bins):
        if cnt[b] == 0:
            continue
        out.append(
            ReliabilityBin(
                lo=b / n_bins,
                hi=(b + 1) / n_bins,
                count=cnt[b],
                mean_pred=sums[b] / cnt[b],
                obs_freq=obs[b] / cnt[b],
            )
        )
    return out


def _prepare(year: int, df: pd.DataFrame) -> tuple[DixonColesModel, MatrixCache, pd.DataFrame]:
    """Treina o modelo com jogos anteriores à Copa `year` e devolve (modelo, cache de mando, teste)."""
    start = _WORLD_CUP_START[year]
    train = df[df["date"] < pd.Timestamp(start)].copy()
    test = df[(df["tournament"] == "FIFA World Cup") & (df["date"].dt.year == year)].copy()
    if test.empty:
        raise ValueError(f"Nenhum jogo da Copa {year} no histórico (rode fetch-data?).")
    model = DixonColesModel(FitConfig()).fit(train, ref_date=pd.Timestamp(start))
    cache = MatrixCache(model, _WORLD_CUP_HOSTS.get(year, ()))
    return model, cache, test


def _calibration_inputs(cache: MatrixCache, test: pd.DataFrame) -> tuple[list[tuple[float, float, float]], list[int]]:
    """Probabilidades (mandante, empate, visitante) e índice do resultado real de cada jogo de teste.

    Base risk-independente da calibração — usada por `run_backtest` e pelo pooling entre Copas.
    """
    probs: list[tuple[float, float, float]] = []
    outcomes: list[int] = []
    for _, m in test.iterrows():
        mat = cache.matrix(canonical(m["home_team"]), canonical(m["away_team"]), bool(m["neutral"]))
        probs.append(outcome_probs_from_matrix(mat))
        outcomes.append(_outcome_index(int(m["home_score"]), int(m["away_score"])))
    return probs, outcomes


def run_backtest(year: int = 2022, risks: tuple[float, ...] = (0.0, 0.5, 1.0), n_sims: int = 0) -> BacktestResult:
    if year not in _WORLD_CUP_START:
        raise ValueError(f"Sem data de início cadastrada para {year}. Opções: {sorted(_WORLD_CUP_START)}")
    df = load_historical()
    _model, cache, test = _prepare(year, df)
    award = _award_scorer()

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
            pts += _knockout_bonus_for(m, mat, award)  # +pênaltis quando o jogo foi à disputa (ENG-12)
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

    # calibração (uma vez; não depende do risco)
    probs_all, outcomes_all = _calibration_inputs(cache, test)
    brier = multiclass_brier(probs_all, outcomes_all)
    reliability_draw = reliability_curve([p[1] for p in probs_all], [o == 1 for o in outcomes_all])

    # defensivo: bases/fixtures antigos podem não ter a coluna (load_historical real sempre tem)
    pen_col = test["penalty_winner"] if "penalty_winner" in test.columns else pd.Series("", index=test.index)
    n_pens = int((pen_col.astype(str).str.len() > 0).sum())
    result = BacktestResult(
        year=year,
        n_matches=len(test),
        by_risk=by_risk,
        brier=brier,
        reliability_draw=reliability_draw,
        n_penalty_shootouts=n_pens,
    )
    _print_report(result)
    return result


def pooled_draw_calibration(
    years: tuple[int, ...] = (2010, 2014, 2018, 2022),
) -> tuple[float, list[ReliabilityBin], int]:
    """Calibração agregada nas Copas dadas: (Brier multiclasse, curva de confiabilidade do empate,
    nº de jogos). Pooling dá faixas com mais jogos — base estatística para o veredito do ENG-18."""
    df = load_historical()
    all_probs: list[tuple[float, float, float]] = []
    all_outcomes: list[int] = []
    for year in years:
        _, cache, test = _prepare(year, df)
        probs, outcomes = _calibration_inputs(cache, test)
        all_probs.extend(probs)
        all_outcomes.extend(outcomes)
    brier = multiclass_brier(all_probs, all_outcomes)
    reliability = reliability_curve([p[1] for p in all_probs], [o == 1 for o in all_outcomes])
    return brier, reliability, len(all_probs)


@dataclass
class BlendTracking:
    """Tally prospectivo do blend vs. modelo-puro (Brier multiclasse) — Gate 3 do ENG-19.

    Os campos `*_total` medem o mercado de totals (ENG-35): Brier **binário** de P(over da linha)
    do modelo vs. da matriz blendada com totals, nos jogos disputados que têm o mercado registrado.
    `n_totals=0` ⇒ sem jogos com totals ainda (métrica silenciosa).
    """

    weight: float
    n: int
    brier_model: float
    brier_blend: float
    n_totals: int = 0
    brier_total_model: float = 0.0
    brier_total_blend: float = 0.0

    @property
    def delta(self) -> float:
        """Brier do modelo − Brier do blend. Positivo ⇒ blend melhor (Brier menor é melhor)."""
        return self.brier_model - self.brier_blend

    @property
    def delta_totals(self) -> float:
        """Brier do modelo − Brier do blend no over/under (ENG-35). Positivo ⇒ blend melhor."""
        return self.brier_total_model - self.brier_total_blend


def _as_of_group_matrices(edition: Edition, historical: pd.DataFrame, boost: float | None = None):
    """Itera `(fixture, matriz as-of)` dos jogos de grupo já disputados, reajustando o modelo por dia.

    Base comum dos diagnósticos da **edição viva** (blend — ENG-19; regime de empates — ENG-22): cada
    jogo usa o modelo ajustado só com o conhecido até a véspera (`Edition.as_of`), agrupando por data
    para 1 fit por dia (out-of-sample por construção). `boost` sobrescreve o peso dos jogos da edição
    no ajuste (calibração — ENG-44); `None` usa o default de `build_training_frame`.
    """
    from collections import defaultdict

    from .pipeline import build_training_frame

    by_date: dict[str, list] = defaultdict(list)
    for f in edition.fixtures:
        if f.is_group and f.played:
            by_date[f.date].append(f)
    for d in sorted(by_date):
        model = DixonColesModel(FitConfig()).fit(
            build_training_frame(edition.as_of(d), historical, boost=boost), ref_date=pd.Timestamp(d)
        )
        cache = MatrixCache(model, edition.hosts)
        for f in by_date[d]:
            yield f, cache.matrix(f.home, f.away, f.neutral)


@dataclass
class BoostTracking:
    """Brier out-of-sample do modelo (sem blend) para um valor de `edition_boost` (ENG-44)."""

    boost: float
    n: int
    brier_model: float


def boost_sweep(edition: Edition, boosts: Sequence[float]) -> list[BoostTracking]:
    """Brier as-of do modelo numa grade de `boost` — calibra `edition_boost` com dado (ENG-44).

    Para cada peso, reajusta as-of (1 fit/dia) e mede o Brier multiclasse 1×2 dos jogos de grupo
    disputados, prevendo cada um só com o conhecido até a véspera. Mede o **modelo puro** (sem blend):
    é o boost que se calibra, e o blend com mercado mascararia seu efeito. ⚠️ Só jogos de grupo (o KO
    tem placar com prorrogação — 1×2 ambíguo, mesma razão do `blend-track`); e o mínimo é in-sample
    da grade num n ainda pequeno — evidência direcional, não verdade fina.
    """
    from .fetch_data import load_historical
    from .scoring import outcome_probs_from_matrix

    historical = load_historical()
    out: list[BoostTracking] = []
    for b in boosts:
        probs: list[tuple[float, float, float]] = []
        outcomes: list[int] = []
        for f, matrix in _as_of_group_matrices(edition, historical, boost=b):
            probs.append(outcome_probs_from_matrix(matrix))
            outcomes.append(0 if f.home_goals > f.away_goals else (1 if f.home_goals == f.away_goals else 2))
        out.append(BoostTracking(boost=b, n=len(probs), brier_model=multiclass_brier(probs, outcomes)))
    return out


def _collect_blend_games(edition: Edition) -> list[tuple[Fixture, np.ndarray]]:
    """Jogos de grupo disputados com odds + matriz **as-of** (1 fit/dia) — base do report e do sweep.

    Só grupo: no mata-mata a convenção martj42 registra o placar **com prorrogação**, o que torna o
    desfecho de 90' (o que as odds 1×2 precificam) ambíguo em jogo decidido na ET — incluir esses
    jogos corromperia o Brier em silêncio.

    Sem odds na edição, nenhum jogo entra no blend ⇒ retorna cedo, **sem** carregar a base histórica
    (o report/sweep de blend não precisa dela quando não há mercado — e evita exigir o
    `historical_results.csv` gitignored onde ele não existe, p.ex. no CI).
    """
    if not edition.odds:
        return []
    return [
        (f, mat)
        for f, mat in _as_of_group_matrices(edition, load_historical())
        if f.match_id in edition.odds and f.home_goals is not None and f.away_goals is not None
    ]


def _tracking_for_weight(edition: Edition, games: list[tuple[Fixture, np.ndarray]], w: float) -> BlendTracking:
    """Tally de Brier (1×2 e totals) de um peso `w` sobre os jogos já coletados."""
    from .blend import blend_matrix_with_odds, devig, log_opinion_pool, prob_total_over

    model_probs: list[tuple[float, float, float]] = []
    blend_probs: list[tuple[float, float, float]] = []
    outcomes: list[int] = []
    # métrica de totals (ENG-35): Brier binário de P(over) — modelo vs blend com totals
    total_sq_model: list[float] = []
    total_sq_blend: list[float] = []
    for f, mat in games:
        hg, ag = f.home_goals, f.away_goals
        assert hg is not None  # garantido por _collect_blend_games
        assert ag is not None
        mp = outcome_probs_from_matrix(mat)
        model_probs.append(mp)
        blend_probs.append(log_opinion_pool(mp, devig(edition.odds[f.match_id]), w))
        outcomes.append(_outcome_index(hg, ag))
        totals = edition.totals.get(f.match_id)
        if totals is not None:
            line = totals[0]
            went_over = float(hg + ag > line)
            blended = blend_matrix_with_odds(mat, edition.odds[f.match_id], w, totals=totals)
            total_sq_model.append((prob_total_over(mat, line) - went_over) ** 2)
            total_sq_blend.append((prob_total_over(blended, line) - went_over) ** 2)

    n_totals = len(total_sq_model)
    return BlendTracking(
        weight=w,
        n=len(outcomes),
        brier_model=multiclass_brier(model_probs, outcomes),
        brier_blend=multiclass_brier(blend_probs, outcomes),
        n_totals=n_totals,
        brier_total_model=sum(total_sq_model) / n_totals if n_totals else 0.0,
        brier_total_blend=sum(total_sq_blend) / n_totals if n_totals else 0.0,
    )


def prospective_blend_report(edition: Edition, weight: float | None = None) -> BlendTracking:
    """Valida o blend prospectivamente nos jogos de grupo já disputados que têm odds (ENG-19, Gate 3).

    Compara o **Brier multiclasse** do modelo-puro vs. do blend(`weight`) com o resultado real, usando
    o modelo **as-of** de cada jogo (`_as_of_group_matrices`). Como `weight` é pré-registrado, é
    out-of-sample. Sem jogos-com-odds ⇒ tudo zero (registre odds em `odds.csv`).
    """
    w = edition.scoring.blend_weight if weight is None else weight
    if not any(f.is_group and f.played and f.match_id in edition.odds for f in edition.fixtures):
        return BlendTracking(weight=w, n=0, brier_model=0.0, brier_blend=0.0)
    return _tracking_for_weight(edition, _collect_blend_games(edition), w)


def blend_weight_sweep(edition: Edition, weights: Sequence[float]) -> list[BlendTracking]:
    """Brier do blend numa **grade de pesos** — escolhe `blend_weight` com dado, não com prior (ENG-38).

    Uma única passada as-of coleta as matrizes (o custo caro, 1 fit/dia); cada peso é só uma
    reavaliação do pool logarítmico. ⚠️ O w* minimiza o Brier **in-sample da grade** (n ainda
    pequeno): use como evidência direcional, não como verdade fina — degraus de 0,1 bastam.
    """
    games = _collect_blend_games(edition)
    if not games:
        return [BlendTracking(weight=w, n=0, brier_model=0.0, brier_blend=0.0) for w in weights]
    return [_tracking_for_weight(edition, games, w) for w in weights]


@dataclass
class DrawRegime:
    """Regime de empates da edição viva: observados vs. esperados pelo modelo, com z-score (ENG-22)."""

    n: int
    observed: int
    expected: float
    z: float

    @property
    def significant(self) -> bool:
        """|z| ≥ 2σ: o desvio deixa de ser explicável por variância — gatilho para abrir a correção."""
        return abs(self.z) >= 2.0


def draw_regime_stats(p_draws: Sequence[float], is_draw: Sequence[bool]) -> DrawRegime:
    """z-score do nº de empates: `(observado − Σp) / sqrt(Σ p(1−p))` — soma de Bernoulli (Poisson-binomial).

    Cada jogo é um Bernoulli com seu próprio P(empate); a média é `Σp` e a variância `Σ p(1−p)`.
    Positivo = mais empates que o modelo esperava. Mede regime vs. ruído, não calibra nada.
    """
    n = len(p_draws)
    observed = sum(is_draw)
    expected = float(sum(p_draws))
    var = sum(p * (1.0 - p) for p in p_draws)
    z = (observed - expected) / var**0.5 if var > 0 else 0.0
    return DrawRegime(n=n, observed=observed, expected=expected, z=z)


def draw_regime_report(edition: Edition) -> DrawRegime:
    """Aplica `draw_regime_stats` aos jogos de grupo já disputados (modelo as-of) — monitor do ENG-22.

    **Só medição**: um veredito `significant` (≥2σ) é o **gatilho** para abrir um item-filho de correção
    (tilt de empate), nunca para agir automático — forçar empates baixa os pontos esperados se o desvio
    for variância (ver ENG-18: o modelo é bem calibrado em empate no agregado).
    """
    if not any(f.is_group and f.played for f in edition.fixtures):
        return DrawRegime(n=0, observed=0, expected=0.0, z=0.0)
    p_draws: list[float] = []
    is_draw: list[bool] = []
    for f, mat in _as_of_group_matrices(edition, load_historical()):
        hg, ag = f.home_goals, f.away_goals
        if hg is None or ag is None:
            continue
        p_draws.append(outcome_probs_from_matrix(mat)[1])
        is_draw.append(hg == ag)
    return draw_regime_stats(p_draws, is_draw)


def _knockout_bonus_for(row: pd.Series, matrix, award: Scorer) -> float:
    """Bônus de prorrogação/pênaltis (Sistema I) de um jogo de KO decidido **nos pênaltis**.

    Só os jogos com `penalty_winner` (do `shootouts` mesclado em `fetch_data`) são determináveis da
    fonte: foram à disputa (`extra_time` real = "penalties") e sabemos o vencedor → concede o bônus de
    ida-aos-pênaltis (+3) e o de acerto do vencedor (+3). Jogos decididos **dentro** da prorrogação não
    são separáveis no martj42 (sem fase/flag de ET), então não recebem bônus aqui (limitação SPEC §9.2).
    """
    pen_winner = str(row.get("penalty_winner", "") or "")
    if not pen_winner:
        return 0.0
    home, away = canonical(row["home_team"]), canonical(row["away_team"])
    kp = predict_knockout(home, away, matrix, award)
    actual_pen = "home" if canonical(pen_winner) == home else "away"
    return award.knockout_bonus(kp.extra_time, kp.penalty_winner, "penalties", actual_pen)


def _award_scorer() -> Scorer:
    """Pontuação fiel (risk=0.5) usada para conceder pontos, independente da estratégia."""
    cfg = ScoringConfig(system="sistema_i", risk=0.5)
    return Scorer(cfg)


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
    if r.n_penalty_shootouts:
        print(f"({r.n_penalty_shootouts} jogo(s) decidido(s) nos pênaltis — bônus de KO incluído no total.)")

    # calibração do modelo (independe do risco)
    print(f"\n🎯 Calibração (modelo) — Brier multiclasse = {r.brier:.4f}  (0 = perfeito, 0,667 = uniforme)")
    if r.reliability_draw:
        print("   Confiabilidade do empate (prob prevista → freq observada):")
        print(f"   {'faixa':>11} | {'jogos':>5} | {'previsto':>8} | {'observado':>9}")
        for b in r.reliability_draw:
            print(
                f"   {int(b.lo * 100):>3}–{int(b.hi * 100):>3}% | {b.count:>5} | "
                f"{b.mean_pred * 100:>7.1f}% | {b.obs_freq * 100:>8.1f}%"
            )
