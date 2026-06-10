"""Testes de helpers de renderização e do tratamento de erro da CLI."""

from __future__ import annotations

from worldcup import fetch_data
from worldcup.cli import _esc, main
from worldcup.fetch_data import NetworkError


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
