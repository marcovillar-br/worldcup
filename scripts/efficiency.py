#!/usr/bin/env python3
"""CLI da eficiência da campanha: seus pontos reais vs o teto do tool (palpite as-of).

Wrapper fino (ENG-60): argparse + impressão. O **núcleo de medição** — reconstrução as-of,
pontuação, teto congelado (`ceiling.csv`), sondas de anomalia — vive em `worldcup.efficiency`
(sob mypy, cobertura e a rede de testes do pacote); a semântica está documentada lá e na skill
`palpites-copa` (passo 6).

Uso:
  uv run python scripts/efficiency.py --edition 2026 --my-points 143 [--leader 173] [--compare-archive]
Roda no venv (importa `worldcup`).
"""

from __future__ import annotations

import argparse

from worldcup.edition import load_edition
from worldcup.efficiency import (
    _ceiling_path,
    _parse_score,
    archive_scores,
    asof_scores,
    ceiling_anomalies,
    code_fingerprint,
    cross_source_ko_check,
    dead_path_canary,
    load_ceiling,
    mechanical_suspects,
    provenance_split,
    reconcile_ceiling,
    save_ceiling,
)
from worldcup.fetch_data import PROJECT_ROOT
from worldcup.scoring import Scorer


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Eficiência da campanha: pontos reais vs teto do tool (as-of)")
    p.add_argument("--edition", type=int, default=2026)
    p.add_argument("--my-points", type=float, default=None, help="seus pontos reais no bolão")
    p.add_argument("--leader", type=float, default=None, help="pontos do líder do grupo (contexto)")
    p.add_argument("--sims", type=int, default=2000, help="sims do Monte Carlo (só resolve o bracket de mata-mata)")
    p.add_argument("--compare-archive", action="store_true", help="compara com os snapshots reais arquivados")
    p.add_argument(
        "--reset-ceiling",
        action="store_true",
        help="descarta o cache de teto congelado (ceiling.csv) e recongela na medição atual (ENG-34)",
    )
    args = p.parse_args(argv)

    edition = load_edition(args.edition)
    scores = asof_scores(edition, args.sims)
    archive = archive_scores(edition, scores)  # ENG-34/46: fonte imutável preferida (grupos + KO novo formato)

    # ENG-34: teto headline congelado por jogo — estável entre rodagens (base/odds/código novos não
    # mudam o teto de um jogo já medido; divergências viram drift reportado, não substituição muda).
    cache = {} if args.reset_ceiling else load_ceiling(_ceiling_path(edition))
    fingerprint = code_fingerprint(PROJECT_ROOT)  # ENG-50: procedência do congelamento
    headline, updated_cache, drift = reconcile_ceiling(scores, archive, cache, fingerprint)
    save_ceiling(_ceiling_path(edition), updated_cache)
    seeded = len(updated_cache) - len(cache)
    stale_prov, unknown_prov = provenance_split(cache, fingerprint)  # do cache LIDO, não do gravado

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
        total += headline[mid]  # ENG-34: headline usa o teto CONGELADO, não a reconstrução volátil
        drift_mark = " ~" if any(m == mid for m, _f, _l in drift) else ""
        line = f"{mid:>3} {s['stage']:6} {s['palpite']:5} {s['real']:5} {headline[mid]:>4.0f}{drift_mark}"
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
        w = edition.scoring.weight(s["stage"])
        oracle += scorer.weighted_points(real, real, s["probs"], w)
        # teto do bônus KO: cravar o desfecho real (prorrogação +3, e nos pênaltis +3 do vencedor) ×peso
        act_et, act_pen = s.get("act_et"), s.get("act_pen")
        if act_et is not None:
            oracle += scorer.knockout_bonus(act_et, act_pen, act_et, act_pen) * w

    print(f"\nJogos pontuados: {len(scores)}")
    cfg = f"risk {edition.scoring.risk} + blend {edition.scoring.blend_weight}"
    print(f"Teto do tool (as-of, {cfg}): {total:.0f} pts ({total / len(scores):.2f}/jogo)")
    n_arch = sum(1 for e in updated_cache.values() if e["source"] == "archive")
    seed_note = f" (+{seeded} semeado{'s' if seeded != 1 else ''} nesta rodada)" if seeded else ""
    reset_note = " [--reset-ceiling: recongelado do zero]" if args.reset_ceiling else ""
    print(
        f"   ↳ ENG-34: teto CONGELADO por jogo em ceiling.csv — {len(updated_cache)} no cache "
        f"({n_arch} de snapshot real, {len(updated_cache) - n_arch} reconstruídos){seed_note}{reset_note}"
    )
    if drift:
        print(f"   ⚠️  DRIFT em {len(drift)} jogo(s): a reconstrução viva mudou vs o congelado (headline usa o")
        print("       CONGELADO). Causa: base/odds/código mudaram desde a 1ª medição. Recongele com --reset-ceiling.")
        for mid, frozen, live in sorted(drift):
            print(f"       J{mid}: congelado {frozen:.0f} → vivo {live:.0f} ({live - frozen:+.0f})")
    print(f"Teto teórico (oráculo, cravar todo placar): {oracle:.0f} pts ({oracle / len(scores):.2f}/jogo)")
    print(f"   captura do tool sobre o teórico: {100.0 * total / oracle:.1f}%  (qualidade do modelo+blend;")
    print("   o resto é ruído irredutível do futebol — inatingível por qualquer estratégia, não execução)")
    print("⚠️  APROXIMADO: a base (1–13) usa a probabilidade interna do app (inobservável) ⇒ ±~1/jogo")
    print("    de incerteza. O bônus de placar é exato; a base não. Teto e eficiência são estimativas")
    print("    (ENG-24 / SPEC §4) — não leia o % como cravado.")
    latent: list[int] = []
    contradiction: list[int] = []
    credited = tied = 0
    if has_ko:
        print("ℹ️  Mata-mata: placar dos 90' com PESO DE FASE (R32–SF ×2, final ×4) E o bônus de prorrogação/")
        print("    pênaltis (+3/+3 ×peso) onde a fonte (martj42 shootouts) confirma o desfecho (ENG-27).")
        latent, contradiction = cross_source_ko_check(edition, scores)
        credited, tied = dead_path_canary(scores)
        if latent:
            ids = ", ".join("J" + str(m) for m in latent)
            print(f"    {len(latent)} jogo(s) empatado(s) nos 90' ainda sem shootout na fonte (latência) →")
            print(f"    bônus de KO não pontuado neste teto: {ids}")
        # Sonda 1 (ENG-49): as duas fontes do desfecho discordam ⇒ erro, não latência.
        if contradiction:
            ids = ", ".join("J" + str(m) for m in contradiction)
            print(f"🚨 CONTRADIÇÃO DE FONTE em {len(contradiction)} jogo(s): {ids}")
            print("    A edição afirma o desfecho (shootouts.csv/regulation.csv) e a base martj42 não confirma.")
            print("    Isto NÃO é latência: é bug de lookup, curadoria errada ou fonte corrigida. Investigue")
            print("    ANTES de interpretar o teto — o bônus destes jogos está fora dele. (ENG-49)")
        # Sonda 2 (ENG-50): um ramo que deveria rodar nunca rodou.
        if tied and credited == 0:
            print(f"🚨 CANÁRIO DE CAMINHO MORTO: {tied} KO(s) empatado(s) nos 90' e o bônus de ET/pênaltis")
            print("    foi creditado em ZERO deles. Ou o torneio é bizarro, ou o código está quebrado —")
            print("    a hipótese mecânica vem primeiro. Foi exatamente o estado do ENG-48. (ENG-50)")
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
            print(f"Líder: {args.leader:.0f} — {'ACIMA' if above else 'abaixo'} do teto do tool.")

    # ENG-50: o invariante "o teto é um teto" foi violado ⇒ imprimir as sondas MECÂNICAS antes de
    # qualquer leitura estatística. Não há explicação pré-escrita aqui de propósito: a variância
    # explica qualquer resíduo, inclusive código quebrado, e por isso vem por último — depois que
    # as sondas voltam limpas. Foi o que faltou em 08/07 e 10/07 (ENG-48).
    anomalies = ceiling_anomalies(total, args.my_points, args.leader)
    if anomalies:
        n_recon = sum(1 for m in scores if m not in archive)
        suspects = mechanical_suspects(
            latent=latent,
            contradiction=contradiction,
            credited=credited,
            tied=tied,
            stale=stale_prov,
            unknown=unknown_prov,
            recon_only=n_recon,
        )
        print("\n🚨 ANOMALIA: o teto deveria ser um teto.")
        for a in anomalies:
            print(f"   • {a}")
        print("   Sondas mecânicas (descarte-as ANTES de atribuir a variância):")
        for ok, text in suspects:
            print(f"     {'✓' if ok else '✗'} {text}")
        dirty = [t for ok, t in suspects if not ok]
        if dirty:
            print(f"   ⇒ {len(dirty)} sonda(s) suja(s): o teto pode estar SUBESTIMADO. Investigue antes de concluir")
            print("     que alguém superou o tool. Um teto subestimado produz exatamente este sintoma.")
        else:
            print("   ⇒ sondas limpas. Só agora a leitura estatística é legítima: superar o teto do tool é")
            print("     possível por variância de placares exatos (que regride), não por estratégia superior.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
