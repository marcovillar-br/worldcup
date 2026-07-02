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
    totals = {22: (2.5, 1.85, 1.95)}  # 24 sem totals -> colunas em branco
    fetch_odds.write_odds(path, odds, totals)
    assert fetch_odds.read_existing(path) == (odds, totals)


def test_read_existing_missing_is_empty(tmp_path):
    assert fetch_odds.read_existing(tmp_path / "nope.csv") == ({}, {})


def test_read_existing_legacy_csv_without_totals_columns(tmp_path):
    # arquivo pré-ENG-35 (só 1×2) segue válido: totals vazio, 1×2 intacto
    path = tmp_path / "odds.csv"
    path.write_text("match_id,home,draw,away\n22,3.17,2.71,2.77\n")
    h2h, totals = fetch_odds.read_existing(path)
    assert h2h == {22: (3.17, 2.71, 2.77)}
    assert totals == {}


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
    odds, _totals, _fallback, _skipped = fetch_odds.map_to_fixtures([ev], ed, "pinnacle")
    assert odds[77] == (1.30, 6.20, 11.0)  # alinhado (mandante France, visitante Sweden)
    # orientação invertida no feed continua alinhando pelos NOMES (não pela ordem da API)
    ev_rev = _h2h_event("Sweden", "France", 11.0, 6.20, 1.30)
    odds_rev, _t, _f, _s = fetch_odds.map_to_fixtures([ev_rev], ed, "pinnacle")
    assert odds_rev[77] == (1.30, 6.20, 11.0)


def _totals_market(line, over_price, under_price):
    return {
        "key": "totals",
        "outcomes": [
            {"name": "Over", "price": over_price, "point": line},
            {"name": "Under", "price": under_price, "point": line},
        ],
    }


def test_map_to_fixtures_extracts_totals_from_preferred_book():
    from worldcup.edition import load_edition

    ed = load_edition(2026).as_of("2026-06-28")
    ev = _h2h_event("France", "Sweden", 1.30, 6.20, 11.0)
    ev["bookmakers"][0]["markets"].append(_totals_market(2.5, 1.85, 1.95))
    _odds, totals, _fallback, _skipped = fetch_odds.map_to_fixtures([ev], ed, "pinnacle")
    assert totals[77] == (2.5, 1.85, 1.95)


def test_map_to_fixtures_totals_fallback_uses_modal_line():
    # sem a casa preferida no totals: linha modal entre as casas + mediana dos preços NAQUELA linha
    from worldcup.edition import load_edition

    ed = load_edition(2026).as_of("2026-06-28")
    ev = _h2h_event("France", "Sweden", 1.30, 6.20, 11.0)  # h2h da pinnacle, sem totals dela
    ev["bookmakers"].extend(
        [
            {"key": "bet1", "markets": [_totals_market(2.5, 1.80, 2.00)]},
            {"key": "bet2", "markets": [_totals_market(2.5, 1.90, 1.90)]},
            {"key": "bet3", "markets": [_totals_market(3.0, 2.10, 1.70)]},  # linha minoritária: fora
        ]
    )
    _odds, totals, _fallback, _skipped = fetch_odds.map_to_fixtures([ev], ed, "pinnacle")
    assert totals[77] == (2.5, 1.85, 1.95)  # medianas só da linha modal 2.5


def test_map_to_fixtures_event_without_totals_still_yields_h2h():
    # degradação graciosa: evento sem o mercado de totals entra só com o 1×2
    from worldcup.edition import load_edition

    ed = load_edition(2026).as_of("2026-06-28")
    ev = _h2h_event("France", "Sweden", 1.30, 6.20, 11.0)
    odds, totals, _fallback, _skipped = fetch_odds.map_to_fixtures([ev], ed, "pinnacle")
    assert 77 in odds
    assert totals == {}
