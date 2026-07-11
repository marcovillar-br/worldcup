#!/usr/bin/env python3
"""Verifica a **coerência interna** do palpite renderizado (ENG-52) — ferramenta on-demand.

Confronta partes da mesma tabela entre si (encadeamento do bracket, avança ∈ participantes, sem time
repetido na rodada, 1×2 ~100%). Uma tabela que se autocontradiz é bug de derivação, não opinião
(ver ENG-51). O `pipeline.run` já roda estas checagens como asserção dura;
este script as roda sobre um `out/palpites-<ano>.csv` já gravado, sem refazer a simulação.

Uso:
  uv run python scripts/check_output_consistency.py --edition 2026
  uv run python scripts/check_output_consistency.py --csv out/palpites-2026.csv --edition 2026

Sai com código 1 se houver qualquer violação (útil em pipe/CI local).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from worldcup.consistency import check_prediction_consistency
from worldcup.edition import load_edition

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Coerência interna do palpite renderizado (ENG-52)")
    p.add_argument("--edition", type=int, default=2026)
    p.add_argument("--csv", type=Path, default=None, help="CSV do palpite (default: out/palpites-<ano>.csv)")
    args = p.parse_args(argv)

    csv_path = args.csv or PROJECT_ROOT / "out" / f"palpites-{args.edition}.csv"
    if not csv_path.exists():
        print(f"❌ não encontrei {csv_path} — rode `uv run worldcup predict --edition {args.edition}` antes.")
        return 2

    with csv_path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    edition = load_edition(args.edition)
    violations = check_prediction_consistency(edition, rows)

    if not violations:
        print(f"✅ {csv_path.name}: {len(rows)} jogos, coerência interna íntegra (INV-1 a INV-4).")
        return 0

    print(f"🚨 {csv_path.name}: {len(violations)} violação(ões) de coerência interna:")
    for v in violations:
        print(f"   • {v}")
    print("\nUma tabela que se autocontradiz é bug de derivação (ver ENG-51/52), não palpite.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
