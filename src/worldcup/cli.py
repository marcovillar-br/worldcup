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


CSV_COLUMNS = [
    "jogo", "data", "fase", "grupo", "mandante", "palpite", "visitante",
    "P_mandante", "P_empate", "P_visitante", "ousado", "mais_provavel",
    "prorrogacao", "penaltis", "avanca", "status", "placar_real",
]


def save_outputs(run: PredictionRun, year: int) -> tuple[Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / f"palpites-{year}.csv"
    md_path = OUT_DIR / f"palpites-{year}.md"
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(run.rows)
    md_path.write_text(render_markdown(run), encoding="utf-8")
    return csv_path, md_path


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
    csv_path, md_path = save_outputs(pred, args.edition)
    print_console_summary(pred)
    print(f"\n💾 CSV: {csv_path}\n💾 Markdown (pronto p/ copiar): {md_path}")
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
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
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
