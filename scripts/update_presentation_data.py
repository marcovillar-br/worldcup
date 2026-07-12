#!/usr/bin/env python3
"""Atualiza os campos **deriváveis** de `data/editions/<edição>/presentation.toml` a partir do
estado atual: `out/palpites-<edição>.{csv,md}` (jogos disputados, favoritos ao título),
`docs/BACKLOG.md` (melhorias entregues) e `blend-track` (Brier modelo vs. blend).

Roda logo depois de `sync-results --archive`/`predict --archive`, antes de
`build_presentation.py --docs` — é o passo que fecha o loop de "atualizar a apresentação sozinho"
depois de "atualizar os palpites".

**Não toca** em campos que exigem dado externo ou curadoria editorial: `campanha.pontos` e
`campanha.eficiencia_pct` (só existem no seu placar real do bolão — ninguém deriva isso de dado
local); `campanha.fase` e `bracket_destaque.*` (qual seleção acompanhar, qual jogo destacar — é
escolha de narrativa, não cálculo). O script avisa que esses campos merecem revisão manual.

Uso: `uv run python scripts/update_presentation_data.py [--edition 2026]`
"""

from __future__ import annotations

import argparse
import csv
import datetime
import math
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

_MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
_CHAMP_LINE = re.compile(r"^- \*\*(.+?)\*\* — ([\d.]+)%$", re.MULTILINE)


def _format_as_of(d: datetime.date) -> str:
    return f"{d.day:02d} {_MESES_PT[d.month - 1]} {d.year}"


def _count_played(csv_path: Path) -> tuple[int, int]:
    """(jogos disputados, total) via a coluna `status` do CSV de palpites."""
    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return sum(1 for r in rows if r["status"] == "FINAL"), len(rows)


def _top_favoritos(md_path: Path, n: int = 5) -> list[dict[str, Any]]:
    """As `n` maiores probabilidades de campeão, lidas da seção Monte Carlo do `palpites.md`."""
    text = md_path.read_text(encoding="utf-8")
    return [{"nome": nome, "pct": float(pct)} for nome, pct in _CHAMP_LINE.findall(text)[:n]]


def _melhorias_entregues(backlog_path: Path) -> int:
    return backlog_path.read_text(encoding="utf-8").count("✅")


def _validacao(edition: int) -> dict[str, Any] | None:
    """Brier modelo-puro vs. blend nos jogos de grupo já disputados com odds (mesma métrica do
    `worldcup blend-track`), via chamada direta à biblioteca — evita parsear stdout do CLI."""
    from worldcup.backtest import prospective_blend_report
    from worldcup.edition import load_edition

    res = prospective_blend_report(load_edition(edition))
    if res.n == 0:
        return None
    # floor (não round): garante que a barra do blend fique visivelmente menor sempre que ele
    # reduzir o Brier — mesmo por margem pequena — em vez de arredondar para o mesmo tamanho.
    width_blend = math.floor(res.brier_blend / res.brier_model * 100) if res.brier_model else 100
    return {
        "brier_modelo": round(res.brier_model, 3),
        "brier_modelo_width_pct": 100,
        "brier_blend": round(res.brier_blend, 3),
        "brier_blend_width_pct": width_blend,
        "jogos_rastreados": res.n,
    }


def render_toml(edition: int, data: dict[str, Any]) -> str:
    """Serializa `data` de volta ao formato do `presentation.toml` (mesmo layout do arquivo original;
    `tomllib` só lê, então a escrita é um template — não uma lib de TOML genérica)."""
    c, b, v, e = data["campanha"], data["bracket_destaque"], data["validacao"], data["evolucao"]
    favoritos_block = "\n".join(
        f'[[campanha.favoritos]]\nnome = "{f["nome"]}"\npct = {f["pct"]}' for f in c["favoritos"]
    )
    # o caminho é uma LISTA de passos (não slots fixos qf/sf/final): a seleção em destaque avança de
    # fase e o passo antigo deixa de existir. Com slots fixos, o deck continuava anunciando "bate a
    # Suíça (QF, 55%)" depois da Suíça já ter sido eliminada. `pct` é opcional (a final não tem).
    passos_block = "\n\n".join(
        "[[bracket_destaque.passos]]\n"
        + f'fase = "{p["fase"]}"\nrival = "{p["rival"]}"'
        + (f"\npct = {p['pct']}" if p.get("pct") is not None else "")
        for p in b["passos"]
    )
    return f"""# Dados vivos do deck de apresentação (scripts/build_presentation.py --edition {edition}).
#
# Números da campanha que mudam a cada rodada — extraídos do código para que o script fique
# agnóstico à edição (nenhum número de campanha vive em scripts/build_presentation.py).
# Campos deriváveis (jogos_disputados, favoritos, validacao, evolucao) são atualizados por
# scripts/update_presentation_data.py; os demais (pontos, eficiencia_pct, fase, bracket_destaque)
# exigem input do usuário ou curadoria editorial — revise-os manualmente a cada rodada.

as_of = "{data["as_of"]}"

[campanha]
jogos_disputados = {c["jogos_disputados"]}
pontos = {c["pontos"]}
eficiencia_pct = {c["eficiencia_pct"]}
fase = "{c["fase"]}"

{favoritos_block}

[bracket_destaque]
selecao = "{b["selecao"]}"
jogos_para_ficar_de_olho = "{b["jogos_para_ficar_de_olho"]}"

{passos_block}

[validacao]
brier_modelo = {v["brier_modelo"]}
brier_modelo_width_pct = {v["brier_modelo_width_pct"]}
brier_blend = {v["brier_blend"]}
brier_blend_width_pct = {v["brier_blend_width_pct"]}
jogos_rastreados = {v["jogos_rastreados"]}

[evolucao]
melhorias_entregues = {e["melhorias_entregues"]}
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--edition", type=int, default=2026, help="edição a atualizar (default: 2026)")
    args = p.parse_args(argv)
    edition_dir = PROJECT_ROOT / "data" / "editions" / str(args.edition)

    toml_path = edition_dir / "presentation.toml"
    with toml_path.open("rb") as f:
        data = tomllib.load(f)

    csv_path = PROJECT_ROOT / "out" / f"palpites-{args.edition}.csv"
    md_path = PROJECT_ROOT / "out" / f"palpites-{args.edition}.md"
    played, total = _count_played(csv_path)
    data["campanha"]["jogos_disputados"] = played
    favoritos = _top_favoritos(md_path)
    data["campanha"]["favoritos"] = favoritos

    data["evolucao"]["melhorias_entregues"] = _melhorias_entregues(PROJECT_ROOT / "docs" / "BACKLOG.md")

    validacao = _validacao(args.edition)
    if validacao is not None:
        data["validacao"] = validacao

    data["as_of"] = _format_as_of(datetime.date.today())

    toml_path.write_text(render_toml(args.edition, data), encoding="utf-8")

    print(f"✅ presentation.toml: {played}/{total} jogos, {len(favoritos)} favoritos, as_of={data['as_of']}")
    if validacao is None:
        print("ℹ️  blend-track sem jogos com odds ainda — validacao.* preservada como estava.")
    print(
        "⚠️  Revise manualmente: campanha.pontos, campanha.eficiencia_pct (exigem seu placar real), "
        "campanha.fase e bracket_destaque.* (curadoria editorial do bracket em destaque)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
