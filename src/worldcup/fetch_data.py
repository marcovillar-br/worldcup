"""Download e normalização da base histórica de jogos internacionais.

Fonte: dataset público `martj42/international_results` (resultados de seleções desde 1872).
Salvamos apenas jogos **já disputados** a partir de um corte de data, com os nomes de
seleção canonizados, em `data/historical_results.csv`.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd

from .teams import canonical

DEFAULT_URL = (
    "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
)
SHOOTOUTS_URL = (
    "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv"
)
DEFAULT_CUTOFF = "2006-01-01"

# Diretórios padrão do projeto (data/ ao lado da raiz do repositório).
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORICAL_CSV = DATA_DIR / "historical_results.csv"

COLUMNS = ["date", "home_team", "away_team", "home_score", "away_score", "tournament", "neutral"]


def download_raw(url: str = DEFAULT_URL, timeout: int = 60) -> pd.DataFrame:
    """Baixa o CSV bruto da fonte e retorna como DataFrame (inclui jogos futuros)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 worldcup"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (URL fixa confiável)
        raw = resp.read().decode("utf-8")
    from io import StringIO

    return pd.read_csv(StringIO(raw))


def download_shootouts(url: str = SHOOTOUTS_URL, timeout: int = 60) -> pd.DataFrame:
    """Baixa o CSV de disputas de pênaltis (date, home_team, away_team, winner)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 worldcup"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (URL fixa confiável)
        raw = resp.read().decode("utf-8")
    from io import StringIO

    return pd.read_csv(StringIO(raw))


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
    url: str = DEFAULT_URL,
    cutoff: str = DEFAULT_CUTOFF,
    out_path: Path = HISTORICAL_CSV,
) -> Path:
    """Baixa, normaliza e grava a base histórica. Retorna o caminho do CSV salvo."""
    df = download_raw(url)
    norm = normalize(df, cutoff=cutoff, played_only=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    norm.to_csv(out_path, index=False)
    return out_path


def load_historical(path: Path = HISTORICAL_CSV) -> pd.DataFrame:
    """Carrega a base histórica salva (erro claro se ainda não foi baixada)."""
    if not path.exists():
        raise FileNotFoundError(
            f"Base histórica não encontrada em {path}. Rode `uv run worldcup fetch-data` primeiro."
        )
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df
