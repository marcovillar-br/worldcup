#!/usr/bin/env python3
"""Checagem de line-length em Markdown (hook de pre-commit, stdlib pura).

Régua: máximo 100 caracteres por linha (UTF-8 completo, não bytes).
Isenções: data/editions/*/history/*.md (snapshots), linhas de tabela (|...|),
URLs/links longos, blocos de código (```), comandos `uv run`, diagramas C4.

Uso: `check_markdown_line_length.py [caminho...]` (default: ./*.md)
Sai com código 1 se houver violação; 0 se está conforme.
"""

from __future__ import annotations

import sys
from pathlib import Path

MAX_LINE_LENGTH = 100


def _is_exempted(path: Path, line: str) -> bool:
    """Retorna True se a linha está isenta da régua."""
    # Isenção 1: snapshots históricos (data/editions/*/history/*.md)
    if "data/editions" in str(path) and "history" in str(path):
        return True

    # Isenção 2: linhas de tabela (começam com |)
    if line.lstrip().startswith("|"):
        return True

    # Isenção 3: linhas com URLs (contêm http:// ou https://)
    if "http://" in line or "https://" in line:
        return True

    # Isenção 4: linhas de código inline (contêm ```)
    if "```" in line:
        return True

    # Isenção 5: comandos `uv run` (hard to break)
    if "uv run" in line:
        return True

    # Isenção 6: diagramas C4 (Component, Container, System, etc)
    if any(
        kw in line
        for kw in [
            "Component(",
            "Container(",
            "System(",
            "System_Ext(",
            "ContainerDb(",
        ]
    ):
        return True

    # Isenção 7: HTML/tags (< e >)
    return "<" in line and ">" in line


def check_file(path: Path) -> list[tuple[int, int, str]]:
    """Retorna lista de (line_num, actual_length, line) que violam o máximo."""
    errors: list[tuple[int, int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        # Arquivo não é UTF-8 válido, pula
        return errors

    for line_num, line in enumerate(lines, 1):
        # Contar caracteres, não bytes (len() em Python 3 conta caracteres)
        char_count = len(line)
        if char_count > MAX_LINE_LENGTH and not _is_exempted(path, line):
            errors.append((line_num, char_count, line))

    return errors


def main() -> int:
    """Processa arquivos e reporta violações."""
    # Se chamado sem argumentos, busca todos os .md no repo
    if len(sys.argv) == 1:  # noqa: SIM108
        paths = list(Path().rglob("*.md"))
    else:
        paths = [Path(p) for p in sys.argv[1:]]

    found_errors = False
    for path in paths:
        if not path.exists():
            continue
        errors = check_file(path)
        if errors:
            found_errors = True
            for line_num, char_count, line_text in errors:
                print(f"{path}:{line_num}: linha tem {char_count} caracteres (máximo {MAX_LINE_LENGTH})")
                # Trecho da linha (primeiros 80 chars) para contexto
                preview = line_text[:80].replace("\n", "\\n")
                if len(line_text) > 80:
                    preview += "…"
                print(f"  {preview}")

    return 1 if found_errors else 0


if __name__ == "__main__":
    sys.exit(main())
