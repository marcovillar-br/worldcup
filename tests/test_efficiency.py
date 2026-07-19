"""Testes da lógica pura de worldcup.efficiency (desfecho de KO + bônus ponderado; ENG-27/ENG-60)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pandas as pd

from worldcup import efficiency
from worldcup.edition import Edition, Fixture, ScoringConfig, load_edition
from worldcup.fetch_data import PROJECT_ROOT
from worldcup.scoring import Scorer


def _pens(date: str, home: str, away: str, winner: str) -> dict:
    return {(date, frozenset({home, away})): winner}


def test_actual_ko_outcome_regulation():
    # placar dos 90' decidido → não houve prorrogação/pênaltis
    assert efficiency._actual_ko_outcome(2, 1, "2026-06-29", "Brazil", "Brazil", "Japan", {}) == (None, None)


def test_actual_ko_outcome_penalties():
    # 90' empate + na fonte com vencedor de pênaltis → ("penalties", lado do vencedor)
    pens = _pens("2026-06-29", "Germany", "Paraguay", "Paraguay")
    assert efficiency._actual_ko_outcome(1, 1, "2026-06-29", "Paraguay", "Germany", "Paraguay", pens) == (
        "penalties",
        "away",
    )


def test_actual_ko_outcome_extra_time():
    # 90' empate + na fonte SEM shootout → decidido na prorrogação; vencedor = quem avançou
    pens = {("2026-06-29", frozenset({"Netherlands", "Morocco"})): ""}
    assert efficiency._actual_ko_outcome(1, 1, "2026-06-29", "Morocco", "Netherlands", "Morocco", pens) == (
        "away",
        None,
    )


def test_actual_ko_outcome_extra_time_with_empty_ko_outcome_uses_consolidated():
    # ENG-63: KO decidido por gol na ET fica com ko_outcome VAZIO (o consolidado já decide quem
    # avança, então o sync não preenche o campo) — o vencedor sai do placar consolidado do fixture
    pens = {("2026-07-11", frozenset({"Norway", "England"})): ""}
    assert efficiency._actual_ko_outcome(1, 1, "2026-07-11", None, "Norway", "England", pens, consolidated=(1, 2)) == (
        "away",
        None,
    )
    assert efficiency._actual_ko_outcome(
        1,
        1,
        "2026-07-11",
        None,
        "Argentina",
        "Switzerland",
        pens | {("2026-07-11", frozenset({"Argentina", "Switzerland"})): ""},
        consolidated=(3, 1),
    ) == ("home", None)


def test_actual_ko_outcome_no_ko_outcome_and_tied_consolidated_stays_unknown():
    # consolidado empatado sem shootout na fonte e sem ko_outcome: não há de onde tirar o desfecho
    pens = {("2026-07-11", frozenset({"Norway", "England"})): ""}
    assert efficiency._actual_ko_outcome(1, 1, "2026-07-11", None, "Norway", "England", pens, consolidated=(1, 1)) == (
        None,
        None,
    )


def test_actual_ko_outcome_latency_skips():
    # 90' empate mas o jogo ainda NÃO está na fonte (chave ausente) → não inferir (latência)
    assert efficiency._actual_ko_outcome(1, 1, "2026-06-29", "Morocco", "Netherlands", "Morocco", {}) == (
        None,
        None,
    )


def test_penalty_lookup_casa_com_a_data_do_fixture():
    """Produtor (`_penalty_lookup`, coluna `datetime64`) e consumidor (`Fixture.date`, `str`) casam.

    Regressão: a chave era `str(datetime64)` = `'2026-06-29 00:00:00'` e nunca batia com o
    `'2026-06-29'` do fixture — todo KO empatado nos 90' caía no ramo de latência e **perdia o
    bônus** de prorrogação/pênaltis. Os testes acima montavam o `pens` à mão, no formato do
    consumidor, e por isso não pegavam o mismatch: este teste passa pelo lookup de verdade.
    """
    historical = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-06-29", "2026-06-29"]),
            "home_team": ["Germany", "Netherlands"],
            "away_team": ["Paraguay", "Morocco"],
            "penalty_winner": ["Paraguay", ""],
        }
    )
    pens = efficiency._penalty_lookup(historical)

    assert ("2026-06-29", frozenset({"Germany", "Paraguay"})) in pens

    # 90' empate + shootout na fonte → pênaltis, lado do vencedor
    assert efficiency._actual_ko_outcome(1, 1, "2026-06-29", "Paraguay", "Germany", "Paraguay", pens) == (
        "penalties",
        "away",
    )
    # 90' empate + na fonte SEM shootout → prorrogação, vencedor = quem avançou
    assert efficiency._actual_ko_outcome(1, 1, "2026-06-29", "Morocco", "Netherlands", "Morocco", pens) == (
        "away",
        None,
    )


def _fx(mid: int, hg: int | None, ag: int | None) -> Fixture:
    return Fixture(match_id=mid, stage="R32", date="2026-07-01", home="1G", away="3rd", home_goals=hg, away_goals=ag)


def test_regulation_90_prefers_reg_score_for_et_goal():
    # ENG-45: KO decidido por gol na ET → o gravado inclui a prorrogação; o slot de 90' usa o 90'.
    # Costura (ENG-48/55): edição REAL — `regulation_90` delega a `Edition.score_90`, e um dublê
    # (SimpleNamespace) só testaria a nossa suposição sobre a interface, não a interface.
    ed = load_edition(2026)
    et_id = next(iter(ed.regulation))
    fx = next(f for f in ed.fixtures if f.match_id == et_id)
    assert efficiency.regulation_90(ed, fx) == ed.regulation[et_id]
    assert efficiency.regulation_90(ed, fx) != (fx.home_goals, fx.away_goals)  # difere do consolidado


def test_regulation_90_falls_back_to_recorded():
    ed = load_edition(2026)
    plain = next(f for f in ed.fixtures if f.played and f.match_id not in ed.regulation)
    assert efficiency.regulation_90(ed, plain) == (plain.home_goals, plain.away_goals)  # o gravado É o 90'
    unplayed = next(f for f in ed.fixtures if not f.played)
    assert efficiency.regulation_90(ed, unplayed) is None


def test_eng45_et_goal_scored_against_90_and_gets_bonus():
    # Regressão ENG-45: o placar de 90' faz o jogo cair no caminho de ET (empate nos 90'), resolvendo
    # o bônus; com o placar GRAVADO (com ET) a lógica antiga o tratava como decidido nos 90'.
    ed = load_edition(2026)
    fx = next(f for f in ed.fixtures if f.match_id == 82)  # J82: gravado 3x2, mas 2x2 nos 90'
    reg90 = efficiency.regulation_90(ed, fx)
    assert reg90 is not None
    assert reg90[0] == reg90[1]  # premissa do caso: os 90' terminaram empatados
    pens = {("2026-07-01", frozenset({"Belgium", "Senegal"})): ""}  # na fonte, sem shootout ⇒ ET
    assert efficiency._actual_ko_outcome(reg90[0], reg90[1], "2026-07-01", "Belgium", "Belgium", "Senegal", pens) == (
        "home",
        None,
    )
    # contraste (o bug): usar o gravado (com ET) ⇒ "decidido nos 90'", sem bônus e slot pontuado errado
    assert fx.home_goals is not None
    assert fx.away_goals is not None
    assert efficiency._actual_ko_outcome(
        fx.home_goals, fx.away_goals, "2026-07-01", "Belgium", "Belgium", "Senegal", pens
    ) == (None, None)


def _recon(pts: float, palpite: str = "2x1", real: str = "2x1") -> dict:
    return {"pts": pts, "palpite": palpite, "real": real}


def test_reconcile_ceiling_freezes_measured_game():
    # ENG-34: jogo já no cache (asof) não re-pontua no headline mesmo se a reconstrução viva mudar
    cache = {5: {"pts": 10.0, "palpite": "1x0", "real": "1x0", "source": "asof"}}
    headline, updated, drift = efficiency.reconcile_ceiling({5: _recon(7.0)}, {}, cache)
    assert headline[5] == 10.0  # congelado, não os 7 vivos
    assert updated[5]["pts"] == 10.0  # cache inalterado
    assert drift == [(5, 10.0, 7.0)]  # divergência reportada (asof) — headline usa o congelado


def test_reconcile_ceiling_prefers_archive_at_first_measurement():
    # 1ª medição de um jogo com snapshot real ⇒ congela o valor do archive, não a reconstrução
    headline, updated, drift = efficiency.reconcile_ceiling({6: _recon(8.0)}, {6: 12.0}, {})
    assert headline[6] == 12.0
    assert updated[6]["source"] == "archive"
    assert drift == []


def test_reconcile_ceiling_asof_when_no_archive():
    # sem snapshot real ⇒ congela a reconstrução as-of
    headline, updated, _ = efficiency.reconcile_ceiling({7: _recon(8.0)}, {}, {})
    assert headline[7] == 8.0
    assert updated[7]["source"] == "asof"


def test_reconcile_ceiling_no_drift_for_archive_source():
    # congelado de archive diverge da reconstrução por NATUREZA (ruído) — não é drift temporal
    cache = {5: {"pts": 12.0, "palpite": "2x0", "real": "3x0", "source": "archive"}}
    headline, _updated, drift = efficiency.reconcile_ceiling({5: _recon(8.0)}, {}, cache)
    assert headline[5] == 12.0
    assert drift == []  # fonte archive não gera drift (fica no --compare-archive)


def test_ceiling_cache_roundtrip(tmp_path):
    path = tmp_path / "ceiling.csv"
    entries = {5: {"pts": 10.0, "palpite": "1x0", "real": "1x0", "source": "asof", "code": "cafe1234"}}
    efficiency.save_ceiling(path, entries)
    loaded = efficiency.load_ceiling(path)
    assert loaded == entries
    assert efficiency.load_ceiling(tmp_path / "nope.csv") == {}


def test_load_ceiling_aceita_csv_pre_eng50_sem_coluna_code(tmp_path):
    # compatibilidade: ceiling.csv antigo (sem `code`) carrega com procedência vazia, não explode
    path = tmp_path / "ceiling.csv"
    path.write_text("match_id,pts,palpite,real,source\n5,10.0000,1x0,1x0,asof\n")
    loaded = efficiency.load_ceiling(path)
    assert loaded[5]["code"] == ""
    assert efficiency.provenance_split(loaded, "cafe1234") == ([], [5])  # desconhecida, não desatualizada


def test_parse_ko_layers():
    # ENG-46: inverso de pipeline._ko_layer_text (string renderizada → vocabulário do Scorer)
    assert efficiency._parse_ko_layers("Brasil", "Brasil", "Brasil", "Noruega") == ("home", "home")
    assert efficiency._parse_ko_layers("Noruega", "Noruega", "Brasil", "Noruega") == ("away", "away")
    assert efficiency._parse_ko_layers("Vai aos pênaltis", "Brasil", "Brasil", "Noruega") == ("penalties", "home")
    assert efficiency._parse_ko_layers("—", "", "Brasil", "Noruega") == (None, None)


def test_archive_ko_points_scoreline_plus_bonus():
    # ENG-46: pontua o palpite de 90' do snapshot vs o placar real dos 90' + o bônus de ET (do asof).
    # Palpite 1x1 (empate nos 90'), real 1x1 nos 90', foi aos pênaltis e o tool cravou o vencedor:
    # base+exato do empate ×2 (R32) + bônus +3 ida pênaltis +3 vencedor, ×2.
    s = Scorer(ScoringConfig(system="sistema_i", risk=0.5))
    row = {
        "palpite": "1x1",
        "P_mandante": "30%",
        "P_empate": "40%",
        "P_visitante": "30%",
        "prorrogacao": "Vai aos pênaltis",
        "penaltis": "Brasil",
        "mandante": "Brasil",
        "visitante": "Noruega",
    }
    pts_hit = efficiency._archive_ko_points(row, (1, 1), "penalties", "home", 2.0, s)
    pts_no_bonus = efficiency._archive_ko_points(row, (1, 1), None, None, 2.0, s)
    assert pts_hit == pts_no_bonus + s.knockout_bonus("penalties", "home", "penalties", "home") * 2.0
    assert pts_hit > pts_no_bonus  # o bônus de ET/pênaltis entra


def test_archive_ko_points_uses_90_score_not_recorded():
    # o palpite é pontuado contra o placar dos 90' passado (real90), não o placar-com-ET
    s = Scorer(ScoringConfig(system="sistema_i", risk=0.5))
    row = {
        "palpite": "2x1",
        "P_mandante": "50%",
        "P_empate": "25%",
        "P_visitante": "25%",
        "prorrogacao": "—",
        "penaltis": "—",
        "mandante": "Bélgica",
        "visitante": "Senegal",
    }
    # contra 2x2 (empate nos 90') o palpite 2x1 erra o resultado; contra 3x2 acertaria o vencedor
    assert efficiency._archive_ko_points(row, (2, 2), None, None, 2.0, s) < efficiency._archive_ko_points(
        row, (3, 2), None, None, 2.0, s
    )


def test_weighted_ko_bonus_is_doubled_in_r32():
    # o bônus de KO também leva o peso de fase: pênaltis acertados = +3/+3 unit → ×2 = +12 no R32
    s = Scorer(ScoringConfig(system="sistema_i", risk=0.5))
    w = 2.0
    assert s.knockout_bonus("penalties", "home", "penalties", "home") * w == 12.0
    # só a ida aos pênaltis certa (errou o vencedor): +3 unit ×2 = 6
    assert s.knockout_bonus("penalties", "home", "penalties", "away") * w == 6.0


# ── sondas: contradição de fonte (ENG-49) e canário de caminho morto (ENG-50) ──────────────────


def _score(ko: bool, real: str, act_et: str | None = None, in_source: bool = True) -> dict:
    return {"ko": ko, "real": real, "act_et": act_et, "in_source": in_source}


def test_cross_source_ko_check_separa_latencia_de_contradicao():
    # a edição afirma pênaltis no J74 e gol na prorrogação no J82; nada sobre o J96
    ed = SimpleNamespace(shootouts={74: "Paraguay"}, regulation={82: (2, 2)})
    scores = {
        74: _score(True, "1x1", None),  # fonte TEM o jogo e não confirma → CONTRADIÇÃO (ENG-48)
        96: _score(True, "0x0", None),  # ninguém afirma → latência genuína (fonte não ingeriu)
        82: _score(True, "2x2", "penalties"),  # edição diz ET, fonte diz pênaltis → CONTRADIÇÃO
        75: _score(True, "1x1", "away"),  # fonte resolveu, edição silente → ok
        88: _score(True, "2x1", None),  # não empatou nos 90' → nem entra na conta
        1: _score(False, "1x1", None),  # jogo de grupo → irrelevante
    }
    latency, contradiction = efficiency.cross_source_ko_check(cast("Edition", ed), scores)
    assert latency == [96]
    assert contradiction == [74, 82]


def test_jogo_ainda_fora_da_fonte_e_latencia_mesmo_com_a_edicao_ja_afirmando():
    """ENG-49: curadoria manual corre NA FRENTE da fonte — isso é latência, não contradição.

    O martj42 publica com ~1 dia de atraso. Um KO de ontem, já curado no `regulation.csv`, ainda
    não está na base: a fonte não tem o que confirmar. Antes, a sonda só olhava "a edição afirma e
    a fonte não confirma" e cuspia `🚨 contradição … NÃO é latência: bug de lookup, curadoria
    errada` — mandando investigar curadoria correta (aconteceu com J99/J100 em 12/07). Uma sonda
    que grita erro no caso banal é uma sonda que será ignorada quando gritar de verdade.
    """
    ed = SimpleNamespace(shootouts={}, regulation={99: (1, 1), 100: (1, 1)})
    scores = {
        99: _score(True, "1x1", None, in_source=False),  # jogado ontem; a fonte ainda não o tem
        100: _score(True, "1x1", None, in_source=False),
    }
    latency, contradiction = efficiency.cross_source_ko_check(cast("Edition", ed), scores)
    assert contradiction == []  # nada a investigar: a fonte simplesmente não chegou lá
    assert latency == [99, 100]


def test_dead_path_canary_conta_populacao_nao_caso():
    scores = {
        74: _score(True, "1x1", None),
        75: _score(True, "1x1", None),
        88: _score(True, "3x2", None),  # decidido nos 90' → não é população do canário
    }
    assert efficiency.dead_path_canary(scores) == (0, 2)  # dispara: 2 empatados, 0 creditados
    scores[75] = _score(True, "1x1", "penalties")
    assert efficiency.dead_path_canary(scores) == (1, 2)  # não dispara: o ramo rodou


def test_cross_source_ko_check_casa_com_as_chaves_da_edicao_real():
    """A sonda casa contra a `Edition` de verdade — não contra um dict fabricado.

    Guarda a mesma costura que o ENG-48 quebrou, um nível acima: `shootouts.csv`/`regulation.csv`
    são indexados por `match_id` **int**. Se o carregador passar a devolver chave `str`, o
    `mid in edition.shootouts` silencia e a contradição vira "latência" — o bug de novo, com
    outra roupa.
    """
    ed = load_edition(2026)
    assert ed.shootouts, "a edição 2026 tem shootouts curados — o teste perde o sentido sem eles"
    assert all(isinstance(k, int) for k in ed.shootouts)
    assert all(isinstance(k, int) for k in ed.regulation)

    mid = next(iter(ed.shootouts))  # jogo que a edição afirma ter ido aos pênaltis
    latency, contradiction = efficiency.cross_source_ko_check(ed, {mid: _score(True, "1x1", None)})
    assert contradiction == [mid]
    assert latency == []


# ── gatilho de anomalia + procedência do congelamento (ENG-50) ─────────────────────────────────


def test_ceiling_anomalies_dispara_so_acima_do_teto():
    assert efficiency.ceiling_anomalies(423.0, 409.0, 400.0) == []  # ninguém acima ⇒ nada a investigar
    assert efficiency.ceiling_anomalies(423.0, None, None) == []
    anomalies = efficiency.ceiling_anomalies(399.0, 409.0, 471.0)  # o estado real de 10/07 sob o ENG-48
    assert len(anomalies) == 2
    assert "seus pontos" in anomalies[0]
    assert "líder" in anomalies[1]


def test_mechanical_suspects_marca_canario_e_contradicao():
    # estado do ENG-48: bônus creditado em zero, fontes discordando, tetos sem procedência
    suspects = efficiency.mechanical_suspects(
        latent=[96], contradiction=[74, 75], credited=0, tied=5, stale=[], unknown=[1, 2], recon_only=30
    )
    assert [ok for ok, _ in suspects] == [False, False, False, False, False]  # tudo sujo

    # pós-fix, sem latência e com procedência: sondas limpas ⇒ a leitura estatística fica legítima
    clean = efficiency.mechanical_suspects(
        latent=[], contradiction=[], credited=4, tied=5, stale=[], unknown=[], recon_only=0
    )
    assert all(ok for ok, _ in clean)


def test_code_fingerprint_muda_com_o_conteudo(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    before = efficiency.code_fingerprint(tmp_path, ("a.py",))
    assert before == efficiency.code_fingerprint(tmp_path, ("a.py",))  # estável
    (tmp_path / "a.py").write_text("x = 2")
    assert efficiency.code_fingerprint(tmp_path, ("a.py",)) != before  # pega alteração não commitada


def test_code_fingerprint_cobre_o_pontuador_do_teto():
    # os arquivos vigiados existem e são os que decidem quanto vale um teto congelado
    for rel in efficiency.CEILING_CODE_FILES:
        assert (PROJECT_ROOT / rel).exists(), rel
    assert efficiency.code_fingerprint(PROJECT_ROOT)  # não explode no repo real


def test_provenance_split_separa_desatualizado_de_desconhecido():
    cache: dict[int, dict] = {
        1: {"pts": 7.0, "code": "aaaaaaaa"},  # congelado sob o código atual
        2: {"pts": 7.0, "code": "bbbbbbbb"},  # sob código diferente → recongelar
        3: {"pts": 7.0, "code": ""},  # pré-ENG-50 → procedência desconhecida
        4: {"pts": 7.0},  # coluna ausente (csv antigo) → idem
    }
    stale, unknown = efficiency.provenance_split(cache, "aaaaaaaa")
    assert stale == [2]
    assert unknown == [3, 4]


def test_ceiling_roundtrip_preserva_procedencia(tmp_path):
    # a costura: save_ceiling escreve `code`, load_ceiling o lê de volta (não fabricado no teste)
    path = tmp_path / "ceiling.csv"
    entries = {5: {"pts": 10.0, "palpite": "1x0", "real": "1x0", "source": "asof", "code": "deadbeef"}}
    efficiency.save_ceiling(path, entries)
    assert efficiency.load_ceiling(path) == entries
    stale, unknown = efficiency.provenance_split(efficiency.load_ceiling(path), "deadbeef")
    assert stale == []
    assert unknown == []


def test_reconcile_ceiling_carimba_procedencia_no_congelamento():
    _headline, updated, _drift = efficiency.reconcile_ceiling({7: _recon(8.0)}, {}, {}, "cafe1234")
    assert updated[7]["code"] == "cafe1234"
