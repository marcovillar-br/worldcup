#!/usr/bin/env python3
"""Busca odds 1X2 da The Odds API e MESCLA em data/editions/<ed>/odds.csv (ENG-19).

Rotina por rodada do blend com odds (ver BOLAO.md). Faz:
  1. lê a chave `ODDS_API_KEY` (do ambiente ou do `.env` na raiz);
  2. baixa as odds h2h (decimal) da Copa (`soccer_fifa_world_cup`);
  3. casa cada evento com um jogo de grupo **ainda não disputado** do fixture (por nomes canônicos);
  4. extrai a odd da **Pinnacle** (casa sharp; mediana das casas como fallback);
  5. **MESCLA** no `odds.csv` existente — atualiza/adiciona os jogos atuais e **preserva** os que
     saíram da lista (já disputados): senão o `blend-track` perderia o tally acumulado.

Uso: `uv run python scripts/fetch_odds.py [--edition 2026] [--region eu]`.
Roda no venv (importa `worldcup`). Não commita a chave (vive no `.env`, gitignored).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import urllib.error
import urllib.request
from pathlib import Path

from worldcup.edition import EDITIONS_DIR, Edition, load_edition
from worldcup.teams import canonical

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPORT = "soccer_fifa_world_cup"
API_URL = "https://api.the-odds-api.com/v4/sports/{sport}/odds/"

Triple = tuple[float, float, float]


def load_api_key() -> str:
    """Chave da The Odds API: do ambiente `ODDS_API_KEY` ou da linha correspondente no `.env`."""
    key = os.environ.get("ODDS_API_KEY")
    if key:
        return key
    env = PROJECT_ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("ODDS_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip()
    raise SystemExit("❌ ODDS_API_KEY não encontrada (defina no ambiente ou no .env).")


def merge_odds(existing: dict[int, Triple], fetched: dict[int, Triple]) -> dict[int, Triple]:
    """Mescla preservando o histórico: `fetched` atualiza/adiciona; jogos só em `existing`
    (já disputados, fora da lista da API) **são mantidos** — base do tally acumulado do blend-track."""
    return {**existing, **fetched}


def read_existing(path: Path) -> dict[int, Triple]:
    if not path.exists():
        return {}
    out: dict[int, Triple] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            cells = [(row.get(k) or "").strip() for k in ("home", "draw", "away")]
            if all(cells):
                out[int(row["match_id"])] = (float(cells[0]), float(cells[1]), float(cells[2]))
    return out


def write_odds(path: Path, odds: dict[int, Triple]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["match_id", "home", "draw", "away"])
        for mid in sorted(odds):
            w.writerow([mid, *odds[mid]])


def fetch_events(api_key: str, region: str) -> tuple[list[dict], str]:
    """Eventos com odds da Copa + créditos restantes (header da API)."""
    params = f"?apiKey={api_key}&regions={region}&markets=h2h&oddsFormat=decimal"
    url = API_URL.format(sport=SPORT) + params
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            remaining = resp.headers.get("x-requests-remaining", "?")
            return json.load(resp), remaining
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        raise SystemExit(f"❌ The Odds API HTTP {err.code}: {body}") from err
    except urllib.error.URLError as err:
        raise SystemExit(f"❌ Falha de rede ao buscar odds: {err.reason}") from err


def _book_price_map(event: dict, book: str) -> dict[str, float] | None:
    """Odds h2h de uma casa específica como {nome_canônico|'Draw': preço}; None se ausente."""
    bk = next((b for b in event["bookmakers"] if b["key"] == book), None)
    if not bk:
        return None
    mkt = next((m for m in bk["markets"] if m["key"] == "h2h"), None)
    if not mkt:
        return None
    return {("Draw" if o["name"] == "Draw" else canonical(o["name"])): float(o["price"]) for o in mkt["outcomes"]}


def _median_price_map(event: dict) -> dict[str, list[float]]:
    """Acumula preços de todas as casas por resultado (para a mediana de fallback)."""
    acc: dict[str, list[float]] = {}
    for b in event["bookmakers"]:
        mkt = next((m for m in b["markets"] if m["key"] == "h2h"), None)
        if not mkt:
            continue
        for o in mkt["outcomes"]:
            key = "Draw" if o["name"] == "Draw" else canonical(o["name"])
            acc.setdefault(key, []).append(float(o["price"]))
    return acc


def map_to_fixtures(events: list[dict], edition: Edition, book: str) -> tuple[dict[int, Triple], int, list[str]]:
    """Casa eventos→jogos de grupo não disputados; alinha odds à ordem home/away do fixture.

    Devolve (odds por match_id, nº via fallback de mediana, lista de pulados com motivo).
    """
    unplayed = {frozenset((f.home, f.away)): f for f in edition.fixtures if f.is_group and not f.played}
    odds: dict[int, Triple] = {}
    fallback = 0
    skipped: list[str] = []
    for ev in events:
        try:
            key = frozenset((canonical(ev["home_team"]), canonical(ev["away_team"])))
        except Exception:
            skipped.append(f"{ev['home_team']} x {ev['away_team']} (nome não-canônico)")
            continue
        f = unplayed.get(key)
        if f is None:
            continue  # já disputado, não-grupo, ou fora desta edição
        price = _book_price_map(ev, book)
        if price is None:  # fallback: mediana das casas
            med = _median_price_map(ev)
            price = {k: statistics.median(v) for k, v in med.items()} if med else None
            if price is not None:
                fallback += 1
        if price is None:
            skipped.append(f"J{f.match_id} (sem odds h2h)")
            continue
        try:
            odds[f.match_id] = (price[f.home], price["Draw"], price[f.away])
        except KeyError as err:
            skipped.append(f"J{f.match_id} (resultado ausente: {err})")
    return odds, fallback, skipped


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Busca e mescla odds (The Odds API) em odds.csv (ENG-19)")
    p.add_argument("--edition", type=int, default=2026)
    p.add_argument("--region", default="eu", help="região da The Odds API (eu tem Pinnacle)")
    p.add_argument("--book", default="pinnacle", help="casa preferida (fallback: mediana das casas)")
    args = p.parse_args(argv)

    edition = load_edition(args.edition)
    path = EDITIONS_DIR / str(args.edition) / "odds.csv"
    existing = read_existing(path)

    events, remaining = fetch_events(load_api_key(), args.region)
    fetched, fallback, skipped = map_to_fixtures(events, edition, args.book)

    merged = merge_odds(existing, fetched)
    added = sorted(set(fetched) - set(existing))
    updated = sorted(set(fetched) & set(existing))
    preserved = sorted(set(existing) - set(fetched))
    write_odds(path, merged)

    print(f"📥 The Odds API: {len(events)} eventos, {remaining} créditos restantes.")
    print(
        f"✅ odds.csv: {len(merged)} jogos no total "
        f"(+{len(added)} novos, {len(updated)} atualizados, {len(preserved)} preservados/disputados)."
    )
    if fallback:
        print(f"   ⚠️  {fallback} jogo(s) sem '{args.book}' → mediana das casas.")
    if skipped:
        print(f"   ⏭️  pulados: {', '.join(skipped)}")
    print(f"   Próximo: `uv run worldcup predict --edition {args.edition}` e, após resultados, `blend-track`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
