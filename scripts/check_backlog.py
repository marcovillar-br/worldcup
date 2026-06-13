#!/usr/bin/env python3
"""Checagem de integridade do docs/BACKLOG.md (hook de pre-commit, stdlib pura).

Garante as invariantes que prosa não garante:
  - IDs únicos (sem colisão no índice nem no detalhe);
  - índice ↔ detalhe casados (todo ID do índice tem seção e vice-versa);
  - status do índice == status do detalhe (o clássico que desincroniza);
  - item ✅ (feito) tem ref de commit preenchida (não "—").

Uso: `check_backlog.py [caminho...]` (default: docs/BACKLOG.md). Sai com código 1 e mensagens
claras se houver violação; 0 se estiver íntegro. Não depende de terceiros.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STATUS_EMOJIS = {"🔴", "🟡", "✅", "⚪"}
DONE = "✅"

# Linha do índice: | [ENG-1](#eng-1) | P1 | sync | 🔴 | título |
_INDEX_ROW = re.compile(r"^\|\s*\[(?P<id>[A-Z]+-\d+)\]\(#[^)]+\)\s*\|[^|]*\|[^|]*\|\s*(?P<status>\S+)\s*\|")
# Cabeçalho de detalhe: ## ENG-1
_DETAIL_HEAD = re.compile(r"^##\s+(?P<id>[A-Z]+-\d+)\s*$")
# Ref de commit no detalhe: **Commit:** abc1234  (ou "—" quando ainda aberto)
_COMMIT_LINE = re.compile(r"^\*\*Commit:\*\*\s*(?P<ref>.+?)\s*$")


def _first_emoji(text: str) -> str | None:
    for ch in text:
        if ch in STATUS_EMOJIS:
            return ch
    return None


def check(path: Path) -> list[str]:
    """Retorna a lista de problemas encontrados (vazia = íntegro)."""
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    index_status: dict[str, str] = {}
    for ln in lines:
        m = _INDEX_ROW.match(ln)
        if not m:
            continue
        iid, status = m.group("id"), m.group("status")
        if iid in index_status:
            errors.append(f"{path}: ID duplicado no índice: {iid}")
        if status not in STATUS_EMOJIS:
            errors.append(f"{path}: {iid}: status do índice inválido: {status!r} (use {sorted(STATUS_EMOJIS)})")
        index_status[iid] = status

    # detalhe: status (1º emoji após o cabeçalho) e ref de commit
    detail_status: dict[str, str] = {}
    detail_commit: dict[str, str] = {}
    current: str | None = None
    for ln in lines:
        head = _DETAIL_HEAD.match(ln)
        if head:
            current = head.group("id")
            if current in detail_status:
                errors.append(f"{path}: seção de detalhe duplicada: {current}")
            detail_status[current] = ""  # marca presença; emoji preenchido abaixo
            continue
        if current is None:
            continue
        if not detail_status.get(current):
            emoji = _first_emoji(ln)
            if emoji:
                detail_status[current] = emoji
        cm = _COMMIT_LINE.match(ln)
        if cm and current not in detail_commit:
            detail_commit[current] = cm.group("ref")

    index_ids, detail_ids = set(index_status), set(detail_status)
    for iid in sorted(index_ids - detail_ids):
        errors.append(f"{path}: {iid} no índice sem seção de detalhe (## {iid})")
    for iid in sorted(detail_ids - index_ids):
        errors.append(f"{path}: {iid} tem detalhe mas falta no índice")

    for iid in sorted(index_ids & detail_ids):
        si, sd = index_status[iid], detail_status[iid]
        if not sd:
            errors.append(f"{path}: {iid}: detalhe sem status (emoji)")
        elif si != sd:
            errors.append(f"{path}: {iid}: status diverge — índice {si} vs detalhe {sd}")
        ref = detail_commit.get(iid, "—")
        if (si == DONE or sd == DONE) and ref.strip() in {"", "—", "-"}:
            errors.append(f"{path}: {iid}: marcado ✅ mas sem ref de commit (**Commit:**)")

    return errors


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv] or [Path("docs/BACKLOG.md")]
    problems: list[str] = []
    for p in paths:
        if p.name != "BACKLOG.md":
            continue
        if not p.exists():
            problems.append(f"{p}: arquivo não encontrado")
            continue
        problems.extend(check(p))
    if problems:
        print("❌ BACKLOG.md com problemas de integridade:", file=sys.stderr)
        for e in problems:
            print(f"   - {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
