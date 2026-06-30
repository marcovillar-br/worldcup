"""Testes da lógica pura do scripts/fetch_odds.py (merge acumulativo + round-trip do odds.csv)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "fetch_odds.py"
_spec = importlib.util.spec_from_file_location("fetch_odds", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
fetch_odds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fetch_odds)


def test_merge_preserves_played_and_updates_current():
    existing = {1: (2.0, 3.0, 4.0), 2: (1.5, 4.0, 6.0)}  # jogo 1 já disputado (some da API)
    fetched = {2: (1.6, 3.8, 5.5), 3: (2.2, 3.1, 3.4)}  # 2 atualizado, 3 novo
    merged = fetch_odds.merge_odds(existing, fetched)
    assert merged[1] == (2.0, 3.0, 4.0)  # PRESERVADO — senão o blend-track perde o tally
    assert merged[2] == (1.6, 3.8, 5.5)  # atualizado
    assert merged[3] == (2.2, 3.1, 3.4)  # adicionado


def test_read_write_round_trip(tmp_path):
    path = tmp_path / "odds.csv"
    odds = {22: (3.17, 2.71, 2.77), 24: (9.5, 4.75, 1.41)}
    fetch_odds.write_odds(path, odds)
    assert fetch_odds.read_existing(path) == odds


def test_read_existing_missing_is_empty(tmp_path):
    assert fetch_odds.read_existing(tmp_path / "nope.csv") == {}


def _h2h_event(home, away, home_price, draw_price, away_price):
    return {
        "home_team": home,
        "away_team": away,
        "bookmakers": [
            {
                "key": "pinnacle",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": home, "price": home_price},
                            {"name": away, "price": away_price},
                            {"name": "Draw", "price": draw_price},
                        ],
                    }
                ],
            }
        ],
    }


def test_map_to_fixtures_matches_resolved_knockout_game():
    # ENG-28: jogo de mata-mata resolvido pelo bracket real entra no casamento, com odds alinhadas.
    from worldcup.edition import load_edition

    ed = load_edition(2026).as_of("2026-06-28")  # grupos completos, R32 resolvível (J77 = France x Sweden)
    ev = _h2h_event("France", "Sweden", 1.30, 6.20, 11.0)
    odds, _fallback, _skipped = fetch_odds.map_to_fixtures([ev], ed, "pinnacle")
    assert odds[77] == (1.30, 6.20, 11.0)  # alinhado (mandante France, visitante Sweden)
    # orientação invertida no feed continua alinhando pelos NOMES (não pela ordem da API)
    ev_rev = _h2h_event("Sweden", "France", 11.0, 6.20, 1.30)
    odds_rev, _f, _s = fetch_odds.map_to_fixtures([ev_rev], ed, "pinnacle")
    assert odds_rev[77] == (1.30, 6.20, 11.0)
