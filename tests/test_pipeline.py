"""Testes de utilitários do pipeline."""

from conftest import mini_historical
from worldcup import pipeline
from worldcup.edition import load_edition
from worldcup.pipeline import _pct_round


def test_pct_round_sums_to_100():
    # caso que arredondado independentemente daria 73+19+9 = 101
    assert sum(_pct_round(0.726, 0.194, 0.089)) == 100
    # caso que daria 50+26+23 = 99
    assert sum(_pct_round(0.504, 0.263, 0.233)) == 100


def test_pct_round_preserves_order():
    ph, pd_, pa = _pct_round(0.726, 0.194, 0.089)
    assert ph > pd_ > pa


def test_pct_round_exact_values_unchanged():
    assert _pct_round(0.5, 0.3, 0.2) == [50, 30, 20]


def test_pct_round_extra_unit_goes_to_largest_remainder():
    # 33.4 / 33.3 / 33.3  -> resto sobra 1, vai para a maior fração (a primeira)
    assert _pct_round(0.334, 0.333, 0.333) == [34, 33, 33]


# ------------------------------------------------- e2e do pipeline real no CI (ENG-20)
def test_pipeline_run_e2e_invariants(monkeypatch):
    """Roda `pipeline.run` de ponta a ponta com histórico sintético e afirma invariantes
    estruturais — fecha o ponto cego de o CI nunca exercitar fit→sim→bracket→predict."""
    monkeypatch.setattr(pipeline, "load_historical", mini_historical)
    ed = load_edition(2026).as_of("2026-06-11")  # pré-torneio: 104 jogos não disputados
    result = pipeline.run(ed, n_sims=100, seed=1)

    assert len(result.rows) == len(ed.fixtures) == 104
    assert all(r["status"] == "PREVISTO" for r in result.rows)  # nada disputado no pré-torneio

    group_rows = [r for r in result.rows if r["fase"] == "group"]
    assert len(group_rows) == 72
    for r in group_rows:
        ph, pdr, pa = (int(r[k].rstrip("%")) for k in ("P_mandante", "P_empate", "P_visitante"))
        assert ph + pdr + pa == 100  # Hamilton (_pct_round) garante soma exata
        assert "x" in r["palpite"]  # todo jogo previsto tem placar

    ko_rows = [r for r in result.rows if r["fase"] != "group"]
    assert len(ko_rows) == 32
    for r in ko_rows:
        assert r["mandante"] != "?"  # chaveamento resolvido
        assert r["avanca"]  # quem avança preenchido

    assert abs(sum(result.champion_prob.values()) - 1.0) < 0.02  # probabilidades de título normalizadas


def test_final_ko_layers_real_outcomes():
    """ENG-30/58: camadas de um KO disputado, **da edição real** — nada de Fixture fabricado.

    O teste passa pela costura de verdade (`regulation.csv`/`shootouts.csv` → `Edition.score_90` →
    camadas): fabricar o `Fixture` à mão testaria a suposição do teste sobre o formato, não o
    formato (ENG-48) — foi assim que o placar de 120' virou "placar dos 90'" na tabela.
    """
    from worldcup.pipeline import _final_ko_layers

    e = load_edition(2026)
    by_id = {f.match_id: f for f in e.fixtures}

    # decidido nos 90' → "—"/"—", avança o vencedor real
    assert _final_ko_layers(e, by_id[76], "Brazil", "Japan") == ("—", "—", "Brasil")
    # decidido nos 90' SEM ko_outcome no fixture (fonte inconsistente) → avança quem fez mais gols
    assert _final_ko_layers(e, by_id[77], "France", "Sweden") == ("—", "—", "França")
    # empate nos 90' + shootout capturado → "Vai aos pênaltis" + vencedor (+ placar da disputa, ENG-59)
    assert _final_ko_layers(e, by_id[74], "Germany", "Paraguay") == (
        "Vai aos pênaltis",
        "Paraguai (3x4)",
        "Paraguai",
    )
    # J82: 2×2 nos 90' (regulation.csv), 3×2 com o gol na ET → a ET decidiu, NÃO o tempo normal
    assert e.score_90(by_id[82]) == (2, 2)
    assert _final_ko_layers(e, by_id[82], "Belgium", "Senegal") == ("Bélgica (3x2)", "—", "Bélgica")
    # J96: empate 0×0 até os 120' e alguém avançou ⇒ foi aos pênaltis (vencedor = quem avançou)
    assert _final_ko_layers(e, by_id[96], "Switzerland", "Colombia") == (
        "Vai aos pênaltis",
        "Suíça (4x3)",
        "Suíça",
    )
    # jogo ainda não disputado → sem camadas
    assert _final_ko_layers(e, by_id[104], "Spain", "Argentina") == ("", "", "")


def test_penalty_score_is_optional_in_the_layers():
    """ENG-59: sem placar da disputa capturado, a camada mostra só o vencedor — não quebra nem mente.

    A fonte (martj42) publica apenas `winner`; o placar é curadoria manual e pode faltar (edição nova,
    jogo recém-terminado). A ausência tem de degradar para o comportamento pré-ENG-59.
    """
    from worldcup.pipeline import _final_ko_layers

    e = load_edition(2026)
    sem_placar = e.model_copy(update={"shootout_scores": {}})
    j74 = next(f for f in e.fixtures if f.match_id == 74)
    assert _final_ko_layers(sem_placar, j74, "Germany", "Paraguay") == ("Vai aos pênaltis", "Paraguai", "Paraguai")


def test_played_ko_row_shows_90_minute_score():
    """ENG-58: a coluna de placar é o slot de **90'** — num KO decidido na ET, não o consolidado."""
    e = load_edition(2026)
    by_id = {f.match_id: f for f in e.fixtures}
    # o consolidado do fixtures.csv (3×2) inclui o gol da prorrogação; o bolão pontua o 90' (2×2)
    assert (by_id[82].home_goals, by_id[82].away_goals) == (3, 2)
    assert e.score_90(by_id[82]) == (2, 2)
    assert e.score_90(by_id[99]) == (1, 1)
    assert e.score_90(by_id[100]) == (1, 1)


def test_edition_loads_shootouts():
    from worldcup.edition import load_edition

    sh = load_edition(2026).shootouts
    # capturado de fontes verificadas: J74 Paraguai, J75 Marrocos, J88 Egito a pênaltis
    assert sh.get(74) == "Paraguay"
    assert sh.get(75) == "Morocco"
    assert sh.get(88) == "Egypt"


def test_build_training_frame_no_double_count():
    """Jogos da edição presentes na base histórica (fetch-data no meio da Copa) não são contados em
    dobro: entram uma vez só, com o boost — não também a peso 1.0 pela base."""
    import pandas as pd

    from worldcup.pipeline import build_training_frame

    ed = load_edition(2026).as_of("2026-06-20")  # alguns jogos de grupo já disputados
    played = next(f for f in ed.fixtures if f.played and f.home in ed.teams and f.away in ed.teams)

    # base histórica que JÁ contém o jogo da edição (mesmo par/dia) + uma linha de enchimento
    historical = pd.DataFrame(
        [
            {
                "date": pd.Timestamp(played.date),
                "home_team": played.home,
                "away_team": played.away,
                "home_score": 9,  # placar "errado" na base: deve ser descartado em favor do fixture
                "away_score": 9,
                "tournament": "FIFA World Cup",
                "neutral": played.neutral,
            },
            {
                "date": pd.Timestamp("2000-01-01"),
                "home_team": played.home,
                "away_team": played.away,
                "home_score": 0,
                "away_score": 0,
                "tournament": "Friendly",
                "neutral": True,
            },
        ]
    )
    train = build_training_frame(ed, historical, boost=5.0)

    key = train.apply(lambda r: (str(r["date"])[:10], frozenset((r["home_team"], r["away_team"]))), axis=1)
    match_key = (str(played.date)[:10], frozenset((played.home, played.away)))
    matches = train[key == match_key]
    assert len(matches) == 1  # uma única cópia, não duas
    assert matches.iloc[0]["weight_mult"] == 5.0  # a do fixture (boost explícito), não a 1.0 da base
    assert matches.iloc[0]["home_score"] == played.home_goals  # placar autoritativo é o do fixture
    # a linha de enchimento (dia diferente) permanece intacta
    assert (train["tournament"] == "Friendly").sum() == 1


def test_build_training_frame_feeds_knockout_with_boost():
    """ENG-42: jogo de KO disputado (fixture guarda slot `W##`/`2D`) entra no treino com os nomes
    reais das seleções e o boost — não fica preso à base histórica a peso 1.0."""
    import pandas as pd

    from worldcup.pipeline import build_training_frame
    from worldcup.sync import resolve_live_bracket

    ed = load_edition(2026).as_of("2026-07-04")  # mata-mata em andamento (16-avos disputados)
    ko = resolve_live_bracket(ed)
    played_ko = next(f for f in ed.fixtures if f.played and not f.is_group and f.match_id in ko)
    home, away = ko[played_ko.match_id]
    assert played_ko.home not in ed.teams  # o fixture guarda slot (`W##`/`2D`), não a seleção real
    assert home in ed.teams  # ...que resolve_live_bracket resolve para a seleção real

    train = build_training_frame(ed, pd.DataFrame(columns=["date", "home_team", "away_team"]), boost=5.0)
    key = train.apply(lambda r: (str(r["date"])[:10], frozenset((r["home_team"], r["away_team"]))), axis=1)
    match = train[key == (str(played_ko.date)[:10], frozenset((home, away)))]
    assert len(match) == 1  # entra pelos nomes reais, uma vez
    assert match.iloc[0]["weight_mult"] == 5.0  # entra no frame boostado (não filtrado como slot órfão)


def test_build_training_frame_trains_on_regulation_time_not_the_consolidated_score():
    """ENG-55: o modelo estima taxas de gol de **90'** (a camada de ET reescala λ por 30/90), então
    um KO decidido por gol na prorrogação tem de entrar no treino pelo placar do tempo normal — não
    pelo consolidado do `fixtures.csv`, que inclui a ET e transforma um empate em vitória.

    Costura (ENG-48): o esperado sai de `Edition.score_90`, a função de produção que define "o que
    aconteceu nos 90'" — não de um placar fabricado à mão aqui.
    """
    import pandas as pd

    from worldcup.pipeline import build_training_frame
    from worldcup.sync import resolve_live_bracket

    ed = load_edition(2026)
    et_id = next(iter(ed.regulation))  # KO com gol na prorrogação ⇒ consolidado ≠ 90'
    fx = next(f for f in ed.fixtures if f.match_id == et_id)
    reg = ed.score_90(fx)
    assert reg is not None
    assert reg != (fx.home_goals, fx.away_goals)  # premissa do caso: os dois placares divergem mesmo

    home, away = resolve_live_bracket(ed)[et_id]
    train = build_training_frame(ed, pd.DataFrame(columns=["date", "home_team", "away_team"]))
    key = train.apply(lambda r: (str(r["date"])[:10], frozenset((r["home_team"], r["away_team"]))), axis=1)
    row = train[key == (str(fx.date)[:10], frozenset((home, away)))].iloc[0]

    assert (row["home_score"], row["away_score"]) == reg  # treina no 90'...
    assert (row["home_score"], row["away_score"]) != (fx.home_goals, fx.away_goals)  # ...não no consolidado
    assert row["home_score"] == row["away_score"]  # e o empate dos 90' sobrevive ao ajuste


def test_build_training_frame_trains_on_the_90_of_the_historical_base_too():
    """ENG-54: o outro lado da união. Um KO histórico decidido por gol na prorrogação entra no
    ajuste pelo placar do **tempo normal**, não pelo consolidado da fonte — senão o modelo aprende
    que empate é mais raro do que é (um 1×1 decidido na ET vira "vitória").

    Costura (ENG-48): o esperado sai de `fetch_data.score_90`, a função de produção que define "o
    que aconteceu nos 90'" na base — não de um placar fabricado aqui.
    """
    import pandas as pd

    from worldcup.fetch_data import normalize, score_90
    from worldcup.pipeline import build_training_frame

    # Croácia 1×1 Brasil (2022): os dois gols na prorrogação ⇒ 0×0 nos 90'
    games = pd.DataFrame(
        [
            {
                "date": "2022-12-09",
                "home_team": "Croatia",
                "away_team": "Brazil",
                "home_score": 1,
                "away_score": 1,
                "tournament": "FIFA World Cup",
                "neutral": True,
            }
        ]
    )
    goals = pd.DataFrame(
        [
            {"date": "2022-12-09", "home_team": "Croatia", "away_team": "Brazil", "team": t, "minute": m}
            for t, m in (("Brazil", 105), ("Croatia", 117))
        ]
    )
    historical = normalize(games, cutoff="2006-01-01", goalscorers=goals)
    historical["date"] = pd.to_datetime(historical["date"])
    expected = score_90(historical)  # a produção diz qual é o placar dos 90'
    assert (expected.iloc[0]["home_score"], expected.iloc[0]["away_score"]) == (0, 0)  # premissa do caso

    ed = load_edition(2026).as_of("2026-06-11")  # pré-torneio: a edição não contribui nada
    train = build_training_frame(ed, historical)
    row = train[train["home_team"] == "Croatia"].iloc[0]
    assert (row["home_score"], row["away_score"]) == (expected.iloc[0]["home_score"], expected.iloc[0]["away_score"])
    assert row["home_score"] == row["away_score"]  # o empate dos 90' sobrevive ao ajuste


def test_ingestion_gaps_healthy_edition_is_empty():
    # ENG-43: na 2026 real o bracket resolve todo KO disputado ⇒ nenhum jogo fica fora do ajuste
    assert pipeline.ingestion_gaps(load_edition(2026)) == []


def test_ingestion_gaps_flags_unresolved_ko(monkeypatch):
    # bracket vazio ⇒ nenhum KO resolve ⇒ os KO disputados caem fora do ajuste; grupos (times reais) não
    ed = load_edition(2026)
    monkeypatch.setattr("worldcup.sync.resolve_live_bracket", lambda e: {})
    gaps = set(pipeline.ingestion_gaps(ed))
    played_ko = {f.match_id for f in ed.fixtures if f.played and not f.is_group}
    played_group = {f.match_id for f in ed.fixtures if f.played and f.is_group}
    assert gaps == played_ko  # todo KO disputado vira gap
    assert not (gaps & played_group)  # nenhum grupo vira gap
