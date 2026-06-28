# Changelog

Todas as mudanças relevantes deste projeto. Formato baseado em
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento
[SemVer](https://semver.org/lang/pt-BR/).

**Convenção de tag:** cada marco recebe uma tag `vX.Y.Z` apontando para o commit do release;
a seção correspondente aqui sai de `[Não lançado]` para `[X.Y.Z] - AAAA-MM-DD`. A versão é
mantida em `pyproject.toml` e `src/worldcup/__init__.py` (bump manual nos dois).

## [Não lançado]

Leva de acurácia (blend com odds), endurecimento do motor e da rede de testes (ENG-12..ENG-23).

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
- **Bônus de mata-mata no backtest** (ENG-12): `fetch_data` mescla `shootouts.csv` → coluna
  `penalty_winner` na base histórica, e `backtest` concede os bônus de prorrogação/pênaltis nos jogos
  decididos nos pênaltis (`Scorer.knockout_bonus`, antes config morta). Jogos decididos dentro da
  prorrogação seguem não-identificáveis na fonte (martj42 não traz a fase) — limitação documentada.
- **Apresentação do projeto** (`scripts/build_presentation.py`): gera um deck HTML autocontido (tema
  dark "Placar Noturno", palco 16:9 com auto-resize, navegação por botões/teclado/dots, deep-link
  `#slide-k`, contadores animados e modo impressão/PDF) explicando o projeto para leigos. Saída
  versionada em `docs/apresentacao.html` (regenerável pelo script). Self-contained (CSS+JS inline,
  SVG-first, fotos CC embutidas em base64, sem CDN).
- **Eficiência da campanha** (`scripts/efficiency.py`): mede `seus_pontos / teto-do-tool`
  reconstruindo o palpite **as-of** de cada manhã (mesmo caminho do `predict --as-of`) e pontuando
  pelo Sistema I; `--compare-archive` separa o teto verificável (snapshots reais) do reconstruído e
  expõe o ruído de reconstrução. Passo 6 da skill `palpites-copa`.
- **Teto teórico (oráculo)** no `efficiency.py`: além do teto do tool, reporta a pontuação de cravar
  o placar exato de todo jogo e duas capturas complementares (`tool/oráculo` = qualidade do
  modelo+blend; `seus_pontos/oráculo` = distância da perfeição). Diagnóstico de teto, não de execução
  (o oráculo é dominado por ruído irredutível — o tool perfeito captura ~34% dele).

- **Slide de balanço da fase de grupos** na apresentação (`build_presentation`): resumo dos 72 jogos
  (28% de empates, zebra Cabo Verde no grupo da Espanha) + expectativa do mata-mata (corrida ao
  título, final prevista Espanha×Argentina, jogos 50/50 a observar). Números da campanha/Brier/
  favoritos atualizados para o fim dos grupos (28/06): 2º lugar, 235 pts (72/104), eficiência 103%,
  blend-track n=49 (modelo 0,442 / blend 0,418).

### Corrigido
- **Rótulo da fase R32 estava errado: "32-avos" → "16-avos de final"** (`render._STAGE_LABEL`). A
  rodada de 32 seleções tem **16 jogos** (1/16 da final), logo é "16-avos" — coerente com "oitavas"
  (8 jogos) e "quartas" (4). Snapshots já versionados em `history/` ficam como estão (registros
  imutáveis do que o tool emitiu no dia).
- **Alocação dos melhores terceiros podia divergir da tabela oficial da FIFA** (`_assign_thirds`): o
  casamento por restrição (backtracking) devolvia o **primeiro** emparelhamento válido, que não é
  único — em 2026 saiu diferente do Annex C oficial (J74/J77/J81 com Bósnia/Paraguai/Suécia rodados).
  Adicionado override por edição em `tournament.toml::[group_stage.third_allocation]` (`match_id →
  grupo`), aplicado quando o conjunto de grupos bate com os terceiros classificados — usado no bracket
  real (`sync`) e no determinístico/Monte Carlo (`format_engine`). 2026 cravado na row 67 (grupos
  B/D/E/F/I/J/K/L), verificado vs bracket oficial (Yahoo/Sky) + Wikipedia. Tabela completa de 495
  combinações segue pendente (SPEC §9.3).
- **Suíte de testes resiliente ao avanço da Copa**: `test_sync_results_fills_unplayed_group_games`
  esvazia 2 jogos no clone em vez de depender de partidas de grupo em aberto nos dados reais (quebrava
  quando a fase de grupos terminava).
- **Bônus de placar do Sistema I eram somados, não hierárquicos** (`scoring.points`): o app concede só
  o MAIOR nível atingido (exato +5 > gols do vencedor +3 > saldo +2 > gols do perdedor +1), não a soma.
  O bug inflava todo placar cravado (ex.: favorito 2×0 dava base+11 ≈ 13 em vez de base+5 = 7) e
  **enviesava o `best_prediction` contra empates** (jogo decidido somava mais bônus que empate). Achado
  por confronto com as telas "Pontos por Jogo" do app; validado em 12 jogos (8 exatos, 4 off ≤1 só na
  base). Corrige eficiência (estava inflada) e faz o modelo voltar a palpitar empates. (ENG-23)
- Fit do Dixon-Coles **converge** via gradiente analítico (antes esgotava o orçamento de avaliações
  do scipy e parava longe do ótimo, sem sinal além do aviso). (ENG-16)

### Mudado
- **Doc de estratégia/backtest realinhada à régua hierárquica** (auditoria pós-ENG-23): a tabela do
  backtest 2022 (SPEC §9.1, MODEL_CARD) foi atualizada (agora 187/159/181 por risco 0.0/0.5/1.0) e a
  tese "agressivo faz ~28% mais pontos" foi **removida** — era artefato do bug de pontuação somada;
  com a régua corrigida, subir o risco não melhora os pontos de forma confiável. README não recomenda
  mais `--risk 0.7/1.0` para subir no ranking.
- **Esquema do `historical_results.csv` documentado** no `docs/DATA.md` (8 colunas, incl. a nova
  `penalty_winner` mesclada do `shootouts.csv`); `efficiency.py` citado no PRD (M3) e no GLOSSARIO.
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
