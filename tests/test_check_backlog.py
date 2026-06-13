"""Testes do checker de integridade do BACKLOG.md (scripts/check_backlog.py).

Roda o script como subprocess (ele vive em scripts/, fora do pacote) sobre arquivos temporários.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_backlog.py"

_OK = """\
| ID | Pri | Área | Status | Item |
|----|-----|------|--------|------|
| [ENG-1](#eng-1) | P1 | sync | ✅ | feito |
| [ENG-2](#eng-2) | P2 | x | 🔴 | aberto |

## ENG-1
**t** · P1 · `a` · ✅ feito
**Commit:** abc1234

## ENG-2
**t** · P2 · `b` · 🔴 todo
**Commit:** —
"""


def _run(content: str, tmp_path: Path) -> subprocess.CompletedProcess:
    f = tmp_path / "BACKLOG.md"
    f.write_text(content, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(f)], capture_output=True, text=True)


def test_valid_backlog_passes(tmp_path):
    assert _run(_OK, tmp_path).returncode == 0


def test_status_divergence_fails(tmp_path):
    bad = _OK.replace("| [ENG-2](#eng-2) | P2 | x | 🔴 |", "| [ENG-2](#eng-2) | P2 | x | 🟡 |")
    r = _run(bad, tmp_path)
    assert r.returncode == 1
    assert "status diverge" in r.stderr


def test_done_without_commit_fails(tmp_path):
    bad = _OK.replace("**Commit:** abc1234", "**Commit:** —")
    r = _run(bad, tmp_path)
    assert r.returncode == 1
    assert "sem ref de commit" in r.stderr


def test_index_without_detail_fails(tmp_path):
    # remove a seção de detalhe do ENG-2
    bad = _OK.split("## ENG-2")[0]
    r = _run(bad, tmp_path)
    assert r.returncode == 1
    assert "sem seção de detalhe" in r.stderr


def test_real_backlog_is_valid():
    real = SCRIPT.parent.parent / "docs" / "BACKLOG.md"
    r = subprocess.run([sys.executable, str(SCRIPT), str(real)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
