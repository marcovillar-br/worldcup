"""Smoke tests da camada de apresentação (render.py)."""

from __future__ import annotations

from worldcup.edition import load_edition
from worldcup.pipeline import PredictionRun
from worldcup.render import CSV_COLUMNS, _champion_note, render_html, render_markdown


def _run_with(rows: list[dict], champion_prob: dict | None = None) -> PredictionRun:
    ed = load_edition(2026)
    return PredictionRun(
        rows=rows,
        champion_prob=champion_prob or {"Brazil": 0.3, "France": 0.2},
        advance_prob={},
        edition=ed,
    )


def _final_row(**over) -> dict:
    row = dict.fromkeys(CSV_COLUMNS, "")
    row.update(
        {
            "jogo": "104",
            "fase": "final",
            "mandante": "França",
            "visitante": "Argentina",
            "palpite": "1x2",
            "avanca": "Argentina",
            "status": "PREVISTO",
        }
    )
    row.update(over)
    return row


def _group_row(**over) -> dict:
    row = dict.fromkeys(CSV_COLUMNS, "")
    row.update(
        {
            "jogo": "1",
            "data": "2026-06-11",
            "fase": "group",
            "grupo": "A",
            "mandante": "México",
            "palpite": "2x0",
            "visitante": "África do Sul",
            "P_mandante": "73",
            "P_empate": "19",
            "P_visitante": "9",
            "status": "PREVISTO",
        }
    )
    row.update(over)
    return row


def test_render_markdown_has_sections_and_champion():
    md = render_markdown(_run_with([_group_row()]))
    assert "# Palpites" in md
    assert "Probabilidade de título" in md
    assert "Fase de Grupos" in md
    assert "**2x0**" in md  # palpite em destaque


def test_render_html_is_self_contained_and_escapes():
    # nome com caractere especial deve sair escapado (sem injeção)
    run = _run_with([_group_row(mandante='<b>x"&', ousado="⚡")])
    html_out = render_html(run)
    assert html_out.startswith("<!doctype html>")
    assert "<style>" in html_out  # CSS embutido (autocontido)
    assert "&lt;b&gt;" in html_out  # < > escapados
    assert "&quot;" in html_out  # aspas escapadas
    assert "<b>x" not in html_out  # o original não-escapado não vaza


def test_render_html_marks_final_games_with_real_score():
    run = _run_with([_group_row(status="FINAL", placar_real="1x1", palpite="2x0")])
    html_out = render_html(run)
    assert "1x1" in html_out  # mostra o placar real, não o palpite
    assert "tag fin" in html_out  # marca como final


def test_champion_note_only_when_favorite_differs_from_bracket():
    # favorito (Espanha) ≠ campeão do bracket (Argentina) → explica; iguais → sem nota
    assert _champion_note("Espanha", "Argentina") is not None
    assert _champion_note("Argentina", "Argentina") is None
    assert _champion_note("Espanha", "") is None  # sem final resolvida


def test_render_expoe_inv7_no_html_e_md_quando_favorito_diverge_do_bracket():
    # favorito marginal = Espanha (champion_prob), campeão do bracket = Argentina (avança na final)
    run = _run_with([_final_row()], champion_prob={"Spain": 0.30, "France": 0.29, "Argentina": 0.24})
    html_out = render_html(run)
    md_out = render_markdown(run)
    for text in (html_out, md_out):
        assert "Espanha" in text  # favorito sugerido
        assert "slots separados" in text  # a explicação do INV-7 está presente
    assert 'class="note"' in html_out  # estilizado como nota no HTML


def test_final_group_game_shows_dash_not_zeros_in_mev():
    # jogo FINAL não tem previsão (já aconteceu): M/E/V vira "—", não "0/0/0" (HTML) nem "//" (MD).
    # P_* vazios, como um jogo realmente disputado sai do pipeline.
    final_row = _group_row(status="FINAL", placar_real="1x1", P_mandante="", P_empate="", P_visitante="")
    run = _run_with([final_row])
    html_out = render_html(run)
    md_out = render_markdown(run)
    assert "0/0/0" not in html_out
    assert "//" not in md_out
    assert "—" in html_out
    assert "| — |" in md_out  # célula de probabilidades da linha de grupo

    # o jogo ainda PREVISTO mostra as probabilidades normalmente (não "—")
    previsto = render_html(_run_with([_group_row(P_mandante="73", P_empate="19", P_visitante="9")]))
    assert "73/19/9" in previsto


def test_outputs_render_for_knockout_rows():
    ko = dict.fromkeys(CSV_COLUMNS, "")
    ko.update(
        {
            "jogo": "73",
            "data": "2026-06-28",
            "fase": "R32",
            "mandante": "Brasil",
            "visitante": "Coreia do Sul",
            "palpite": "2x1",
            "prorrogacao": "-",
            "penaltis": "-",
            "avanca": "Brasil",
            "status": "PREVISTO",
        }
    )
    md = render_markdown(_run_with([ko]))
    html_out = render_html(_run_with([ko]))
    assert "16-avos de final" in md
    assert "Brasil" in html_out
    assert "Coreia do Sul" in html_out
