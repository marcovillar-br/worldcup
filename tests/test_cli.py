"""Testes de helpers de renderização da CLI."""

from __future__ import annotations

from worldcup.cli import _esc


def test_esc_escapes_html_metacharacters():
    assert _esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert _esc("Tom & Jerry") == "Tom &amp; Jerry"


def test_esc_escapes_quotes_for_attribute_context():
    # aspas precisam ser escapadas: nomes reais têm apóstrofo (ex.: Côte d'Ivoire) e o helper
    # pode ser usado dentro de atributos (style/title) — sem isso, vetor de injeção.
    assert _esc('a"b') == "a&quot;b"
    assert _esc("Côte d'Ivoire") == "Côte d&#x27;Ivoire"
