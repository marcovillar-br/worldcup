#!/usr/bin/env python3
"""Busca odds 1X2 + totals da The Odds API e MESCLA em data/editions/<ed>/odds.csv (ENG-19/ENG-35).

Rotina por rodada do blend com odds (ver BOLAO.md). Faz:
  1. lê a chave `ODDS_API_KEY` (do ambiente ou do `.env` na raiz);
  2. baixa as odds h2h + totals (decimal) da Copa (`soccer_fifa_world_cup`);
  3. casa cada evento com um jogo **ainda não disputado** — de grupo, ou de mata-mata já definido pelo
     bracket real (ENG-28) — do fixture (por nomes canônicos);
  4. extrai a odd da **Pinnacle** (casa sharp; mediana das casas como fallback — no totals, mediana
     na linha **modal** entre as casas, para não misturar preços de linhas diferentes);
  5. **MESCLA** no `odds.csv` existente — atualiza/adiciona os jogos atuais e **preserva** os que
     saíram da lista (já disputados): senão o `blend-track` perderia o tally acumulado. As colunas
     `total_line,over,under` são opcionais (ENG-35): arquivos antigos seguem válidos.

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
from worldcup.sync import resolve_live_bracket
from worldcup.teams import canonical

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPORT = "soccer_fifa_world_cup"
API_URL = "https://api.the-odds-api.com/v4/sports/{sport}/odds/"

Triple = tuple[float, float, float]
# Totals de um jogo: (linha de gols, odd decimal do over, odd decimal do under) — ENG-35.
Totals = tuple[float, float, float]


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


def read_existing(path: Path) -> tuple[dict[int, Triple], dict[int, Totals]]:
    """Lê o odds.csv existente → (1×2 por jogo, totals por jogo). Colunas de totals são opcionais
    (arquivos pré-ENG-35 não as têm ⇒ totals vazio)."""
    if not path.exists():
        return {}, {}
    h2h: dict[int, Triple] = {}
    totals: dict[int, Totals] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            mid = int(row["match_id"])
            cells = [(row.get(k) or "").strip() for k in ("home", "draw", "away")]
            if all(cells):
                h2h[mid] = (float(cells[0]), float(cells[1]), float(cells[2]))
            tcells = [(row.get(k) or "").strip() for k in ("total_line", "over", "under")]
            if all(tcells):
                totals[mid] = (float(tcells[0]), float(tcells[1]), float(tcells[2]))
    return h2h, totals


def write_odds(path: Path, odds: dict[int, Triple], totals: dict[int, Totals] | None = None) -> None:
    """Grava o odds.csv com as colunas de totals (vazias nos jogos sem o mercado)."""
    totals = totals or {}
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["match_id", "home", "draw", "away", "total_line", "over", "under"])
        for mid in sorted(odds):
            w.writerow([mid, *odds[mid], *(totals.get(mid) or ("", "", ""))])


def fetch_events(api_key: str, region: str) -> tuple[list[dict], str]:
    """Eventos com odds da Copa + créditos restantes (header da API)."""
    params = f"?apiKey={api_key}&regions={region}&markets=h2h,totals&oddsFormat=decimal"
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


def _totals_from_outcomes(outcomes: list[dict]) -> Totals | None:
    """Par over/under de um mercado de totals → (linha, over, under); None se incompleto."""
    over = next((o for o in outcomes if o["name"] == "Over"), None)
    under = next((o for o in outcomes if o["name"] == "Under"), None)
    if over is None or under is None or over.get("point") is None:
        return None
    return (float(over["point"]), float(over["price"]), float(under["price"]))


def _book_totals(event: dict, book: str) -> Totals | None:
    """Totals da casa preferida; None se ela não cota o mercado no evento."""
    bk = next((b for b in event["bookmakers"] if b["key"] == book), None)
    if not bk:
        return None
    mkt = next((m for m in bk["markets"] if m["key"] == "totals"), None)
    if not mkt:
        return None
    return _totals_from_outcomes(mkt["outcomes"])


def _median_totals(event: dict) -> Totals | None:
    """Fallback de totals: escolhe a linha **modal** entre as casas e tira a mediana dos preços
    cotados naquela linha — misturar preços de linhas diferentes enviesaria o par over/under."""
    by_line: dict[float, list[tuple[float, float]]] = {}
    for b in event["bookmakers"]:
        mkt = next((m for m in b["markets"] if m["key"] == "totals"), None)
        if not mkt:
            continue
        t = _totals_from_outcomes(mkt["outcomes"])
        if t is not None:
            by_line.setdefault(t[0], []).append((t[1], t[2]))
    if not by_line:
        return None
    # linha modal; empate de contagem → a linha mais baixa (determinístico)
    line = max(sorted(by_line), key=lambda ln: len(by_line[ln]))
    overs = [p[0] for p in by_line[line]]
    unders = [p[1] for p in by_line[line]]
    return (line, statistics.median(overs), statistics.median(unders))


def _matchable_fixtures(edition: Edition) -> dict[frozenset[str], tuple[int, str, str]]:
    """Jogos **não disputados** casáveis com o feed de odds → `{par de times: (match_id, mandante, visitante)}`.

    Grupos: os times são os próprios `home`/`away` do fixture. Mata-mata (ENG-28): os fixtures guardam
    **slots** (`1A`, `W73`), então resolvemos o bracket pelos resultados reais (`resolve_live_bracket`)
    e incluímos os confrontos de KO **já determinados** e ainda não disputados, com os times resolvidos.
    """
    out: dict[frozenset[str], tuple[int, str, str]] = {}
    for f in edition.fixtures:
        if f.is_group and not f.played:
            out[frozenset((f.home, f.away))] = (f.match_id, f.home, f.away)
    by_id = {f.match_id: f for f in edition.fixtures}
    for mid, (home, away) in resolve_live_bracket(edition).items():
        f = by_id.get(mid)
        if f is not None and not f.played:
            out[frozenset((home, away))] = (mid, home, away)
    return out


def map_to_fixtures(
    events: list[dict], edition: Edition, book: str
) -> tuple[dict[int, Triple], dict[int, Totals], int, list[str]]:
    """Casa eventos→jogos não disputados (grupo + mata-mata resolvido); alinha odds aos times do confronto.

    Devolve (odds 1×2 por match_id, totals por match_id, nº via fallback de mediana, pulados com
    motivo). Totals são melhor-esforço: evento sem o mercado segue só com o 1×2 (blend degrada
    graciosamente para o comportamento pré-ENG-35 naquele jogo).
    """
    unplayed = _matchable_fixtures(edition)
    odds: dict[int, Triple] = {}
    totals: dict[int, Totals] = {}
    fallback = 0
    skipped: list[str] = []
    for ev in events:
        try:
            key = frozenset((canonical(ev["home_team"]), canonical(ev["away_team"])))
        except Exception:
            skipped.append(f"{ev['home_team']} x {ev['away_team']} (nome não-canônico)")
            continue
        hit = unplayed.get(key)
        if hit is None:
            continue  # já disputado, confronto de KO ainda indefinido, ou fora desta edição
        match_id, home, away = hit
        price = _book_price_map(ev, book)
        if price is None:  # fallback: mediana das casas
            med = _median_price_map(ev)
            price = {k: statistics.median(v) for k, v in med.items()} if med else None
            if price is not None:
                fallback += 1
        if price is None:
            skipped.append(f"J{match_id} (sem odds h2h)")
            continue
        try:
            odds[match_id] = (price[home], price["Draw"], price[away])
        except KeyError as err:
            skipped.append(f"J{match_id} (resultado ausente: {err})")
            continue
        t = _book_totals(ev, book) or _median_totals(ev)
        if t is not None:
            totals[match_id] = t
    return odds, totals, fallback, skipped


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Busca e mescla odds (The Odds API) em odds.csv (ENG-19)")
    p.add_argument("--edition", type=int, default=2026)
    p.add_argument("--region", default="eu", help="região da The Odds API (eu tem Pinnacle)")
    p.add_argument("--book", default="pinnacle", help="casa preferida (fallback: mediana das casas)")
    args = p.parse_args(argv)

    edition = load_edition(args.edition)
    path = EDITIONS_DIR / str(args.edition) / "odds.csv"
    existing, existing_totals = read_existing(path)

    events, remaining = fetch_events(load_api_key(), args.region)
    fetched, fetched_totals, fallback, skipped = map_to_fixtures(events, edition, args.book)

    merged = merge_odds(existing, fetched)
    merged_totals = merge_odds(existing_totals, fetched_totals)  # mesma semântica: preserva disputados
    added = sorted(set(fetched) - set(existing))
    updated = sorted(set(fetched) & set(existing))
    preserved = sorted(set(existing) - set(fetched))
    write_odds(path, merged, merged_totals)

    print(f"📥 The Odds API: {len(events)} eventos, {remaining} créditos restantes.")
    print(
        f"✅ odds.csv: {len(merged)} jogos no total "
        f"(+{len(added)} novos, {len(updated)} atualizados, {len(preserved)} preservados/disputados; "
        f"totals em {len(merged_totals)})."
    )
    if fallback:
        print(f"   ⚠️  {fallback} jogo(s) sem '{args.book}' → mediana das casas.")
    if skipped:
        print(f"   ⏭️  pulados: {', '.join(skipped)}")
    print(f"   Próximo: `uv run worldcup predict --edition {args.edition}` e, após resultados, `blend-track`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
