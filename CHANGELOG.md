# Changelog

Todas as mudanças relevantes deste projeto. Formato baseado em
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento
[SemVer](https://semver.org/lang/pt-BR/).

**Convenção de tag:** cada marco recebe uma tag `vX.Y.Z` apontando para o commit do release;
a seção correspondente aqui sai de `[Não lançado]` para `[X.Y.Z] - AAAA-MM-DD`. A versão é
mantida em `pyproject.toml` e `src/worldcup/__init__.py` (bump manual nos dois).

## [Não lançado]

Leva de acurácia (blend com odds), endurecimento do motor e da rede de testes (ENG-13..ENG-22).

### Adicionado
- **Blend com odds de mercado** (`blend.py`): des-vig → pool logarítmico → reescala da matriz, com
  `odds.csv` por jogo, `scoring.toml::blend_weight` (2026 = 0.6), CLI `predict --blend-weight` e
  `scripts/fetch_odds.py` (The Odds API, chave no `.env`). (ENG-19)
- **`blend-track`**: valida o blend prospectivamente (Brier multiclasse blend-vs-modelo as-of) e
  exibe o **monitor de regime de empates** (z-score; gatilho 2σ para reconsiderar tilt). (ENG-19, ENG-22)
- **Calibração probabilística** no backtest: Brier multiclasse + curva de confiabilidade do empate,
  agregados nas 4 Copas — veredito de que o modelo é bem calibrado em empate. (ENG-18)
- Testes **e2e do pipeline** e de integração do `sync` rodando no CI (fixture histórico sintético,
  sem depender do `historical_results.csv`); piso de cobertura `fail_under` 65→80. (ENG-20)

### Corrigido
- Fit do Dixon-Coles **converge** via gradiente analítico (antes esgotava o orçamento de avaliações
  do scipy e parava longe do ótimo, sem sinal além do aviso). (ENG-16)

### Mudado
- Defaults do `FitConfig` recalibrados por **LOO-CV** (meia-vida 2,5→2,0, ridge 0,05→0,10; +9,2% de
  pontos no backtest das 4 Copas). (ENG-17)
- Curva de pontos base reproduz o app (log-linear `1 + 7,55·log10(1/p)`); `risk` **desacoplado** da
  régua, virou um tilt só na escolha do palpite. (ENG-14)
- `fetch-data`/`sync-results` aceitam **fontes em cascata** (`--source-url`) com fallback. (ENG-15)
- `monte_carlo()` default `n_sims` 8000→5000 (alinhado ao caminho real e ao SPEC). (ENG-13)
- Camada meta podada e **canônicos de blend/odds declarados** por audiência (README/AGENTS/SPEC/
  BOLAO); memória de campanha higienizada. (ENG-21)

## [0.2.0] - 2026-06-13

Leva de endurecimento de engenharia (backlog `docs/BACKLOG.md`, ENG-1..ENG-9 e ENG-11).

### Adicionado
- Flag global `-v`/`--verbose` e `logging` na biblioteca: avisos antes silenciosos agora são
  visíveis e capturáveis em teste (seleções descartadas pelo `min_matches`, fit não-convergido). (ENG-4)
- Validação de schema do CSV da fonte pública: falha cedo e clara (`DataSourceError`) se o
  formato mudar, em vez de um `KeyError` críptico adiante. (ENG-5)
- Medição de cobertura no CI (`pytest-cov`) com piso `fail_under = 65` (cobertura ~74%). (ENG-8)
- Guardrail de tradução: toda seleção de cada edição precisa ter exibição em PT, senão o teste
  falha (evita cair no inglês silenciosamente). (ENG-9)
- `mypy` passa a cobrir `tests/`. (ENG-7)

### Corrigido
- `sync`: o reencontro do mesmo par de seleções na mesma Copa (grupo + mata-mata) não colapsa mais
  num único placar — desambiguação por data; corrige risco de preencher um jogo com o placar do
  outro. (ENG-1)
- `backtest`: aplica o mando do anfitrião pela mesma `MatrixCache` da produção (antes ignorava,
  pontuando jogos do país-sede de forma diferente do caminho real). (ENG-2)
- `model`: avisa quando o otimizador não converge (antes usava o resultado silenciosamente). (ENG-3)

### Mudado
- Camada de apresentação extraída para `render.py`; `cli.py` passou a só orquestrar (520 → 285
  linhas). Sem mudança de comportamento. (ENG-6)
- Documentação: `docs/SPEC.md` §9.2 declarado canônico para "Limitações conhecidas" (antes
  duplicada nos três docs sem dono). (ENG-11)

## [0.1.0]

- Versão inicial: modelo Dixon–Coles, pontuação Sistema I, simulação Monte Carlo + chaveamento,
  realimentação por resultados reais (`sync-results`/`record`), saídas CSV/MD/HTML, orientação a
  dados por edição (`data/editions/<ano>/`) e backtest.
