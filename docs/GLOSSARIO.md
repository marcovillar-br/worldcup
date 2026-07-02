# Glossário — worldcup

Termos e conceitos que o produto manipula. Referência para o [`PRD.md`](PRD.md), o
[`SPEC.md`](SPEC.md) (matemática) e o [`AGENTS.md`](../AGENTS.md) (código). Onde útil, aponto a
seção do SPEC ou o módulo de `src/worldcup/` que materializa o conceito.

---

## Bolão e pontuação

- **Bolão** — competição de palpites: cada participante crava o placar dos jogos e pontua conforme
  acerta. O produto otimiza para *um* bolão específico (app *Bolão de Futebol 2026*).
- **Sistema I** — o sistema de pontos probabilístico do app ("o mais justo e equilibrado"): a base
  varia com a probabilidade do resultado (**zebra vale mais**) mais um bônus **hierárquico** de
  placar (só o maior nível conta). Configurado em `scoring.toml [sistema_i]`.
- **Palpite** — o placar escolhido para um jogo (ex.: `2×1`). Não é o placar mais provável, e sim o
  de maior **valor esperado** de pontos. Em mata-mata inclui prorrogação/pênaltis e quem avança.
- **Régua de pontos / base** — os pontos-base de um palpite acertado, função da probabilidade `p` do
  resultado: `base = 1 + 7,55·log10(1/p)`, truncada a **[1, 13]**. Fiel ao Simulador do app
  (SPEC §4).
- **Bônus de placar (hierárquicos)** — somados à base, mas o app concede
  **só o maior nível atingido**, não a soma: **exato** +5 > **gols do vencedor** +3 > **saldo**
  (diferença de gols) +2 > **gols do perdedor** +1. A **goleada** (margem ≥3) +1 é um extra que
  empilha. No mata-mata, **prorrogação** +3 e **pênaltis** +3 são camadas à parte (também somadas).
- **Zebra** — resultado improvável (favorito tropeça). Como a base cresce com `1/p`, cravar a zebra
  rende muito mais pontos — daí a estratégia não ser sempre o favorito.
- **Peso por fase / Equilíbrio gradual** — multiplicador da pontuação por etapa: grupos **1×**,
  R32–SF **2×**, final **4×** (`scoring.toml [phase_weights]`). Aplicado à **partida inteira**
  (base + bônus) via `Scorer.weighted_points(...) = points(...) · weight(stage)` (ENG-27): não muda
  o placar ótimo de um jogo isolado (multiplicador constante), mas o **teto/eficiência** do
  mata-mata é 2–4× o de um jogo de grupo.
- **Fases do mata-mata (R32/R16/QF/SF)** — siglas internas
  (do inglês *Round of 32/16*, *Quarter/Semi-final*) e o nome em PT-BR: **R32 = 16-avos de final**
  (16 jogos), **R16 = oitavas** (8), **QF = quartas** (4), **SF = semifinais** (2), `3rd_place` =
  disputa de 3º, `final`. ⚠️ Em PT-BR a rodada de 32 seleções é "16-avos" (1/16 da final), **não**
  "32-avos".
- **Resolução de chaveamento** — cálculo **determinístico** do bracket de mata-mata a partir dos
  resultados reais (standings dos grupos + `ko_outcome` dos KO disputados), sem o modelo
  probabilístico — preenche os slots `1A`/`2B`/`3rd`/`W##`/`L##`. `sync._resolve_real_bracket`
  (do feed) e `sync.resolve_live_bracket`
  (do próprio fixture, usado pelo `fetch_odds` para casar odds de KO; ENG-28).
- **Prorrogação (camada de mata-mata)** — após empate nos 90', a 2ª das 3 camadas independentes de
  palpite (90' / prorrogação / pênaltis). `knockout.predict_knockout` prevê
  P(vence mandante / vai aos pênaltis / vence visitante) por **Poisson independente** com taxa ≈
  taxa de 90' × 30/90 (a ET tem ~1/3 do tempo) e escolhe o desfecho mais provável
  (= E[pts]; ENG-29). Bônus +3 (×peso).
- **Shootout / disputa de pênaltis** — cobranças que definem o vencedor de um jogo de KO empatado
  após prorrogação. 3ª camada de palpite (bônus +3 ×peso). Dados em `shootouts.csv`
  (`match_id,winner`): do martj42 (ingestão) ou do arquivo da edição
  (`Edition.shootouts`, captura manual sob latência).
- **Pontos esperados (E[pts])** — média ponderada dos pontos de um palpite sobre todos os placares
  possíveis (pela matriz do modelo). O objetivo que o produto maximiza.
- **Risk (risco / ousadia)** — knob de **estratégia** (não da régua do app): `best_prediction`
  maximiza `E[pts]·(1/P)^(2·risk−1)`. `0.5` = fiel (E[pts] puro); `>0.5` arrisca mais zebra; `<0.5`
  puxa ao favorito. Default fiel **0.5** (SPEC §5).
  *Default Pydantic do campo é 0.6 — cada edição fixa no `scoring.toml`.*
- **best_prediction** — a rotina (`scoring.Scorer`) que varre os placares candidatos e devolve o de
  maior objetivo de risco; reporta o E[pts] **não-tiltado**.

## Modelo estatístico

- **Modelo Dixon–Coles** — modelo de gols baseado em **Poisson** com correção para placares baixos
  (`0×0`, `1×0`, `0×1`, `1×1`); estima força de ataque/defesa de cada seleção
  (`model.DixonColesModel`).
- **Matriz de placares `P(i,j)`** — distribuição de probabilidade sobre os placares
  (i gols do mandante × j do visitante), saída de `score_matrix`. Base de tudo: simulação, palpite e
  blend.
- **Ataque / defesa / base** — parâmetros de força por seleção (ataque), de fragilidade (defesa) e a
  constante de escala de gols (base). `λ` (gols esperados do mandante) depende de
  `ataque[h] − defesa[a] + base`.
- **λ / μ** — gols esperados do mandante (`λ`) e do visitante (`μ`); alimentam as Poisson da matriz.
- **rho (ρ)** — parâmetro da correção Dixon–Coles que reajusta a massa dos quatro placares baixos
  (corrige a sub/superestimação de empates 0×0/1×1 do Poisson independente).
- **Decaimento temporal / meia-vida** — jogos antigos pesam menos no ajuste:
  `peso = 0.5^(idade/meia-vida)`, **meia-vida 2,0 anos** (tunada por backtest — ENG-17). Jogo de 2
  anos pesa metade.
- **Peso de torneio** — importância da competição no treino: Copa 1,0; continentais 0,8–0,85;
  eliminatórias 0,8; Nations League 0,75; Gold Cup e não-listados 0,70; amistoso 0,5
  (`model._TOURNAMENT_WEIGHTS`).
- **Mando (`host_away`)** — vantagem de jogar em casa, aplicada ao **anfitrião** (`neutral=false`).
  O mando segue quem está em `tournament.toml::hosts`, mesmo que a escala oficial liste o anfitrião
  como visitante (jogos 50/51/60 da Copa 2026).
- **Ridge / regularização** — *prior* fraco que puxa ataque/defesa para a média da liga; evita
  estimativas absurdas para seleções com poucos jogos (regressão à média).
- **Identificabilidade** — ataque/defesa só importam pela diferença; pós-ajuste são centrados em
  média zero e o deslocamento é absorvido na **base** (SPEC §3.3).

## Blend com mercado (odds)

- **Blend** — combinar a matriz do modelo com as **odds de mercado** para ganhar acurácia
  (o modelo é cego a escalação/lesão/motivação, que o mercado precifica). Pipeline: devig → log
  opinion pool → rescale (`blend`; ENG-19, SPEC §3.5).
- **Odds decimais** — cotação de mercado por resultado (mandante/empate/visitante); em `odds.csv`
  como `match_id,home,draw,away`.
- **Vig / margem / devig** — a **margem** (overround) é o lucro embutido da casa, que faz as
  probabilidades implícitas somarem >100%. **Des-vigar** (`devig`) remove essa margem e devolve
  probabilidades calibradas.
- **Log opinion pool** — fusão de duas opiniões por **média geométrica ponderada**:
  `p ∝ modelo^(1−w)·mercado^w`, com `w = blend_weight`.
- **Rescale / 1×2-alvo** — reescalar a matriz de placares para bater com o 1×2-alvo do blend,
  **preservando** a forma condicional dos placares (`rescale_matrix`).
- **blend_weight (w)** — peso do mercado no blend (0 = só modelo; 1 = só mercado). A edição 2026 usa
  **0.6** (prior de princípio: odds de fechamento são bem calibradas).
- **Pinnacle** — casa de aposta de referência (odds "afiadas"), fonte preferida via
  **The Odds API**.

## Validação e calibração

- **Backtest** — rodar o produto numa Copa passada com o conhecimento da época e somar os pontos do
  Sistema I — valida o modelo sem vazar o futuro (cli `backtest`).
- **Brier (multiclasse)** — erro quadrático médio das probabilidades previstas vs. o resultado real
  (3 classes: mandante/empate/visitante). **Menor = melhor**. Métrica de acurácia do `blend-track`.
- **Calibração** — alinhamento entre probabilidade prevista e frequência observada
  (eventos a 30% acontecem ~30% das vezes). ENG-18.
- **Regime de empates** — monitor (ENG-22) de empates observados vs esperados na Copa em curso, com
  **z-score**; gatilho de ação só além de ~2σ (senão é variância).
- **blend-track** — comando que acumula o Brier blend-vs-modelo nos jogos disputados com odds e roda
  o monitor de empates; o veredito vai pro `BOLAO.md`.
- **Eficiência (da campanha)** — quanto dos pontos que o tool renderia o apostador capturou:
  `eficiência = seus_pontos / teto`, onde o **teto** é a soma dos pontos do palpite **as-of**
  (o que o tool mostrava na manhã de cada jogo) contra os resultados reais. Calculada por
  `scripts/efficiency.py` (flag `--my-points`); é **aproximada** (±~1/jogo), porque a base do
  Sistema I depende da probabilidade interna do app, que não observamos ([ENG-24]).

## Simulação e formato

- **Monte Carlo** — milhares de simulações do torneio (default **5000**) para estimar classificações
  e **P(título)** por seleção (`format_engine`).
- **Standings / desempate** — classificação de grupo por pontos → saldo → gols pró → sorteio
  (desempate **simplificado**, sem confronto direto/fair-play oficiais).
- **Chaveamento determinístico** — o bracket "esperado" montado a partir das probabilidades, exibido
  ao usuário (distinto das simulações, que exploram cenários).
- **Mata-mata (3 camadas)** — previsão de placar dos **90'**, **prorrogação** e **pênaltis**, mais
  quem avança (`knockout.predict_knockout`; SPEC §6).
- **Melhores terceiros / Annex C** — os 8 melhores 3ºs colocados que avançam na Copa 2026; alocados
  por **casamento de restrição** (aproximação do Annex C da FIFA).

## Dados e operação

- **Edição (edition-agnostic)** — uma Copa específica, descrita só por dados em
  `data/editions/<ano>/`. Copa nova = pasta nova, sem mudar código.
- **Slot de chaveamento** — referência simbólica num fixture ainda indefinido: `1A`/`2A`
  (1º/2º do grupo A), `3rd` (terceiro elegível), `W73` (vencedor do jogo 73), `L101` (perdedor).
  Resolvidos por resultados reais.
- **match_id** — numeração **interna** dos jogos (1–104), referenciada pelos slots `W##`/`L##`.
  **Não** é o número oficial da FIFA — ao cruzar, guie-se pelos **nomes** das seleções.
- **Realimentação (feedback)** — reinjetar os resultados reais no treino (peso alto) e no
  chaveamento à medida que a Copa avança; só os jogos pendentes são repalpitados (SPEC §8).
- **sync-results / record** — realimentação **automática** (baixa todos os placares e repalpita) vs.
  **manual** (registra um placar específico; `--ko-winner` p/ mata-mata empatado).
- **FINAL / PREVISTO** — estado de cada linha na saída: jogo já disputado
  (`FINAL`, mostra o placar real) vs. ainda por jogar (`PREVISTO`, mostra o palpite).
- **Nome canônico vs exibição** — internamente as seleções usam o nome **canônico em inglês**
  (do dataset); a exibição é em **português** (`teams.display`). Arquivos de dados usam o canônico.
- **Snapshot / history / `--archive`** — cópia versionada e imutável dos palpites de um dia, em
  `data/editions/<ano>/history/<data>.{csv,md}`; preserva como os palpites evoluíram.
- **`--as-of` / reconstruído** — regenerar a visão de um dia passado
  (só com resultados até a véspera), sem tocar nas saídas vivas; o arquivo leva sufixo
  `.reconstruido` e é regenerável (gitignored).
- **PredictionRun** — o objeto que `pipeline.run` devolve com tudo de um run
  (palpites, probabilidades, metadados); o `render` gera CSV/MD/HTML a partir dele (sem I/O).
- **martj42 dataset** — fonte pública (GitHub, CSV) de `results.csv`/`shootouts.csv` de jogos
  internacionais; base de treino normalizada por `fetch_data`.
- **The Odds API** — provedor das odds de mercado (chave no `.env`); consumido por
  `scripts/fetch_odds.py`.
- **BOLAO.md / memória de campanha** — diário **agnóstico a ferramenta** das decisões da campanha
  que não são rederiváveis dos dados/código (risco escolhido, situação no ranking, regras do grupo).
