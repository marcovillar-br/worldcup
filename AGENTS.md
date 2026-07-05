# AGENTS.md — guia para agentes neste repositório

Gerador de palpites de bolão da Copa do Mundo. Modelo estatístico (Poisson/Dixon–Coles) treinado em
resultados históricos de seleções; gera o palpite de cada jogo maximizando os **pontos esperados**
do bolão. Calibrado para o **Sistema I** do app *Bolão de Futebol 2026* (base 1–13 por probabilidade
+ bônus **hierárquicos** de placar — só o maior nível conta, não a soma; **zebra vale mais**).

**Metodologia (matemática, derivações, exemplos numéricos): [`docs/SPEC.md`](docs/SPEC.md).**
**Arquitetura visual (C4: Contexto→Container→Componentes→Dinâmica): [`docs/C4.md`](docs/C4.md).**
**Produto (requisitos, personas, escopo): [`docs/PRD.md`](docs/PRD.md)**
**· termos: [`docs/GLOSSARIO.md`](docs/GLOSSARIO.md).**
**Modelo (uso, métricas, calibração): [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md)**
**· dados (proveniência, licença): [`docs/DATA.md`](docs/DATA.md).**

## Tom da interação

Comunicação **sem falsa modéstia nem bajulação**. Priorize avaliação técnica honesta e específica
em vez de concordância ou elogio:

- Nada de cumprimentos vazios ("ótima pergunta", "excelente ideia") nem de validar uma ideia só por
  ser do usuário.
- Aponte riscos, trade-offs e erros **diretamente** — inclusive os seus próprios. Quando algo
  estiver errado ou for má ideia, diga com franqueza e proponha a alternativa.
- Quando discordar, discorde e justifique. O usuário prefere **correção direta a confirmação**;
  concordância automática destrói o valor da revisão.

## Princípio central: agnóstico à edição

Nada específico de um ano fica no código. Cada edição é descrita por **dados** em
`data/editions/<ano>/`. Para uma Copa futura, adicione `data/editions/<ano>/` — o código não muda.

## Comandos (sempre via uv)

Ambiente: `uv sync` (a partir do `uv.lock`). O **catálogo completo da CLI `worldcup`**
(`predict`/`sync-results`/`record`/`backtest`/`blend-track`, com `--archive` e `--as-of`)
é canônico no **[`README.md`](README.md)** — não duplicar aqui. As checagens de qualidade
ficam abaixo.

## Qualidade (rode antes de concluir mudanças)

```bash
uv run ruff check .          # lint (regras em pyproject; line-length 120)
uv run ruff format           # formatador (--check no CI; --fix para o lint)
uv run mypy                  # type checking estático (config em pyproject)
uv run pytest                # testes
uv run pre-commit install    # (1x) ativa o hook local de ruff lint+format
```

As mesmas checagens rodam no CI (`.github/workflows/ci.yml`, Python 3.11 e 3.13) em
push/PR. O pre-commit roda o ruff (rápido), o aviso `bolao-sync` e o `backlog-integrity`
(bloqueia se o `docs/BACKLOG.md` quebrar invariantes — ver `scripts/check_backlog.py`); mypy e
testes ficam no CI. Convenções de código que ferramenta não pega ficam aqui no AGENTS.md
(não há doc de regras separado).

## Arquitetura (`src/worldcup/`)

- `edition.py` — modelos **Pydantic v2** + `load_edition()`; carrega e valida a spec.
  `Edition.as_of(data)` devolve a edição como conhecida no início de uma data (base do `--as-of`).
- `teams.py` — nome canônico (inglês, do dataset) ↔ exibição em português.
- `fetch_data.py` — baixa `results.csv`/`shootouts.csv` (martj42), normaliza →
  `data/historical_results.csv`.
- `model.py` — `DixonColesModel`: ajuste ponderado (decaimento temporal + peso de torneio + mando),
  filtra seleções não-FIFA; `score_matrix(home, away, neutral, host_away=…)`
  (mando do anfitrião via `host_away`, ver *Mando* abaixo).
- `scoring.py` — `Scorer`: pontos do Sistema I + `best_prediction()` (maximiza pontos esperados);
  `risk` controla a ousadia (0.5 = fiel; >0.5 arrisca mais zebras).
- `knockout.py` — `predict_knockout()`: 3 camadas (placar 90', prorrogação, pênaltis) + quem avança.
  `pool_behind` (via `predict --pool-behind [empate|zebra]`, default do flag `empate`): modo endgame
  de bolão, só nos jogos de peso máximo (final) e só quando o usuário está atrás (bolão é jogo
  diferencial). `"empate"` (ENG-39/40, dominante): 90' no melhor empate por E[pts], camadas fiéis;
  `"zebra"` (ENG-36, superada): lado azarão nas 3 camadas. Números em `scripts/eng36_pool_sim.py`.
- `blend.py` — blend com odds de mercado (ENG-19): `devig` (tira a margem) → `log_opinion_pool`
  (média geométrica ponderada modelo×mercado, peso `blend_weight`) → `rescale_matrix`
  (ajusta matriz ao 1×2-alvo preservando forma condicional). Com **totals** (ENG-35): `devig_pair` →
  `implied_total_rate` (λ implícito da linha, Poisson) → `tilt_matrix_to_total`
  (tilting `c^(i+j)` ao λ do pool geométrico), iterado com rescale (1×2 exato). Aplicado em
  `pipeline.run` só nos jogos com odds; sem odds ou `blend_weight=0` ⇒ matriz intacta; sem totals ⇒
  blend só de 1×2.
- `format_engine.py` — simulação genérica: standings, Monte Carlo, chaveamento determinístico.
- `backtest.py` — valida o modelo nas 4 Copas passadas (`backtest`) e o blend prospectivamente na
  edição viva (`blend-track`): `multiclass_brier`, `reliability_draw`/`pooled_draw_calibration` +
  monitor de regime de empates (z-score). Treina só com jogos anteriores a cada Copa. Sweeps as-of
  de calibração: `blend-track --sweep` (blend_weight, ENG-38) e `blend-track --boost-sweep`
  (`edition_boost`, ENG-44) — Brier out-of-sample por valor, só jogos de grupo.
- `sync.py` — resolve o bracket só com resultados reais e preenche `fixtures.csv`.
- `pipeline.py` — orquestra fetch→fit→(realimenta)→simula→palpites.
- `render.py` — camada de **apresentação** (funções puras): `render_markdown`/`render_html` +
  `CSV_COLUMNS`. Geram texto a partir do `PredictionRun` (não do CSV); HTML autocontido e
  print-friendly. Sem I/O.
- `status.py` — briefing read-only de start-of-day (ENG-31): funções puras `build_status`/
  `format_status` montam uma foto compacta do estado (disputados/total, fase, jogos de hoje,
  próximos palpites, standing, pendências) a partir da edição + último `out/` + linha de standing do
  `BOLAO.md`. **Não muta nada** ("ver" separado de "fazer").
- `cli.py` — argparse; entrypoint `worldcup` (+ alias `ws` = `worldcup status`, via `main_status`).
  **Só orquestra**: parsing, escrita em disco
  (`save_outputs`/`archive_outputs`, que chamam o `render`), o subcomando `status` (read-only) e a
  saída de console. `-v/--verbose` configura o nível de log da biblioteca.

## Modelo de dados de uma edição (`data/editions/2026/`)

- `tournament.toml` — formato (grupos, avanço, melhores 3ºs, fases, desempates, anfitriões). Tabela
  opcional `[group_stage.third_allocation]` (`match_id → grupo`) crava a alocação **oficial** dos
  melhores terceiros (Annex C) para a combinação realizada — usada quando o conjunto de grupos bate
  com os terceiros classificados; senão cai no casamento por restrição. Ver SPEC §7.3.
- `groups.csv` — `group,team` (nomes canônicos em inglês).
- `fixtures.csv` — os 104 jogos. **O chaveamento mora aqui**, via slots em `home`/`away`: `1A`/`2A`
  (1º/2º do grupo A), `3rd` (+ `third_groups` permitidos), `W73` (vencedor do jogo 73),
  `L101` (perdedor). Colunas `home_goals,away_goals,ko_outcome` guardam o resultado real. `match_id`
  é a numeração **interna** (e os slots `W##`/`L##` a referenciam), **não** o número oficial da FIFA
  — não coincidem (ex.: jogo `50` aqui = *Match 51* FIFA). Ao cruzar com a escala oficial, guie-se
  pelos **nomes das seleções**, nunca pelo número.
- `scoring.toml` — sistema de pontos + pesos por fase (default: Sistema I + Equilíbrio gradual).
  Campo `risk` (ousadia da escolha; `0.5` = fiel/E[pts] puro — **a edição 2026 usa `0.5`**). ⚠️ O
  default do **campo ausente** é `0.6` (`ScoringConfig`, não `0.5`): cada edição deve
  **fixar `risk` no `scoring.toml`**; omiti-lo herda um leve viés de ousadia (0.6), não o fiel 0.5.
  Também `blend_weight` (peso do mercado no blend com odds; `0` = só modelo, ausência do campo ⇒ 0;
  **a edição 2026 usa `0.8`** — prior 0.6 do ENG-19 elevado com dado via
  `blend-track --sweep`, ENG-38). E `edition_boost` (peso de cada jogo disputado da edição no
  ajuste — ENG-42/44; `1.0` = sem boost, pesa como jogo histórico; ausência ⇒ 1.0). **A edição
  2026 usa `1.0`**: `blend-track --boost-sweep` mostrou Brier as-of **monotônico crescente** em
  boost (boostar a forma recente superajusta e piora a previsão) — o valor antigo em código era
  6.0. `pipeline.build_training_frame` lê o campo (KO disputado é resolvido de slot p/ seleção via
  `sync.resolve_live_bracket` e entra pelo mesmo caminho; o dedup por (data, par) evita
  double-count com a base — ENG-41).
- `odds.csv` — **opcional** (ENG-19): `match_id,home,draw,away` em odds decimais, mais as colunas
  **opcionais** `total_line,over,under` (mercado de over/under — ENG-35; arquivos antigos sem elas
  seguem válidos). Ausente ⇒ blend desligado. Preenchido por `scripts/fetch_odds.py` (busca The Odds
  API + **mescla**, preservando jogos já disputados — `blend-track` acumula tally; à mão,
  **acrescente**, não sobrescreva). Linhas em branco ignoradas. **`odds.csv` é gitignored** — ToS da
  The Odds API não permite redistribuir em repo público (ver `docs/DATA.md` §6); vive só local.
  Veredito de blend reproduzível localmente. Mantenha arquivo (não apague); **nunca** versione odds
  nem chave (em `.env`).
- `shootouts.csv` — **opcional** (ENG-30): `match_id,winner`
  (vencedor de disputa de pênaltis, nome canônico). Carregado em `Edition.shootouts`; usado para
  mostrar o desfecho real (prorrogação/pênaltis/quem avançou) dos jogos de KO **já disputados**
  quando a fonte oficial ainda tem latência (ENG-15). **Captura manual:** preencha
  **só com placares verificados em ≥2 fontes confiáveis**
  (regra `confirmar-placares-multiplas-fontes`). Versionado (fato público, durável); linhas sem
  vencedor são ignoradas. `Edition.as_of()` descarta os shootouts de jogos a partir da data
  (consistência).
- `regulation.csv` — **opcional** (ENG-45): `match_id,reg_home,reg_away`
  (placar do **tempo normal**, 90'). Só para KO decididos por **gol na prorrogação**, em que o
  placar gravado em `fixtures.csv` inclui a ET e difere do 90' (ex.: J82 gravado `3×2`, mas `2×2`
  nos 90'). O bolão pontua o slot de 90' contra o tempo normal, então `efficiency.py` usa este
  placar (`Edition.regulation`, via `regulation_90`) — senão o teto infla (creditaria o exato/saldo
  do placar-com-ET). Pênaltis puros **não** entram (o gravado já é o 90', empate preservado —
  `shootouts.csv` cuida do desfecho). **Captura manual** sob a mesma regra de ≥2 fontes; versionado;
  `Edition.as_of()` descarta as entradas de jogos a partir da data.
- `BOLAO.md` — **memória de campanha** do bolão (agnóstica a ferramenta): decisões vivas que não
  são rederiváveis de dados/código (`risk` escolhido, situação no ranking, regras do bolão).
  **Leia no início da sessão e atualize quando uma decisão de campanha acontecer.**
- `history/<data>.{csv,md}` — **snapshots diários** dos palpites
  (`predict --archive`, default = hoje). Só CSV (canônico/diffável) + MD; nunca HTML. Gravados por
  `cli.archive_outputs`; re-arquivar na **mesma data** (ex.: pós-`record`) faz **merge por jogo**
  (ENG-33): o palpite da manhã de jogo que já virou `FINAL` é preservado — só reconstruídos
  sobrescrevem (regeneráveis por definição). **Versionamento por reprodutibilidade**: o run **real**
  do dia é **rastreado** (depois que resultados entram e o modelo reajusta, não é mais reproduzível
  — daí versionar); o snapshot **reconstruído** (sufixo `.reconstruido` + banner no MD) é
  **gitignored**, porque é regenerável sob demanda por `predict --as-of AAAA-MM-DD` — que
  reaproveita `Edition.as_of()` (descarta resultados a partir da data), grava no `history/`
  **sem tocar em `out/`** e, com a data de hoje, reproduz o run real (consistência verificável).

## Convenções e cuidados

- **Nomes de seleção**: canônico em inglês internamente; PT só na exibição (`teams.display`).
  Arquivos de dados usam o canônico. Novos aliases vão em `teams._ALIASES`.
- **Mando**: aplicado quando `neutral == false` (anfitriões em casa). A flag vem da fonte. O mando é
  de quem está em `tournament.toml::hosts`, **não** da coluna `home`: a escala oficial pode listar
  anfitrião como visitante num jogo no estádio dele (Copa 2026, jogos 50/51/60); vantagem segue
  anfitrião. Regra centralizada em `MatrixCache._host_away` → `score_matrix(host_away=…)`.
- **Gerados (no .gitignore)**: `out/`, `data/historical_results.csv`, caches,
  **`data/editions/*/odds.csv`** (odds reais — gitignored por ToS, ver `docs/DATA.md` §6). Versionar
  só specs, código, testes e skill. **Exceção deliberada:** runs **reais** em
  `data/editions/<ano>/history/` são versionados — snapshots imutáveis; `*.reconstruido.*` ficam em
  `.gitignore` (regeneráveis via `--as-of`).
- **Higiene de artefatos**: limpeza é **sob demanda** via `scripts/clean-artifacts.sh`
  (dry-run por padrão; `--force` apaga). Poda transcripts de sessão (`~/.claude/.../*.jsonl`) com
  mais de 7 dias preservando a sessão ativa, e o scratch `tmp/`. **A memória
  (`.claude/.../memory/*.md`) nunca entra em deleção automática** — higieniza-se por revisão
  (dedup/remover obsoleto/validar contra o repo). Nunca apagar artefato por glob amplo.
- **Tabela longa**: ao mexer no formato de saída, o palpite tem 104 linhas (72 grupo + 32 KO).
- **Sincronia de artefatos** — **princípio permanente: mantenha TODOS os artefatos e a documentação
  sempre atualizados; nenhuma mudança fica órfã.** Toda mudança anda com sua documentação
  **no mesmo commit**. Antes de concluir, varra os públicos afetados — não só os óbvios: (a)
  andamento da Copa (`sync-results`/`record`) → atualize o *Estado atual* do `BOLAO.md` (um hook de
  pre-commit avisa se `fixtures.csv` mudar sem ele); (b) mudança de comportamento/estrutura da
  aplicação → atualize `AGENTS.md`, `README.md` e/ou `docs/SPEC.md` conforme o público afetado,
  **e registre em `CHANGELOG.md`** (seção `[Não lançado]`, no padrão Keep a Changelog); (c) item do
  backlog resolvido → marque ✅ em [`docs/BACKLOG.md`](docs/BACKLOG.md) no mesmo commit; (d)
  **bump de versão** → mude `pyproject.toml` **e** `src/worldcup/__init__.py`, rode `uv lock` e
  inclua o `uv.lock` no **mesmo commit** — o CI roda `uv sync --locked` e quebra se o lock não
  refletir a nova versão (já aconteceu: um commit vermelho entre o bump e o sync do lock); (e)
  **novo script/ferramenta em `scripts/`** → documente-o **onde seus pares já aparecem**
  (`README.md`, `CHANGELOG.md`, a skill relevante, e — quando integra dado/arquitetura —
  `docs/DATA.md`/`docs/C4.md`/`docs/PRD.md`), e não só num lugar. Commit de código sem o
  doc/artefato correspondente está **incompleto**.
- **Backlog de engenharia**: melhorias e dívidas vivem em [`docs/BACKLOG.md`](docs/BACKLOG.md)
  (fonte de verdade, rastreada). Consulte ao trabalhar em melhorias; cada item tem refs, critério
  de aceite e o commit que o fechou.
- Rode as checagens de **Qualidade** (ruff, mypy, pytest) antes de concluir mudanças.
- **Régua de markdown**: linhas de prosa em `.md` respeitam **≤100 caracteres UTF-8** (não bytes).
  `scripts/check_markdown_line_length.py` detecta violações — ferramenta **on-demand** (não é
  hook de pre-commit; reflow automático de prosa é frágil, ver ENG-37). Isenções automáticas:
  tabelas (`|`), URLs, comandos (`uv run`), diagramas C4, blocos de código. Quebras de linha
  quando necessário: manuais/revisadas, nunca `textwrap.fill` cru — ele quebra em qualquer
  espaço sem noção de rótulo+número/parênteses/chamadas de função, produzindo fragmentos órfãos.

## Limitações conhecidas

Modelo puramente estatístico (favorece quem vem bem; pode subestimar potência em má fase recente);
desempates de grupo simplificados (sem confronto direto oficial); alocação dos 8 melhores terceiros
por casamento de restrição (Annex C da FIFA aproximado). **Fonte canônica:**
[`docs/SPEC.md`](docs/SPEC.md) §9.2 (o `README.md` traz a versão para o usuário).

## Skills

- `.claude/skills/palpites-copa/` — orquestra `sync-results`/`record` + `predict` e apresenta os
  palpites da próxima rodada. Use durante a Copa para atualizar rodada a rodada.
- `.claude/skills/backlog/` — dinâmica de registro/revisão/resolução de itens em `docs/BACKLOG.md`
  (verbos e invariantes; o formato é o do próprio backlog). Use ao anotar ou fechar melhorias.
