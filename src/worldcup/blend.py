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
"""

from __future__ import annotations

import numpy as np

from .scoring import outcome_probs_from_matrix

# Probabilidades/massas abaixo disso são tratadas como zero protegido (evita log(0) e divisão por 0).
_EPS = 1e-12

Triple = tuple[float, float, float]


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


def blend_matrix_with_odds(matrix: np.ndarray, odds: Triple, weight: float) -> np.ndarray:
    """Compõe os três passos: des-vig das odds → pool com as probs do modelo → reescala a matriz.

    `weight=0` devolve a matriz do modelo intacta (atalho — degradação graciosa também cobre odds
    ausentes, tratada por quem chama).
    """
    if weight <= 0.0:
        return matrix
    model_probs = outcome_probs_from_matrix(matrix)
    market_probs = devig(odds)
    blended = log_opinion_pool(model_probs, market_probs, weight)
    return rescale_matrix(matrix, blended)
