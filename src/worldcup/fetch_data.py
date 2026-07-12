"""Download e normalização da base histórica de jogos internacionais.

Fonte primária: dataset público `martj42/international_results` (resultados de seleções desde 1872).
`download_from_urls()` tenta cada URL em ordem, caindo para a próxima em caso de `NetworkError` ou
`DataSourceError`. Use `fetch(urls=[...])` ou a flag `--source-url` da CLI para configurar fontes
alternativas quando a primária estiver atrasada ou fora do ar.
"""

from __future__ import annotations

import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from .teams import canonical

logger = logging.getLogger(__name__)


class NetworkError(Exception):
    """Falha ao baixar dados da fonte pública (sem conexão, timeout ou fonte fora do ar)."""


class DataSourceError(Exception):
    """A fonte respondeu, mas o CSV não tem as colunas esperadas (schema mudou?)."""


DEFAULT_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
SHOOTOUTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv"
GOALSCORERS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/goalscorers.csv"
DEFAULT_CUTOFF = "2006-01-01"

# Diretórios padrão do projeto (data/ ao lado da raiz do repositório).
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORICAL_CSV = DATA_DIR / "historical_results.csv"

COLUMNS = ["date", "home_team", "away_team", "home_score", "away_score", "tournament", "neutral"]
SHOOTOUT_COLUMNS = ["date", "home_team", "away_team", "winner"]
GOALSCORER_COLUMNS = ["date", "home_team", "away_team", "team", "minute"]

# Fim do tempo normal. O martj42 **achata o acréscimo no minuto 90** (o minuto 90 tem ~2.000 gols
# contra ~700 nos vizinhos, e 91–96 despencam para 4–17), então `minute > 90` é prorrogação de
# verdade — não um gol de acréscimo dos 90'. É essa convenção que torna o ENG-54 resolúvel.
REGULATION_MINUTE = 90

# Saída persistida = colunas da fonte + pênaltis + o placar dos 90' (ENG-54).
# `penalty_winner` != "" marca um jogo decidido nos pênaltis e diz quem venceu (ENG-12).
# `reg_home_score`/`reg_away_score` = placar no fim do **tempo normal**, reconstruído do
# `goalscorers.csv` (ver `regulation_scores`). `home_score`/`away_score` seguem sendo o placar
# **consolidado** da fonte (inclui prorrogação) — o `sync` precisa dele para preencher o
# `fixtures.csv`. Quem quer os 90' passa por `score_90()`, nunca lê `reg_*` na mão.
OUTPUT_COLUMNS = [*COLUMNS, "penalty_winner", "reg_home_score", "reg_away_score"]


def _require_columns(df: pd.DataFrame, expected: list[str], source: str) -> None:
    """Falha cedo e claro se a fonte mudar o schema (em vez de um KeyError críptico adiante)."""
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise DataSourceError(
            f"O CSV de {source} não tem as colunas esperadas (faltam: {', '.join(missing)}). "
            f"Recebidas: {', '.join(map(str, df.columns))}. A fonte pública pode ter mudado o formato."
        )


def _download_text(url: str, timeout: int, retries: int = 1) -> str:
    """Baixa o texto de uma URL, com 1 retry, traduzindo falha de rede em `NetworkError`.

    Só aceita `http`/`https`: bloqueia `file://` (leitura de arquivo local), `ftp://` e afins que o
    `urllib` suporta — a URL vem da flag `--source-url` (ver `cli`), então restringir o esquema é
    defesa em profundidade contra apontar o downloader para um recurso não-HTTP.
    """
    scheme = urllib.parse.urlparse(url).scheme.lower()
    if scheme not in ("http", "https"):
        raise NetworkError(f"Esquema de URL não suportado: {scheme or '(vazio)'!r} em {url}. Use http/https.")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 worldcup"})
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as err:
            last_err = err
            if attempt < retries:
                time.sleep(1)
    raise NetworkError(
        f"Não foi possível baixar {url} ({last_err}). Verifique sua conexão e tente novamente em instantes."
    ) from last_err


def download_raw(url: str = DEFAULT_URL, timeout: int = 60) -> pd.DataFrame:
    """Baixa o CSV bruto da fonte e retorna como DataFrame (inclui jogos futuros)."""
    df = pd.read_csv(StringIO(_download_text(url, timeout)))
    _require_columns(df, COLUMNS, "resultados")
    return df


def download_from_urls(urls: list[str], timeout: int = 60) -> pd.DataFrame:
    """Tenta cada URL em ordem; retorna o primeiro DataFrame válido.

    Cai para a próxima fonte em caso de `NetworkError` ou `DataSourceError`.
    Relança o último erro se todas falharem.
    """
    last_err: Exception = NetworkError("Nenhuma URL fornecida")
    for i, url in enumerate(urls):
        try:
            df = download_raw(url, timeout)
            if i > 0:
                logger.info("Usando fonte alternativa: %s", url)
            return df
        except (NetworkError, DataSourceError) as err:
            last_err = err
            if i < len(urls) - 1:
                logger.warning("Fonte %s falhou (%s); tentando próxima...", url, err)
    raise last_err


def download_shootouts(url: str = SHOOTOUTS_URL, timeout: int = 60) -> pd.DataFrame:
    """Baixa o CSV de disputas de pênaltis (date, home_team, away_team, winner)."""
    df = pd.read_csv(StringIO(_download_text(url, timeout)))
    _require_columns(df, SHOOTOUT_COLUMNS, "pênaltis")
    return df


def download_goalscorers(url: str = GOALSCORERS_URL, timeout: int = 60) -> pd.DataFrame:
    """Baixa o CSV de gols (date, home_team, away_team, team, scorer, minute, own_goal, penalty)."""
    df = pd.read_csv(StringIO(_download_text(url, timeout)))
    _require_columns(df, GOALSCORER_COLUMNS, "gols")
    return df


def normalize(
    df: pd.DataFrame,
    cutoff: str = DEFAULT_CUTOFF,
    played_only: bool = True,
    shootouts: pd.DataFrame | None = None,
    goalscorers: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Filtra por data, opcionalmente só jogos disputados, canoniza nomes/tipos e mescla pênaltis/90'.

    Com `shootouts` (schema `SHOOTOUT_COLUMNS`), adiciona a coluna `penalty_winner` (nome canônico do
    vencedor da disputa, ou `""` se o jogo não foi a pênaltis), casando por `(date, home, away)`.
    Com `goalscorers` (schema `GOALSCORER_COLUMNS`), adiciona `reg_home_score`/`reg_away_score` — o
    placar dos **90'** (ver `regulation_scores`); sem eles, os 90' caem no placar consolidado.
    """
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out[out["date"] >= pd.Timestamp(cutoff)]
    if played_only:
        out = out.dropna(subset=["home_score", "away_score"])
    out["home_team"] = out["home_team"].map(canonical)
    out["away_team"] = out["away_team"].map(canonical)
    out["neutral"] = out["neutral"].astype(str).str.upper().eq("TRUE")
    if played_only:
        out["home_score"] = out["home_score"].astype(int)
        out["away_score"] = out["away_score"].astype(int)
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out["penalty_winner"] = _merge_penalty_winner(out, shootouts)
    out["reg_home_score"], out["reg_away_score"] = regulation_scores(out, goalscorers)
    return out[OUTPUT_COLUMNS].reset_index(drop=True)


def regulation_scores(games: pd.DataFrame, goalscorers: pd.DataFrame | None) -> tuple[pd.Series, pd.Series]:
    """Placar dos **90'** de cada jogo de `games`, reconstruído da lista de gols (ENG-54).

    A fonte grava o placar **consolidado** (com prorrogação): a final de 2022 aparece `3×3` (foi
    `2×2` nos 90') e Croácia×Brasil `1×1` (foi `0×0`). Mas o modelo estima taxas de gol de 90' — e a
    camada de ET do `knockout` reescala λ por 30/90, o que só vale se λ for de 90' — enquanto o bolão
    pontua o slot de 90' contra o tempo normal. Treinar/pontuar no consolidado infla o λ e, pior,
    **apaga empates** (um 1×1 decidido na ET vira "vitória").

    Reconstrução: 90' = todos os gols do jogo **menos** os de `minute > REGULATION_MINUTE`.

    **Portão de confiança.** Só reconstrói quando a lista de gols do jogo **bate exatamente** com o
    placar consolidado (soma por lado) e nenhum gol tem minuto ilegível. Uma lista incompleta
    subtrairia gols que não existem e inventaria empates — pior que o viés que se quer corrigir.
    Jogo que não passa no portão mantém o consolidado (é o status quo, nunca uma regressão): a fonte
    não cobre amistosos, mas amistoso não tem prorrogação, então a lacuna é inofensiva onde importa.
    """
    home, away = games["home_score"].copy(), games["away_score"].copy()
    if goalscorers is None or goalscorers.empty or games.empty:
        return home, away

    g = goalscorers.copy()
    g["date"] = pd.to_datetime(g["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ("home_team", "away_team", "team"):
        g[col] = g[col].map(canonical)
    g["minute"] = pd.to_numeric(g["minute"], errors="coerce")
    scored_home, scored_away = g["team"].eq(g["home_team"]), g["team"].eq(g["away_team"])
    in_90 = g["minute"].le(REGULATION_MINUTE)

    key = ["date", "home_team", "away_team"]
    tally = (
        g[key]
        .assign(
            _tot_h=scored_home.astype(int),
            _tot_a=scored_away.astype(int),
            _reg_h=(scored_home & in_90).astype(int),
            _reg_a=(scored_away & in_90).astype(int),
            # minuto ilegível ⇒ não dá para saber se o gol foi na ET ⇒ o jogo inteiro fica de fora
            _unknown=g["minute"].isna().astype(int),
        )
        .groupby(key, as_index=False)
        .sum()
    )
    # `tally` é único por chave ⇒ o merge preserva 1:1 as linhas de `games` (não infla).
    t = games[key].merge(tally, on=key, how="left").fillna(0)
    # jogo sem gol algum (0×0) não aparece no goalscorers ⇒ tally 0×0 == placar ⇒ passa no portão
    trusted = (
        (t["_tot_h"].to_numpy() == home.to_numpy())
        & (t["_tot_a"].to_numpy() == away.to_numpy())
        & (t["_unknown"].to_numpy() == 0)
    )
    reg_h = np.where(trusted, t["_reg_h"].to_numpy(), home.to_numpy())
    reg_a = np.where(trusted, t["_reg_a"].to_numpy(), away.to_numpy())
    # o dtype segue o do placar consolidado (não `int` fixo): com `played_only=False` o placar de um
    # jogo não disputado é NaN, que não cabe num int. Um NaN nunca passa no portão (NaN != placar),
    # então o jogo cai no consolidado — e o NaN precisa sobreviver ao retorno.
    return (
        pd.Series(reg_h, index=games.index).astype(home.dtype),
        pd.Series(reg_a, index=games.index).astype(away.dtype),
    )


def score_90(historical: pd.DataFrame) -> pd.DataFrame:
    """Cópia da base **como o bolão a vê**: placar dos 90' + o desfecho real da prorrogação (ENG-54).

    **Fonte única da verdade sobre "o que aconteceu nos 90'" na base histórica** — o gêmeo de
    `Edition.score_90` (ENG-55) para os jogos que vêm de fora da edição. Quem estima taxas de gol de
    90' (o **ajuste**) ou pontua os slots do bolão (o **backtest**) passa por aqui; quem precisa do
    placar consolidado (o `sync`, que preenche o `fixtures.csv`) usa a base crua. Ninguém lê
    `reg_home_score` na mão — a semântica mora nesta função, não espalhada pelos consumidores
    (a lição do ENG-48).

    Devolve duas coisas de uma vez, e **de propósito**: `home_score`/`away_score` viram os 90', e a
    coluna `et_outcome` guarda o desfecho do slot de prorrogação. Separar as duas viraria uma
    armadilha de ordem — `et_outcome` precisa do placar consolidado, que este mesmo passo sobrescreve.

    Base antiga/sintética sem as colunas `reg_*` ⇒ devolve o consolidado, `et_outcome` vazio
    (nenhuma correção conhecida).
    """
    out = historical.copy()
    if "reg_home_score" not in out.columns or "reg_away_score" not in out.columns:
        out["et_outcome"] = ""
        return out
    out["et_outcome"] = extra_time_outcome(out)
    out["home_score"] = out["reg_home_score"].astype(int)
    out["away_score"] = out["reg_away_score"].astype(int)
    return out


def extra_time_outcome(games: pd.DataFrame) -> pd.Series:
    """Desfecho **real** do slot de prorrogação do bolão, por jogo (ENG-54).

    `"penalties"` (foi à disputa), `"home"`/`"away"` (um lado venceu **dentro** da prorrogação) ou
    `""` (decidido nos 90', ou indeterminável). Espera a base **crua** — precisa do consolidado.

    Um jogo decidido na ET é exatamente aquele que **empatou nos 90'** e terminou **decidido** no
    consolidado, sem ter ido a pênaltis. Antes da reconstrução dos 90' esses jogos eram invisíveis
    (a fonte não traz fase nem flag de ET), e o backtest não conseguia creditar o bônus de
    prorrogação neles — só nos de pênaltis (a limitação que o ENG-12 registrou).
    """
    if games.empty:
        return pd.Series([], dtype=str)
    pens = games.get("penalty_winner", pd.Series("", index=games.index)).astype(str).fillna("")
    reg_h, reg_a = games["reg_home_score"], games["reg_away_score"]
    full_h, full_a = games["home_score"], games["away_score"]
    drew_in_90 = reg_h.eq(reg_a)
    et_winner = np.where(full_h > full_a, "home", "away")
    decided_in_et = drew_in_90 & full_h.ne(full_a) & pens.eq("")
    return pd.Series(
        np.where(pens.ne(""), "penalties", np.where(decided_in_et, et_winner, "")),
        index=games.index,
        dtype=object,
    )


def _merge_penalty_winner(games: pd.DataFrame, shootouts: pd.DataFrame | None) -> pd.Series:
    """Série `penalty_winner` (canônico, ou `""`) alinhada a `games`, casando por (date, home, away)."""
    if shootouts is None or shootouts.empty:
        return pd.Series([""] * len(games), index=games.index)
    sh = shootouts.copy()
    sh["date"] = pd.to_datetime(sh["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ("home_team", "away_team", "winner"):
        sh[col] = sh[col].map(canonical)
    key = ["date", "home_team", "away_team"]
    merged = games[key].merge(sh[[*key, "winner"]].drop_duplicates(key), on=key, how="left")
    return pd.Series(merged["winner"].fillna("").to_numpy(), index=games.index)


def fetch(
    urls: list[str] | None = None,
    cutoff: str = DEFAULT_CUTOFF,
    out_path: Path = HISTORICAL_CSV,
) -> Path:
    """Baixa, normaliza e grava a base (resultados + pênaltis + 90'). Retorna o caminho salvo."""
    df = download_from_urls(urls or [DEFAULT_URL])
    shootouts = _try_download_shootouts()
    goalscorers = _try_download_goalscorers()
    norm = normalize(df, cutoff=cutoff, played_only=True, shootouts=shootouts, goalscorers=goalscorers)
    et = int(((norm["reg_home_score"] != norm["home_score"]) | (norm["reg_away_score"] != norm["away_score"])).sum())
    logger.info("Placar dos 90' reconstruído: %d jogo(s) com gol na prorrogação corrigido(s) (ENG-54).", et)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    norm.to_csv(out_path, index=False)
    return out_path


def _try_download_shootouts() -> pd.DataFrame | None:
    """Baixa os pênaltis; se falhar (rede/schema), segue sem eles (`penalty_winner` fica vazio)."""
    try:
        return download_shootouts()
    except (NetworkError, DataSourceError) as err:
        logger.warning("Pênaltis indisponíveis (%s); seguindo sem 'penalty_winner'.", err)
        return None


def _try_download_goalscorers() -> pd.DataFrame | None:
    """Baixa a lista de gols; se falhar, segue sem ela — os 90' caem no consolidado (status quo)."""
    try:
        return download_goalscorers()
    except (NetworkError, DataSourceError) as err:
        logger.warning("Lista de gols indisponível (%s); o placar dos 90' cai no consolidado.", err)
        return None


def load_historical(path: Path = HISTORICAL_CSV) -> pd.DataFrame:
    """Carrega a base histórica salva (erro claro se ainda não foi baixada).

    Garante as colunas derivadas mesmo em bases geradas por versões antigas — quem quer os 90' chama
    `score_90()`, que assim nunca precisa lidar com a ausência delas.
    """
    if not path.exists():
        raise FileNotFoundError(f"Base histórica não encontrada em {path}. Rode `uv run worldcup fetch-data` primeiro.")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    if "penalty_winner" not in df.columns:  # compat: base gerada antes do merge de pênaltis (ENG-12)
        df["penalty_winner"] = ""
    df["penalty_winner"] = df["penalty_winner"].fillna("")
    for col, src in (("reg_home_score", "home_score"), ("reg_away_score", "away_score")):
        if col not in df.columns:  # compat: base gerada antes da reconstrução dos 90' (ENG-54)
            df[col] = df[src]
        df[col] = df[col].fillna(df[src]).astype(int)
    return df
