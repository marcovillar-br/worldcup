"""Briefing read-only de start-of-day (ENG-31).

Uma **foto compacta e idempotente** do estado da campanha para reidratar o contexto no início
de uma sessão sem rodar a pipeline nem ler o `BOLAO.md` inteiro: jogos disputados/total, fase
atual, fixtures de hoje (disputado/pendente), próximos palpites, standing e o que depende do
usuário. Aqui mora só a **lógica pura** (montagem + formatação); o `cli.cmd_status` faz a I/O
(carrega a edição, lê o último `out/` e a linha de standing do `BOLAO.md`).

Princípio: *ver* separado de *fazer* — o `status` nunca muta nada; a mutação (`sync`/`predict`)
segue na skill `palpites-copa`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .teams import display

if TYPE_CHECKING:
    from .edition import Edition

# Nomes de fase em PT (apresentação; não é específico de ano — os códigos vêm de knockout_stages).
_STAGE_PT = {
    "group": "Fase de grupos",
    "R32": "16-avos",
    "R16": "Oitavas",
    "QF": "Quartas",
    "SF": "Semifinais",
    "3rd_place": "Disputa de 3º",
    "final": "Final",
}


@dataclass
class TodayGame:
    match_id: int
    label: str
    played: bool
    score: str | None  # "3×0" se disputado, senão None


@dataclass
class UpcomingGame:
    match_id: int
    label: str
    pick: str  # "0×0 → México" (KO) ou "1×0" (grupo)


@dataclass
class StatusReport:
    name: str
    played: int
    total: int
    stage: str  # fase atual (display)
    risk: float
    blend_weight: float
    today: str  # ISO AAAA-MM-DD
    today_games: list[TodayGame] = field(default_factory=list)
    upcoming: list[UpcomingGame] = field(default_factory=list)
    standing: str | None = None
    overdue: list[int] = field(default_factory=list)  # não disputados com date < hoje
    has_picks: bool = True  # existe out/ para resolver nomes/palpites
    stale: bool = False  # out/ atrás dos fixtures (faltou predict)
    fit_gaps: list[int] = field(default_factory=list)  # disputados fora do ajuste do modelo (ENG-43)


def _label(edition: Edition, match_id: int, home: str, away: str, picks: dict[int, dict[str, str]]) -> str:
    """Nome legível do confronto. Usa o `out/` (nomes resolvidos, inclusive slots de KO) se houver;
    senão cai no display direto do fixture (grupo = times reais; KO sem out/ = slots crus)."""
    row = picks.get(match_id)
    if row and row.get("mandante") and row.get("visitante"):
        return f"{row['mandante']} × {row['visitante']}"
    return f"{display(home)} × {display(away)}"


def _pick_str(row: dict[str, str]) -> str:
    palpite = (row.get("palpite", "").strip() or "—").replace("x", "×")  # placar uniforme com o de hoje
    avanca = row.get("avanca", "").strip()
    if row.get("fase", "") != "group" and avanca:
        return f"{palpite} → {avanca}"
    return palpite


def build_status(
    edition: Edition,
    picks: dict[int, dict[str, str]],
    today: str,
    standing: str | None,
    *,
    upcoming_n: int = 6,
    fit_gaps: list[int] | None = None,
) -> StatusReport:
    """Monta o `StatusReport` a partir da edição, do último `out/` (picks por match_id) e da data.

    `picks` mapeia `match_id -> linha do out/palpites-<ano>.csv` (vazio se não houver `out/`).
    `today` é a data ISO tratada como "hoje"; `standing` é a linha de standing do `BOLAO.md`.
    Tudo read-only e determinístico.
    """
    fixtures = sorted(edition.fixtures, key=lambda f: f.match_id)
    played = [f for f in fixtures if f.played]
    unplayed = [f for f in fixtures if not f.played]

    stage_code = unplayed[0].stage if unplayed else (fixtures[-1].stage if fixtures else "—")
    stage = _STAGE_PT.get(stage_code, stage_code) if unplayed else "Copa encerrada"

    today_games = [
        TodayGame(
            match_id=f.match_id,
            label=_label(edition, f.match_id, f.home, f.away, picks),
            played=f.played,
            score=f"{f.home_goals}×{f.away_goals}" if f.played else None,
        )
        for f in fixtures
        if f.date == today
    ]

    upcoming = [
        UpcomingGame(
            match_id=f.match_id,
            label=_label(edition, f.match_id, f.home, f.away, picks),
            pick=_pick_str(picks[f.match_id]) if f.match_id in picks else "—",
        )
        for f in unplayed[:upcoming_n]
    ]

    overdue = [f.match_id for f in unplayed if f.date < today]

    has_picks = bool(picks)
    final_in_picks = sum(1 for r in picks.values() if r.get("status", "") == "FINAL")
    stale = has_picks and final_in_picks < len(played)

    return StatusReport(
        name=edition.spec.name,
        played=len(played),
        total=len(fixtures),
        stage=stage,
        risk=edition.scoring.risk,
        blend_weight=edition.scoring.blend_weight,
        today=today,
        today_games=today_games,
        upcoming=upcoming,
        standing=standing,
        overdue=overdue,
        has_picks=has_picks,
        stale=stale,
        fit_gaps=fit_gaps or [],
    )


def _br_date(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}" if len(iso) == 10 else iso


def format_status(r: StatusReport) -> str:
    """Renderiza o `StatusReport` como um bloco compacto de console (uma tela)."""
    width = 46
    lines = [
        f"📊 worldcup status · {r.name}",
        "─" * width,
        f"{r.played}/{r.total} jogos · {r.stage} · risk {r.risk:g} · blend {r.blend_weight:g}",
    ]

    if r.fit_gaps:  # ENG-43: staleness da base — resultado disputado que não entrou no ajuste
        ids = ", ".join(f"J{m}" for m in r.fit_gaps)
        lines.append(f"⚠️  {len(r.fit_gaps)} disputado(s) FORA do ajuste: {ids} (bracket de KO não resolvido)")

    # alinhamento dos rótulos de jogo (hoje + próximos juntos)
    labels = [g.label for g in r.today_games] + [g.label for g in r.upcoming]
    pad = min(max((len(x) for x in labels), default=0), 34)

    lines.append(f"\nHOJE {_br_date(r.today)}:")
    if r.today_games:
        for tg in r.today_games:
            mark = f"✓ {tg.score}" if tg.played else "⏳ pendente"
            lines.append(f"  J{tg.match_id:<3} {tg.label:<{pad}}  {mark}")
    else:
        lines.append("  (sem jogos hoje)")

    if r.upcoming:
        lines.append("\nPRÓXIMOS:")
        for ug in r.upcoming:
            lines.append(f"  J{ug.match_id:<3} {ug.label:<{pad}}  {ug.pick}")

    lines.append(f"\nSTANDING: {r.standing or '—'}")

    needs = ["pontos atuais no app — p/ a eficiência (efficiency.py --my-points <PTS>)"]
    if r.overdue:
        ids = ", ".join(f"J{m}" for m in r.overdue)
        needs.append(f"{ids} já passaram da data e não estão preenchidos — rode sync-results (ou registre à mão)")
    if not r.has_picks:
        needs.append("sem out/palpites — rode `worldcup predict` para gerar os palpites")
    elif r.stale:
        needs.append("out/ está atrás dos resultados já registrados — rode `worldcup predict` para repalpitar")

    lines.append("⚠️  PRECISA DE VOCÊ:")
    lines.extend(f"  • {n}" for n in needs)

    return "\n".join(lines)
