"""Testes de helpers de renderização e do tratamento de erro da CLI."""

from __future__ import annotations

import csv

from worldcup import cli, fetch_data
from worldcup.cli import main
from worldcup.edition import load_edition
from worldcup.fetch_data import NetworkError
from worldcup.pipeline import PredictionRun
from worldcup.render import CSV_COLUMNS, _esc


def test_esc_escapes_html_metacharacters():
    assert _esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert _esc("Tom & Jerry") == "Tom &amp; Jerry"


def test_esc_escapes_quotes_for_attribute_context():
    # aspas precisam ser escapadas: nomes reais têm apóstrofo (ex.: Côte d'Ivoire) e o helper
    # pode ser usado dentro de atributos (style/title) — sem isso, vetor de injeção.
    assert _esc('a"b') == "a&quot;b"
    assert _esc("Côte d'Ivoire") == "Côte d&#x27;Ivoire"


def test_main_translates_network_error_to_exit_code(monkeypatch, capsys):
    def offline(*_a, **_k):
        raise NetworkError("Não foi possível baixar X. Verifique sua conexão.")

    monkeypatch.setattr(fetch_data, "_download_text", offline)
    code = main(["fetch-data"])
    assert code == 1
    assert "🌐" in capsys.readouterr().err  # mensagem amigável, sem traceback


def _tiny_run():
    ed = load_edition(2026)
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
    return PredictionRun(rows=[row], champion_prob={"Brazil": 0.2}, advance_prob={}, edition=ed)


def test_archive_outputs_writes_versioned_csv_md(tmp_path, monkeypatch):
    # snapshot vai para data/editions/<ano>/history/ (rastreado), não para out/ (gitignored)
    monkeypatch.setattr(cli, "EDITIONS_DIR", tmp_path)
    csv_p, md_p = cli.archive_outputs(_tiny_run(), 2026, "2026-06-11")
    assert csv_p == tmp_path / "2026" / "history" / "2026-06-11.csv"
    assert csv_p.exists()
    assert md_p.exists()
    assert csv_p.read_text().splitlines()[0].startswith("jogo,data,fase")  # CSV canônico
    assert "reconstruído" not in md_p.read_text()  # run real: sem banner


def test_archive_outputs_preserves_morning_pick_on_rearchive(tmp_path, monkeypatch, capsys):
    # ENG-33: re-arquivar no mesmo dia (pós-record/sync) não pode rebaixar palpite→FINAL —
    # o palpite da manhã é o dado não-reprodutível que o snapshot existe para preservar.
    monkeypatch.setattr(cli, "EDITIONS_DIR", tmp_path)
    cli.archive_outputs(_tiny_run(), 2026, "2026-06-11")  # manhã: J1 PREVISTO 2x0

    evening = _tiny_run()
    evening.rows[0].update(status="FINAL", palpite="1x1", placar_real="1x1")  # J1 já disputado
    row2 = dict.fromkeys(CSV_COLUMNS, "")
    row2.update(
        {
            "jogo": "2",
            "data": "2026-06-11",
            "fase": "group",
            "grupo": "B",
            "mandante": "Canadá",
            "palpite": "1x0",
            "visitante": "Catar",
            "status": "PREVISTO",
        }
    )
    evening.rows.append(row2)
    csv_p, md_p = cli.archive_outputs(evening, 2026, "2026-06-11")

    with csv_p.open(newline="") as fh:
        rows = {r["jogo"]: r for r in csv.DictReader(fh)}
    assert rows["1"]["status"] == "PREVISTO"  # palpite da manhã preservado
    assert rows["1"]["palpite"] == "2x0"
    assert rows["2"]["palpite"] == "1x0"  # linha nova entra normalmente
    assert "preservado o palpite da manhã de J1" in capsys.readouterr().out
    assert "2x0" in md_p.read_text()  # MD rerenderizado das linhas mescladas, não do run cru


def test_archive_outputs_updates_still_pending_pick_on_rearchive(tmp_path, monkeypatch):
    # ENG-33: jogo ainda PREVISTO nos dois runs atualiza normalmente (repalpite intradiário vale)
    monkeypatch.setattr(cli, "EDITIONS_DIR", tmp_path)
    cli.archive_outputs(_tiny_run(), 2026, "2026-06-11")
    later = _tiny_run()
    later.rows[0]["palpite"] = "3x0"
    csv_p, _ = cli.archive_outputs(later, 2026, "2026-06-11")
    with csv_p.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["palpite"] == "3x0"


def test_archive_outputs_marks_reconstructed(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "EDITIONS_DIR", tmp_path)
    csv_p, md_p = cli.archive_outputs(_tiny_run(), 2026, "2026-06-11", reconstructed=True)
    assert csv_p.name == "2026-06-11.reconstruido.csv"  # sufixo no nome
    assert "reconstruído" in md_p.read_text()  # banner de aviso no topo do MD


def test_predict_parser_accepts_pool_behind():
    # ENG-36/40: flag opt-in do modo endgame; default None (fiel); sem valor ⇒ 'empate'
    # (política dominante, ENG-39); 'zebra' mantida para a reavaliação da véspera.
    from worldcup.cli import build_parser

    p = build_parser()
    for cmd in ("predict", "sync-results"):
        assert p.parse_args([cmd]).pool_behind is None
        assert p.parse_args([cmd, "--pool-behind"]).pool_behind == "empate"
        assert p.parse_args([cmd, "--pool-behind", "zebra"]).pool_behind == "zebra"


def test_blend_track_boost_sweep(monkeypatch, capsys):
    # ENG-44: --boost-sweep imprime o Brier as-of do modelo por valor de boost, marcando o mínimo.
    from worldcup import backtest
    from worldcup.backtest import BoostTracking

    def fake_sweep(edition, boosts):
        # o mínimo cai num boost baixo (≠ 6.0 em uso) — o caso que motivou o ENG-44
        briers = {2.0: 0.40}
        return [BoostTracking(boost=b, n=48, brier_model=briers.get(b, 0.45)) for b in boosts]

    monkeypatch.setattr(backtest, "boost_sweep", fake_sweep)
    code = main(["blend-track", "--boost-sweep"])
    out = capsys.readouterr().out
    assert code == 0
    assert "boost= 2.0" in out
    assert "← mínimo" in out
    assert "(em uso)" in out  # marca o boost corrente (edition.scoring.edition_boost)
    assert "boost* = 2.0" in out


# ── standing do BOLAO.md (briefing do `status`) ───────────────────────────────────────────────


def test_read_standing_pega_a_entrada_mais_recente_nao_uma_do_historico():
    """O `status` mostrava um standing de 9 dias atrás, em silêncio (12/07 exibia o de 03/07).

    A busca era `"Standing" in line`, e o bloco `## Estado atual` contém também as entradas de
    **histórico** — que trazem standings antigos. A manchete do dia usava o rótulo `Placar`, então a
    palavra `Standing` só aparecia lá embaixo, no histórico: o parser casava com ela e devolvia um
    número velho como se fosse o atual. Um briefing que mente sobre a posição é pior que não ter.
    """
    real = cli._read_standing(2026)
    assert real is not None
    assert "453" in real  # a manchete do fechamento (19/07), a mais recente
    assert "15" in real
    assert "425" not in real  # a de 12/07, que vive no histórico do mesmo bloco


def test_read_standing_ancora_no_negrito_e_ignora_mencao_solta(tmp_path, monkeypatch):
    """Ancorar no **negrito** (a manchete) e não em "a linha contém a palavra"."""
    bolao = tmp_path / "2026" / "BOLAO.md"
    bolao.parent.mkdir(parents=True)
    bolao.write_text(
        "## Estado atual\n"
        "- o placar consolidado não é o dos 90' — cuidado ao ler o Standing bruto da fonte\n"
        "- **Placar (12/07): 425 pts, 19º. Líder 509.** prosa que não deve entrar no briefing\n"
        "- **Standing (03/07): 325 pts, 17º**\n"
        "## Histórico\n"
        "- **Standing (01/07): 285 pts, 21º**\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "EDITIONS_DIR", tmp_path)
    got = cli._read_standing(2026)
    assert got == "(12/07): 425 pts, 19º. Líder 509"  # manchete do dia, sem a prosa nem o rótulo
