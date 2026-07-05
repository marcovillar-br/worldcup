"""Testes do briefing de start-of-day (`status.build_status`/`format_status`, ENG-31)."""

from __future__ import annotations

from worldcup.edition import Edition, Fixture, ScoringConfig, load_edition
from worldcup.status import build_status, format_status

# Casca estrutural real (grupos/spec válidos); cada teste troca fixtures/scoring por model_copy
# (não revalida) — o status só lê spec.name, scoring e fixtures, então a casca basta.
_BASE = load_edition(2026)


def _fx(mid: int, date: str, home: str, away: str, *, stage: str = "group", hg=None, ag=None) -> Fixture:
    return Fixture(match_id=mid, stage=stage, date=date, home=home, away=away, home_goals=hg, away_goals=ag)


def _edition(fixtures: list[Fixture], *, risk: float = 0.5, blend: float = 0.6) -> Edition:
    return _BASE.model_copy(update={"fixtures": fixtures, "scoring": ScoringConfig(risk=risk, blend_weight=blend)})


def _pick(
    mid: int, mandante: str, visitante: str, palpite: str, *, fase: str, avanca: str = "", status: str = "PREVISTO"
):
    return {
        "jogo": str(mid),
        "fase": fase,
        "mandante": mandante,
        "visitante": visitante,
        "palpite": palpite,
        "avanca": avanca,
        "status": status,
    }


def test_today_separates_played_from_pending():
    fixtures = [
        _fx(77, "2026-06-30", "France", "Sweden", stage="R32", hg=3, ag=0),
        _fx(79, "2026-06-30", "Mexico", "Ecuador", stage="R32"),
        _fx(80, "2026-07-01", "England", "DR Congo", stage="R32"),
    ]
    picks = {
        77: _pick(77, "França", "Suécia", "3×0", fase="R32", avanca="França", status="FINAL"),
        79: _pick(79, "México", "Equador", "0×0", fase="R32", avanca="México"),
        80: _pick(80, "Inglaterra", "RD Congo", "1×0", fase="R32", avanca="Inglaterra"),
    }
    r = build_status(_edition(fixtures), picks, "2026-06-30", "11º · 271 pts")

    assert (r.played, r.total) == (1, 3)
    assert r.stage == "16-avos"  # fase do primeiro não disputado (J79)
    ids = {g.match_id: g for g in r.today_games}
    assert set(ids) == {77, 79}  # só os de hoje
    assert ids[77].played
    assert ids[77].score == "3×0"
    assert not ids[79].played
    assert ids[79].score is None
    assert ids[77].label == "França × Suécia"
    # próximos = não disputados por match_id, com palpite e seta de KO
    assert [g.match_id for g in r.upcoming] == [79, 80]
    assert r.upcoming[0].pick == "0×0 → México"
    assert r.standing == "11º · 271 pts"


def test_overdue_games_flagged():
    fixtures = [
        _fx(79, "2026-06-29", "Mexico", "Ecuador", stage="R32"),  # ontem, sem placar
        _fx(80, "2026-07-01", "England", "DR Congo", stage="R32"),
    ]
    r = build_status(_edition(fixtures), {}, "2026-06-30", None)
    assert r.overdue == [79]
    out = format_status(r)
    assert "J79" in out
    assert "sync-results" in out


def test_stale_out_when_picks_behind_results():
    fixtures = [
        _fx(77, "2026-06-30", "France", "Sweden", stage="R32", hg=3, ag=0),  # disputado
        _fx(79, "2026-06-30", "Mexico", "Ecuador", stage="R32"),
    ]
    # out/ ainda mostra J77 como PREVISTO (faltou repalpitar após o record)
    picks = {77: _pick(77, "França", "Suécia", "3×0", fase="R32", status="PREVISTO")}
    r = build_status(_edition(fixtures), picks, "2026-06-30", None)
    assert r.stale is True
    assert "repalpitar" in format_status(r)


def test_no_picks_falls_back_and_asks_for_predict():
    fixtures = [_fx(79, "2026-06-30", "Mexico", "Ecuador", stage="R32")]
    r = build_status(_edition(fixtures), {}, "2026-06-30", None)
    assert r.has_picks is False
    g = r.today_games[0]
    assert g.label == "México × Equador"  # display() resolve nomes canônicos
    assert "worldcup predict" in format_status(r)


def test_no_games_today():
    fixtures = [_fx(80, "2026-07-01", "England", "DR Congo", stage="R32")]
    r = build_status(_edition(fixtures), {}, "2026-06-30", None)
    assert r.today_games == []
    assert "(sem jogos hoje)" in format_status(r)


def test_group_pick_has_no_arrow():
    fixtures = [_fx(50, "2026-06-25", "Brazil", "Serbia")]
    picks = {50: _pick(50, "Brasil", "Sérvia", "2×0", fase="group", avanca="Brasil")}
    r = build_status(_edition(fixtures), picks, "2026-06-25", None)
    assert r.upcoming[0].pick == "2×0"  # grupo não mostra "→ avança"


def test_format_always_asks_for_user_points():
    r = build_status(_edition([_fx(80, "2026-07-01", "England", "DR Congo", stage="R32")]), {}, "2026-06-30", None)
    out = format_status(r)
    assert "PRECISA DE VOCÊ" in out
    assert "efficiency.py" in out


def test_status_flags_fit_gaps():
    # ENG-43: jogos disputados fora do ajuste aparecem como alerta de staleness no briefing
    ed = _edition([_fx(1, "2026-06-11", "Mexico", "South Africa", hg=2, ag=0)])
    out = format_status(build_status(ed, {}, "2026-07-05", None, fit_gaps=[99, 100]))
    assert "FORA do ajuste" in out
    assert "J99" in out
    assert "J100" in out


def test_status_silent_without_fit_gaps():
    ed = _edition([_fx(1, "2026-06-11", "Mexico", "South Africa", hg=2, ag=0)])
    assert "FORA do ajuste" not in format_status(build_status(ed, {}, "2026-07-05", None))
