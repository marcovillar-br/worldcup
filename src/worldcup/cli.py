"""Interface de linha de comando do worldcup.

Subcomandos:
  fetch-data     baixa e normaliza a base histórica
  predict        gera os palpites de uma edição (tabela + CSV + Markdown)
  sync-results   baixa os resultados reais da internet, preenche os jogos e repalpita
  record         registra/corrige manualmente o placar de um jogo (realimentação)
  backtest       valida o modelo numa Copa passada

A apresentação (Markdown/HTML/esquema do CSV) mora em `render.py`; aqui só orquestramos
(parsing de argumentos, escrita em disco e a saída de console).
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import date
from pathlib import Path

from .edition import EDITIONS_DIR, load_edition
from .fetch_data import DEFAULT_CUTOFF, DEFAULT_URL, DataSourceError, NetworkError, fetch
from .pipeline import PredictionRun, run
from .render import CSV_COLUMNS, render_html, render_markdown

OUT_DIR = Path(__file__).resolve().parent.parent.parent / "out"


# ----------------------------------------------------------------- escrita em disco
def save_outputs(run: PredictionRun, year: int) -> tuple[Path, Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / f"palpites-{year}.csv"
    md_path = OUT_DIR / f"palpites-{year}.md"
    html_path = OUT_DIR / f"palpites-{year}.html"
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(run.rows)
    md_path.write_text(render_markdown(run), encoding="utf-8")
    html_path.write_text(render_html(run), encoding="utf-8")
    return csv_path, md_path, html_path


def archive_outputs(run: PredictionRun, year: int, date_str: str, *, reconstructed: bool = False) -> tuple[Path, Path]:
    """Grava um snapshot imutável dos palpites do dia em `data/editions/<year>/history/`.

    Diferente de `out/` (regenerável e gitignored), o snapshot é **versionado**: depois que
    novos resultados entram e o modelo reajusta, o palpite de um dia não é mais reproduzível —
    é justamente essa não-reprodutibilidade que justifica guardar. Só CSV (canônico, diffável)
    + MD (legível); HTML fica de fora. `reconstructed=True` marca dias gerados a posteriori
    (sufixo no nome do arquivo + aviso no topo do MD), para não confundir com um run real.
    """
    hist = EDITIONS_DIR / str(year) / "history"
    hist.mkdir(parents=True, exist_ok=True)
    suffix = ".reconstruido" if reconstructed else ""
    csv_path = hist / f"{date_str}{suffix}.csv"
    md_path = hist / f"{date_str}{suffix}.md"
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(run.rows)
    md = render_markdown(run)
    if reconstructed:
        md = (
            f"> ⚠️ Snapshot **reconstruído** para {date_str}: gerado a posteriori reajustando o modelo "
            f"apenas com os resultados conhecidos até essa data. **Não** é o que a ferramenta produziu "
            f"naquele dia (o `out/` já fora sobrescrito) — é uma aproximação fiel à metodologia.\n\n"
        ) + md
    md_path.write_text(md, encoding="utf-8")
    return csv_path, md_path


def print_console_summary(run: PredictionRun) -> None:
    from .teams import display

    champ = sorted(run.champion_prob.items(), key=lambda x: -x[1])[:5]
    print("\n🏆 Candidatos a campeão:")
    for t, p in champ:
        print(f"   {display(t):16s} {p * 100:4.1f}%")

    upcoming = [r for r in run.rows if r["status"] == "PREVISTO"]
    print(f"\n📋 Próximos jogos a palpitar (mostrando até 12 de {len(upcoming)}):")
    for r in upcoming[:12]:
        if r["fase"] == "group":
            print(
                f"   J{r['jogo']:>3} {r['data']} [{r['grupo']}] "
                f"{r['mandante']:>16} {r['palpite']:>4} {r['visitante']:<16} "
                f"({r['P_mandante']}/{r['P_empate']}/{r['P_visitante']}) {r['ousado']}"
            )
        else:
            print(
                f"   J{r['jogo']:>3} {r['data']} [{r['fase']:>9}] "
                f"{r['mandante']:>16} {r['palpite']:>4} {r['visitante']:<16} "
                f"-> avança {r['avanca']}"
            )


# ----------------------------------------------------------------- subcomandos
def cmd_fetch_data(args: argparse.Namespace) -> int:
    urls = args.source_url or [DEFAULT_URL]
    path = fetch(urls=urls, cutoff=args.cutoff)
    print(f"✅ Base histórica salva em {path}")
    return 0


def cmd_predict(args: argparse.Namespace) -> int:
    edition = load_edition(args.edition)
    if args.risk is not None:
        edition.scoring.risk = args.risk
    if getattr(args, "blend_weight", None) is not None:
        edition.scoring.blend_weight = args.blend_weight

    as_of = getattr(args, "as_of", None)
    if as_of is not None:
        try:
            as_of = date.fromisoformat(as_of).isoformat()
        except ValueError:
            print(f"❌ --as-of inválido: {as_of!r}. Use AAAA-MM-DD.", file=sys.stderr)
            return 1
        # Visão reconstruída: não sobrescreve out/ (palpites vivos da campanha); grava só no history/.
        edition = edition.as_of(as_of)
        print(f"⏪ Visão reconstruída de {as_of} ({edition.spec.name}, {args.sims} simulações)...")
        print("   usando apenas os resultados conhecidos até a véspera; out/ não será alterado.")
        pred = run(edition, n_sims=args.sims, seed=args.seed)
        print_console_summary(pred)
        a_csv, _a_md = archive_outputs(pred, args.edition, as_of, reconstructed=True)
        print(f"\n🗄️  Snapshot reconstruído: {a_csv}")
        return 0

    print(f"⚙️  Gerando palpites de {edition.spec.name} ({args.sims} simulações)...")
    pred = run(edition, n_sims=args.sims, seed=args.seed)
    csv_path, md_path, html_path = save_outputs(pred, args.edition)
    print_console_summary(pred)
    print(
        f"\n💾 CSV: {csv_path}\n💾 Markdown (pronto p/ copiar): {md_path}\n💾 HTML (visualizar/imprimir): {html_path}"
    )
    if getattr(args, "archive", None) is not None:
        date_str = date.today().isoformat() if args.archive == "@today" else args.archive
        a_csv, _a_md = archive_outputs(pred, args.edition, date_str)
        print(f"🗄️  Snapshot versionado do dia: {a_csv}")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    path = EDITIONS_DIR / str(args.edition) / "fixtures.csv"
    with path.open(newline="") as fh:
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
    print(
        f"✅ Jogo {args.match} registrado: {args.home}x{args.away}. "
        f"Rode `worldcup predict --edition {args.edition}` para repalpitar."
    )
    return 0


def cmd_sync_results(args: argparse.Namespace) -> int:
    from .sync import sync_results

    print("🌐 Baixando resultados reais da fonte pública...")
    urls = args.source_url or None
    counts = sync_results(args.edition, results_urls=urls)
    print(
        f"✅ Sincronizado: {counts['group']} jogos de grupo + {counts['knockout']} de mata-mata "
        f"preenchidos ({counts['total_played_in_source']} jogos da Copa já disputados na fonte)."
    )
    if args.no_predict:
        print(f"Rode `worldcup predict --edition {args.edition}` para repalpitar.")
        return 0
    return cmd_predict(args)


def cmd_backtest(args: argparse.Namespace) -> int:
    from .backtest import run_backtest

    run_backtest(args.edition, n_sims=args.sims)
    return 0


def cmd_blend_track(args: argparse.Namespace) -> int:
    from .backtest import draw_regime_report, prospective_blend_report

    edition = load_edition(args.edition)

    res = prospective_blend_report(edition, args.blend_weight)
    if res.n == 0:
        print(
            "ℹ️  Nenhum jogo disputado com odds em odds.csv. Registre as odds da rodada em "
            f"data/editions/{args.edition}/odds.csv (match_id,home,draw,away) + os resultados."
        )
    else:
        better = "blend MELHOR" if res.delta > 0 else "modelo MELHOR" if res.delta < 0 else "empate"
        print(f"📈 Tracking prospectivo do blend (w={res.weight:.2f}) — {res.n} jogo(s) com odds:")
        print(f"   Brier modelo-puro : {res.brier_model:.4f}")
        print(f"   Brier blend       : {res.brier_blend:.4f}")
        print(f"   Δ = {res.delta:+.4f}  ({better}; menor Brier é melhor)")

    # Monitor de regime de empates (ENG-22) — sobre todos os jogos de grupo disputados.
    draw = draw_regime_report(edition)
    if draw.n:
        verdict = (
            "⚠️ SINAL ≥2σ — reconsiderar tilt de empate (abrir item-filho)"
            if draw.significant
            else "variância (gatilho ≥2σ não atingido — não agir)"
        )
        print(
            f"📊 Regime de empates ({draw.n} jogos): observados {draw.observed} "
            f"({100 * draw.observed / draw.n:.0f}%) vs esperados {draw.expected:.1f} "
            f"({100 * draw.expected / draw.n:.0f}%) — z={draw.z:+.2f} → {verdict}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="worldcup", description="Gerador de palpites de bolão da Copa")
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="mostra avisos informativos da biblioteca (seleções descartadas, etc.)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch-data", help="baixa e normaliza a base histórica")
    f.add_argument("--cutoff", default=DEFAULT_CUTOFF, help="data mínima (YYYY-MM-DD)")
    f.add_argument(
        "--source-url",
        action="append",
        default=None,
        metavar="URL",
        help="URL alternativa de resultados (pode repetir para fallback em cascata; default: martj42)",
    )
    f.set_defaults(func=cmd_fetch_data)

    pr = sub.add_parser("predict", help="gera os palpites de uma edição")
    pr.add_argument("--edition", type=int, default=2026)
    pr.add_argument("--sims", type=int, default=5000, help="nº de simulações Monte Carlo")
    pr.add_argument("--seed", type=int, default=12345)
    pr.add_argument("--risk", type=float, default=None, help="sobrescreve o risco (0..1)")
    pr.add_argument(
        "--blend-weight",
        type=float,
        default=None,
        metavar="W",
        help="peso do mercado no blend com odds.csv (0..1; 0=só modelo, default da edição)",
    )
    pr.add_argument(
        "--archive",
        nargs="?",
        const="@today",
        default=None,
        metavar="DATA",
        help="arquiva snapshot versionado em data/editions/<ed>/history/<DATA>.{csv,md} (default: hoje)",
    )
    pr.add_argument(
        "--as-of",
        default=None,
        metavar="AAAA-MM-DD",
        help="visão reconstruída de uma data passada (só resultados até a véspera); grava em "
        "history/<DATA>.reconstruido.{csv,md} sem tocar em out/",
    )
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
    sr.add_argument(
        "--blend-weight",
        type=float,
        default=None,
        metavar="W",
        help="peso do mercado no blend com odds.csv (0..1; 0=só modelo, default da edição)",
    )
    sr.add_argument("--no-predict", action="store_true", help="só sincroniza, não repalpita")
    sr.add_argument(
        "--source-url",
        action="append",
        default=None,
        metavar="URL",
        help="URL alternativa de resultados (pode repetir para fallback em cascata; default: martj42)",
    )
    sr.add_argument(
        "--archive",
        nargs="?",
        const="@today",
        default=None,
        metavar="DATA",
        help="arquiva snapshot versionado em data/editions/<ed>/history/<DATA>.{csv,md} (default: hoje)",
    )
    sr.set_defaults(func=cmd_sync_results)

    bt = sub.add_parser("backtest", help="valida o modelo numa Copa passada")
    bt.add_argument("--edition", type=int, default=2022)
    bt.add_argument("--sims", type=int, default=2000)
    bt.set_defaults(func=cmd_backtest)

    blt = sub.add_parser("blend-track", help="Brier do blend vs modelo nos jogos com odds (ENG-19)")
    blt.add_argument("--edition", type=int, default=2026)
    blt.add_argument(
        "--blend-weight",
        type=float,
        default=None,
        metavar="W",
        help="peso do mercado a avaliar (0..1; default: o da edição)",
    )
    blt.set_defaults(func=cmd_blend_track)

    return p


def _configure_logging(verbose: bool) -> None:
    """Avisos da biblioteca vão para stderr. Default WARNING; --verbose desce a INFO.

    A saída ao usuário continua em `print()` (stdout); o `logging` é só para os avisos
    da biblioteca (`model`/`sync`/`pipeline`), capturáveis em teste via `caplog`.
    """
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _configure_logging(getattr(args, "verbose", False))
    try:
        return args.func(args)
    except NetworkError as err:
        print(f"🌐 {err}", file=sys.stderr)
        return 1
    except DataSourceError as err:
        print(f"⚠️  {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
