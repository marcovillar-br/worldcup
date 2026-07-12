"""Testes do tratamento de erro de rede no download da base."""

from __future__ import annotations

import urllib.error
from io import StringIO

import pytest

from worldcup import fetch_data
from worldcup.fetch_data import DataSourceError, NetworkError, _download_text, download_from_urls


class _FakeResp:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *exc) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_download_text_raises_networkerror_after_retries(monkeypatch):
    calls = []

    def boom(req, timeout):
        calls.append(1)
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(fetch_data.urllib.request, "urlopen", boom)
    monkeypatch.setattr(fetch_data.time, "sleep", lambda _s: None)  # não espera no teste

    with pytest.raises(NetworkError):
        _download_text("https://example.test/x", timeout=1, retries=2)
    assert len(calls) == 3  # tentativa inicial + 2 retries


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://host/x", "gopher://host", "/etc/passwd"])
def test_download_text_rejects_non_http_scheme(url, monkeypatch):
    """Só http/https: file://, ftp:// e afins são barrados antes de qualquer I/O de rede."""

    def must_not_open(req, timeout):  # pragma: no cover - não deve ser chamado
        raise AssertionError("urlopen não deveria ser chamado para esquema não-HTTP")

    monkeypatch.setattr(fetch_data.urllib.request, "urlopen", must_not_open)
    with pytest.raises(NetworkError, match=r"[Ee]squema"):
        _download_text(url, timeout=1)


def test_download_text_retries_then_succeeds(monkeypatch):
    state = {"n": 0}

    def flaky(req, timeout):
        state["n"] += 1
        if state["n"] == 1:
            raise TimeoutError("blip")
        return _FakeResp(b"ok,data\n1,2\n")

    monkeypatch.setattr(fetch_data.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(fetch_data.time, "sleep", lambda _s: None)

    assert _download_text("https://example.test/x", timeout=1, retries=1) == "ok,data\n1,2\n"
    assert state["n"] == 2  # falhou uma vez, sucesso na segunda


def test_download_raw_rejects_unexpected_schema(monkeypatch):
    # a fonte respondeu, mas faltam colunas -> erro explícito e cedo (ENG-5), não KeyError adiante
    csv_sem_colunas = "date,home_team,away_team\n2026-06-11,Mexico,South Africa\n"
    monkeypatch.setattr(fetch_data, "_download_text", lambda url, timeout: csv_sem_colunas)
    with pytest.raises(DataSourceError, match="home_score"):
        fetch_data.download_raw()


def test_download_shootouts_rejects_unexpected_schema(monkeypatch):
    csv_sem_winner = "date,home_team,away_team\n2026-06-11,Mexico,South Africa\n"
    monkeypatch.setattr(fetch_data, "_download_text", lambda url, timeout: csv_sem_winner)
    with pytest.raises(DataSourceError, match="winner"):
        fetch_data.download_shootouts()


_VALID_CSV = (
    "date,home_team,away_team,home_score,away_score,tournament,neutral\n"
    "2026-06-11,Mexico,South Africa,2,0,FIFA World Cup,False\n"
)

_PRIMARY = "https://primary.test/r.csv"
_FALLBACK = "https://fallback.test/r.csv"


def _make_fake_raw(valid_csv: str):
    from io import StringIO

    import pandas as pd

    def _fake(url: str, timeout: int = 60) -> pd.DataFrame:
        return pd.read_csv(StringIO(valid_csv))

    return _fake


def test_download_from_urls_falls_back_on_network_error(monkeypatch):
    """Primeira URL com NetworkError → usa a segunda."""
    called = []
    good = _make_fake_raw(_VALID_CSV)

    def fake_download_raw(url: str, timeout: int = 60):
        called.append(url)
        if url == _PRIMARY:
            raise NetworkError("offline")
        return good(url, timeout)

    monkeypatch.setattr(fetch_data, "download_raw", fake_download_raw)
    df = download_from_urls([_PRIMARY, _FALLBACK])
    assert called == [_PRIMARY, _FALLBACK]
    assert len(df) == 1


def test_download_from_urls_falls_back_on_schema_error(monkeypatch):
    """Primeira URL com DataSourceError → usa a segunda."""
    called = []
    good = _make_fake_raw(_VALID_CSV)

    def fake_download_raw(url: str, timeout: int = 60):
        called.append(url)
        if url == _PRIMARY:
            raise DataSourceError("schema mudou")
        return good(url, timeout)

    monkeypatch.setattr(fetch_data, "download_raw", fake_download_raw)
    df = download_from_urls([_PRIMARY, _FALLBACK])
    assert called == [_PRIMARY, _FALLBACK]
    assert len(df) == 1


def test_download_from_urls_raises_when_all_fail(monkeypatch):
    """Todas as URLs falham → relança o último erro."""

    def fake_download_raw(url: str, timeout: int = 60):
        raise NetworkError(f"offline: {url}")

    monkeypatch.setattr(fetch_data, "download_raw", fake_download_raw)
    with pytest.raises(NetworkError, match="offline"):
        download_from_urls([_PRIMARY, _FALLBACK])


def _games_df():
    import pandas as pd

    return pd.read_csv(
        StringIO(
            "date,home_team,away_team,home_score,away_score,tournament,neutral\n"
            "2022-12-09,Croatia,Brazil,1,1,FIFA World Cup,True\n"  # foi a pênaltis
            "2022-12-10,England,France,1,2,FIFA World Cup,True\n"  # decidido em 90'
        )
    )


def test_normalize_merges_penalty_winner():
    # o shootouts adiciona penalty_winner casando por (date, home, away); só o jogo de pênaltis recebe
    import pandas as pd

    shootouts = pd.read_csv(StringIO("date,home_team,away_team,winner\n2022-12-09,Croatia,Brazil,Croatia\n"))
    out = fetch_data.normalize(_games_df(), cutoff="2006-01-01", shootouts=shootouts)
    assert "penalty_winner" in out.columns
    rows = {(r.home_team, r.away_team): r.penalty_winner for r in out.itertuples()}
    assert rows[("Croatia", "Brazil")] == "Croatia"
    assert rows[("England", "France")] == ""  # não foi a pênaltis


def test_normalize_without_shootouts_leaves_penalty_winner_empty():
    out = fetch_data.normalize(_games_df(), cutoff="2006-01-01", shootouts=None)
    assert list(out["penalty_winner"]) == ["", ""]


# ------------------------------------------------- placar dos 90' (ENG-54)
def _goals_df(rows: str):
    import pandas as pd

    return pd.read_csv(StringIO("date,home_team,away_team,team,scorer,minute,own_goal,penalty\n" + rows))


# Croácia 1×1 Brasil (2022): Neymar aos 105', Petković aos 117' — 0×0 nos 90'.
# Inglaterra 1×2 França: os 3 gols no tempo normal — o placar dos 90' é o próprio consolidado.
_REAL_GOALS = (
    "2022-12-09,Croatia,Brazil,Brazil,Neymar,105,FALSE,FALSE\n"
    "2022-12-09,Croatia,Brazil,Croatia,Petkovic,117,FALSE,FALSE\n"
    "2022-12-10,England,France,France,Tchouameni,17,FALSE,FALSE\n"
    "2022-12-10,England,France,England,Kane,54,FALSE,TRUE\n"
    "2022-12-10,England,France,France,Giroud,78,FALSE,FALSE\n"
)


def test_regulation_score_strips_extra_time_goals():
    # o jogo decidido na ET volta a ser o EMPATE que foi nos 90' — o dano central do ENG-54
    out = fetch_data.normalize(_games_df(), cutoff="2006-01-01", goalscorers=_goals_df(_REAL_GOALS))
    rows = {(r.home_team, r.away_team): (r.reg_home_score, r.reg_away_score) for r in out.itertuples()}
    assert rows[("Croatia", "Brazil")] == (0, 0)  # 1×1 no consolidado (gols aos 105' e 117')
    assert rows[("England", "France")] == (1, 2)  # sem gol na ET ⇒ 90' == consolidado
    # o consolidado permanece intacto na base: é dele que o `sync` preenche o fixtures.csv
    assert [(r.home_score, r.away_score) for r in out.itertuples()] == [(1, 1), (1, 2)]


def test_regulation_score_keeps_stoppage_time_goals_of_the_90():
    # a fonte achata o acréscimo no minuto 90 (por isso `minute > 90` é ET, não acréscimo). Um gol
    # aos 90' decide o jogo e NÃO pode ser subtraído — subtrair inventaria um empate.
    goals = "2022-12-10,England,France,England,Kane,90,FALSE,FALSE\n"
    games = fetch_data.normalize(
        _games_df().assign(home_score=[1, 1], away_score=[1, 0]),
        cutoff="2006-01-01",
        goalscorers=_goals_df(goals),
    )
    eng = next(r for r in games.itertuples() if r.home_team == "England")
    assert (eng.reg_home_score, eng.reg_away_score) == (1, 0)  # vitória nos 90', preservada


def test_regulation_score_falls_back_when_goal_list_is_incomplete():
    # PORTÃO: lista de gols que não bate com o placar ⇒ mantém o consolidado. Subtrair de uma lista
    # incompleta inventaria empates — pior que o viés que se quer corrigir.
    partial = "2022-12-09,Croatia,Brazil,Brazil,Neymar,105,FALSE,FALSE\n"  # falta o gol da Croácia
    out = fetch_data.normalize(_games_df(), cutoff="2006-01-01", goalscorers=_goals_df(partial))
    cro = next(r for r in out.itertuples() if r.home_team == "Croatia")
    assert (cro.reg_home_score, cro.reg_away_score) == (1, 1)  # consolidado, não (0, 0)


def test_regulation_score_falls_back_when_a_minute_is_unreadable():
    # minuto ilegível ⇒ não dá para saber se o gol foi na ET ⇒ o jogo inteiro fica de fora do portão
    unreadable = (
        "2022-12-09,Croatia,Brazil,Brazil,Neymar,?,FALSE,FALSE\n"
        "2022-12-09,Croatia,Brazil,Croatia,Petkovic,117,FALSE,FALSE\n"
    )
    out = fetch_data.normalize(_games_df(), cutoff="2006-01-01", goalscorers=_goals_df(unreadable))
    cro = next(r for r in out.itertuples() if r.home_team == "Croatia")
    assert (cro.reg_home_score, cro.reg_away_score) == (1, 1)


def test_score_90_swaps_the_score_and_labels_the_extra_time_outcome():
    import pandas as pd

    shootouts = pd.read_csv(StringIO("date,home_team,away_team,winner\n2022-12-09,Croatia,Brazil,Croatia\n"))
    base = fetch_data.normalize(
        _games_df(), cutoff="2006-01-01", shootouts=shootouts, goalscorers=_goals_df(_REAL_GOALS)
    )
    view = fetch_data.score_90(base)
    cro = next(r for r in view.itertuples() if r.home_team == "Croatia")
    assert (cro.home_score, cro.away_score) == (0, 0)  # o ajuste/backtest enxergam os 90'
    assert cro.et_outcome == "penalties"
    eng = next(r for r in view.itertuples() if r.home_team == "England")
    assert eng.et_outcome == ""  # decidido nos 90' ⇒ sem slot de prorrogação


def test_extra_time_outcome_names_the_side_that_won_in_extra_time():
    # empate nos 90' + decisão no consolidado + sem pênaltis ⇒ alguém venceu DENTRO da prorrogação.
    # Era justamente esse jogo que o backtest não conseguia identificar antes do ENG-54.
    goals = (
        "2022-12-10,England,France,England,Kane,54,FALSE,FALSE\n"
        "2022-12-10,England,France,France,Giroud,78,FALSE,FALSE\n"
        "2022-12-10,England,France,France,Mbappe,113,FALSE,FALSE\n"
    )
    base = fetch_data.normalize(
        _games_df().assign(home_score=[1, 1], away_score=[1, 2]),
        cutoff="2006-01-01",
        goalscorers=_goals_df(goals),
    )
    view = fetch_data.score_90(base)
    eng = next(r for r in view.itertuples() if r.home_team == "England")
    assert (eng.home_score, eng.away_score) == (1, 1)  # empatado nos 90'
    assert eng.et_outcome == "away"  # a França venceu na prorrogação


def test_score_90_on_a_base_without_the_columns_keeps_the_consolidated():
    # compat: base gerada antes do ENG-54 ⇒ nenhuma correção conhecida, e nada explode
    games = _games_df()
    view = fetch_data.score_90(games)
    assert list(view["home_score"]) == list(games["home_score"])
    assert list(view["et_outcome"]) == ["", ""]


def test_regulation_score_survives_an_unplayed_game():
    # `played_only=False` mantém o jogo futuro com placar NaN. O NaN não cabe num int e nunca passa
    # no portão — o 90' tem de cair no consolidado (NaN), não estourar o carregamento da base.
    import pandas as pd

    future = _games_df().assign(home_score=[1, None], away_score=[1, None])
    out = fetch_data.normalize(future, cutoff="2006-01-01", played_only=False, goalscorers=_goals_df(_REAL_GOALS))
    played, unplayed = out.iloc[0], out.iloc[1]
    assert (played["reg_home_score"], played["reg_away_score"]) == (0, 0)  # Croácia×Brasil: 90' reconstruído
    assert pd.isna(unplayed["reg_home_score"])  # jogo futuro: sem placar, sem 90' a reconstruir
    assert pd.isna(unplayed["reg_away_score"])
