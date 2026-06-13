"""Guardrail de tradução: toda seleção de cada edição tem nome de exibição PT (ENG-9)."""

from __future__ import annotations

from worldcup.edition import EDITIONS_DIR, load_edition
from worldcup.teams import _PT_DISPLAY, canonical


def test_every_edition_team_has_pt_display():
    # uma seleção sem entrada em _PT_DISPLAY cairia no inglês silenciosamente (display()).
    years = sorted(int(p.name) for p in EDITIONS_DIR.iterdir() if (p / "groups.csv").exists())
    assert years, "nenhuma edição com groups.csv encontrada"

    missing: dict[int, list[str]] = {}
    for year in years:
        edition = load_edition(year)
        for team in edition.teams:
            if canonical(team) not in _PT_DISPLAY:
                missing.setdefault(year, []).append(team)

    assert not missing, f"seleções sem tradução PT em teams._PT_DISPLAY: {missing}"
