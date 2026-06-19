"""Testes dos helpers puros de sincronização de resultados + integração (ENG-20)."""

from __future__ import annotations

import shutil

import pandas as pd
import pytest

from worldcup import sync
from worldcup.edition import EDITIONS_DIR, load_edition
from worldcup.sync import _resolve_real_bracket, _result_for, _winner, write_fixtures_atomic

_EMPTY_SHOOTOUTS = pd.DataFrame(columns=["date", "home_team", "away_team", "winner"])


def test_result_for_handles_orientation():
    scores = {("Brazil", "Scotland"): [("2026-06-20", 2, 0)]}
    assert _result_for(scores, "Brazil", "Scotland") == (2, 0)
    # orientação invertida: placar é espelhado
    assert _result_for(scores, "Scotland", "Brazil") == (0, 2)
    assert _result_for(scores, "Brazil", "Japan") is None


def test_result_for_disambiguates_rematch_by_date():
    # mesmo par 2× na Copa (grupo + reencontro no mata-mata), mesma orientação na fonte
    scores = {("Brazil", "Argentina"): [("2026-06-20", 1, 1), ("2026-07-05", 2, 0)]}
    # cada jogo recebe o placar do SEU dia (sem o bug de colapsar no último)
    assert _result_for(scores, "Brazil", "Argentina", "2026-06-20") == (1, 1)
    assert _result_for(scores, "Brazil", "Argentina", "2026-07-05") == (2, 0)
    # orientação invertida continua espelhando, por data
    assert _result_for(scores, "Argentina", "Brazil", "2026-06-20") == (1, 1)
    assert _result_for(scores, "Argentina", "Brazil", "2026-07-05") == (0, 2)
    # ambíguo (2 jogos) e data que não casa nenhuma: não chuta
    assert _result_for(scores, "Brazil", "Argentina", "2026-06-30") is None
    assert _result_for(scores, "Brazil", "Argentina") is None


def test_result_for_single_game_ignores_date_mismatch():
    # com um único jogo registrado, devolve direto mesmo se a data não casar (robustez)
    scores = {("Brazil", "Scotland"): [("2026-06-20", 2, 0)]}
    assert _result_for(scores, "Brazil", "Scotland", "2026-06-21") == (2, 0)


def test_winner_decisive():
    assert _winner("Brazil", "Scotland", 2, 0, {}) == "Brazil"
    assert _winner("Brazil", "Scotland", 0, 1, {}) == "Scotland"


def test_winner_on_penalties_uses_shootouts():
    shootouts = {frozenset({"Argentina", "France"}): "Argentina"}
    assert _winner("Argentina", "France", 3, 3, shootouts) == "Argentina"
    # empate sem registro de pênaltis -> indefinido
    assert _winner("Argentina", "France", 3, 3, {}) is None


def test_write_fixtures_atomic_roundtrip(tmp_path):
    path = tmp_path / "fixtures.csv"
    rows = [{"match_id": "1", "home": "Brazil"}, {"match_id": "2", "home": "France"}]
    write_fixtures_atomic(path, rows)
    text = path.read_text()
    assert text.splitlines() == ["match_id,home", "1,Brazil", "2,France"]
    # nenhum temporário deixado pra trás
    assert [p.name for p in path.parent.iterdir() if p.name.startswith(".fixtures-")] == []


def test_write_fixtures_atomic_preserves_original_on_failure(tmp_path):
    path = tmp_path / "fixtures.csv"
    original = "match_id,home\n1,Brazil\n"
    path.write_text(original)
    # 2ª linha tem coluna extra -> DictWriter levanta no meio da escrita (após o header já no temp)
    bad_rows = [{"match_id": "1"}, {"match_id": "2", "EXTRA": "x"}]
    with pytest.raises(ValueError, match="fields not in fieldnames"):
        write_fixtures_atomic(path, bad_rows)
    # o original (spec versionada) fica intacto e o temporário é removido
    assert path.read_text() == original
    assert [p.name for p in path.parent.iterdir() if p.name.startswith(".fixtures-")] == []


# --------------------------------------------- integração de sync (ENG-20)
def test_resolve_real_bracket_round_of_32(monkeypatch):
    """Com todos os grupos completos, o chaveamento real resolve a 1ª rodada de KO (R32)
    com seleções reais — exercita _resolve_real_bracket (standings + thirds + slots)."""
    ed = load_edition(2026)
    # placar sintético: mandante vence 1x0 em todo jogo de grupo (grupos completos)
    scores = {(f.home, f.away): [(f.date, 1, 0)] for f in ed.group_fixtures()}
    resolved = _resolve_real_bracket(ed, scores, {})

    teams = set(ed.teams)
    assert resolved, "nenhum confronto de KO resolvido"
    assert all(h in teams and a in teams for h, a in resolved.values())  # só seleções reais
    # a 1ª rodada de KO (slots de grupo, não W##) deve estar toda resolvida
    r1 = [f for f in ed.knockout_fixtures() if not (f.home.startswith(("W", "L")) or f.away.startswith(("W", "L")))]
    assert {f.match_id for f in r1} <= set(resolved)


def test_sync_results_fills_unplayed_group_games(tmp_path, monkeypatch):
    """sync_results preenche jogos de grupo ainda em aberto a partir de resultados sintéticos,
    sem tocar nos já preenchidos — exercita o caminho de IO completo num clone temporário."""
    shutil.copytree(EDITIONS_DIR / "2026", tmp_path / "2026")
    ed = load_edition(2026, base_dir=tmp_path)
    unplayed = [f for f in ed.group_fixtures() if not f.played][:2]
    assert len(unplayed) == 2

    res_df = pd.DataFrame(
        [
            {
                "tournament": "FIFA World Cup",
                "date": f.date,
                "home_team": f.home,
                "away_team": f.away,
                "home_score": 2,
                "away_score": 1,
            }
            for f in unplayed
        ]
    )
    monkeypatch.setattr(sync, "download_from_urls", lambda urls: res_df)
    monkeypatch.setattr(sync, "download_shootouts", lambda: _EMPTY_SHOOTOUTS)

    counts = sync.sync_results(2026, base_dir=tmp_path)
    assert counts["group"] == 2

    reloaded = load_edition(2026, base_dir=tmp_path)
    for f in unplayed:
        got = next(x for x in reloaded.fixtures if x.match_id == f.match_id)
        assert (got.home_goals, got.away_goals) == (2, 1)


def test_edition_results_lists_rematch_and_filters_non_wc(monkeypatch):
    """_edition_results: ignora jogos não-Copa, guarda reencontro como lista (não sobrescreve)
    e lê o vencedor de pênaltis dos shootouts."""
    res_df = pd.DataFrame(
        [
            {
                "tournament": "FIFA World Cup",
                "date": "2026-06-19",
                "home_team": "Brazil",
                "away_team": "Haiti",
                "home_score": 3,
                "away_score": 0,
            },
            {
                "tournament": "FIFA World Cup",
                "date": "2026-07-05",
                "home_team": "Brazil",
                "away_team": "Haiti",
                "home_score": 1,
                "away_score": 1,
            },  # reencontro no KO
            {
                "tournament": "Friendly",
                "date": "2026-01-01",
                "home_team": "Brazil",
                "away_team": "Haiti",
                "home_score": 5,
                "away_score": 0,
            },  # não-Copa: ignorado
        ]
    )
    so_df = pd.DataFrame([{"date": "2026-07-05", "home_team": "Brazil", "away_team": "Haiti", "winner": "Brazil"}])
    monkeypatch.setattr(sync, "download_from_urls", lambda urls: res_df)
    monkeypatch.setattr(sync, "download_shootouts", lambda: so_df)

    scores, shootouts = sync._edition_results(2026)
    assert len(scores[("Brazil", "Haiti")]) == 2  # reencontro vira lista, não sobrescreve
    assert shootouts[frozenset({"Brazil", "Haiti"})] == "Brazil"
