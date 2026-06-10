"""Interface de linha de comando do worldcup.

Subcomandos:
  fetch-data     baixa e normaliza a base histórica
  predict        gera os palpites de uma edição (tabela + CSV + Markdown)
  sync-results   baixa os resultados reais da internet, preenche os jogos e repalpita
  record         registra/corrige manualmente o placar de um jogo (realimentação)
  backtest       valida o modelo numa Copa passada
"""

from __future__ import annotations

import argparse
import csv
import html
import sys
from pathlib import Path

from .edition import EDITIONS_DIR, load_edition
from .fetch_data import DEFAULT_CUTOFF, fetch
from .pipeline import PredictionRun, run

OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out"

_STAGE_LABEL = {
    "group": "Fase de Grupos",
    "R32": "32-avos de final",
    "R16": "Oitavas de final",
    "QF": "Quartas de final",
    "SF": "Semifinais",
    "3rd_place": "Disputa de 3º lugar",
    "final": "Final",
}


# ----------------------------------------------------------------- relatórios
def render_markdown(run: PredictionRun) -> str:
    e = run.edition
    out: list[str] = [f"# Palpites — {e.spec.name}", ""]

    champ = sorted(run.champion_prob.items(), key=lambda x: -x[1])[:8]
    if champ:
        from .teams import display

        out += ["## 🏆 Probabilidade de título (Monte Carlo)", ""]
        out += [f"- **{display(t)}** — {p*100:.1f}%" for t, p in champ]
        out += ["", f"_Palpite de campeão sugerido: **{display(champ[0][0])}**._", ""]

    by_stage: dict[str, list[dict]] = {}
    for r in run.rows:
        by_stage.setdefault(r["fase"], []).append(r)

    for stage, label in _STAGE_LABEL.items():
        rows = by_stage.get(stage)
        if not rows:
            continue
        out += [f"## {label}", ""]
        if stage == "group":
            out += ["| Jogo | Data | Grupo | Mandante | Palpite | Visitante | Probabilidades | Ousado | + provável |",
                    "|---|---|---|---|---|---|---|---|---|"]
            for r in rows:
                probs = f"{r['P_mandante']}/{r['P_empate']}/{r['P_visitante']}"
                out.append(
                    f"| {r['jogo']} | {r['data']} | {r['grupo']} | {r['mandante']} | "
                    f"**{r['palpite']}** | {r['visitante']} | {probs} | {r['ousado']} | "
                    f"{r['mais_provavel']} |"
                )
        else:
            out += ["| Jogo | Data | Confronto | Palpite (90') | Prorrogação | Pênaltis | Avança |",
                    "|---|---|---|---|---|---|---|"]
            for r in rows:
                out.append(
                    f"| {r['jogo']} | {r['data']} | {r['mandante']} x {r['visitante']} | "
                    f"**{r['palpite']}** | {r['prorrogacao']} | {r['penaltis']} | "
                    f"**{r['avanca']}** |"
                )
        out.append("")

    out += ["---",
            "_Sistema I (probabilístico): o placar de cada jogo maximiza os pontos esperados. "
            "⚡ marca palpites ousados (contra o favorito). Ajuste o risco em `scoring.toml`._"]
    return "\n".join(out)


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
@media print {
  body { padding: 0; font-size: 11px; max-width: none; }
  h2 { break-after: avoid; }
  section { break-inside: avoid; }
  tr { break-inside: avoid; }
  .pick, .champ { break-inside: avoid; }
}
"""


def render_html(run: PredictionRun) -> str:
    from .teams import display

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
                f'<span class="val">{p*100:.1f}%</span></div>'
            )
        parts.append("</div>")
        parts.append(f'<p class="pick">Palpite de campeão sugerido: <b>{_esc(display(champ[0][0]))}</b></p>')
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
                ph, pd_, pa = _pct(r["P_mandante"]), _pct(r["P_empate"]), _pct(r["P_visitante"])
                score = r["placar_real"] if final else r["palpite"]
                tag = ('<span class="tag fin">final</span>' if final
                       else ('<span class="bolt tag">⚡ zebra</span>' if upset else ""))
                parts.append(
                    f"<tr class='{cls}'><td class='num'>{_esc(r['jogo'])}</td><td>{_esc(r['data'])}</td>"
                    f"<td class='num'>{_esc(r['grupo'])}</td><td>{_esc(r['mandante'])}</td>"
                    f"<td class='num score'>{_esc(score)}</td><td>{_esc(r['visitante'])}</td>"
                    f"<td class='num'>{ph}/{pd_}/{pa}</td>"
                    f"<td><span class='bar'><i class='h' style='width:{ph}%'></i>"
                    f"<i class='d' style='width:{pd_}%'></i><i class='a' style='width:{pa}%'></i></span></td>"
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
        "Linhas em cinza são jogos já disputados (placar real). "
        "Cada palpite no app fecha 5 minutos antes do jogo.</p>"
    )
    parts.append("</body></html>")
    return "\n".join(parts)


CSV_COLUMNS = [
    "jogo", "data", "fase", "grupo", "mandante", "palpite", "visitante",
    "P_mandante", "P_empate", "P_visitante", "ousado", "mais_provavel",
    "prorrogacao", "penaltis", "avanca", "status", "placar_real",
]


def save_outputs(run: PredictionRun, year: int) -> tuple[Path, Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / f"palpites-{year}.csv"
    md_path = OUT_DIR / f"palpites-{year}.md"
    html_path = OUT_DIR / f"palpites-{year}.html"
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(run.rows)
    md_path.write_text(render_markdown(run), encoding="utf-8")
    html_path.write_text(render_html(run), encoding="utf-8")
    return csv_path, md_path, html_path


def print_console_summary(run: PredictionRun) -> None:
    from .teams import display

    champ = sorted(run.champion_prob.items(), key=lambda x: -x[1])[:5]
    print("\n🏆 Candidatos a campeão:")
    for t, p in champ:
        print(f"   {display(t):16s} {p*100:4.1f}%")

    upcoming = [r for r in run.rows if r["status"] == "PREVISTO"]
    print(f"\n📋 Próximos jogos a palpitar (mostrando até 12 de {len(upcoming)}):")
    for r in upcoming[:12]:
        if r["fase"] == "group":
            print(f"   J{r['jogo']:>3} {r['data']} [{r['grupo']}] "
                  f"{r['mandante']:>16} {r['palpite']:>4} {r['visitante']:<16} "
                  f"({r['P_mandante']}/{r['P_empate']}/{r['P_visitante']}) {r['ousado']}")
        else:
            print(f"   J{r['jogo']:>3} {r['data']} [{r['fase']:>9}] "
                  f"{r['mandante']:>16} {r['palpite']:>4} {r['visitante']:<16} "
                  f"-> avança {r['avanca']}")


# ----------------------------------------------------------------- subcomandos
def cmd_fetch_data(args: argparse.Namespace) -> int:
    path = fetch(cutoff=args.cutoff)
    print(f"✅ Base histórica salva em {path}")
    return 0


def cmd_predict(args: argparse.Namespace) -> int:
    edition = load_edition(args.edition)
    if args.risk is not None:
        edition.scoring.risk = args.risk
    print(f"⚙️  Gerando palpites de {edition.spec.name} ({args.sims} simulações)...")
    pred = run(edition, n_sims=args.sims, seed=args.seed)
    csv_path, md_path, html_path = save_outputs(pred, args.edition)
    print_console_summary(pred)
    print(f"\n💾 CSV: {csv_path}\n💾 Markdown (pronto p/ copiar): {md_path}"
          f"\n💾 HTML (visualizar/imprimir): {html_path}")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    path = EDITIONS_DIR / str(args.edition) / "fixtures.csv"
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    found = False
    for r in rows:
        if int(r["match_id"]) == args.match:
            r["home_goals"], r["away_goals"] = str(args.home), str(args.away)
            if args.ko_winner:
                r["ko_outcome"] = args.ko_winner
            found = True
            break
    if not found:
        print(f"❌ Jogo {args.match} não encontrado em {path}", file=sys.stderr)
        return 1
    from .sync import write_fixtures_atomic

    write_fixtures_atomic(path, rows)
    print(f"✅ Jogo {args.match} registrado: {args.home}x{args.away}. "
          f"Rode `worldcup predict --edition {args.edition}` para repalpitar.")
    return 0


def cmd_sync_results(args: argparse.Namespace) -> int:
    from .sync import sync_results

    print("🌐 Baixando resultados reais da fonte pública...")
    counts = sync_results(args.edition)
    print(f"✅ Sincronizado: {counts['group']} jogos de grupo + {counts['knockout']} de mata-mata "
          f"preenchidos ({counts['total_played_in_source']} jogos da Copa já disputados na fonte).")
    if args.no_predict:
        print(f"Rode `worldcup predict --edition {args.edition}` para repalpitar.")
        return 0
    return cmd_predict(args)


def cmd_backtest(args: argparse.Namespace) -> int:
    from .backtest import run_backtest

    run_backtest(args.edition, n_sims=args.sims)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="worldcup", description="Gerador de palpites de bolão da Copa")
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch-data", help="baixa e normaliza a base histórica")
    f.add_argument("--cutoff", default=DEFAULT_CUTOFF, help="data mínima (YYYY-MM-DD)")
    f.set_defaults(func=cmd_fetch_data)

    pr = sub.add_parser("predict", help="gera os palpites de uma edição")
    pr.add_argument("--edition", type=int, default=2026)
    pr.add_argument("--sims", type=int, default=5000, help="nº de simulações Monte Carlo")
    pr.add_argument("--seed", type=int, default=12345)
    pr.add_argument("--risk", type=float, default=None, help="sobrescreve o risco (0..1)")
    pr.set_defaults(func=cmd_predict)

    rc = sub.add_parser("record", help="registra o placar real de um jogo")
    rc.add_argument("--edition", type=int, default=2026)
    rc.add_argument("--match", type=int, required=True, help="match_id do jogo")
    rc.add_argument("--home", type=int, required=True, help="gols do mandante")
    rc.add_argument("--away", type=int, required=True, help="gols do visitante")
    rc.add_argument("--ko-winner", default=None, help="vencedor (mata-mata em caso de empate nos 90')")
    rc.set_defaults(func=cmd_record)

    sr = sub.add_parser("sync-results", help="baixa resultados reais e repalpita")
    sr.add_argument("--edition", type=int, default=2026)
    sr.add_argument("--sims", type=int, default=5000)
    sr.add_argument("--seed", type=int, default=12345)
    sr.add_argument("--risk", type=float, default=None)
    sr.add_argument("--no-predict", action="store_true", help="só sincroniza, não repalpita")
    sr.set_defaults(func=cmd_sync_results)

    bt = sub.add_parser("backtest", help="valida o modelo numa Copa passada")
    bt.add_argument("--edition", type=int, default=2022)
    bt.add_argument("--sims", type=int, default=2000)
    bt.set_defaults(func=cmd_backtest)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
