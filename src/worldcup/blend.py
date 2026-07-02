"""Blend das probabilidades do modelo com odds de mercado (ENG-19).

O modelo Dixon-Coles é puramente estatístico — cego a escalações, lesões, suspensões e motivação.
As **odds de fechamento** de uma casa de apostas incorporam essa informação e são um preditor
público bem calibrado. Este módulo combina as duas fontes em três passos puros:

  1. **des-vig** (`devig`): odds decimais → probabilidades implícitas, removendo a margem da casa
     (normalização multiplicativa/proporcional);
  2. **pool logarítmico de opiniões** (`log_opinion_pool`): média geométrica ponderada das duas
     triplas (mandante/empate/visitante), com peso `w∈[0,1]` (0 = só modelo, 1 = só mercado);
  3. **reescala da matriz** (`rescale_matrix`): ajusta a matriz de placares do modelo para bater as
     probabilidades-alvo de 1×2, **preservando** a forma condicional dos placares dentro de cada
     resultado — assim `best_prediction`/bônus de placar exato seguem funcionando.

`blend_matrix_with_odds` compõe os três. A ausência de odds para um jogo ⇒ a matriz volta intacta
(degradação graciosa): o blend nunca é obrigatório.

**Totals (ENG-35).** O rescale de 1×2 preserva a forma condicional — ou seja, os *gols esperados*
(onde vivem o exato +5 e o `winner_goals` +3 do Sistema I) ficavam 100% modelo. O mercado de
**over/under** corrige isso: `devig_pair` tira a margem do par over/under, `implied_total_rate`
inverte a linha para o λ-total implícito do mercado (Poisson), e o pool logarítmico de duas
Poissons é **exatamente** Poisson com taxa `λm^(1−w)·λq^w` (média geométrica — mesma família do
pool de 1×2). `tilt_matrix_to_total` aplica o alvo por *tilting exponencial* (`célula·c^(i+j)`),
que num produto de Poissons equivale a escalar as duas taxas por `c` — preserva a partição
mandante/visitante e a correlação DC. Como tilt e rescale de 1×2 interagem, `blend_matrix_with_odds`
itera os dois e termina no rescale (1×2 exato; total dentro de tolerância). Sem totals ⇒ caminho
antigo intacto.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import poisson

from .scoring import outcome_probs_from_matrix

# Probabilidades/massas abaixo disso são tratadas como zero protegido (evita log(0) e divisão por 0).
_EPS = 1e-12

Triple = tuple[float, float, float]
# Mercado de totals de um jogo: (linha de gols, odd decimal do over, odd decimal do under).
TotalsTriple = tuple[float, float, float]


def devig(odds: Triple) -> Triple:
    """Odds decimais (mandante, empate, visitante) → probabilidades implícitas sem a margem da casa.

    Probabilidade bruta de cada resultado = `1/odd`; a soma (overround) passa de 1 por causa da
    margem. Normaliza dividindo pela soma (des-vig **proporcional**, o baseline padrão).
    """
    if any(o <= 1.0 for o in odds):
        raise ValueError(f"odds decimais devem ser > 1.0, recebido {odds}")
    raw = [1.0 / o for o in odds]
    total = sum(raw)
    return (raw[0] / total, raw[1] / total, raw[2] / total)


def log_opinion_pool(model: Triple, market: Triple, weight: float) -> Triple:
    """Pool logarítmico (média geométrica ponderada) de duas triplas de probabilidade.

    `p_k ∝ model_k^(1−w) · market_k^w`, renormalizado. `weight=0` ⇒ idêntico ao modelo;
    `weight=1` ⇒ idêntico ao mercado. Mais estável que a média linear quando as fontes concordam
    (afia a massa) e é a forma canônica de combinar opiniões probabilísticas.
    """
    if not 0.0 <= weight <= 1.0:
        raise ValueError(f"weight deve estar em [0, 1], recebido {weight}")
    m = np.clip(np.asarray(model, dtype=float), _EPS, None)
    q = np.clip(np.asarray(market, dtype=float), _EPS, None)
    pooled = m ** (1.0 - weight) * q**weight
    pooled /= pooled.sum()
    return (float(pooled[0]), float(pooled[1]), float(pooled[2]))


def rescale_matrix(matrix: np.ndarray, target: Triple) -> np.ndarray:
    """Reescala a matriz de placares para que P(mandante/empate/visitante) batam `target`.

    Multiplica cada célula pelo fator `target_classe / massa_atual_da_classe`, por classe de
    resultado (vitória mandante = abaixo da diagonal, empate = diagonal, vitória visitante = acima).
    Preserva a **massa total** da matriz e a distribuição condicional dos placares dentro de cada
    classe (a razão entre dois placares de vitória do mandante não muda) — só desloca massa entre as
    três classes. `target` é renormalizado por segurança.
    """
    ph, pdr, pa = outcome_probs_from_matrix(matrix)
    total_mass = ph + pdr + pa
    if total_mass <= _EPS:
        return matrix.copy()
    tgt = np.asarray(target, dtype=float)
    tgt = tgt / tgt.sum()
    # massa-alvo de cada classe preservando a massa total da matriz
    target_mass = tgt * total_mass
    factor_home = target_mass[0] / max(ph, _EPS)
    factor_draw = target_mass[1] / max(pdr, _EPS)
    factor_away = target_mass[2] / max(pa, _EPS)

    n = matrix.shape[0]
    rows = np.arange(n)[:, None]
    cols = np.arange(n)[None, :]
    factors = np.where(rows > cols, factor_home, np.where(rows == cols, factor_draw, factor_away))
    return matrix * factors


def devig_pair(over: float, under: float) -> tuple[float, float]:
    """Odds decimais de over/under → probabilidades implícitas sem a margem (des-vig proporcional).

    Mesma normalização do `devig` de 1×2, em 2 vias. Linhas inteiras (push) e quarter-lines são
    tratadas como o limiar contínuo mais próximo — aproximação documentada (ver SPEC §8).
    """
    if over <= 1.0 or under <= 1.0:
        raise ValueError(f"odds decimais devem ser > 1.0, recebido ({over}, {under})")
    raw_over, raw_under = 1.0 / over, 1.0 / under
    total = raw_over + raw_under
    return raw_over / total, raw_under / total


def expected_total_goals(matrix: np.ndarray) -> float:
    """Gols totais esperados `E[i+j]` sob a matriz de placares (normalizada pela massa)."""
    n = matrix.shape[0]
    totals = np.arange(n)[:, None] + np.arange(n)[None, :]
    mass = matrix.sum()
    if mass <= _EPS:
        return 0.0
    return float((matrix * totals).sum() / mass)


def implied_total_rate(line: float, p_over: float) -> float:
    """λ-total implícito do mercado: resolve `P(Poisson(λ) > line) = p_over` por bissecção.

    `line` é a linha de gols (tipicamente x.5); `p_over` a probabilidade des-vigada do over.
    A função `λ ↦ P(T > line)` é estritamente crescente ⇒ raiz única.
    """
    if not 0.0 < p_over < 1.0:
        raise ValueError(f"p_over deve estar em (0, 1), recebido {p_over}")
    k = int(np.floor(line))  # P(T > line) = P(T ≥ k+1) = sf(k)
    lo, hi = 1e-6, 30.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if float(poisson.sf(k, mid)) < p_over:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def tilt_matrix_to_total(matrix: np.ndarray, target_total: float) -> np.ndarray:
    """Tilting exponencial da matriz para `E[gols totais] = target_total`: célula `(i,j)` × `c^(i+j)`.

    Num produto de Poissons, multiplicar por `c^(i+j)` equivale a escalar as duas taxas por `c` —
    preserva a razão mandante/visitante e a forma DC; só a taxa total muda. `c` sai por bissecção
    (E[total] é estritamente crescente em `c`). A massa total da matriz é preservada. O alvo é
    truncado ao máximo representável pela matriz (grade 0..n−1 por lado).
    """
    mass = matrix.sum()
    if mass <= _EPS:
        return matrix.copy()
    n = matrix.shape[0]
    totals = np.arange(n)[:, None] + np.arange(n)[None, :]
    max_total = float(2 * (n - 1))
    target = min(max(target_total, _EPS), max_total - 1e-9)

    def _expected(c: float) -> float:
        tilted = matrix * np.power(c, totals)
        return float((tilted * totals).sum() / tilted.sum())

    lo, hi = 1e-6, 1e6
    for _ in range(200):
        mid = np.sqrt(lo * hi)  # bissecção geométrica (c varia em ordens de magnitude)
        if _expected(mid) < target:
            lo = mid
        else:
            hi = mid
    c = np.sqrt(lo * hi)
    tilted = matrix * np.power(c, totals)
    return tilted * (mass / tilted.sum())


def prob_total_over(matrix: np.ndarray, line: float) -> float:
    """P(gols totais > `line`) sob a matriz (normalizada pela massa) — métrica do blend-track."""
    n = matrix.shape[0]
    totals = np.arange(n)[:, None] + np.arange(n)[None, :]
    mass = matrix.sum()
    if mass <= _EPS:
        return 0.0
    return float(matrix[totals > line].sum() / mass)


def blend_matrix_with_odds(
    matrix: np.ndarray, odds: Triple, weight: float, totals: TotalsTriple | None = None
) -> np.ndarray:
    """Compõe os passos: des-vig das odds → pool com as probs do modelo → reescala a matriz.

    Com `totals` (linha, over, under — ENG-35), também ancora a **taxa total de gols** no pool
    modelo×mercado: tilt exponencial ao λ combinado, iterado com o rescale de 1×2 (que fica exato
    por vir por último; o total converge em poucas iterações). `weight=0` devolve a matriz do
    modelo intacta (atalho — degradação graciosa também cobre odds ausentes, tratada por quem chama).
    """
    if weight <= 0.0:
        return matrix
    model_probs = outcome_probs_from_matrix(matrix)
    market_probs = devig(odds)
    blended = log_opinion_pool(model_probs, market_probs, weight)
    if totals is None:
        return rescale_matrix(matrix, blended)

    line, over, under = totals
    p_over, _p_under = devig_pair(over, under)
    lam_market = implied_total_rate(line, p_over)
    lam_model = expected_total_goals(matrix)
    # pool logarítmico de Poissons ⇒ Poisson com a média geométrica ponderada das taxas
    lam_target = max(lam_model, _EPS) ** (1.0 - weight) * lam_market**weight
    out = matrix
    for _ in range(3):
        out = tilt_matrix_to_total(out, lam_target)
        out = rescale_matrix(out, blended)
    return out
