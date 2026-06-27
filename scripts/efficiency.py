#!/usr/bin/env python3
"""Mede a EFICIÊNCIA da campanha: seus pontos reais vs o teto do tool (palpite as-of).

Para cada jogo já disputado, reconstrói a previsão que o tool teria mostrado na **manhã do
jogo** (estado de conhecimento as-of: só resultados anteriores), pelo MESMO caminho do
`predict --as-of` (modelo Dixon-Coles + blend de odds, config real da edição), e pontua esse
palpite pelo Sistema I contra o resultado real. A soma é o **teto** que seguir o tool à risca
renderia. `eficiência = seus_pontos / teto`.

Reporta também um **teto teórico (oráculo)**: a pontuação de cravar o placar **exato** de todo
jogo (base + bônus máximo). Dá duas leituras complementares — `tool / oráculo` (qualidade do
modelo+blend; o resto é ruído irredutível do futebol) e `seus_pontos / oráculo` (sua distância
da perfeição, que mistura execução + limite do modelo + azar). A **eficiência** (vs teto do tool)
continua sendo a métrica de execução; o oráculo é diagnóstico de teto, não de jogada.

Self-contained: NÃO lê os CSVs de `history/` — recomputa a previsão. Assim o número é
reprodutível mesmo onde não houve snapshot arquivado.

Limitações:
  - **Base inobservável (ENG-24):** o bônus de placar (exato/vencedor/saldo/perdedor) é
    determinístico e hierárquico, então o pegamos exato. Mas a **base variável (1–13)** é função da
    **probabilidade interna do app**, que difere da nossa (modelo+blend) e não é observável — então a
    base carrega **±~1 ponto por jogo** de incerteza. Logo o teto e a eficiência são **aproximados**,
    não exatos (confirmado: na validação contra o app, ~1/3 dos jogos erraram por ≤1 só na base).
    Ver `docs/SPEC.md` §4.
  - Fase de grupos: bônus de placar exatos; base aproximada (acima).
  - Mata-mata: pontua o placar dos **90'**; os bônus de prorrogação/pênaltis NÃO são pontuados
    (os dados reais guardam só o vencedor do confronto, não a camada que o decidiu — daí não
    serem reconstrutíveis). Um aviso é impresso se houver jogo de mata-mata disputado.

`--compare-archive`: além do as-of, pontua os snapshots **reais** arquivados em `history/`
(`<data>.csv`, sem sufixo `.reconstruido`) e lista os jogos onde a reconstrução diverge do que
o tool de fato mostrou naquela manhã — útil para saber quanto do "gap" é ruído de reconstrução
(dias sem snapshot arquivado) e não execução.

Uso:
  uv run python scripts/efficiency.py --edition 2026 --my-points 143 [--leader 173] [--compare-archive]
Roda no venv (importa `worldcup`).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from worldcup.blend import blend_matrix_with_odds
from worldcup.edition import Edition, load_edition
from worldcup.fetch_data import load_historical
from worldcup.format_engine import MatrixCache, deterministic_bracket, monte_carlo
from worldcup.knockout import predict_knockout
from worldcup.model import DixonColesModel, FitConfig
from worldcup.scoring import Scorer, outcome_probs_from_matrix

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _parse_score(s: str) -> tuple[int, int]:
    h, a = s.lower().split("x")
    return int(h), int(a)


def _pct(s: str) -> float:
    return float(s.strip().rstrip("%")) / 100.0


def asof_scores(edition: Edition, sims: int) -> dict[int, dict]:
    """Pontua, por jogo já disputado, o palpite as-of do tool contra o resultado real.

    Para cada data com jogos disputados, monta `edition.as_of(data)` (descarta resultados a
    partir dela), reajusta o modelo e prevê os jogos daquela data (que voltam a ser PREVISTOS).
    Devolve {match_id: {palpite, real, probs, pts, stage, ko_warn}}.
    """
    scorer = Scorer(edition.scoring)
    played = [f for f in edition.fixtures if f.played]
    by_id = {f.match_id: f for f in edition.fixtures}
    dates = sorted({f.date for f in played})
    historical = load_historical()
    blend_weight = edition.scoring.blend_weight

    out: dict[int, dict] = {}
    for date in dates:
        ed = edition.as_of(date)
        model = DixonColesModel(FitConfig()).fit(_train(ed, historical))
        cache = MatrixCache(model, ed.hosts)
        todays = [f for f in ed.fixtures if f.date == date]
        ko_today = [f for f in todays if not f.is_group]
        bracket = {}
        if ko_today:  # mata-mata precisa do bracket resolvido (por resultados reais)
            sim = monte_carlo(ed, model, cache, n_sims=sims, seed=12345)
            bracket = {rm.fixture.match_id: rm for rm in deterministic_bracket(ed, sim, cache)}

        for f in todays:
            real = by_id[f.match_id]  # da edição completa: tem o resultado real
            if real.home_goals is None or real.away_goals is None:
                continue
            actual = (real.home_goals, real.away_goals)
            home: str | None
            away: str | None
            if f.is_group:
                home, away = f.home, f.away
            else:
                rm = bracket.get(f.match_id)
                home, away = (rm.home, rm.away) if rm else (f.home, f.away)
            if not home or not away:
                continue
            mat = cache.matrix(home, away, f.neutral)
            odds = edition.odds.get(f.match_id)
            if odds is not None and blend_weight > 0.0:
                mat = blend_matrix_with_odds(mat, odds, blend_weight)
            probs = outcome_probs_from_matrix(mat)

            if f.is_group:
                p = scorer.best_prediction(mat)
                pred = (p.home_goals, p.away_goals)
            else:
                kp = predict_knockout(home, away, mat, scorer)
                pred = (kp.home_goals, kp.away_goals)
            pts = scorer.points(pred, actual, probs)  # 90' (mata-mata: sem bônus de prorrog./pênaltis)
            out[f.match_id] = {
                "palpite": f"{pred[0]}x{pred[1]}",
                "real": f"{actual[0]}x{actual[1]}",
                "probs": probs,
                "pts": pts,
                "stage": f.stage,
                "ko": not f.is_group,
            }
    return out


def _train(edition: Edition, historical):
    # import tardio para não puxar pandas no --help
    from worldcup.pipeline import build_training_frame

    return build_training_frame(edition, historical)


def archive_scores(edition: Edition) -> dict[int, float]:
    """Pontua os snapshots REAIS arquivados (history/<data>.csv) — o que o tool de fato mostrou."""
    scorer = Scorer(edition.scoring)
    hist = edition.directory / "history"
    out: dict[int, float] = {}
    for f in edition.fixtures:
        if f.home_goals is None or f.away_goals is None:
            continue
        snap = hist / f"{f.date}.csv"  # só snapshot REAL (não .reconstruido)
        if not snap.exists():
            continue
        with snap.open() as fh:
            row = next((r for r in csv.DictReader(fh) if int(r["jogo"]) == f.match_id), None)
        if not row or row["status"] != "PREVISTO" or not row["P_mandante"].strip():
            continue  # naquele snapshot o jogo já era FINAL (run pós-jogo) — não serve
        if not f.is_group:
            continue  # bônus de mata-mata fora de escopo
        pred = _parse_score(row["palpite"])
        probs = (_pct(row["P_mandante"]), _pct(row["P_empate"]), _pct(row["P_visitante"]))
        out[f.match_id] = scorer.points(pred, (f.home_goals, f.away_goals), probs)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Eficiência da campanha: pontos reais vs teto do tool (as-of)")
    p.add_argument("--edition", type=int, default=2026)
    p.add_argument("--my-points", type=float, default=None, help="seus pontos reais no bolão")
    p.add_argument("--leader", type=float, default=None, help="pontos do líder do grupo (contexto)")
    p.add_argument("--sims", type=int, default=2000, help="sims do Monte Carlo (só resolve o bracket de mata-mata)")
    p.add_argument("--compare-archive", action="store_true", help="compara com os snapshots reais arquivados")
    args = p.parse_args(argv)

    edition = load_edition(args.edition)
    scores = asof_scores(edition, args.sims)
    archive = archive_scores(edition) if args.compare_archive else {}

    has_ko = any(s["ko"] for s in scores.values())
    hdr = f"{'J':>3} {'fase':6} {'palp':5} {'real':5} {'pts':>4}"
    if args.compare_archive:
        hdr += f" {'arquiv':>6} {'Δ':>3}"
    print(hdr)
    total = 0.0
    total_arch = 0.0
    diverged = []
    for mid in sorted(scores):
        s = scores[mid]
        total += s["pts"]
        line = f"{mid:>3} {s['stage']:6} {s['palpite']:5} {s['real']:5} {s['pts']:>4.0f}"
        if args.compare_archive:
            a = archive.get(mid)
            if a is None:
                line += f" {'—':>6} {'':>3}"
            else:
                total_arch += a
                d = s["pts"] - a
                line += f" {a:>6.0f} {d:>+3.0f}"
                if d != 0:
                    diverged.append((mid, a, s["pts"]))
        print(line)

    # Teto teórico (oráculo): cravar o placar EXATO de todo jogo — base + bônus máximo.
    # Reusa as probs as-of já computadas (a base ainda é aproximada, ENG-24). Mede a fração
    # do máximo teórico que cada estratégia captura: o tool (qualidade do modelo) e você.
    scorer = Scorer(edition.scoring)
    oracle = 0.0
    for s in scores.values():
        real = _parse_score(s["real"])
        oracle += scorer.points(real, real, s["probs"])

    print(f"\nJogos pontuados: {len(scores)}")
    cfg = f"risk {edition.scoring.risk} + blend {edition.scoring.blend_weight}"
    print(f"Teto do tool (as-of, {cfg}): {total:.0f} pts ({total / len(scores):.2f}/jogo)")
    print(f"Teto teórico (oráculo, cravar todo placar): {oracle:.0f} pts ({oracle / len(scores):.2f}/jogo)")
    print(f"   captura do tool sobre o teórico: {100.0 * total / oracle:.1f}%  (qualidade do modelo+blend;")
    print("   o resto é ruído irredutível do futebol — inatingível por qualquer estratégia, não execução)")
    print("⚠️  APROXIMADO: a base (1–13) usa a probabilidade interna do app (inobservável) ⇒ ±~1/jogo")
    print("    de incerteza. O bônus de placar é exato; a base não. Teto e eficiência são estimativas")
    print("    (ENG-24 / SPEC §4) — não leia o % como cravado.")
    if has_ko:
        print("⚠️  Mata-mata presente: o placar dos 90' foi pontuado, mas os bônus de prorrogação/")
        print("    pênaltis NÃO entram (dados reais guardam só o vencedor) — o teto de KO é subestimado.")
    if args.compare_archive:
        arch_ids = [m for m in scores if m in archive]
        if arch_ids:
            sub = sum(scores[m]["pts"] for m in arch_ids)
            print(f"\nSubconjunto com snapshot REAL arquivado ({len(arch_ids)} jogos):")
            print(f"   as-of reconstruído : {sub:.0f}")
            print(f"   snapshot arquivado : {total_arch:.0f}  (Δ={sub - total_arch:+.0f} = ruído de reconstrução)")
        recon_only = [m for m in scores if m not in archive]
        if recon_only:
            print(f"   {len(recon_only)} jogo(s) SEM snapshot real → teto 100% reconstruído (não verificável):")
            print(f"      {', '.join('J' + str(m) for m in recon_only)}")
        if diverged:
            items = ", ".join(f"J{m}({b - a:+.0f})" for m, a, b in diverged)
            print(f"   divergências as-of vs arquivado: {len(diverged)} jogo(s) ({items})")

    if args.my_points is not None:
        eff = 100.0 * args.my_points / total
        cap = 100.0 * args.my_points / oracle
        print(f"\nSeus pontos: {args.my_points:.0f}   Eficiência: {eff:.1f}%  (vs teto do tool — sua execução)")
        print(f"   sua captura do teto teórico: {cap:.1f}%  (vs oráculo — inclui o limite do modelo + azar)")
        if args.leader is not None:
            above = args.leader > total
            note = (
                "nem seguir o tool à risca alcançaria hoje; líder pegou variância de exatos a favor"
                if above
                else "alcançável seguindo o tool"
            )
            print(f"Líder: {args.leader:.0f} — {'ACIMA' if above else 'abaixo'} do teto do tool ({note}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
