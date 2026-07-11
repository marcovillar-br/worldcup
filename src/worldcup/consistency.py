"""Coerência interna do palpite renderizado (ENG-52).

Funções **puras** que confrontam partes do mesmo output entre si — não com a realidade, mas com sua
própria consistência. Um palpite que se autocontradiz ("X avança a semi" mas "Y joga a final") é um
bug de derivação, não uma opinião: nasceu quando o chaveamento e o palpite exibido passaram a decidir
"quem vence" por caminhos diferentes (ENG-51). Estas checagens transformam esse tipo de contradição
em erro **ruidoso** — usadas como asserção dura no `pipeline.run` (o pipeline recusa emitir uma tabela
incoerente) e como ferramenta on-demand (`scripts/check_output_consistency.py`).

Operam sobre as linhas já renderizadas (nomes de exibição), o mesmo dicionário que vira CSV — assim
guardam o **artefato final**, não um passo intermediário.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .edition import Edition

_KO_STAGE_ORDER = ("R32", "R16", "QF", "SF", "3rd_place", "final")


def _adv_and_loser(row: dict) -> tuple[str, str | None]:
    """`(avança, perdedor)` de uma linha de KO — o perdedor é o participante que não avançou."""
    adv = row.get("avanca", "")
    home, away = row.get("mandante", ""), row.get("visitante", "")
    if adv == home:
        return adv, away
    if adv == away:
        return adv, home
    return adv, None


def check_prediction_consistency(edition: Edition, rows: list[dict]) -> list[str]:
    """Lista de violações de coerência do palpite (vazia = íntegro). Não muta nada.

    Só **contradições lógicas** do artefato (a asserção dura do `pipeline.run` depende disto — não
    pode ter falso positivo):
      - INV-1 (encadeamento do bracket; o bug do ENG-51): o participante de um slot `Wxx`/`Lxx` é
        exatamente quem **avançou**/**perdeu** o jogo `xx`;
      - INV-2: `avança` é um dos dois participantes do jogo;
      - INV-3: nenhum time aparece duas vezes na **mesma rodada** de mata-mata;
      - INV-4: o 1×2 exibido soma ~100% (tolerância de arredondamento).

    **Não** se verifica "avança = vencedor do placar de 90'": o placar (melhor exato não-empate por
    E[pts]) e o avanço (P(avançar) ≥ 50%) saem da mesma matriz mas otimizam slots **independentes**
    do bolão — podem divergir legitimamente (ex.: mando avança nos pênaltis, mas o placar não-empate
    mais provável é uma vitória magra do visitante). Diferente do INV-1, não é a mesma pergunta.
    """
    out: list[str] = []
    by_id = {int(r["jogo"]): r for r in rows}
    ko_slots = {f.match_id: (f.home, f.away) for f in edition.knockout_fixtures()}
    ko_stages = {f.stage for f in edition.knockout_fixtures()}
    unresolved = {"", "?"}

    # INV-1: slots Wxx/Lxx resolvem para quem avançou/perdeu do jogo referenciado
    for mid, (home_slot, away_slot) in ko_slots.items():
        row = by_id.get(mid)
        if row is None:
            continue
        for slot, actual in ((home_slot, row.get("mandante", "")), (away_slot, row.get("visitante", ""))):
            if not (slot and slot[0] in "WL" and slot[1:].isdigit()):
                continue
            ref = by_id.get(int(slot[1:]))
            if ref is None:
                continue
            adv, loser = _adv_and_loser(ref)
            expected = adv if slot[0] == "W" else loser
            if expected and actual not in unresolved and expected != actual:
                out.append(f"INV-1 J{mid} slot {slot}: esperava '{expected}' (do J{slot[1:]}), tabela traz '{actual}'")

    # INV-2: avança ∈ {mandante, visitante}
    for mid, row in by_id.items():
        adv = row.get("avanca", "")
        if adv and adv not in {row.get("mandante", ""), row.get("visitante", "")}:
            out.append(f"INV-2 J{mid}: avança '{adv}' não é '{row.get('mandante')}' nem '{row.get('visitante')}'")

    # INV-3: sem time repetido dentro de uma rodada de KO (grupos jogam várias vezes — não se aplica)
    for stage in ko_stages:
        teams = [
            t
            for r in rows
            if r.get("fase") == stage
            for t in (r.get("mandante", ""), r.get("visitante", ""))
            if t not in unresolved
        ]
        dups = sorted(t for t, c in Counter(teams).items() if c > 1)
        if dups:
            out.append(f"INV-3 rodada {stage}: time(s) repetido(s) {dups}")

    # INV-4: 1×2 exibido soma ~100%
    for mid, row in by_id.items():
        if not row.get("P_mandante"):
            continue
        try:
            total = sum(int(row[c].rstrip("%")) for c in ("P_mandante", "P_empate", "P_visitante"))
        except (ValueError, KeyError):
            continue
        if not 99 <= total <= 101:
            out.append(f"INV-4 J{mid}: 1×2 soma {total}% (esperado ~100%)")

    return out
