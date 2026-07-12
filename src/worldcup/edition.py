"""Carregamento e validação (Pydantic v2) da spec de uma edição da Copa.

Uma edição é totalmente descrita por arquivos em `data/editions/<ano>/`:
  - tournament.toml          formato (grupos, avanço, terceiros, fases, anfitriões, desempates)
  - groups.csv               seleções por grupo
  - fixtures.csv             todos os jogos (grupo com times reais; mata-mata com slots)
  - scoring.toml             pontuação do bolão (sistema, risco, pesos por fase)

O código é agnóstico à edição: para 2030 basta adicionar uma nova pasta.
"""

from __future__ import annotations

import csv
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
EDITIONS_DIR = PROJECT_ROOT / "data" / "editions"

VALID_SYSTEMS = {"sistema_i", "simplificado", "so_vencedor"}


class GroupStageSpec(BaseModel):
    num_groups: int = Field(gt=0)
    group_size: int = Field(gt=0)
    advance_per_group: int = Field(gt=0)
    best_thirds: int = Field(ge=0)
    tiebreakers: list[str]
    knockout_stages: list[str]
    # Override opcional da alocação dos melhores terceiros (tabela oficial Annex C da FIFA).
    # Mapeia o match_id de cada slot de terceiro -> grupo cujo 3º o preenche, para UMA combinação
    # realizada de terceiros classificados. Quando o conjunto de grupos do override bate com os
    # terceiros que de fato se classificaram, o motor usa esta tabela; senão cai no casamento por
    # restrição (`_assign_thirds`). Permite cravar a alocação oficial sem hardcode no código.
    third_allocation: dict[int, str] = Field(default_factory=dict)


class TournamentSpec(BaseModel):
    name: str
    edition: int
    hosts: list[str] = Field(default_factory=list)
    group_stage: GroupStageSpec


class Fixture(BaseModel):
    match_id: int
    stage: str
    group: str | None = None
    date: str
    home: str
    away: str
    neutral: bool = True
    third_groups: list[str] = Field(default_factory=list)
    home_goals: int | None = None
    away_goals: int | None = None
    ko_outcome: str | None = None  # vencedor real do confronto de mata-mata (nome da seleção)

    @property
    def is_group(self) -> bool:
        return self.stage == "group"

    @property
    def played(self) -> bool:
        return self.home_goals is not None and self.away_goals is not None


class ScoringConfig(BaseModel):
    system: str = "sistema_i"
    risk: float = Field(default=0.6, ge=0.0, le=1.0)
    # peso do mercado no blend com odds (ENG-19): 0 = só modelo (default), 1 = só mercado.
    blend_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    # peso de cada jogo já disputado da edição no ajuste do modelo (ENG-42/44): 1 = pesa como um
    # jogo histórico (sem boost). O sweep as-of da 2026 mostrou Brier monotônico crescente em boost
    # (1.0 = mínimo) — boostar superajusta a forma recente. Default 1.0 (sem boost); cada edição
    # pode sobrescrever com `blend-track --boost-sweep`.
    edition_boost: float = Field(default=1.0, ge=1.0)
    phase_weights: dict[str, float] = Field(default_factory=dict)
    sistema_i: dict[str, float] = Field(default_factory=dict)
    simplificado: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_system(self) -> ScoringConfig:
        if self.system not in VALID_SYSTEMS:
            raise ValueError(f"system inválido: {self.system!r}. Use um de {sorted(VALID_SYSTEMS)}.")
        return self

    def weight(self, stage: str) -> float:
        return self.phase_weights.get(stage, 1.0)


class Edition(BaseModel):
    spec: TournamentSpec
    groups: dict[str, list[str]]  # grupo -> seleções
    fixtures: list[Fixture]
    scoring: ScoringConfig
    directory: Path
    # odds de mercado opcionais por jogo (match_id -> odds decimais mandante/empate/visitante).
    # Carregadas de odds.csv se existir; ausência ⇒ blend desligado para o jogo (ENG-19).
    odds: dict[int, tuple[float, float, float]] = Field(default_factory=dict)
    # mercado de totals opcional por jogo (match_id -> (linha de gols, odd over, odd under)),
    # das colunas total_line/over/under do MESMO odds.csv (opcionais — ENG-35). Sem totals para
    # um jogo ⇒ o blend corrige só o 1×2 (comportamento pré-ENG-35).
    totals: dict[int, tuple[float, float, float]] = Field(default_factory=dict)
    # vencedores de disputas de pênaltis por jogo de KO (match_id -> seleção canônica), capturados
    # à mão quando a fonte oficial ainda não tem (latência). De shootouts.csv se existir (ENG-30).
    shootouts: dict[int, str] = Field(default_factory=dict)
    # placar dos **90'** (tempo normal) de jogos de KO decididos por **gol na prorrogação** — nesses,
    # o placar gravado em fixtures inclui a ET e difere do 90' (ENG-45). O bolão pontua o slot de 90'
    # contra o tempo normal, então guardamos o 90' aqui (match_id -> (mandante, visitante)). De
    # regulation.csv se existir. Jogos de pênaltis puros NÃO precisam de entrada (o gravado já é o 90').
    regulation: dict[int, tuple[int, int]] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    # ---- consultas convenientes ----
    def score_90(self, fixture: Fixture) -> tuple[int, int] | None:
        """Placar dos **90'** (tempo normal) de um jogo disputado; `None` se ainda não foi.

        **Fonte única da verdade sobre "o que aconteceu nos 90'"** (ENG-55). O `fixtures.csv` grava o
        placar **consolidado**: num KO decidido por gol na prorrogação ele inclui a ET (J82 = `3×2`,
        mas `2×2` nos 90'). Quem precisa dos 90' — o **ajuste do modelo** (que estima taxas de gol de
        90' e cuja camada de ET reescala λ por 30/90, logo λ **tem** de ser a taxa de 90') e a
        **pontuação** (o bolão mede o slot de 90' contra o tempo normal) — deve passar por aqui, não
        ler `home_goals`/`away_goals` cru.

        `regulation.csv` (ENG-45) cobre exatamente os KO com gol na ET. Jogos de pênaltis puros não
        precisam de entrada: o gravado já **é** o 90' (o empate está preservado).
        """
        if not fixture.played or fixture.home_goals is None or fixture.away_goals is None:
            return None
        return self.regulation.get(fixture.match_id, (fixture.home_goals, fixture.away_goals))

    @property
    def teams(self) -> list[str]:
        return [t for ts in self.groups.values() for t in ts]

    @property
    def hosts(self) -> list[str]:
        return self.spec.hosts

    def group_fixtures(self) -> list[Fixture]:
        return [f for f in self.fixtures if f.is_group]

    def knockout_fixtures(self) -> list[Fixture]:
        return [f for f in self.fixtures if not f.is_group]

    def as_of(self, date_str: str) -> Edition:
        """Edição como conhecida no **início** de `date_str` (formato AAAA-MM-DD).

        Descarta os resultados dos jogos a partir dessa data (inclusive) — eles ainda não
        haviam acontecido naquela manhã. Reproduz o estado de conhecimento de um dia para
        gerar a "visão reconstruída" dos palpites, sem mexer no histórico em disco.
        """
        cutoff = date_str.strip()
        fixtures = [
            f.model_copy(update={"home_goals": None, "away_goals": None, "ko_outcome": None}) if f.date >= cutoff else f
            for f in self.fixtures
        ]
        future = {f.match_id for f in self.fixtures if f.date >= cutoff}
        shootouts = {mid: w for mid, w in self.shootouts.items() if mid not in future}
        regulation = {mid: s for mid, s in self.regulation.items() if mid not in future}
        return self.model_copy(update={"fixtures": fixtures, "shootouts": shootouts, "regulation": regulation})

    # ---- validação estrutural ----
    @model_validator(mode="after")
    def _validate(self) -> Edition:
        gs = self.spec.group_stage
        if len(self.groups) != gs.num_groups:
            raise ValueError(f"esperados {gs.num_groups} grupos, encontrados {len(self.groups)}")
        for g, ts in self.groups.items():
            if len(ts) != gs.group_size:
                raise ValueError(f"grupo {g} tem {len(ts)} times (esperado {gs.group_size})")
        all_teams = self.teams
        if len(set(all_teams)) != len(all_teams):
            raise ValueError("há seleções repetidas entre os grupos")

        team_set = set(all_teams)
        group_games = self.group_fixtures()
        for f in group_games:
            if f.home not in team_set or f.away not in team_set:
                raise ValueError(f"jogo {f.match_id}: time fora dos grupos ({f.home} x {f.away})")

        ko = self.knockout_fixtures()
        third_slots = sum(1 for f in ko if "3rd" in (f.home, f.away))
        if third_slots != gs.best_thirds:
            raise ValueError(f"esperados {gs.best_thirds} slots de terceiro no mata-mata, achei {third_slots}")
        for f in ko:
            if f.stage not in gs.knockout_stages:
                raise ValueError(f"jogo {f.match_id}: fase '{f.stage}' fora de knockout_stages")
        return self


def _read_toml(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _load_groups(path: Path) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            groups.setdefault(row["group"], []).append(row["team"])
    return groups


def _parse_int(value: str) -> int | None:
    value = (value or "").strip()
    return int(value) if value else None


def _load_fixtures(path: Path) -> list[Fixture]:
    fixtures: list[Fixture] = []
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            tg = (row.get("third_groups") or "").strip()
            fixtures.append(
                Fixture(
                    match_id=int(row["match_id"]),
                    stage=row["stage"],
                    group=(row.get("group") or "").strip() or None,
                    date=row["date"],
                    home=row["home"],
                    away=row["away"],
                    neutral=str(row.get("neutral", "true")).strip().lower() in {"true", "1"},
                    third_groups=tg.split("|") if tg else [],
                    home_goals=_parse_int(row.get("home_goals", "")),
                    away_goals=_parse_int(row.get("away_goals", "")),
                    ko_outcome=(row.get("ko_outcome") or "").strip() or None,
                )
            )
    return fixtures


def _load_odds(path: Path) -> dict[int, tuple[float, float, float]]:
    """Lê `odds.csv` (opcional): `match_id,home,draw,away` em odds decimais. Ausente ⇒ vazio.

    Linhas com odds em branco são ignoradas (permite preencher só os jogos da próxima rodada).
    """
    if not path.exists():
        return {}
    odds: dict[int, tuple[float, float, float]] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            cells = [(row.get(k) or "").strip() for k in ("home", "draw", "away")]
            if not all(cells):
                continue
            h, d, a = (float(c) for c in cells)
            odds[int(row["match_id"])] = (h, d, a)
    return odds


def _load_totals(path: Path) -> dict[int, tuple[float, float, float]]:
    """Lê as colunas opcionais de totals do `odds.csv`: `total_line,over,under` (ENG-35).

    Arquivos antigos (só 1×2) não têm as colunas ⇒ vazio; linhas com totals em branco são
    ignoradas (jogo segue com blend só de 1×2).
    """
    if not path.exists():
        return {}
    totals: dict[int, tuple[float, float, float]] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            cells = [(row.get(k) or "").strip() for k in ("total_line", "over", "under")]
            if not all(cells):
                continue
            line, over, under = (float(c) for c in cells)
            totals[int(row["match_id"])] = (line, over, under)
    return totals


def _load_shootouts(path: Path) -> dict[int, str]:
    """Lê `shootouts.csv` (opcional): `match_id,winner` (vencedor dos pênaltis). Ausente ⇒ vazio.

    Captura manual para a edição viva quando a fonte oficial ainda não trouxe o shootout (ENG-30).
    Linhas sem vencedor são ignoradas; o nome é normalizado para o canônico.
    """
    if not path.exists():
        return {}
    from .teams import canonical

    out: dict[int, str] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            winner = (row.get("winner") or "").strip()
            if not winner:
                continue
            out[int(row["match_id"])] = canonical(winner)
    return out


def _load_regulation(path: Path) -> dict[int, tuple[int, int]]:
    """Lê `regulation.csv` (opcional): `match_id,reg_home,reg_away` — o placar dos **90'** de um KO
    decidido por **gol na prorrogação** (ENG-45). Ausente ⇒ vazio.

    Só precisa de entrada para jogos em que o placar gravado em `fixtures.csv` **inclui a ET** e
    difere do tempo normal (ex.: 3×2 no fim, mas 2×2 nos 90'). Pênaltis puros não entram (lá o
    gravado já é o 90', empate preservado — `shootouts.csv` cuida do desfecho). Linhas sem os dois
    placares são ignoradas. **Captura manual** sob a regra de confirmar placar em ≥2 fontes.
    """
    if not path.exists():
        return {}
    out: dict[int, tuple[int, int]] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            rh = (row.get("reg_home") or "").strip()
            ra = (row.get("reg_away") or "").strip()
            if not rh or not ra:
                continue
            out[int(row["match_id"])] = (int(rh), int(ra))
    return out


def load_edition(year: int, base_dir: Path = EDITIONS_DIR) -> Edition:
    """Carrega e valida a edição `year` a partir de `data/editions/<year>/`."""
    directory = base_dir / str(year)
    if not directory.exists():
        raise FileNotFoundError(f"Edição não encontrada: {directory}")

    spec = TournamentSpec(**_read_toml(directory / "tournament.toml"))
    scoring = ScoringConfig(**_read_toml(directory / "scoring.toml"))
    groups = _load_groups(directory / "groups.csv")
    fixtures = _load_fixtures(directory / "fixtures.csv")
    odds = _load_odds(directory / "odds.csv")
    totals = _load_totals(directory / "odds.csv")
    shootouts = _load_shootouts(directory / "shootouts.csv")
    regulation = _load_regulation(directory / "regulation.csv")
    return Edition(
        spec=spec,
        groups=groups,
        fixtures=fixtures,
        scoring=scoring,
        directory=directory,
        odds=odds,
        totals=totals,
        shootouts=shootouts,
        regulation=regulation,
    )
