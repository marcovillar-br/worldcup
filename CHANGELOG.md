# Changelog

Todas as mudanças relevantes deste projeto. Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
versionamento: [SemVer](https://semver.org/lang/pt-BR/).

**Convenção de tag:** cada marco recebe uma tag `vX.Y.Z` apontando para o commit do release;
a seção correspondente aqui sai de `[Não lançado]` para `[X.Y.Z] - AAAA-MM-DD`. A versão é
mantida em `pyproject.toml` e `src/worldcup/__init__.py` (bump manual nos dois).

## [Não lançado]

Leva de acurácia (blend com odds), endurecimento do motor e da rede de testes (ENG-12..ENG-23).

### Corrigido
- **A tabela mostrava o placar de 120' na coluna "Palpite (90')" e apagava a prorrogação**
  (ENG-58, `pipeline._final_ko_layers`): nos jogos de mata-mata já disputados, o display lia
  `home_goals`/`away_goals` **crus** do `fixtures.csv` — o placar **consolidado**, que inclui os
  gols da prorrogação — em vez de passar por `Edition.score_90` (a fonte única do ENG-55, que o
  `AGENTS.md` já mandava usar). Efeito: J82 aparecia `3×2` (foi `2×2` nos 90'), J99 `1×2` (`1×1`) e
  J100 `3×1` (`1×1`); e, como o consolidado está desempatado, as colunas **Prorrogação** e
  **Pênaltis** saíam `—`/`—`, como se o jogo tivesse acabado no tempo normal. O `regulation.csv`
  existia e estava correto — só a apresentação não o consultava. Agora as camadas nomeiam o
  vencedor da prorrogação (com o placar de 120'), a coluna de placar traz o slot de 90' (que é o
  que o bolão pontua), e um 120' empatado resolve os pênaltis pelo `shootouts.csv` **ou** pelo
  `ko_outcome` — o que também preenche o J96 (`0×0`, Suíça nos pênaltis), antes em branco. O teste
  antigo fabricava o `Fixture` à mão e ficou verde o mata-mata inteiro (ENG-48): o novo carrega a
  edição real e atravessa a costura `regulation.csv` → `Edition.score_90` → camadas.
- **O `status` exibia um standing de 9 dias atrás, em silêncio** (`cli._read_standing`): a extração
  procurava a palavra `Standing` em qualquer linha do bloco `## Estado atual` do `BOLAO.md` — mas
  esse bloco guarda também as entradas de **histórico**, com standings antigos. A manchete do dia
  usava o rótulo `Placar`, então a palavra `Standing` só aparecia lá embaixo, no histórico: o parser
  casava com ela e devolvia 325 pts/17º (03/07) como se fosse a posição atual (425 pts/19º). Fix: a
  busca passa a ancorar no **negrito** (a manchete é sempre `**Rótulo (data): …**`, o que delimita o
  fato sem arrastar prosa) e aceita `Standing` **ou** `Placar`. Um briefing que mente sobre a
  posição é pior que não ter briefing.
- **A sonda de contradição de fonte acusava erro em latência banal** (ENG-49, `efficiency.py`):
  `cross_source_ko_check` classificava como **contradição** ("NÃO é latência: bug de lookup,
  curadoria errada, ou fonte corrigida") todo KO em que a edição afirmava o desfecho e a fonte não
  confirmava — **sem checar se o jogo sequer estava na fonte**. Mas o martj42 publica com ~1 dia de
  atraso e a curadoria manual corre **na frente** dele por design: um KO de ontem, já curado no
  `regulation.csv`, cai exatamente nesse caso. Aconteceu com J99/J100 em 12/07, mandando investigar
  uma curadoria correta. Fix: `asof_scores` grava `in_source` (a presença da chave em
  `_penalty_lookup` é o que diz se o jogo chegou à fonte) e a sonda o consulta — fonte **sem** o
  jogo ⇒ latência; fonte **com** o jogo e discordando ⇒ contradição. A leitura é **estrita**
  (`s["in_source"]`) de propósito: com `.get()`, um produtor que parasse de emitir a chave faria
  tudo virar "latência" e a sonda apagaria em silêncio — a falha do ENG-48. Uma sonda que grita erro
  no caso banal é uma sonda que será ignorada quando gritar de verdade, que é justamente o fracasso
  que o ENG-49 existe para evitar.
- **A base histórica gravava o placar COM prorrogação — o modelo treinava em placar de 120'**
  (ENG-54): o `results.csv` (martj42) registra o placar consolidado (a final de 2022 aparece `3×3`;
  foi `2×2` nos 90'), então o `DixonColesModel` aprendia taxas de gol de 120' como se fossem de 90'
  — e a camada de prorrogação reescala λ por 30/90 **assumindo** que λ é de 90'. Pior, um empate de
  90' decidido por gol na ET entrava como **vitória**. O item se dava como insolúvel ("a base não
  tem coluna de rodada nem de tempo do gol"); a premissa **nunca fora verificada** e é falsa: o
  martj42 publica `goalscorers.csv`, com a coluna **`minute`**. E a fonte **achata o acréscimo dos
  90' no minuto 90** (o minuto 90 concentra ~2.000 gols contra ~700 nos vizinhos; 91–96 caem para
  4–17), o que torna `minute > 90` inequivocamente prorrogação. Fix: `fetch_data.regulation_scores`
  reconstrói o tempo normal (consolidado **menos** os gols de `minute > 90`) e persiste
  `reg_home_score`/`reg_away_score`, atrás de um **portão de confiança** — só reconstrói quando a
  lista de gols bate **exatamente** com o placar consolidado (lista incompleta inventaria empates);
  reconcilia **100%** dos 7.413 jogos com gols listados. `fetch_data.score_90` vira a **fonte
  única** dos 90' na base (gêmea de `Edition.score_90`), e o `backtest` passa a treinar **e
  pontuar** nos 90', creditando o bônus de prorrogação também nos jogos decididos por **gol na
  ET** (61 na base), antes invisíveis. Validação: final 2022 → `2×2`; Croácia×Brasil → `0×0`;
  Alemanha×Argentina (2014) → `0×0`; Holanda×Espanha (2010) → `0×0`.
  ⚠️ **Mas a contaminação era pequena, e o item errou ao atribuir a ela o excesso de empates**: são
  **76 jogos em 19.771** (0,6% do peso do ajuste; 0,5% contando só os 61 que viram empate→vitória),
  e corrigi-los move a taxa de empate da base de **23,2% para 23,5%** — não para os ~28% que se
  supunha. O gap contra os empates observados segue **aberto e sem mecanismo conhecido** (ENG-56).
  Efeito nos palpites de 2026: J101 França×Espanha passou de `2×1` a `1×1` (E[pts] quase empatado
  entre os dois); os demais, inalterados.
  **Consequência boa:** o backtest de política de KO volta a ser evidência válida — e, re-medido com
  a régua certa, o ban de empate do ENG-32 vale **+0,23 pt/jogo (t=+0,54; IC95% [-0,62, +1,09])**
  nos 64 KO das 4 Copas (o placar diverge em 18 jogos, os pontos mudam em 15): o backtest **não
  distingue** as políticas. Os "+70 pts" que o "provaram" eram artefato da régua antiga.
- **O ajuste do modelo treinava com o placar consolidado (com prorrogação)** (ENG-55):
  `pipeline.build_training_frame` mandava `fixtures.csv::home_goals/away_goals` para o
  `DixonColesModel` — nos KO decididos por gol na ET esse placar inclui a prorrogação, mesmo com o
  90' disponível em `regulation.csv` desde o ENG-45. Em 2026, três empates de 90' (J82 `2×2`, J99
  `1×1`, J100 `1×1`) eram ensinados ao modelo como **vitórias**, no torneio de maior peso do ajuste.
  Isso infla o λ e **apaga empates** — e envenena a camada de prorrogação, que reescala λ por 30/90
  assumindo que λ é a taxa de 90'. Causa raiz no estilo ENG-48: a semântica "placar dos 90'" morava
  num *script* (`efficiency.py`), fora da biblioteca, então o treinador não tinha como consumi-la.
  Fix: `Edition.score_90()` vira a **fonte única**; treinador e pontuador passam os dois por ela
  (o `efficiency.py` agora **delega**). Efeito em 2026: pequeno (3 jogos a peso 1,0) — Espanha
  27,6→28,4%, Inglaterra 21,7→20,7%, palpites inalterados. É correção de princípio; o dano grande
  está na base histórica (ENG-54).
- **Empate volta a ser palpitável no 90' do mata-mata** (ENG-53, revoga o ENG-32): a camada 1 do KO
  usava `forbid_draw=True` e o tool ficava **proibido** de palpitar empate num jogo eliminatório —
  daí a saída ser sempre `2x1`/`1x2`. As duas premissas do ban caíram: (i) o ganho de E[pts] do
  empate **não** é marginal onde importa — com favorito claro o ban é inócuo (o maximizador livre já
  escolhe o decisivo), mas num KO equilibrado (34%/31%/34%) o empate **é** o E[pts]-máximo, e na
  final de 2026 (peso ×4) valia **+1,42 pt**; (ii) o modelo **não** super-estima empate no KO — sem
  o ban ele palpita empate em 13% dos KO de 2026, contra 25% de empates reais nos 90'. A camada 1
  volta ao `best_prediction` fiel; nenhum limiar novo (o maximizador livre **já** escolhe o empate
  sse ele for o E[pts]-máximo). `Scorer.best_prediction(forbid_draw=…)` permanece, sem uso em
  produção. O modo `pool_behind="empate"` (ENG-39) segue forçando a diagonal na final, por motivo
  diferente (escolha diferencial). Efeito colateral resolvido: nos jogos-moeda o placar forçado
  divergia de `avança` (J102 saía `1x2` mas "avança Inglaterra"); agora sai `1x1`, coerente.

- **Chaveamento e palpite escolhiam vencedores diferentes no mesmo KO** (ENG-51): o blend com odds
  (ENG-19) só entrava na geração do palpite exibido; o `deterministic_bracket` (quem joga o próximo
  jogo) e o `monte_carlo` (probabilidades de campeão) seguiam no modelo puro. Quando o mercado
  **invertia o favorito** do modelo num confronto conhecido, as duas rotas divergiam e a tabela se
  autocontradizia — visto na SF J101 França × Espanha ("avança França" mas "final Espanha ×
  Argentina"). Latente desde o ENG-19; a Copa só produziu o gatilho na semifinal. Fix: o bracket
  decide quem avança com a **mesma** matriz blendada do palpite (`deterministic_bracket(...,
  matrix_fn=…)`); as probabilidades de campeão blendam os confrontos de KO **determinados** que têm
  odds (`monte_carlo(..., ko_blend=…)` via `resolve_live_bracket`) — Espanha caiu de 38,1% para
  29,9% e França subiu para 28,6%. Confrontos futuros (times variáveis por simulação) seguem no
  modelo. Resíduo INV-7 (favorito marginal ≠ campeão do bracket modal) é correto e agora é anotado
  na saída do `predict`.

### Adicionado
- **`scripts/eng54_ko_policy_sim.py`** — refaz, de forma reproduzível, o re-teste da política de 90'
  no mata-mata (ban de empate do ENG-32 × E[pts]-fiel do ENG-53) contra a régua certa, o placar dos
  90'. O veredito do ENG-54 é citado como evidência em quatro documentos; número que sustenta
  decisão precisa ser reproduzível (mesmo espírito do `eng36_pool_sim.py`), e este não era.
- **Explicação do palpite de campeão no HTML/MD dos palpites** (ENG-52, INV-7): quando o favorito
  por probabilidade de título (o campeão sugerido) **difere** do campeão do bracket determinístico,
  `render_html`/`render_markdown` incluem uma nota explicando que são leituras diferentes (chance de
  título vs. resultado mais provável de cada jogo), pontuadas em slots separados pelo bolão — e que,
  para o slot de campeão, vale o favorito. Antes essa explicação só saía no console do `predict`.
- **Guardião de coerência interna do palpite** (ENG-52): `src/worldcup/consistency.py`
  (`check_prediction_consistency`) confronta partes da mesma tabela entre si — encadeamento do
  bracket (`Wxx`/`Lxx` = quem avançou/perdeu), `avança` ∈ participantes, sem time repetido na rodada
  de KO, 1×2 ~100%. Roda como **asserção dura** no `pipeline.run` (recusa emitir tabela
  auto-contraditória) e como ferramenta **on-demand** `scripts/check_output_consistency.py` sobre um
  CSV já gravado. Fecha a lacuna que deixou o ENG-51 passar: nenhum teste perguntava "a tabela que
  entrego se contradiz?".

### Adicionado
- **Dados vivos da apresentação extraídos do código**: `scripts/build_presentation.py` lia números
  da campanha (jogos disputados, pontos, favoritos ao título, bracket em andamento, Brier) como
  constantes hardcoded, exigindo editar o script a cada rodada — violava "nada específico de um
  ano fica no código". Agora esses números vivem em `data/editions/2026/presentation.toml`
  (`--edition` seleciona a edição, default 2026); o script ficou agnóstico.
- **`scripts/update_presentation_data.py`**: atualiza os campos deriváveis desse
  `presentation.toml` (jogos disputados e favoritos ao título via `out/palpites-2026.{csv,md}`,
  Brier modelo-vs-blend via `worldcup.backtest.prospective_blend_report`, contagem de melhorias
  via `docs/BACKLOG.md`) sem exigir edição manual a cada rodada. Preserva os campos que dependem
  de dado externo (`campanha.pontos`/`eficiencia_pct`, só existem no placar real do bolão) ou de
  curadoria editorial (`campanha.fase`, `bracket_destaque.*`). Cablado na skill `palpites-copa`
  (passo 5.5): rodar logo após repalpitar fecha o loop de "atualizar a apresentação sozinho" sem
  pedido separado do usuário.
- **Vigia de staleness do ajuste** (ENG-43): `pipeline.ingestion_gaps(edition)` lista jogos
  **disputados** que não entraram no ajuste do modelo — quando um KO disputado não resolve os slots
  (`resolve_live_bracket`), ele era filtrado pelo `.isin(edition.teams)` de `build_training_frame`
  **em silêncio** (a falha que segurou ENG-41/42 por semanas: o caminho de grupo mascarava o de KO
  quebrado). Agora `worldcup predict` e `worldcup status` **avisam** identificando os jogos fora do
  ajuste; base em dia ⇒ silêncio. Cobertura: `ingestion_gaps` (saudável + KO não resolvido) e o
  alerta no `format_status`.
- **Gatilho de anomalia do teto + procedência do congelamento** (ENG-50, fecha): quando os pontos do
  usuário ou do líder passam do teto, o `efficiency.py` imprime `🚨 ANOMALIA` e as **sondas
  mecânicas** (`mechanical_suspects`) **antes** de qualquer leitura estatística — a variância só é
  oferecida como explicação depois que todas voltam limpas. Some da saída a frase pré-escrita
  "líder pegou variância de exatos" (era exatamente a racionalização que segurou o ENG-48 por duas
  medições). O `ceiling.csv` ganha a coluna `code` (`code_fingerprint`): a impressão digital do
  código que decidiu cada teto congelado (`efficiency.py` + `scoring.py` + `knockout.py`), com
  `provenance_split` separando "congelado sob código diferente" (recongele) de "sem procedência"
  (pré-ENG-50). O congelamento do ENG-34 protege contra **drift**, não contra **bug**. CSVs antigos
  sem a coluna seguem carregando.
- **Duas sondas mecânicas no `efficiency.py`** (ENG-49; 1ª parte do ENG-50), para que uma anomalia
  seja **checada antes de explicada**: (1) `cross_source_ko_check` cruza as duas fontes
  independentes do desfecho de KO — `shootouts.csv`/`regulation.csv` (curadoria) vs `penalty_winner`
  (martj42) — e separa **latência** (ninguém afirma) de **contradição** (a edição afirma e a fonte
  não confirma ⇒ erro, avisa alto); (2) `dead_path_canary` acusa **caminho morto**: KOs empatados
  nos 90' com o bônus de ET/pênaltis creditado em **zero** deles. Ambas disparam sobre o bug do
  ENG-48 reintroduzido e silenciam sem ele.

### Segurança
- **Allowlist de esquema de URL no downloader** (auditoria de segurança, 2026-07-05):
  `fetch_data._download_text` só aceita `http`/`https`. A URL vem da flag `--source-url`, e o
  `urllib` também abre `file://`/`ftp://` — apontar o downloader para `file:///…` leria arquivo
  local. Não era explorável (a URL é sempre digitada pelo próprio usuário, nunca vem de terceiro),
  mas o esquema é barrado antes de qualquer I/O como defesa em profundidade. Restante da auditoria:
  **nenhuma vulnerabilidade explorável** — HTML gerado escapa todo valor dinâmico (`render._esc`),
  segredos (`.env`/`odds.csv`/key) fora do git e nunca em argv/log, `--edition` é `int` (sem
  traversal), sem `eval`/`exec`/`pickle`/`shell=True`.

### Removido
- **Código morto** (auditoria de limpeza, 2026-07-05): `DixonColesModel.outcome_probs`
  (duplicava a lógica de `scoring.outcome_probs_from_matrix` — todos os chamadores usam a versão
  do `scoring`; implementação paralela era risco de divergência) e `Edition.team_group` (zero usos
  em código, testes e docs). Mantidos de propósito: `backtest.pooled_draw_calibration` (sem
  chamador em código, mas é a ferramenta citada como evidência do ENG-18 em `docs/SPEC.md`,
  `docs/MODEL_CARD.md` e `AGENTS.md` — removê-la tornaria o veredito irreprodutível) e os scripts
  de análise documentados (`eng36_pool_sim.py`, `build_presentation.py`).

### Alterado
- **`advance_per_group` agora é lido pelo motor de simulação**: o campo do `tournament.toml` era
  validado mas nunca usado — `format_engine.simulate` fixava top-2 (`st[:2]`) no contador de
  `advance_prob`. Passa a usar `spec.advance_per_group` (comportamento idêntico na 2026, que usa
  2); os slots `1A`/`2A` do chaveamento seguem vindo do `fixtures.csv`, como antes.
- **`edition_boost` calibrado com dado e virou config por edição** (ENG-44): o peso dos jogos
  disputados da edição no ajuste era a constante de código `CURRENT_EDITION_BOOST = 6.0`, nunca
  validada. Novo `blend-track --boost-sweep` mede o Brier as-of do modelo por valor de boost; na
  2026 deu **monotônico crescente** (1.0=0,4707 → 6.0=0,4876 → 12.0=0,5035) — boostar a forma
  recente **superajusta e piora** a previsão. O boost virou campo `edition_boost` no `scoring.toml`
  (default 1.0, como `risk`/`blend_weight`) e a 2026 foi fixada em **1.0** (sem boost). Efeito no
  campeão: campo mais equilibrado (Argentina 22,7%, Espanha 19,7%) em vez do 6.0 volátil
  (Argentina 12,9% / Espanha 29,1%). Cobertura: `test_blend_track_boost_sweep`.

### Corrigido
- **`efficiency.py` nunca creditava o bônus de prorrogação/pênaltis** (ENG-48): `_penalty_lookup`
  indexava a fonte martj42 por `str(<datetime64>)` (`'2026-06-29 00:00:00'`), enquanto
  `_actual_ko_outcome` procurava por `Fixture.date`, que é `str` (`'2026-06-29'`). As chaves nunca
  batiam ⇒ **todo** KO empatado nos 90' caía no ramo de latência e perdia o bônus (+3/+3 ×peso de
  fase). O **teto** saía subestimado e a **eficiência** inflada (em 10/07, 97 jogos: teto 399→423,
  eficiência 102,5%→96,7%; os dois "acima do teto" eram artefato). Os testes fabricavam o `pens` à
  mão no formato do consumidor e nunca exercitavam o produtor — a costura entre eles não tinha
  cobertura. Fix: `_date_key()` normaliza os dois lados; teste de regressão passa pelo
  `_penalty_lookup` real com frame `datetime64`. **Palpites não afetados** (script isolado; nada em
  `src/` o importa). Teto recongelado com `--reset-ceiling`.
- **Auditoria documental completa** (2026-07-05): varredura doc↔código de todos os documentos
  (README, AGENTS, SPEC, C4, MODEL_CARD, DATA, GLOSSARIO, PRD, skills) contra a implementação —
  ~25 divergências, todas de doc defasado (nenhum código errado), concentradas em 4 causas-raiz:
  ENG-44 (`edition_boost`: SPEC/skill/GLOSSARIO/PRD ainda citavam `CURRENT_EDITION_BOOST = 6.0`/
  "peso alto"; hoje 1.0, sem boost), ENG-38 (`blend_weight` 2026: MODEL_CARD/GLOSSARIO/SPEC ainda
  em 0,6; vivo é 0,8), ENG-32 (SPEC §6 dizia que o 90' de KO "pode ser empate"; é `forbid_draw`),
  ENG-34/45 (definição de teto pré-congelamento em README/GLOSSARIO/PRD/skill, sem `ceiling.csv`/
  `regulation.csv`). Também: C4 ganhou o componente `status` (ENG-31) e as arestas reais
  `pipeline→sync`/`backtest→knockout` (+ lista de omitidas corrigida), a Dinâmica do C4 agora
  mostra a realimentação e a ordem real simula→blend (blend só no palpite, por jogo), o README
  documenta os flags que faltavam do catálogo canônico (`--ko-winner`, `--no-predict`, `--seed`,
  `--source-url`, `--cutoff`, `--blend-weight`, `--reset-ceiling`), o PRD ganhou RF-19 (`status`/
  `ws`) e a menção a `--pool-behind`/totals, e a skill/`efficiency.py` corrigem "jogos empatados
  sem shootout são pulados" (o 90' pontua; só o bônus de ET/pênaltis fica de fora — e vem do
  martj42, não do `shootouts.csv` da edição).
- **Teto de KO congelava da reconstrução, não do snapshot real** (ENG-46, extensão do ENG-34): a
  hierarquia do teto congelado prefere o snapshot de `history/`, mas `archive_scores` pulava o
  mata-mata — então KO (peso ×2/×4, onde a fidelidade mais importa) congelava sempre da
  reconstrução. Dois blockers: o snapshot guardava `P_mandante=P(avança)` (sem o 1×2 do **90'** que
  a base exige) e o palpite de ET/pênaltis como string. Agora o `pipeline` grava o **1×2 do 90'** em
  `P_mandante/P_empate/P_visitante` do KO (uniformiza a semântica; colunas CSV-only, sem regressão
  de display) e `archive_scores(edition, asof)` pontua o KO de snapshot **novo formato** (placar 90'
  vs `regulation_90` + bônus de ET/pênaltis, reusando o desfecho real do `asof`). `_parse_ko_layers`
  inverte `_ko_layer_text`. **Limitação:** só ajuda KO arquivado **a partir de agora** (snapshots
  antigos não têm o 1×2 do 90'); na 2026 beneficia QF em diante. Cobertura: `_parse_ko_layers` +
  `_archive_ko_points` em `test_efficiency`.
- **Teto do `efficiency.py` instável entre rodagens** (ENG-34): o headline (teto/eficiência) vinha
  da reconstrução as-of, que re-roda o modelo com base/odds/código **atuais** — então o teto de um
  jogo **já medido** mudava a cada rodagem e a "eficiência" oscilava sem o usuário mexer em nada
  (2026-07-01: o mesmo dia deu 103,4% de manhã e 88,0% à noite, só pelo refit). Novo `ceiling.csv`
  (`match_id,pts,palpite,real,source`, rastreado) **congela** o teto por jogo na 1ª medição,
  preferindo o snapshot real de `history/` (`source=archive`) e caindo na reconstrução
  (`source=asof`) só onde não há snapshot; rodagens seguintes reusam o congelado e **reportam
  drift** (dos congelados `asof`) em vez de sobrescrever. `--reset-ceiling` recongela do zero.
  Efeito imediato: com 60 dos 90 jogos vindo do snapshot real, o teto caiu 392→**361** e a
  eficiência foi a ~100% — a leitura correta para quem segue o tool toda manhã (a reconstrução
  inflava o teto). Cobertura: `reconcile_ceiling` + round-trip do cache em `test_efficiency`.
- **`blend_weight_sweep`/`blend-track` exigiam a base histórica mesmo sem odds** (`backtest`): o
  `_collect_blend_games` avaliava `load_historical()` como argumento **antes** de filtrar por odds,
  então uma edição sem `odds.csv` estourava `FileNotFoundError` quando o `historical_results.csv`
  (gerado, gitignored) não existia — quebrando o CI (`test_blend_weight_sweep_empty_without_odds`,
  vermelho desde 02/07: passava só localmente, com o CSV presente). Agora retorna cedo (`[]`) quando
  não há odds — sem mercado, nenhum jogo entra no blend e a base não é necessária.
- **Teto do tool inflado em KO decidido por gol na prorrogação** (ENG-45, `efficiency.py`): o
  placar gravado em `fixtures.csv` inclui a ET (convenção martj42), mas o bolão pontua o slot de
  90' contra o **tempo normal**. O `efficiency.py` pontuava o palpite de 90' contra o placar-com-ET
  — ex.: **J82 Bélgica gravado 3×2, mas 2×2 nos 90'** — creditando **12 pts** a um palpite `2×1`
  que, contra o `2×2` real dos 90', dá **0**; o "teto do tool" subia indevidamente (na 2026,
  404→392). Novo arquivo opcional `regulation.csv` (`match_id,reg_home,reg_away`, versionado)
  guarda o 90' desses jogos; `Edition.regulation` + `efficiency.regulation_90` o usam para o slot
  de 90' (e o jogo cai no caminho de ET, recebendo o bônus quando a fonte confirma). Só gol-na-ET
  precisa de entrada — pênaltis puros já preservam o empate. Cobertura: `test_load_regulation`,
  `test_as_of_drops_future_regulation`, `test_regulation_90_*`,
  `test_eng45_et_goal_scored_against_90_and_gets_bonus`.
- **`Avança` em branco em jogo de KO decidido no tempo normal** (`_final_ko_layers`): a fonte
  preenche `ko_outcome` de forma inconsistente em jogos de 90' (J77 França 3×0 Suécia vinha vazio),
  e o display só lia esse campo — deixava o `Avança` em branco mesmo com placar decisivo, enquanto
  o bracket derivava o vencedor do placar. Agora, decidido no tempo normal sem `ko_outcome` ⇒
  avança quem fez mais gols (mesma lógica do bracket); empate segue exigindo shootout para não
  afirmar prorrogação sob incerteza. Cobertura: caso do J77 em `test_final_ko_layers_real_outcomes`.
- **Jogos já disputados mostravam `0/0/0` (HTML) e `//` (MD) nas colunas de probabilidade**
  (`render`): jogo `FINAL` não tem previsão de 1×2 (já aconteceu) e sai do pipeline com `P_*`
  vazios; o HTML coagia vazio→0 (`_pct`), exibindo `0/0/0` + barra vazia — parecia "0% de tudo" /
  buraco de render. Agora linhas `FINAL` mostram `—` nas colunas **M / E / V** e **Prob.** (HTML) e
  em **Probabilidades** (MD). Cobertura: `test_final_group_game_shows_dash_not_zeros_in_mev`.
- **Resultados de mata-mata alimentam o ajuste sem o boost** (ENG-42): os jogos de KO guardam
  slots (`W73`, `2D`) em `home`/`away`, então escapavam do filtro `.isin(edition.teams)` e só
  chegavam ao modelo pela base histórica (peso 1.0) — e **só se ela estivesse atualizada** (foi o
  que deixou o modelo cego ao mata-mata em ENG-41). `build_training_frame` agora resolve os slots
  dos KO disputados para os nomes reais via `sync.resolve_live_bracket` e os alimenta pelo mesmo
  caminho boostado dos jogos de grupo, unificando as duas rotas de realimentação. Regressão coberta
  por `test_build_training_frame_feeds_knockout_with_boost`. ⚠️ Expôs que `CURRENT_EDITION_BOOST`
  (6.0) nunca foi calibrado — ver ENG-44.
- **Double-count dos jogos da edição no ajuste do modelo** (ENG-41): quando a base histórica já
  contém a Copa em andamento (acontece ao rodar `fetch-data` no meio do torneio — martj42 traz o
  torneio vivo), os jogos de grupo entravam **duas vezes** no treino (peso 1.0 pela base + boost
  6.0 pelo `fixtures.csv` ⇒ 7.0 efetivo), inflando o peso dos resultados recentes e distorcendo as
  probabilidades. `pipeline.build_training_frame` agora **remove da base** os jogos que já entram
  via fixtures (casa por data + par não-ordenado de seleções; o resultado autoritativo é o do
  fixture). Efeito na edição 2026: favorita ao título de Argentina 31%→24,8% (número correto).
  Regressão coberta por `test_build_training_frame_no_double_count`.
- **Apresentação do projeto defasada** (`build_presentation.py`, 2026-07-05): conteúdo curado
  parado em 28/06 (fase de grupos) e o blend ainda citava "peso 0,6" — mesma classe de drift da
  auditoria documental, agora no deck. Atualizado para 05/07 (90/104 jogos, 363 pts acumulados,
  ~100% de eficiência, favoritos ao título recalibrados, peso do blend 0,8, jogos a observar do
  mata-mata em andamento, contagem de melhorias de engenharia 23→43). `docs/apresentacao.html`
  (cópia versionada) e `out/apresentacao.html` regenerados.
- **Favoritos ao título repetidos nos slides 9 e 10** (`build_presentation.py`, 2026-07-05): o
  painel "o que esperar" do slide 10 chamava `champ_bars()` sem argumento, reproduzindo
  **idênticos** os mesmos 5 favoritos já mostrados no slide 9 logo antes — pré-existente (antes
  mostrava um top-3 truncado dos mesmos números) e agravado ao atualizar os dados hoje. Trocado
  pelo trajeto projetado do favorito até a final (QF/SF, com as probabilidades de cada jogo) —
  informação nova, não a mesma repetida.
- **Aba do navegador da apresentação sem ícone e com título genérico** (`build_presentation.py`):
  sem favicon e `<title>` só "apresentação do projeto". Adicionado favicon SVG inline (data URI,
  sem asset externo) com o ⚽ da marca do cabeçalho do deck (o `<title>` não repete o emoji, que
  fica só no ícone da aba); título trocado para `worldcup - O palpite inteligente`, ecoando o
  subtítulo do slide de capa.

### Alterado
- **`--pool-behind` agora gera EMPATE na final por default; zebra vira opção** (ENG-40):
  `predict`/`sync-results --pool-behind [empate|zebra]` (sem valor ⇒ `empate`).
  `knockout.predict_knockout(pool_behind=)` passa de bool para `None|"empate"|"zebra"`: o modo
  `empate` palpita os 90' no melhor placar de **empate** por E[pts] (diagonal) e mantém camadas
  de prorrogação/pênaltis e avanço fiéis; `zebra` preserva o comportamento do ENG-36 (superado
  pela simulação do ENG-39 em todos os geradores — mantido para a reavaliação da véspera).
  Restrição de peso máximo (só a final) e condicionalidade ao standing inalteradas.

### Adicionado
- **`blend-track --sweep`** (ENG-38): varre `blend_weight` 0,0..1,0 (passo 0,1) sobre os jogos de
  grupo disputados com odds e mostra o Brier de cada peso, com **uma só passada as-of** (1 fit/dia;
  cada peso é só uma reavaliação do pool logarítmico). Motivou subir o `blend_weight` da edição
  2026 de 0,6 (prior) para **0,8** (dado): Brier monotônico decrescente em w — 0,4420 (modelo-puro)
  → 0,4179 (0,6) → 0,4100 (1,0). Só grupo: no KO a convenção martj42 registra o placar com
  prorrogação, o que torna o desfecho de 90' (o que as odds precificam) ambíguo.
- **Política `empate-final` + sensibilidade de gerador no `eng36_pool_sim`** (ENG-39): nova
  política que, atrás no ranking, **empata os 90' da final** (melhor placar da diagonal por E[pts])
  com camadas de prorrogação/pênaltis — a arma do líder, cirúrgica no peso ×4. E
  `--draw-inflate-final P`: infla P(empate 90') **só do gerador** da final (via `rescale_matrix`),
  mantendo as matrizes de palpite cegas — corrige o viés juiz-e-parte da simulação (o gerador
  padrão é o próprio modelo, que subestima empate em final: ~28% vs ~60% histórico desde 1994).
  Resultado: `empate-final` domina `zebra-final` em **todos** os geradores (P(top-3) 8,4% vs 5,5%
  no baseline, 14,3% vs 3,8% no histórico) a custo zero de E[pts] — a regra de endgame do ENG-36
  muda de "zebra na final" para "empate na final" (expor no `predict` = ENG-40).

### Corrigido
- **`resolve_live_bracket` não propagava vencedor de KO decidido nos 90' sem `ko_outcome`**
  (`sync.py`): jogos registrados **à mão** com placar decisivo ficam sem `ko_outcome` (o `record`
  só o exige em empate), e a função exigia o campo para propagar — J77/J78/J79 não resolviam e
  J90/J91/J92 (confrontos já definidos) ficavam **fora do casamento de odds, com o blend
  silenciosamente desligado** (efeito real: o palpite de J91 saía Brasil 3×0 a 85% model-only; o
  mercado precifica ~50%). Agora o placar decide quando `ko_outcome` falta; empate sem `ko_outcome`
  segue indeterminado (pênaltis não confirmados). O `fetch_odds` também **loga** eventos sem
  fixture casável em vez de descartar mudo (foi o que escondeu o bug).
- **`sync-results` quebrava com
  `AttributeError: 'Namespace' object has no attribute 'pool_behind'`**
  (`cli.py`): o parser de `sync-results` nunca ganhou `--pool-behind` (adicionado ao `predict` no
  ENG-36), mas `cmd_sync_results` delega para `cmd_predict`, que lê `args.pool_behind` direto.
  Adicionado `--pool-behind` ao parser de `sync-results`, espelhando o do `predict`.
- **Re-arquivar no mesmo dia não sobrescreve mais o palpite da manhã** (`cli.archive_outputs`):
  o segundo `--archive` do dia (pós-`record`/`sync-results`) gravava os jogos disputados como
  `FINAL` em cima do snapshot da manhã — perdendo o dado não-reprodutível que o `history/` existe
  para preservar (mordeu em 2026-07-01: J80–J82 caíram no teto reconstruído do `efficiency.py`).
  Agora o re-archive faz **merge por jogo**: linha com palpite (`PREVISTO`) que viraria `FINAL` é
  preservada (e logada); jogos pendentes/novos atualizam. Snapshots reconstruídos (`--as-of`) seguem
  sobrescrevendo — são regeneráveis por definição. (ENG-33)
- **Peso de fase aplicado na contabilidade de pontos/teto**
  (`Scorer.weighted_points` + `scripts/efficiency.py`): app pontua mata-mata vezes peso da fase
  (R32–SF ×2, final ×4), mas **nunca era aplicado**
  (`ScoringConfig.weight` existia, ninguém chamava) — teto/eficiência subcontava cada jogo de KO,
  inflando conforme mata-mata avança. Agora placar dos 90' do KO entra ponderado. Pontuação
  da **fase de grupos é idêntica** (peso ×1). (ENG-27 parte 1)
- **Bônus de prorrogação/pênaltis no teto de eficiência** (`scripts/efficiency.py`): reconstrói
  o desfecho da fonte — placar dos 90' (results) + `shootouts`, com a inferência
  *empate-90'-sem-shootout ⇒ decidido na prorrogação* — e soma `knockout_bonus` (+3/+3 ×peso)
  ao teto. Guarda de **latência**: jogos empatados nos 90' ainda não confirmados pela fonte
  (martj42 atrasada) são pulados e listados, nunca inferidos. O oráculo também ganha o teto do bônus
  de KO. (ENG-27 parte 2)
- **Blend com odds agora cobre o mata-mata**
  (`sync.resolve_live_bracket` + `scripts/fetch_odds.py`): o casamento de odds era hardcoded
  para `is_group`, deixando o blend (ENG-19) **desligado em todos os 31 jogos de KO** (peso 2×/4×).
  Agora resolve o bracket pelos resultados reais do fixture (sem rede, sem modelo) e casa
  os confrontos de KO já definidos, alinhando as odds pelos times resolvidos. `odds.csv` 49→62
  jogos; ex.: o palpite de avanço de J78 passou a seguir o mercado. (ENG-28)
- **Palpite de prorrogação por E[pts]** (`knockout.predict_knockout`): a camada 2
  (quem vence a prorrogação / vai aos pênaltis) era um limiar fixo (`cond_home ≥ 0.58`) que ignorava
  P(prorrogação empatada). Agora modela a prorrogação como Poisson (taxa de 90' × 30/90) e escolhe
  o desfecho mais provável (maximiza E[pts]). Efeito: "vai aos pênaltis" vira o modal na maioria
  dos KO (empate ~53% numa ET de 30 min), só favorito forte crava um lado. Camadas 1/3 e o avanço
  inalterados. (ENG-29)
- **Rótulo da fase R32 estava errado: "32-avos" → "16-avos de final"** (`render._STAGE_LABEL`).
  A rodada de 32 seleções tem **16 jogos** (1/16 da final), logo é "16-avos" — coerente
  com "oitavas" (8 jogos) e "quartas" (4). Snapshots já versionados em `history/` ficam como estão
  (registros imutáveis do que o tool emitiu no dia).
- **Alocação dos melhores terceiros podia divergir da tabela oficial da FIFA** (`_assign_thirds`):
  o casamento por restrição (backtracking) devolvia o **primeiro** emparelhamento válido, que não é
  único — em 2026 saiu diferente do Annex C oficial
  (J74/J77/J81 com Bósnia/Paraguai/Suécia rodados). Adicionado override por edição
  em `tournament.toml::[group_stage.third_allocation]` (`match_id → grupo`), aplicado quando
  o conjunto de grupos bate com os terceiros classificados — usado no bracket real (`sync`)
  e no determinístico/Monte Carlo (`format_engine`). 2026 cravado na row 67
  (grupos B/D/E/F/I/J/K/L), verificado vs bracket oficial (Yahoo/Sky) + Wikipedia. Tabela completa
  de 495 combinações segue pendente (SPEC §9.3).
- **Suíte de testes resiliente ao avanço da Copa**: `test_sync_results_fills_unplayed_group_games`
  esvazia 2 jogos no clone em vez de depender de partidas de grupo em aberto nos dados reais
  (quebrava quando a fase de grupos terminava).
- **Bônus de placar do Sistema I eram somados, não hierárquicos** (`scoring.points`): o app concede
  só o MAIOR nível atingido (exato +5 > gols do vencedor +3 > saldo +2 > gols do perdedor +1), não
  a soma. O bug inflava todo placar cravado
  (ex.: favorito 2×0 dava base+11 ≈ 13 em vez de base+5 = 7) e **enviesava o `best_prediction`
  contra empates** (jogo decidido somava mais bônus que empate). Achado por confronto com as telas
  "Pontos por Jogo" do app; validado em 12 jogos (8 exatos, 4 off ≤1 só na base). Corrige eficiência
  (estava inflada) e faz o modelo voltar a palpitar empates. (ENG-23)
- Fit do Dixon-Coles **converge** via gradiente analítico (antes esgotava o orçamento de avaliações
  do scipy e parava longe do ótimo, sem sinal além do aviso). (ENG-16)

### Notas de calibração
- **Curva de base subdeterminada** (ENG-26): 9 pontos de telas reais de jogo do R32 não desempatam
  "coeficiente maior" vs "arredondamento ceil" (hipóteses confundidas) e ambas conflitam
  com o Simulador. Mantido `base_log_coeff = 7,55` + round; resíduo ±1/jogo é limitação aceita
  (ver SPEC §4.1).

### Adicionado
- **Modo endgame de bolão `predict --pool-behind`** (`knockout.predict_knockout(pool_behind=…)` +
  `pipeline.run`): bolão é jogo **diferencial** — o E[pts]-máximo pontua junto com o pelotão
  e preserva a posição; ranking só muda quando o palpite diverge e acerta. A simulação de pelotão
  (`scripts/eng36_pool_sim.py`, 3000 torneios, pelotão sintético ancorado no standing real) mostra:
  atrás, zebra **só na final** multiplica P(#1) por ~6 (0,7%→4,0%; top-3 2,2%→8,5%) custando ~7 pts
  esperados; divergir antes (SF/QF) não adiciona P(#1); mudar só o placar (mesmo lado) não move
  nada; na frente, fiel domina (47% vs 35%). O flag palpita a zebra
  (90' por E[pts] dentro do lado azarão + camadas ET/pênaltis) **apenas nos estágios de peso
  máximo** da edição (a final, no Equilíbrio gradual) — opt-in, condicional ao standing,
  edition-agnóstico. (ENG-36)
- **Blend de totals — a taxa de gols do placar agora segue o mercado** (`blend.py`): o rescale
  de 1×2 preserva a forma condicional, então os gols esperados
  (onde vivem o exato +5 e o `winner_goals` +3) ficavam 100% modelo. Novos passos: `devig_pair`
  (des-vig do over/under) → `implied_total_rate`
  (λ-total implícito da linha, por bissecção na Poisson) → pool geométrico de taxas
  (pool logarítmico de Poissons **é** Poisson na média geométrica) → `tilt_matrix_to_total` (tilting
  `c^(i+j)`, preserva a partição mandante/visitante), iterado com o rescale (1×2 exato). `odds.csv`
  ganha as colunas **opcionais** `total_line,over,under` (arquivos antigos seguem válidos);
  `scripts/fetch_odds.py` busca `h2h,totals`
  (fallback de totals: mediana na linha **modal** entre as casas); `blend-track` ganha o Brier
  binário do over/under (modelo vs blend). Sem totals num jogo ⇒ blend só de 1×2
  (degradação graciosa, caminho antigo byte-idêntico). (ENG-35)
- **Subcomando `worldcup status` (alias `ws`)** — briefing read-only de start-of-day
  (`status.build_status`/`format_status`, `cli.cmd_status`): numa saída só reidrata o contexto
  da campanha — jogos disputados/total, fase atual, jogos de hoje (disputado ✓ / pendente ⏳),
  próximos palpites, standing (lido do `BOLAO.md`) e o que depende do usuário (pontos p/
  a eficiência; jogos atrasados que a fonte ainda não tem; aviso de `out/` obsoleto). Idempotente —
  não muta nada; a mutação segue em `sync-results`/`predict`. `--date AAAA-MM-DD` sobrescreve
  "hoje". (ENG-31)
- **Desfecho real dos jogos de mata-mata já disputados** (`pipeline._final_ko_layers`): jogos de KO
  FINAL agora mostram **quem avançou** (`ko_outcome`) e prorrogação/pênaltis reais — placar dos 90'
  decidido ⇒ "—"; empate ⇒ "vai aos pênaltis" + vencedor quando o shootout é conhecido. Captura
  manual via `data/editions/<ano>/shootouts.csv` (`match_id,winner`, em `Edition.shootouts`)
  para a edição viva quando a fonte oficial tem latência — preenchido **só com placares verificados
  em ≥2 fontes**. (ENG-30)
- **Blend com odds de mercado** (`blend.py`): des-vig → pool logarítmico → reescala da matriz,
  com `odds.csv` por jogo, `scoring.toml::blend_weight` (2026 = 0.6), CLI `predict --blend-weight`
  e `scripts/fetch_odds.py` (The Odds API, chave no `.env`). (ENG-19)
- **`blend-track`**: valida o blend prospectivamente (Brier multiclasse blend-vs-modelo as-of)
  e exibe o **monitor de regime de empates** (z-score; gatilho 2σ para reconsiderar tilt).
  (ENG-19, ENG-22)
- **Calibração probabilística** no backtest: Brier multiclasse + curva de confiabilidade do empate,
  agregados nas 4 Copas — veredito de que o modelo é bem calibrado em empate. (ENG-18)
- Testes **e2e do pipeline** e de integração do `sync` rodando no CI (fixture histórico sintético,
  sem depender do `historical_results.csv`); piso de cobertura `fail_under` 65→80. (ENG-20)
- **Bônus de mata-mata no backtest** (ENG-12): `fetch_data` mescla `shootouts.csv` → coluna
  `penalty_winner` na base histórica, e `backtest` concede os bônus de prorrogação/pênaltis
  nos jogos decididos nos pênaltis (`Scorer.knockout_bonus`, antes config morta). Jogos decididos
  dentro da prorrogação seguem não-identificáveis na fonte (martj42 não traz a fase) — limitação
  documentada.
- **Apresentação do projeto** (`scripts/build_presentation.py`): gera um deck HTML autocontido (tema
  dark "Placar Noturno", palco 16:9 com auto-resize, navegação por botões/teclado/dots, deep-link
  `#slide-k`, contadores animados e modo impressão/PDF) explicando o projeto para leigos. Saída
  versionada em `docs/apresentacao.html` (regenerável pelo script). Self-contained
  (CSS+JS inline, SVG-first, fotos CC embutidas em base64, sem CDN).
- **Eficiência da campanha** (`scripts/efficiency.py`): mede `seus_pontos / teto-do-tool`
  reconstruindo o palpite **as-of** de cada manhã (mesmo caminho do `predict --as-of`) e pontuando
  pelo Sistema I; `--compare-archive` separa o teto verificável (snapshots reais) do reconstruído
  e expõe o ruído de reconstrução. Passo 6 da skill `palpites-copa`.
- **Teto teórico (oráculo)** no `efficiency.py`: além do teto do tool, reporta a pontuação de cravar
  o placar exato de todo jogo e duas capturas complementares (`tool/oráculo` = qualidade
  do modelo+blend; `seus_pontos/oráculo` = distância da perfeição). Diagnóstico de teto, não
  de execução (o oráculo é dominado por ruído irredutível — o tool perfeito captura ~34% dele).

- **Slide de balanço da fase de grupos** na apresentação (`build_presentation`): resumo dos 72 jogos
  (28% de empates, zebra Cabo Verde no grupo da Espanha) + expectativa do mata-mata (corrida
  ao título, final prevista Espanha×Argentina, jogos 50/50 a observar). Números
  da campanha/Brier/favoritos atualizados para o fim dos grupos (28/06): 2º lugar, 235 pts (72/104),
  eficiência 103%, blend-track n=49 (modelo 0,442 / blend 0,418).

### Mudado
- **Palpite de 90' do mata-mata não sai mais empate** (`scoring.best_prediction(forbid_draw=…)` +
  `knockout.predict_knockout` camada 1): o E[pts]-ótimo puro escolhia empate (0×0/1×1) em ~25%
  dos jogos de KO, que **zera sempre que o jogo é decidido no tempo normal**
  (12 de 16 nos backtests). A vantagem de E[pts] era marginal (~0,04/jogo) e apoiada numa leve
  super-estimação de empate no KO (P̄ modelo 0,278 vs real 0,234). Passando a escolher o melhor
  placar **com vencedor**, o realizado sobe **+70 pts** (peso ×2/×4) nos KO de 4 Copas a custo
  de E[pts] ~nulo. Grupos inalterados; camadas de prorrogação/pênaltis/avanço inalteradas
  (independentes do placar de 90'). (ENG-32)
- **Doc de estratégia/backtest realinhada à régua hierárquica** (auditoria pós-ENG-23): a tabela
  do backtest 2022 (SPEC §9.1, MODEL_CARD) foi atualizada (agora 187/159/181 por risco 0.0/0.5/1.0)
  e a tese "agressivo faz ~28% mais pontos" foi **removida** — era artefato do bug de pontuação
  somada; com a régua corrigida, subir o risco não melhora os pontos de forma confiável. README não
  recomenda mais `--risk 0.7/1.0` para subir no ranking.
- **Esquema do `historical_results.csv` documentado** no `docs/DATA.md`
  (8 colunas, incl. a nova `penalty_winner` mesclada do `shootouts.csv`); `efficiency.py` citado
  no PRD (M3) e no GLOSSARIO.
- Defaults do `FitConfig` recalibrados por **LOO-CV** (meia-vida 2,5→2,0, ridge 0,05→0,10; +9,2%
  de pontos no backtest das 4 Copas). (ENG-17)
- Curva de pontos base reproduz o app (log-linear `1 + 7,55·log10(1/p)`); `risk` **desacoplado**
  da régua, virou um tilt só na escolha do palpite. (ENG-14)
- `fetch-data`/`sync-results` aceitam **fontes em cascata** (`--source-url`) com fallback. (ENG-15)
- `monte_carlo()` default `n_sims` 8000→5000 (alinhado ao caminho real e ao SPEC). (ENG-13)
- Camada meta podada e **canônicos de blend/odds declarados** por audiência
  (README/AGENTS/SPEC/BOLAO); memória de campanha higienizada. (ENG-21)

## [0.2.0] - 2026-06-13

Leva de endurecimento de engenharia (backlog `docs/BACKLOG.md`, ENG-1..ENG-9 e ENG-11).

### Adicionado
- Flag global `-v`/`--verbose` e `logging` na biblioteca: avisos antes silenciosos agora são
  visíveis e capturáveis em teste (seleções descartadas pelo `min_matches`, fit não-convergido).
  (ENG-4)
- Validação de schema do CSV da fonte pública: falha cedo e clara (`DataSourceError`) se o formato
  mudar, em vez de um `KeyError` críptico adiante. (ENG-5)
- Medição de cobertura no CI (`pytest-cov`) com piso `fail_under = 65` (cobertura ~74%). (ENG-8)
- Guardrail de tradução: toda seleção de cada edição precisa ter exibição em PT, senão o teste falha
  (evita cair no inglês silenciosamente). (ENG-9)
- `mypy` passa a cobrir `tests/`. (ENG-7)

### Corrigido
- `sync`: o reencontro do mesmo par de seleções na mesma Copa (grupo + mata-mata) não colapsa mais
  num único placar — desambiguação por data; corrige risco de preencher um jogo com o placar
  do outro. (ENG-1)
- `backtest`: aplica o mando do anfitrião pela mesma `MatrixCache` da produção (antes ignorava,
  pontuando jogos do país-sede de forma diferente do caminho real). (ENG-2)
- `model`: avisa quando o otimizador não converge (antes usava o resultado silenciosamente). (ENG-3)

### Mudado
- Camada de apresentação extraída para `render.py`; `cli.py` passou a só orquestrar
  (520 → 285 linhas). Sem mudança de comportamento. (ENG-6)
- Documentação: `docs/SPEC.md` §9.2 declarado canônico para "Limitações conhecidas"
  (antes duplicada nos três docs sem dono). (ENG-11)

## [0.1.0]

- Versão inicial: modelo Dixon–Coles, pontuação Sistema I, simulação Monte Carlo + chaveamento,
  realimentação por resultados reais (`sync-results`/`record`), saídas CSV/MD/HTML, orientação
  a dados por edição (`data/editions/<ano>/`) e backtest.
