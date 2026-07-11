"""Testes da coerência interna do palpite renderizado (ENG-52)."""

from __future__ import annotations

from pathlib import Path

from worldcup.consistency import check_prediction_consistency
from worldcup.edition import Edition, Fixture, GroupStageSpec, ScoringConfig, TournamentSpec


def _edition() -> Edition:
    """Edição mínima: 4 grupos de 3, 2 SF (1A×1B, 1C×1D) + final + 3º lugar (perdedores das SFs)."""
    teams = [f"S{i}" for i in range(12)]
    groups = {g: teams[i * 3 : i * 3 + 3] for i, g in enumerate(["A", "B", "C", "D"])}
    fixtures: list[Fixture] = []
    mid = 1
    for g, ts in groups.items():
        for h, a in ((ts[0], ts[1]), (ts[0], ts[2]), (ts[1], ts[2])):
            fixtures.append(Fixture(match_id=mid, stage="group", group=g, date="2030-06-01", home=h, away=a))
            mid += 1
    for m, stage, h, a in (
        (31, "SF", "1A", "1B"),
        (32, "SF", "1C", "1D"),
        (33, "3rd_place", "L31", "L32"),
        (34, "final", "W31", "W32"),
    ):
        fixtures.append(Fixture(match_id=m, stage=stage, date="2030-07-01", home=h, away=a))
    spec = TournamentSpec(
        name="mini",
        edition=2030,
        hosts=[],
        group_stage=GroupStageSpec(
            num_groups=4,
            group_size=3,
            advance_per_group=1,
            best_thirds=0,
            tiebreakers=["points"],
            knockout_stages=["SF", "3rd_place", "final"],
        ),
    )
    return Edition(spec=spec, groups=groups, fixtures=fixtures, scoring=ScoringConfig(), directory=Path("/tmp"))


def _ko_row(mid: int, stage: str, home: str, away: str, palpite: str, avanca: str) -> dict:
    return {
        "jogo": str(mid),
        "fase": stage,
        "grupo": "",
        "mandante": home,
        "visitante": away,
        "palpite": palpite,
        "P_mandante": "",
        "P_empate": "",
        "P_visitante": "",
        "avanca": avanca,
        "status": "PREVISTO",
    }


def _coherent_rows() -> list[dict]:
    # SF31: S0 vence S3 (avança S0); SF32: S6 vence S9 (avança S6)
    # final: S0×S6; 3º lugar: S3×S9 (os perdedores)
    return [
        _ko_row(31, "SF", "S0", "S3", "1x0", "S0"),
        _ko_row(32, "SF", "S6", "S9", "1x0", "S6"),
        _ko_row(33, "3rd_place", "S3", "S9", "1x0", "S3"),
        _ko_row(34, "final", "S0", "S6", "1x0", "S0"),
    ]


def test_coerente_nao_acusa():
    assert check_prediction_consistency(_edition(), _coherent_rows()) == []


def test_inv1_bracket_incoerente_o_bug_do_eng51():
    # SF31 diz que S3 avança, mas a final ainda traz S0 como W31 → contradição (o bug do ENG-51)
    rows = _coherent_rows()
    rows[0]["avanca"] = "S3"  # J31 agora avança S3
    rows[0]["palpite"] = "0x1"  # e o 90' condiz (senão INV-5 também acusa)
    v = check_prediction_consistency(_edition(), rows)
    assert any("INV-1 J34 slot W31" in x for x in v)  # final espera S3, traz S0
    assert any("INV-1 J33 slot L31" in x for x in v)  # 3º lugar espera S0 (perdedor), traz S3


def test_inv2_avanca_fora_dos_participantes():
    rows = _coherent_rows()
    rows[3]["avanca"] = "S9"  # ninguém que joga a final
    v = check_prediction_consistency(_edition(), rows)
    assert any("INV-2 J34" in x for x in v)


def test_inv3_time_repetido_na_rodada():
    rows = _coherent_rows()
    rows[1]["mandante"] = "S0"  # S0 nas duas SFs
    v = check_prediction_consistency(_edition(), rows)
    assert any("INV-3 rodada SF" in x for x in v)


def test_inv4_probabilidades_nao_somam_100():
    rows = _coherent_rows()
    rows[0].update(P_mandante="50%", P_empate="10%", P_visitante="10%")  # soma 70
    v = check_prediction_consistency(_edition(), rows)
    assert any("INV-4 J31" in x for x in v)


def test_placar_e_avanco_podem_divergir_legitimamente():
    # o placar (melhor exato não-empate) e o avanço (P(avançar)) otimizam slots INDEPENDENTES do
    # bolão — "90' 2x1 mando, mas avança visitante" NÃO é contradição (ao contrário do INV-1).
    rows = _coherent_rows()
    rows[3]["palpite"] = "2x1"  # mando S0 vence o 90'
    rows[3]["avanca"] = "S6"  # avança o visitante
    # a final continua coerente com o resto do bracket (W31=S0, W32=S6 seguem participando)
    assert check_prediction_consistency(_edition(), rows) == []
