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

import pandas as pd

from .teams import canonical

logger = logging.getLogger(__name__)


class NetworkError(Exception):
    """Falha ao baixar dados da fonte pública (sem conexão, timeout ou fonte fora do ar)."""


class DataSourceError(Exception):
    """A fonte respondeu, mas o CSV não tem as colunas esperadas (schema mudou?)."""


DEFAULT_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
SHOOTOUTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv"
DEFAULT_CUTOFF = "2006-01-01"

# Diretórios padrão do projeto (data/ ao lado da raiz do repositório).
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORICAL_CSV = DATA_DIR / "historical_results.csv"

COLUMNS = ["date", "home_team", "away_team", "home_score", "away_score", "tournament", "neutral"]
SHOOTOUT_COLUMNS = ["date", "home_team", "away_team", "winner"]
# Saída persistida = colunas da fonte + o vencedor de pênaltis (mesclado do shootouts.csv).
# `penalty_winner` != "" marca um jogo decidido nos pênaltis (necessariamente mata-mata) e diz quem
# venceu — único desfecho de prorrogação/pênaltis **determinável** da fonte (martj42 não traz a fase
# nem separa 90' de prorrogação; ver ENG-12 e docs/SPEC.md §9.2). Usado pelo backtest p/ os bônus de KO.
OUTPUT_COLUMNS = [*COLUMNS, "penalty_winner"]


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


def normalize(
    df: pd.DataFrame,
    cutoff: str = DEFAULT_CUTOFF,
    played_only: bool = True,
    shootouts: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Filtra por data, opcionalmente só jogos disputados, canoniza nomes/tipos e mescla pênaltis.

    Com `shootouts` (schema `SHOOTOUT_COLUMNS`), adiciona a coluna `penalty_winner` (nome canônico do
    vencedor da disputa, ou `""` se o jogo não foi a pênaltis), casando por `(date, home, away)`.
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
    return out[OUTPUT_COLUMNS].reset_index(drop=True)


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
    """Baixa, normaliza e grava a base histórica (resultados + pênaltis). Retorna o caminho salvo."""
    df = download_from_urls(urls or [DEFAULT_URL])
    shootouts = _try_download_shootouts()
    norm = normalize(df, cutoff=cutoff, played_only=True, shootouts=shootouts)
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


def load_historical(path: Path = HISTORICAL_CSV) -> pd.DataFrame:
    """Carrega a base histórica salva (erro claro se ainda não foi baixada)."""
    if not path.exists():
        raise FileNotFoundError(f"Base histórica não encontrada em {path}. Rode `uv run worldcup fetch-data` primeiro.")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    if "penalty_winner" not in df.columns:  # compat: base gerada antes do merge de pênaltis (ENG-12)
        df["penalty_winner"] = ""
    df["penalty_winner"] = df["penalty_winner"].fillna("")
    return df
