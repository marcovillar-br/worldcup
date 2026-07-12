"""Camada de apresentação dos palpites: Markdown, HTML e o esquema do CSV.

Funções **puras** — recebem um `PredictionRun` e devolvem texto; nenhuma escrita em disco
(isso é orquestração da CLI, em `cli.save_outputs`/`archive_outputs`). O HTML é autocontido e
otimizado para impressão; o CSV é o formato canônico/diffável.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

from .teams import display

if TYPE_CHECKING:
    from .pipeline import PredictionRun

_STAGE_LABEL = {
    "group": "Fase de Grupos",
    "R32": "16-avos de final",
    "R16": "Oitavas de final",
    "QF": "Quartas de final",
    "SF": "Semifinais",
    "3rd_place": "Disputa de 3º lugar",
    "final": "Final",
}

CSV_COLUMNS = [
    "jogo",
    "data",
    "fase",
    "grupo",
    "mandante",
    "palpite",
    "visitante",
    "P_mandante",
    "P_empate",
    "P_visitante",
    "ousado",
    "mais_provavel",
    "prorrogacao",
    "penaltis",
    "avanca",
    "status",
    "placar_real",
]


def _bracket_champion(run: PredictionRun) -> str:
    """Campeão do **bracket determinístico** = quem avança na final (nome de exibição; '' se não há)."""
    final = next((r for r in run.rows if r["fase"] == "final"), None)
    return final["avanca"] if final and final.get("avanca") else ""


def _champion_note(favorite_display: str, bracket_champion: str) -> str | None:
    """Explicação do INV-7 (ENG-52): favorito marginal ≠ campeão do bracket modal — quando diferem.

    O bolão pontua o **slot de campeão** e os **slots de placar** separadamente. O palpite de campeão
    é o favorito por probabilidade de título; o bracket é o cenário mais provável **jogo a jogo** e
    pode coroar outro time. Respondem perguntas diferentes; não se contradizem.
    """
    if not favorite_display or not bracket_champion or favorite_display == bracket_champion:
        return None
    return (
        f"O palpite de campeão é {favorite_display}, o favorito por probabilidade de título. "
        f"No cenário mais provável jogo a jogo (o bracket abaixo), quem levanta a taça é "
        f"{bracket_champion} — as duas leituras respondem perguntas diferentes (chance de título vs. "
        f"resultado mais provável de cada jogo) e o bolão pontua o campeão e os placares em slots "
        f"separados. Para o slot de campeão, marque o favorito ({favorite_display})."
    )


# ----------------------------------------------------------------- Markdown
def render_markdown(run: PredictionRun) -> str:
    e = run.edition
    out: list[str] = [f"# Palpites — {e.spec.name}", ""]

    champ = sorted(run.champion_prob.items(), key=lambda x: -x[1])[:8]
    if champ:
        out += ["## 🏆 Probabilidade de título (Monte Carlo)", ""]
        out += [f"- **{display(t)}** — {p * 100:.1f}%" for t, p in champ]
        out += ["", f"_Palpite de campeão sugerido: **{display(champ[0][0])}**._", ""]
        note = _champion_note(display(champ[0][0]), _bracket_champion(run))
        if note:
            out += [f"> ℹ️ {note}", ""]

    by_stage: dict[str, list[dict]] = {}
    for r in run.rows:
        by_stage.setdefault(r["fase"], []).append(r)

    for stage, label in _STAGE_LABEL.items():
        rows = by_stage.get(stage)
        if not rows:
            continue
        out += [f"## {label}", ""]
        if stage == "group":
            out += [
                "| Jogo | Data | Grupo | Mandante | Palpite | Visitante | Probabilidades | Ousado | + provável |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
            for r in rows:
                # jogo FINAL não tem previsão (já aconteceu) — "—" em vez de "//" das colunas vazias
                probs = "—" if r["status"] == "FINAL" else f"{r['P_mandante']}/{r['P_empate']}/{r['P_visitante']}"
                out.append(
                    f"| {r['jogo']} | {r['data']} | {r['grupo']} | {r['mandante']} | "
                    f"**{r['palpite']}** | {r['visitante']} | {probs} | {r['ousado']} | "
                    f"{r['mais_provavel']} |"
                )
        else:
            out += [
                "| Jogo | Data | Confronto | Palpite (90') | Prorrogação | Pênaltis | Avança |",
                "|---|---|---|---|---|---|---|",
            ]
            for r in rows:
                out.append(
                    f"| {r['jogo']} | {r['data']} | {r['mandante']} x {r['visitante']} | "
                    f"**{r['palpite']}** | {r['prorrogacao']} | {r['penaltis']} | "
                    f"**{r['avanca']}** |"
                )
        out.append("")

    out += [
        "---",
        "_Sistema I (probabilístico): o placar de cada jogo maximiza os pontos esperados. "
        "⚡ marca palpites ousados (contra o favorito). Ajuste o risco em `scoring.toml`._",
    ]
    return "\n".join(out)


# --------------------------------------------------------------------- HTML
def _esc(value: object) -> str:
    """Escapa texto para inserção segura em HTML — inclusive aspas (contexto de atributo)."""
    return html.escape(str(value), quote=True)


def _pct(value: str) -> int:
    """Converte '73%' -> 73 (0 se não parseável)."""
    try:
        return int(str(value).rstrip("%"))
    except ValueError:
        return 0


_HTML_STYLE = """
:root { --ink:#1a1a1a; --muted:#6b7280; --line:#e5e7eb; --home:#2563eb;
        --draw:#9ca3af; --away:#dc2626; --upset:#b45309; --final:#f3f4f6; }
* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
       color: var(--ink); margin: 0; padding: 2rem 1.25rem 4rem; line-height: 1.45;
       max-width: 1040px; margin-inline: auto; -webkit-print-color-adjust: exact;
       print-color-adjust: exact; }
h1 { font-size: 1.6rem; margin: 0 0 .25rem; }
h2 { font-size: 1.15rem; margin: 2rem 0 .6rem; padding-bottom: .3rem;
     border-bottom: 2px solid var(--line); }
.sub { color: var(--muted); font-size: .85rem; margin: 0 0 1.5rem; }
.champ { display: grid; gap: .35rem; margin: .5rem 0 0; }
.champ .row { display: grid; grid-template-columns: 11rem 1fr 3rem; align-items: center;
              gap: .6rem; font-size: .9rem; }
.champ .name { font-weight: 600; }
.champ .track { background: var(--line); border-radius: 999px; height: .8rem; overflow: hidden; }
.champ .fill { display: block; background: linear-gradient(90deg,#1d4ed8,#3b82f6); height: 100%; }
.champ .val { text-align: right; font-variant-numeric: tabular-nums; color: var(--muted); }
.pick { text-align: center; padding: .5rem .75rem; background: #eff6ff;
        border: 1px solid #bfdbfe; border-radius: 8px; margin: .75rem 0 0; font-size: .9rem; }
.note { padding: .5rem .75rem; background: #fffbeb; border: 1px solid #fde68a;
        border-radius: 8px; margin: .5rem 0 0; font-size: .8rem; color: #713f12; line-height: 1.5; }
table { width: 100%; border-collapse: collapse; font-size: .82rem; }
th, td { padding: .4rem .55rem; text-align: left; border-bottom: 1px solid var(--line);
         vertical-align: middle; }
th { font-size: .72rem; text-transform: uppercase; letter-spacing: .03em; color: var(--muted);
     background: #fafafa; }
td.num, th.num { text-align: center; font-variant-numeric: tabular-nums; }
.score { font-weight: 700; white-space: nowrap; }
tr.upset td.score { color: var(--upset); }
tr.upset .bolt { color: var(--upset); }
tr.final { background: var(--final); color: var(--muted); }
tr.final .score { color: var(--muted); }
.bar { display: inline-flex; width: 90px; height: .65rem; border-radius: 999px;
       overflow: hidden; vertical-align: middle; border: 1px solid var(--line); }
.bar i { display: block; height: 100%; }
.bar .h { background: var(--home); } .bar .d { background: var(--draw); } .bar .a { background: var(--away); }
.tag { display: inline-block; font-size: .68rem; padding: .05rem .4rem; border-radius: 999px;
       background: #fef3c7; color: var(--upset); font-weight: 600; }
.tag.fin { background: #e5e7eb; color: var(--muted); }
.legend { margin-top: 2.5rem; font-size: .78rem; color: var(--muted); border-top: 1px solid var(--line);
          padding-top: 1rem; }
.legend b { color: var(--ink); }
@page { size: A4 landscape; margin: 1.2cm 1.5cm; }
@media print {
  body { padding: 0; font-size: 11px; max-width: none; }
  h2 { break-after: avoid; }
  section { break-inside: avoid; }
  tr { break-inside: avoid; }
  .pick, .champ, .note { break-inside: avoid; }
}
"""


def render_html(run: PredictionRun) -> str:
    e = run.edition
    parts: list[str] = [
        "<!doctype html>",
        '<html lang="pt-BR"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>Palpites — {_esc(e.spec.name)}</title>",
        f"<style>{_HTML_STYLE}</style></head><body>",
        f"<h1>🏆 Palpites — {_esc(e.spec.name)}</h1>",
        '<p class="sub">Sistema I (probabilístico) — placar que maximiza os pontos esperados. '
        "⚡ marca palpites ousados (contra o favorito).</p>",
    ]

    champ = sorted(run.champion_prob.items(), key=lambda x: -x[1])[:8]
    if champ:
        top = champ[0][1]
        parts.append("<section><h2>Probabilidade de título (Monte Carlo)</h2>")
        parts.append('<div class="champ">')
        for team, p in champ:
            width = (p / top * 100) if top else 0
            parts.append(
                f'<div class="row"><span class="name">{_esc(display(team))}</span>'
                f'<span class="track"><span class="fill" style="width:{width:.1f}%"></span></span>'
                f'<span class="val">{p * 100:.1f}%</span></div>'
            )
        parts.append("</div>")
        parts.append(f'<p class="pick">Palpite de campeão sugerido: <b>{_esc(display(champ[0][0]))}</b></p>')
        note = _champion_note(display(champ[0][0]), _bracket_champion(run))
        if note:
            parts.append(f'<p class="note">ℹ️ {_esc(note)}</p>')
        parts.append("</section>")

    by_stage: dict[str, list[dict]] = {}
    for r in run.rows:
        by_stage.setdefault(r["fase"], []).append(r)

    for stage, label in _STAGE_LABEL.items():
        rows = by_stage.get(stage)
        if not rows:
            continue
        parts.append(f"<section><h2>{_esc(label)}</h2><table>")
        if stage == "group":
            parts.append(
                "<thead><tr><th class='num'>Jogo</th><th>Data</th><th class='num'>Grupo</th>"
                "<th>Mandante</th><th class='num'>Palpite</th><th>Visitante</th>"
                "<th class='num'>M / E / V</th><th>Prob.</th><th></th></tr></thead><tbody>"
            )
            for r in rows:
                final = r["status"] == "FINAL"
                upset = bool(r["ousado"]) and not final
                cls = "final" if final else ("upset" if upset else "")
                score = r["placar_real"] if final else r["palpite"]
                tag = (
                    '<span class="tag fin">final</span>'
                    if final
                    else ('<span class="bolt tag">⚡ zebra</span>' if upset else "")
                )
                if final:
                    # jogo já aconteceu — sem previsão: "—" nas duas colunas (M/E/V e Prob.),
                    # não "0/0/0" + barra vazia (parecia buraco de render)
                    mev = "<td class='num'>—</td><td class='num'>—</td>"
                else:
                    ph, pd_, pa = _pct(r["P_mandante"]), _pct(r["P_empate"]), _pct(r["P_visitante"])
                    mev = (
                        f"<td class='num'>{ph}/{pd_}/{pa}</td>"
                        f"<td><span class='bar'><i class='h' style='width:{ph}%'></i>"
                        f"<i class='d' style='width:{pd_}%'></i><i class='a' style='width:{pa}%'></i></span></td>"
                    )
                parts.append(
                    f"<tr class='{cls}'><td class='num'>{_esc(r['jogo'])}</td><td>{_esc(r['data'])}</td>"
                    f"<td class='num'>{_esc(r['grupo'])}</td><td>{_esc(r['mandante'])}</td>"
                    f"<td class='num score'>{_esc(score)}</td><td>{_esc(r['visitante'])}</td>"
                    f"{mev}"
                    f"<td>{tag}</td></tr>"
                )
        else:
            parts.append(
                "<thead><tr><th class='num'>Jogo</th><th>Data</th><th>Confronto</th>"
                "<th class='num'>Palpite (90')</th><th>Prorrogação</th><th>Pênaltis</th>"
                "<th>Avança</th></tr></thead><tbody>"
            )
            for r in rows:
                final = r["status"] == "FINAL"
                cls = "final" if final else ""
                score = r["placar_real"] if final else r["palpite"]
                parts.append(
                    f"<tr class='{cls}'><td class='num'>{_esc(r['jogo'])}</td><td>{_esc(r['data'])}</td>"
                    f"<td>{_esc(r['mandante'])} × {_esc(r['visitante'])}</td>"
                    f"<td class='num score'>{_esc(score)}</td><td>{_esc(r['prorrogacao'])}</td>"
                    f"<td>{_esc(r['penaltis'])}</td><td><b>{_esc(r['avanca'])}</b></td></tr>"
                )
        parts.append("</tbody></table></section>")

    parts.append(
        '<p class="legend">Barra de probabilidade: '
        '<b style="color:var(--home)">■</b> mandante · '
        '<b style="color:var(--draw)">■</b> empate · '
        '<b style="color:var(--away)">■</b> visitante. '
        "Linhas em cinza são jogos já disputados (placar real, no slot de 90'). "
        "Nas colunas de prorrogação e pênaltis, o nome é de quem venceu e o placar entre parênteses "
        "vem na ordem <b>mandante × visitante</b> (como o resto da tabela) — "
        "ex.: <i>Paraguai (3x4)</i> = Alemanha 3, Paraguai 4 nos pênaltis. "
        "Cada palpite no app fecha 5 minutos antes do jogo.</p>"
    )
    parts.append("</body></html>")
    return "\n".join(parts)
