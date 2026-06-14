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


def _require_columns(df: pd.DataFrame, expected: list[str], source: str) -> None:
    """Falha cedo e claro se a fonte mudar o schema (em vez de um KeyError críptico adiante)."""
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise DataSourceError(
            f"O CSV de {source} não tem as colunas esperadas (faltam: {', '.join(missing)}). "
            f"Recebidas: {', '.join(map(str, df.columns))}. A fonte pública pode ter mudado o formato."
        )


def _download_text(url: str, timeout: int, retries: int = 1) -> str:
    """Baixa o texto de uma URL, com 1 retry, traduzindo falha de rede em `NetworkError`."""
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


def normalize(df: pd.DataFrame, cutoff: str = DEFAULT_CUTOFF, played_only: bool = True) -> pd.DataFrame:
    """Filtra por data, opcionalmente só jogos disputados, e canoniza nomes/tipos."""
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
    return out[COLUMNS].reset_index(drop=True)


def fetch(
    urls: list[str] | None = None,
    cutoff: str = DEFAULT_CUTOFF,
    out_path: Path = HISTORICAL_CSV,
) -> Path:
    """Baixa, normaliza e grava a base histórica. Retorna o caminho do CSV salvo."""
    df = download_from_urls(urls or [DEFAULT_URL])
    norm = normalize(df, cutoff=cutoff, played_only=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    norm.to_csv(out_path, index=False)
    return out_path


def load_historical(path: Path = HISTORICAL_CSV) -> pd.DataFrame:
    """Carrega a base histórica salva (erro claro se ainda não foi baixada)."""
    if not path.exists():
        raise FileNotFoundError(f"Base histórica não encontrada em {path}. Rode `uv run worldcup fetch-data` primeiro.")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df
