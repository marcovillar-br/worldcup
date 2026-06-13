"""Testes de helpers de renderização e do tratamento de erro da CLI."""

from __future__ import annotations

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


def test_archive_outputs_marks_reconstructed(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "EDITIONS_DIR", tmp_path)
    csv_p, md_p = cli.archive_outputs(_tiny_run(), 2026, "2026-06-11", reconstructed=True)
    assert csv_p.name == "2026-06-11.reconstruido.csv"  # sufixo no nome
    assert "reconstruído" in md_p.read_text()  # banner de aviso no topo do MD
