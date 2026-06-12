# AGENTS.md — guia para agentes neste repositório

Gerador de palpites de bolão da Copa do Mundo. Modelo estatístico (Poisson/Dixon–Coles) treinado
em resultados históricos de seleções; gera o palpite de cada jogo maximizando os **pontos
esperados** do bolão. Calibrado para o **Sistema I** do app *Bolão de Futebol 2026*
(base 1–13 por probabilidade + bônus cumulativos; **zebra vale mais**).

**Metodologia (matemática, derivações, exemplos numéricos): [`docs/SPEC.md`](docs/SPEC.md).**

## Princípio central: agnóstico à edição

Nada específico de um ano fica no código. Cada edição é descrita por **dados** em
`data/editions/<ano>/`. Para uma Copa futura, adicione `data/editions/<ano>/` — o código não muda.

## Comandos (sempre via uv)

```bash
uv sync                                      # ambiente a partir do uv.lock
uv run worldcup fetch-data                   # baixa/normaliza a base histórica
uv run worldcup predict --edition 2026       # gera out/palpites-<ano>.{csv,md,html}
uv run worldcup sync-results --edition 2026  # baixa resultados reais da internet, preenche e repalpita
uv run worldcup record --edition 2026 --match <id> --home X --away Y [--ko-winner <Team>]
uv run worldcup backtest --edition 2022      # valida o modelo numa Copa passada
```

## Qualidade (rode antes de concluir mudanças)

```bash
uv run ruff check .          # lint (regras em pyproject; line-length 120)
uv run ruff format           # formatador (--check no CI; --fix para o lint)
uv run mypy                  # type checking estático (config em pyproject)
uv run pytest                # testes
uv run pre-commit install    # (1x) ativa o hook local de ruff lint+format
```

As mesmas checagens rodam no CI (`.github/workflows/ci.yml`, Python 3.11 e 3.13) em
push/PR. O pre-commit roda só o ruff (rápido); mypy e testes ficam no CI. Convenções de
código que ferramenta não pega ficam aqui no AGENTS.md (não há doc de regras separado).

## Arquitetura (`src/worldcup/`)

- `edition.py` — modelos **Pydantic v2** + `load_edition()`; carrega e valida a spec.
- `teams.py` — nome canônico (inglês, do dataset) ↔ exibição em português.
- `fetch_data.py` — baixa `results.csv`/`shootouts.csv` (martj42), normaliza → `data/historical_results.csv`.
- `model.py` — `DixonColesModel`: ajuste ponderado (decaimento temporal + peso de torneio + mando),
  filtra seleções não-FIFA; `score_matrix(home, away, neutral)`.
- `scoring.py` — `Scorer`: pontos do Sistema I + `best_prediction()` (maximiza pontos esperados);
  `risk` controla a ousadia (0.5 = fiel; >0.5 arrisca mais zebras).
- `knockout.py` — `predict_knockout()`: 3 camadas (placar 90', prorrogação, pênaltis) + quem avança.
- `format_engine.py` — simulação genérica: standings, Monte Carlo, chaveamento determinístico.
- `sync.py` — resolve o bracket só com resultados reais e preenche `fixtures.csv`.
- `pipeline.py` — orquestra fetch→fit→(realimenta)→simula→palpites.
- `cli.py` — argparse; entrypoint `worldcup`. `render_markdown`/`render_html` + `save_outputs`
  (CSV/MD/HTML); HTML é autocontido e print-friendly (gerado do `PredictionRun`, não do CSV).

## Modelo de dados de uma edição (`data/editions/2026/`)

- `tournament.toml` — formato (grupos, avanço, melhores 3ºs, fases, desempates, anfitriões).
- `groups.csv` — `group,team` (nomes canônicos em inglês).
- `fixtures.csv` — os 104 jogos. **O chaveamento mora aqui**, via slots em `home`/`away`:
  `1A`/`2A` (1º/2º do grupo A), `3rd` (+ `third_groups` permitidos), `W73` (vencedor do jogo 73),
  `L101` (perdedor). Colunas `home_goals,away_goals,ko_outcome` guardam o resultado real.
  `match_id` é a numeração **interna** (e os slots `W##`/`L##` a referenciam), **não** o número
  oficial da FIFA — não coincidem (ex.: jogo `50` aqui = *Match 51* FIFA). Ao cruzar com a escala
  oficial, guie-se pelos **nomes das seleções**, nunca pelo número.
- `scoring.toml` — sistema de pontos + pesos por fase (default: Sistema I + Equilíbrio gradual).
- `BOLAO.md` — **memória de campanha** do bolão (agnóstica a ferramenta): decisões vivas que não
  são rederiváveis de dados/código (`risk` escolhido, situação no ranking, regras do bolão).
  **Leia no início da sessão e atualize quando uma decisão de campanha acontecer.**

## Convenções e cuidados

- **Nomes de seleção**: canônico em inglês internamente; PT só na exibição (`teams.display`).
  Arquivos de dados usam o canônico. Novos aliases vão em `teams._ALIASES`.
- **Mando**: aplicado quando `neutral == false` (anfitriões em casa). A flag vem da fonte. O mando é
  de quem está em `tournament.toml::hosts`, **não** necessariamente da coluna `home`: a escala oficial
  pode listar o anfitrião como visitante num jogo no estádio dele (Copa 2026, jogos 50/51/60), e a
  vantagem segue o anfitrião. Regra centralizada em `MatrixCache._host_away` → `score_matrix(host_away=…)`.
- **Gerados (no .gitignore)**: `out/`, `data/historical_results.csv`, caches. Versionar só
  specs de edição, código, testes e a skill.
- **Tabela longa**: ao mexer no formato de saída, o palpite tem 104 linhas (72 grupo + 32 KO).
- Rode as checagens de **Qualidade** (ruff, mypy, pytest) antes de concluir mudanças.

## Limitações conhecidas

Modelo puramente estatístico (favorece quem vem bem; pode subestimar potência em má fase recente);
desempates de grupo simplificados (sem confronto direto oficial); alocação dos 8 melhores terceiros
por casamento de restrição (Annex C da FIFA aproximado). Detalhes no `README.md`.

## Skill

`.claude/skills/palpites-copa/` — orquestra `sync-results`/`record` + `predict` e apresenta os
palpites da próxima rodada. Use durante a Copa para atualizar rodada a rodada.
