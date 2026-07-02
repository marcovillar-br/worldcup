#!/usr/bin/env python3
"""Reformata linhas longas em markdown para ≤100 caracteres (on-demand, frágil).

⚠️ Qualidade de prosa: reflow automático de texto degrada legibilidade. Use com
cuidado; revisão manual dos resultados é RECOMENDADA antes de commitar.

Isenções: tabelas (|), URLs/http, código (```), snapshots históricos.
Reembrulha prosa normal quebrando em espaços, mantendo indentação e estrutura.

Uso: `reformat_markdown_lines.py [caminho...]` (default: ./*.md)
Modifica arquivos em-place.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from textwrap import fill

MAX_LINE_LENGTH = 100


def _is_exempted(path: Path, line: str) -> bool:
    """Retorna True se a linha está isenta da régua."""
    # Isenção 1: snapshots históricos (data/editions/*/history/*.md)
    if "data/editions" in str(path) and "history" in str(path):
        return True
    # Isenção 2: linhas de tabela
    if line.lstrip().startswith("|"):
        return True
    # Isenção 3: linhas com URLs
    if "http://" in line or "https://" in line:
        return True
    # Isenção 4: linhas de delimitador de código
    if "```" in line:
        return True
    # Isenção 5: linhas vazias ou só espaço
    if not line.strip():
        return True
    # Isenção 6: linhas de 4+ espaços (código recuado)
    return line.startswith(("    ", "\t"))


def _get_indent(line: str) -> str:
    """Extrai a indentação (espaços) da linha."""
    match = re.match(r"^(\s*)", line)
    return match.group(1) if match else ""


def _is_list_item(line: str) -> bool:
    """Retorna True se a linha é um item de lista."""
    stripped = line.lstrip()
    return stripped.startswith(("- ", "* ", "+ ")) or re.match(r"^\d+\.\s", stripped)


def reformat_line(line: str) -> str:
    """Reformata uma linha > 100 chars se possível, mantendo indentação."""
    if len(line) <= MAX_LINE_LENGTH:
        return line

    indent = _get_indent(line)
    text = line[len(indent) :]

    # Se é item de lista, tenta quebrar após o marcador
    if _is_list_item(line):
        # Preserva o marcador (- / * / 1. etc)
        match = re.match(r"^(\s*)([-*+]|\d+\.)\s+", line)
        if match:
            prefix = match.group(0)
            rest = line[len(prefix) :]
            if len(prefix) + len(rest) > MAX_LINE_LENGTH:
                # Reembrulha a parte após o marcador
                wrapped = fill(
                    rest,
                    width=MAX_LINE_LENGTH - len(prefix),
                    break_long_words=False,
                    break_on_hyphens=False,
                )
                # Re-indenta as linhas quebradas
                lines = wrapped.split("\n")
                indented = [lines[0]]
                continuation_indent = " " * len(prefix)
                for continuation_line in lines[1:]:
                    indented.append(continuation_indent + continuation_line)
                return prefix + "\n".join(indented)
    else:
        # Prosa normal: reembrulha com indentação
        wrapped = fill(
            text,
            width=MAX_LINE_LENGTH - len(indent),
            break_long_words=False,
            break_on_hyphens=False,
        )
        if "\n" in wrapped:
            lines = wrapped.split("\n")
            return indent + ("\n" + indent).join(lines)
        return indent + wrapped

    return line


def reformat_file(path: Path) -> int:
    """Reformata um arquivo, retorna número de linhas ajustadas."""
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0

    lines = content.splitlines(keepends=False)
    changed_lines = 0
    new_lines = []

    in_code_block = False
    for line in lines:
        # Detecta blocos de código
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue

        if in_code_block:
            new_lines.append(line)
            continue

        if len(line) > MAX_LINE_LENGTH and not _is_exempted(path, line):
            reformatted = reformat_line(line)
            if reformatted != line:
                changed_lines += 1
                # Se quebrou em múltiplas linhas, adiciona cada uma
                new_lines.extend(reformatted.split("\n"))
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if changed_lines > 0:
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return changed_lines


def main() -> int:
    """Processa arquivos."""
    if len(sys.argv) == 1:  # noqa: SIM108
        paths = sorted(Path().rglob("*.md"))
    else:
        paths = [Path(p) for p in sys.argv[1:]]

    total_changed = 0
    for path in paths:
        if not path.exists():
            continue
        changed = reformat_file(path)
        if changed > 0:
            print(f"{path}: {changed} linhas reformatadas")
            total_changed += changed

    print(f"\nTotal: {total_changed} linhas ajustadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
