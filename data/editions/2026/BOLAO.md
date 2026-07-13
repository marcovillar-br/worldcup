# BOLAO.md — memória de campanha (Copa 2026)

Memória persistente da campanha do bolão, **agnóstica a ferramenta**: qualquer agente
(Claude, Codex, Gemini, …) deve **ler este arquivo no início da sessão**
e **atualizá-lo quando uma decisão de campanha acontecer**
(mudança de `risk`, situação no ranking, regra do bolão alterada, etc.).

Registre aqui **só o que não é rederivável** dos dados e do código:
- estado dos jogos → mora em `fixtures.csv` (e `sync-results` reconstrói da internet);
- palpites vigentes → `out/palpites-2026.{csv,md,html}` (regeneráveis com `predict`);
- decisões e contexto humano da campanha → **aqui**.

Use datas absolutas (AAAA-MM-DD). Entradas novas no topo do histórico.

## Estado atual (atualizado em 2026-07-13)

- **13/07: dia sem jogos — semifinais amanhã (14/07).** Nada a registrar (`sync-results`: 0 novos).
  Odds re-sincronizadas (as 2 semis atualizadas; 74 jogos no `odds.csv`) e palpites regenerados com
  snapshot do dia. **Favoritos ao título:** Espanha 28,6%, França 26,3%, Argentina 24,2%,
  Inglaterra 20,9% — o quase-empate das 4 seguiu (nenhuma semi passa de 39% no 1×2). Os 4 jogos
  restantes seguem `1×1` nos 90' + "vai aos pênaltis"; palpite de campeão **Espanha** (bracket
  determinístico: França). Config inalterada: `risk 0.5` + `blend 0.8`.
- **Correção de exibição (13/07, ENG-58): a tabela vinha mentindo sobre o mata-mata disputado.** A
  coluna "Palpite (90')" mostrava o placar **de 120'** nos jogos decididos na prorrogação (J82 saía
  `3×2`, foi `2×2` nos 90'; J99 `1×2`, foi `1×1`; J100 `3×1`, foi `1×1`) e, por consequência, as
  colunas Prorrogação/Pênaltis saíam `—`, como se os jogos tivessem acabado no tempo normal. Era só
  **apresentação** (o `regulation.csv` já estava certo e o `efficiency.py` já o usava): **pontos,
  teto e eficiência não mudam**. Também entrou o **placar das disputas de pênaltis** (ENG-59): J74
  Alemanha 3×4 Paraguai, J75 Holanda 2×3 Marrocos, J88 Austrália 2×4 Egito, J96 Suíça 4×3 Colômbia.
- **100 de 104 jogos disputados — quartas encerradas.** Em 11/07 fecharam as duas últimas, **ambas
  na prorrogação**: **J99 Noruega 1×2 Inglaterra** (1×1 nos 90', Bellingham decide aos 93') e
  **J100 Argentina 3×1 Suíça** (1×1 nos 90'; Suíça com 10 desde os 72'). O tool acertou **os dois
  vencedores** (Inglaterra e Argentina, ambos como "avança"), mas nenhum dos placares de 90'. Como
  os dois tiveram gol na ET, o 90' foi registrado em `regulation.csv` (J99 `1,1`; J100 `1,1`) —
  senão o teto de eficiência infla (ENG-45). A fonte pública (martj42) ainda não tinha os jogos:
  registrados à mão, com placar **e** 90' confirmados em ≥2 fontes (FIFA/ESPN e ESPN/Al Jazeera).
  Restam **4 jogos**: SF J101 França × Espanha (14/07), SF J102 Inglaterra × Argentina (15/07),
  3º lugar (18/07) e final (19/07). Odds re-sincronizadas (74 jogos no `odds.csv`); `blend-track`
  inalterado (só grupos, 49 jogos): blend melhor (Brier 0,4074 vs 0,4091), regime de empates dentro
  da variância (z=+0,80). Config: `risk 0.5` + `blend 0.8`. **As 4 seleções vivas estão num
  quase-empate**: Espanha 28,0%, França 27,3%, Argentina 23,3%, Inglaterra 21,3% (após o ENG-54 e a
  re-sincronização das odds das duas semis em 12/07) —
  nenhuma semi passa de 39% no 1×2, e por isso o palpite de 90' diverge de "avança" (o placar segue
  E[pts], que num jogo-moeda premia o empate; "avança" segue a probabilidade — divergência permitida
  por design, `consistency.py:47`). **Com o ENG-54, J101 passou de `2×1` a `1×1`**: agora os 4 jogos
  restantes saem `1×1` (e os 4 saem "vai aos pênaltis"). **Palpite de campeão: Espanha** (favorito
  por probabilidade; o bracket determinístico dá França — leituras diferentes, não contradição).
- **Placar (12/07): 425 pts, 19º. Líder 509 — gap de 84 com 4 jogos.** Ontem você **não pontuou**:
  os dois jogos terminaram **1×1 nos 90'** e o tool palpitou decisivo (`1×2`, `2×1`) nos dois. **Não
  foi execução nem defeito:** a reconstrução as-of de 11/07 mostra que, mesmo com o empate liberado,
  o tool teria palpitado o mesmo (o empate valia **menos** E[pts] — −0,83 e −1,22 — porque via
  favoritos claros, Inglaterra 50% e Argentina 56%). Dois favoritos segurados no 1×1: azar puro.
  Eficiência segue **96,8%** do teto do tool (439) — o teto **não subiu**, ou seja, seguir o tool à
  risca também renderia zero ontem.
- **Medição de eficiência (12/07): 425/439 = 96,8%. O líder (509) está ACIMA do teto do tool.** Isso
  encerra a dúvida sobre execução: mesmo tendo seguido o tool com perfeição, você teria 439 e ainda
  estaria 70 atrás. **O gargalo é a qualidade do palpite, não a sua disciplina** — e ele tem nome: o
  ENG-32 proibia o tool de palpitar empate no mata-mata, e o mata-mata teve **7 jogos empatados nos
  90'**, justamente onde o peso é ×2/×4. O tool com o ENG-53/54 teria feito ~466 (o `drift` do
  `ceiling.csv` mostra J75 6→26, J88 12→26, J90 6→14). Não recongele o teto (`--reset-ceiling`):
  os tetos congelados refletem o tool que **de fato apareceu** naquelas manhãs, que é o que mede
  execução; recongelar te creditaria palpites que o tool nunca exibiu.
- **Ainda dá para virar?** Os 4 jogos restantes valem no limite absoluto **170 pts** (semis e 3º ×2,
  final ×4, cravando placar raro + bônus de pênaltis em todos) contra um gap de **84**.
  Matematicamente vivo, na prática improvável. E não há jogada extra: o `--pool-behind` forçaria
  empate na final — que é **exatamente o que o palpite fiel já dá** agora que o ENG-53 liberou o
  empate. Seguir o tool é a jogada.
- **Decisão de campanha (12/07): jogar DIFERENCIAL até o fim.** Com 84 de gap e ~26 pontos esperados
  nos 4 jogos restantes, maximizar E[pts] **não alcança o líder** — é matematicamente insuficiente.
  Passamos a rodar `predict --pool-behind empate` (ENG-39/40): a final sai no melhor **empate**.
  Coincidência favorável: com o ENG-53 o empate na final também é o **maior E[pts]** (+1,42), então
  fiel e diferencial concordam pela primeira vez — a jogada não custa nada em pontos esperados.
- **Decisão de campanha (12/07): congelar o modelo até a final — o ENG-56 fica para depois de
  19/07.** É o único item aberto do backlog (o modelo subestima empate; mecanismo desconhecido).
  Mexer nele
  agora significa mexer na **calibração** — o que muda os palpites dos 4 jogos que restam e o teto
  congelado do `ceiling.csv`, no exato momento em que não há amostra nova para validar a mudança.
  O ganho seria de calibração, não de pontos: com 84 de gap, nenhuma correção de ~5 pp na taxa de
  empate vira o bolão. **Regra: nenhuma mudança de modelo/calibração até a final.** Correção de bug
  (como ENG-53/54) é outra coisa e continua valendo — o que está vedado é *tunar* com a Copa viva.
- **Bug ENG-53 encontrado e corrigido nesta rodada** (você estranhou "todos os palpites são 2×1 ou
  1×2"): o tool estava **proibido de palpitar empate** no 90' do mata-mata (ENG-32, `forbid_draw`).
  As duas premissas do ban eram falsas — o empate é o **E[pts]-máximo** num KO equilibrado (custava
  +1,42 na final, de peso ×4) e o modelo **subestima** empate no KO (13% palpitados vs 25%
  reais). Pior:
  a evidência de backtest que sustentava o ban era **artefato da régua** (ENG-54) — a base martj42
  grava o placar **com prorrogação**, então o backtest punia o palpite de empate justamente nos
  jogos que o bolão (que pontua os 90') premiaria. Mesma classe do ENG-48. Palpites agora: J102 e
  J104 saem `1×1`.
- **E a sua pergunta seguinte achou um bug maior (ENG-55/54)**: "nas simulações estamos usando o
  placar consolidado?". **Estávamos.** O `build_training_frame` mandava o placar do `fixtures.csv`
  (com ET) para o **ajuste do modelo**, tendo o 90' no `regulation.csv` — J82, J99 e J100 eram
  ensinados ao modelo como *vitórias*, sendo empates nos 90'. Corrigido (`Edition.score_90` vira
  fonte única; efeito em 2026 é pequeno — Espanha 27,6→28,4%, palpites iguais).
- **ENG-54 resolvido (12/07) — e o resultado desmente o que eu mesmo tinha afirmado.** A base
  histórica também treinava em placar de 120'. Eu havia registrado que isso era **insolúvel** ("os
  jogos decididos por gol na ET são invisíveis na base") e que explicava o modelo subestimar empate.
  **As duas coisas estavam erradas.** (a) O martj42 publica um terceiro arquivo, `goalscorers.csv`,
  com o **minuto** de cada gol — eu nunca tinha verificado a premissa. Reconstruído o placar dos
  90' (subtraindo os gols após o minuto 90), a base ficou correta. (b) Mas a contaminação era
  **pequena**: 76 jogos em 19.771 (~0,5% do peso), e a taxa de empate da base sobe só de **23,2%
  para 23,5%** — não para os 28% que eu supunha. **A explicação que eu tinha dado para o excesso
  de empates está morta** (ENG-56); o monitor que chamava aquilo de "variância" estava mais perto
  de certo do que eu.
  **Efeito prático:** J101 França×Espanha mudou de `2×1` para `1×1`. E o backtest de mata-mata volta
  a valer: re-medido, o ban de empate é **estatisticamente indistinguível** de não ter ban
  (+0,23 pt/jogo, IC95% cruzando o zero) — os "+70 pts" que o justificavam eram da régua velha.
- **Histórico da rodada anterior (11/07):**
  **Bug ENG-51 encontrado e corrigido** (você perguntou "no J101 a Espanha perde?"):
  o chaveamento e o campeão rodavam no modelo puro enquanto o palpite exibido rodava blendado — na
  SF J101 França × Espanha o mercado inverte o favorito do modelo, e a tabela se autocontradizia
  ("avança França" mas "final Espanha × Argentina"). Corrigido: bracket e campeão agora blendam os
  confrontos determinados com odds. **Efeito nos favoritos:** Espanha caiu de 38,1% para
  **29,9%**, França subiu para **28,6%**, Argentina 23,6%, Inglaterra 13,5%, Noruega 2,4%. A final
  do bracket virou França × Argentina (Espanha na SF, cai para o 3º lugar). O favorito a campeã
  (Espanha, marginal) ≠ campeão do bracket (Argentina, modal) — correto, agora anotado na saída.
  **Seus pontos (11/07): 425, 13º** (subiu de 16º) — eficiência **96,8%** do teto do tool (439).
  Líder **487**, acima do teto do tool. O gatilho de anomalia (ENG-50) dispara e mantém 2 sondas
  sujas honestas: J96 sem bônus por latência da fonte, e 30 jogos com teto só reconstruído (a
  reconstrução infla +27 sobre 68 verificáveis) — o teto real pode ser um pouco menor que 439, o
  que empurraria a sua eficiência para cima. As duas sondas que pegariam o ENG-48 (bônus de KO
  creditado; fontes concordam) seguem **limpas**.
- **97 de 104 jogos disputados.** Em 09/07 fechou a 1ª quarta: **J97 Marrocos 0×2 França**
  (tool palpitava 1×2 — lado e avanço certos, placar exato não). Hoje (10/07) joga
  **J98 Espanha × Bélgica** (palpite **2×1**, Espanha avança; 58%/25%/17%). Odds re-sincronizadas
  (3 jogos atualizados, 72 no `odds.csv`); `blend-track` inalterado: blend melhor
  (Brier 0,4074 vs 0,4091 do modelo puro), regime de empates dentro da variância (z=+0,80).
  Candidatos a campeão: **Espanha 28,9%**, Argentina 24,0%, França 23,8% (saltou com a vaga em
  SF), Inglaterra 14,8%, Bélgica 3,5%. Config: `risk 0.5` + `blend 0.8`.
  **Seus pontos (10/07): 409, 16º** (subiu de 17º) — eficiência **96,7%** do teto do tool (423).
  Líder **471**, ainda acima do teto do tool: nem seguir o tool à risca alcançaria hoje — é
  variância de exatos a favor dele, não estratégia melhor.
  ⚠️ **Correção (ENG-48): a eficiência caiu de 102,5% para 96,7% por um bug de medição, não por
  piora sua.** O `efficiency.py` nunca creditava o bônus de prorrogação/pênaltis (chave de data
  `datetime64` vs `str`), subestimando o teto. **Os "acima do teto" de 08/07 e 10/07 eram
  artefato** — desconsidere-os. Palpites nunca foram afetados (o script é isolado). Teto
  recongelado com `--reset-ceiling`.
  Ressalvas de leitura: 30 dos 97 jogos têm teto só reconstruído (J1–J4, J25–J35, J73–J90) e o
  subconjunto com snapshot real mostra Δ=+27 de ruído de reconstrução; só o **J96** segue sem
  shootout na fonte martj42 (latência genuína — a base termina em 03/07), então o bônus de KO dele
  não entra no teto.
- **96 de 104 jogos disputados — J97 Marrocos × França (QF) pendente hoje (09/07)**, ainda sem
  placar na fonte. Odds e blend re-sincronizados (4 jogos atualizados); veredito do
  `blend-track` inalterado: blend segue melhor (Brier 0,4074 vs 0,4091 do modelo puro), regime de
  empates dentro da variância (z=+0,80). Palpite de J97 mantido: **1×2, França avança**.
- **96 de 104 jogos disputados (J1–J96) — fase de oitavas encerrada.** Em 07/07 fecharam as
  últimas duas: **J95 Argentina 3×2 Egito** (tool acertou o lado, 1×2, mas não o placar exato) e
  **J96 Suíça 0×0 Colômbia** (pênaltis, **Suíça avança** — tool tinha cravado Colômbia; erro no
  avanço). 08/07 é dia sem jogos (folga entre oitavas e quartas). Próximo: **J97 Marrocos ×
  França** (09/07, palpite 1×2, França avança). Candidatos a campeão agora: **Espanha 30,3%**,
  Argentina 25,1% (subiu com a queda da Colômbia), Inglaterra 15,3%, França 13,8%, Marrocos 5,8%.
  `odds.csv` com **72 jogos** (fetch de 08/07: +1 novo, 3 atualizados). Config: `risk 0.5` +
  `blend 0.8`. **Seus pontos (08/07): 397, 17º** (caiu de 13º mesmo com eficiência subindo —
  o resto do bolão também pontuou bem nas oitavas) — eficiência **102,6%** do teto do tool (387,
  primeira vez ACIMA do teto); líder **455** segue acima do teto (variância de exatos no KO, não
  estratégia melhor).
- **94 de 104 jogos disputados (J1–J94).** Em 07/07 fecharam as últimas duas oitavas:
  **J93 Portugal 0×1 Espanha** (tool acertou o lado, 1×2, mas não o placar exato) e
  **J94 Estados Unidos 1×4 Bélgica** (tool tinha palpitado 2×1 EUA nos 90', mas o campo
  "avança" — camada independente — já cravava Bélgica; confirmado). Hoje 07/07 jogam as duas
  últimas oitavas: **J95 Argentina × Egito** (palpite 2×0, Argentina avança) e
  **J96 Suíça × Colômbia** (palpite 1×2, Colômbia avança). Candidatos a campeão agora:
  **Espanha 31,2%** (ultrapassou a Argentina), Argentina 22,4%, Inglaterra 14,2%, França 13,3%,
  Marrocos 6,3%. `odds.csv` com **71 jogos** (fetch de 07/07: +1 novo, 4 atualizados). Config:
  `risk 0.5` + `blend 0.8`. **Seus pontos (07/07): 385, 13º** — eficiência 100,5% do teto do tool
  (383); líder **443** segue acima do teto (variância de exatos no KO, não estratégia melhor).
- **92 de 104 jogos disputados (J1–J92).** Em 06/07 fecharam as duas primeiras oitavas:
  **J91 Brasil 0×2 Noruega** (zebra — tool tinha palpitado 2×1 Brasil; **Brasil eliminado**) e
  **J92 México 2×3 Inglaterra** (tool acertou o lado, 1×2, mas não o placar exato). Hoje 06/07
  jogam as próximas oitavas: **J93 Portugal × Espanha** (palpite 1×2, Espanha avança) e
  **J94 Estados Unidos × Bélgica** (palpite 2×1, Bélgica avança). Candidatos a campeão agora
  (Brasil saiu da lista): **Argentina 23,1%**, Espanha 18,8%, Inglaterra 14,9%, França 14,9%,
  Marrocos 7,5%. `odds.csv` com **70 jogos** (fetch de 06/07: +1 novo, 5 atualizados). Config:
  `risk 0.5` + `blend 0.8`. **Seus pontos (06/07): 375** — eficiência 100,5% do teto do tool
  (373); líder **433** segue acima do teto (variância de exatos no KO, não estratégia melhor).
- **90 de 104 jogos disputados (J1–J90).** Em 04/07 fecharam os últimos 16-avos **J89
  Canadá×Marrocos** e **J90 Paraguai×França** (sincronizados pela fonte pública em 05/07).
  **Standing (03/07): 325 pts, 17º** (líder **373**; pendente atualização pós-J86–90). Hoje 05/07
  abrem as **oitavas**:
  **J91 Brasil 2×1 Noruega** (Brasil avança) e **J92 México 1×2 Inglaterra** (Inglaterra avança).
  Candidatos a campeão: **Argentina 22,6%**, Espanha 18,6%, França 14,6%, Brasil 11,4%, Inglaterra
  9,2%.
  `odds.csv` com **69 jogos** (fetch de 05/07: +1 novo, 6 atualizados). Config: `risk 0.5` +
  `blend 0.8`.
- **88 de 104 jogos disputados (J1–J88).** No dia 03/07 fecharam os 16-avos **J86 Argentina 3×2
  Cabo Verde** (tool palpitou 2×0 — acertou lado/avanço), **J87 Colômbia 1×0 Gana** (tool 2×0 —
  lado/avanço certos) e **J88 Austrália 1×1 Egito** (Egito nos pênaltis — tool cravou a zebra do
  avanço). Sincronizados pela fonte pública em 04/07. **Standing (03/07): 325 pts, 17º** (líder
  **373**; pendente atualização pós-J86–88). Hoje 04/07: 16-avos **J89 Canadá×Marrocos** (1×2,
  Marrocos avança) e **J90 Paraguai×França** (0×2, França avança).
- **Config em uso (desde 02/07 à tarde): `risk 0.5` + `blend_weight 0.8`** (era 0,6; subido com
  dado — `blend-track --sweep`, ENG-38: Brier monotônico decrescente em w, 0,4420 modelo-puro →
  0,4100 em w=1,0; 0,8 captura o grosso sem abraçar o extremo em n=49). `odds.csv` com **65 jogos**
  após fix do bracket (J90/J91/J92 estavam SEM blend por bug — ver Histórico 02/07): efeito
  imediato, **J91 Brasil×Noruega caiu de 3×0 (85% model-only) para 2×0** (mercado dá ~50%),
  J92 México×Inglaterra virou 1×2.
- **Regra de endgame REVISTA (ENG-39, 02/07): na manhã da FINAL, se atrás, EMPATE nos 90'**
  (melhor placar de empate por E[pts] + camadas prorrogação/pênaltis) — substitui a zebra do
  ENG-36. Ver Decisões vivas.
- **81 de 104 jogos disputados (J1–J82, menos J81) [snapshot de 01/07].** Fase de grupos completa +
  J73–J80/J82 do mata-mata. Em 01/07 fecharam
  **J80 Inglaterra 2×1 RD Congo** (Kane 2× no 2º tempo, virada)
  e **J82 Bélgica 3×2 Senegal na prorrogação** (2×2 nos 90'; pênalti de Tielemans aos 125' — placar
  registrado com prorrogação, convenção martj42/SPEC; buscados na internet e confirmados em ≥2
  fontes: englandfootball/Olympics/Outlook e ESPN/Outlook/Yahoo). O tool acertou os dois lados
  (J80 palpite 1×0; J82 palpite 2×1 — nos 90' foi empate, mas quem avança bateu).
  **Hoje à noite: J81 EUA × Bósnia** (palpite 3×1 EUA); o resto do R32 vai até 03/07. Em 30/06
  fecharam J77 França 3×0 Suécia (cravado), J78 Costa do Marfim 1×2 Noruega e J79 México 2×0
  Equador.
- **Ontem (29/06): duas zebras no R32.** J74 Alemanha **1×1** Paraguai → **Paraguai avança** nos
  pênaltis (eliminou a Alemanha); J75 Holanda **1×1** Marrocos → **Marrocos avança**
  (eliminou a Holanda); J76 Brasil **2×1** Japão → **Brasil avança**. O tool pegou o lado do Brasil;
  as duas zebras de potência eram improváveis no modelo (favorece quem vem bem).
- **Standing (01/07, pós-J80/J82): 285 pts, 21º** (líder **337**) · **eficiência 88,0%**
  (teto as-of do tool 324). A queda de 103%→88% mora quase toda no **KO reconstruído**: os 9 tetos
  de R32 (J73–J82) não têm snapshot real da manhã e a reconstrução diverge do que o tool mostrou
  (drift medido: Δ+7 nos 60 verificáveis). **Líder 337 segue ACIMA do teto (324)** ⇒ nem seguir o
  tool à risca alcançaria; é variância de exatos no KO (peso ×2), regride. Caiu 11º→21º pelo mesmo
  motivo (exatos alheios no R32). Detalhe na entrada 01/07 do Histórico.
- **`blend-track` (01/07, n=49):** Brier modelo **0,442** vs blend **0,418** — Δ=**+0,024**; blend
  segue melhor. Regime de empates: 20/72 (28%) z=+0,74 — variância, sem ação.
- **Blend AGORA cobre o mata-mata (ENG-28, 30/06):** o `fetch_odds` só casava jogos de grupo — o
  blend estava **desligado em todos os 31 jogos de KO (peso 2×/4×)**. Corrigido: resolve o bracket
  pelos resultados reais e casa os confrontos de KO definidos. `odds.csv` foi de 49→**62 jogos**
  (+13 KO). Efeito imediato: **J78 mudou de "avança Costa do Marfim" para "avança Noruega"**
  (mercado tem Noruega favorita, 2.17). Os palpites de KO agora saem blendados; a sim de campeão
  segue DC-only.
- Favorito ao título (01/07, pós-J80/J82): **Argentina (28,6%)**; Espanha **19,2%**,
  França **14,4%**, **Brasil 13,1%** (bracket aberto — Alemanha/Holanda fora), Portugal 7,1%.
- **Bracket R32 corrigido (ENG-25, 28/06):** a alocação dos terceiros divergia da tabela oficial da
  FIFA — J74/J77/J81 saíam com Bósnia/Paraguai/Suécia rodados. Cravada a alocação oficial
  (row 67, grupos B/D/E/F/I/J/K/L) em `tournament.toml`. Agora: J74 Alemanha×**Paraguai**,
  J77 França×**Suécia**, J81 EUA×**Bósnia**. Os 16 confrontos batem com o oficial
  (Yahoo/Sky/Wikipedia).
- **Config em uso:** `risk 0.5` + `blend_weight 0.6` (blend com odds **ATIVO** — ENG-19; desde 01/07
  também **ancora a taxa de gols no mercado de totals** — ENG-35, efeito imediato: J86/J87 1×0→2×0,
  J89 0×1→1×2 nos jogos com o mercado). Scorer hierárquico (ENG-23). Admin do bolão usa Sistema I
  sem customização. **Rotina por rodada e formato do `odds.csv`: no README**
  (`fetch_odds.py` → `predict` → `blend-track`); a chave da The Odds API vive no `.env`. Odds em
  30/06: **62 jogos** no `odds.csv`
  (49 grupo + 13 KO, após ENG-28 destravar o casamento do mata-mata).

- **Perfil do líder (Thiago Diogo, 337 pts, #1 — screenshots de 01/07, "Pontos por Jogo"):**
  aposta **empate/prorrogação no KO** sistematicamente. R32 dele: J73 16 (cravou 0×1),
  J74 0, **J75 22** (cravou 1×1 +16 e prorrogação empatada +6; errou pênaltis), J76 12, J77 10,
  J78 16, J79 10, J80 10, J82 6 (Pror.) = **102 pts em 9 jogos**. O grosso da vantagem é o
  J75 (+22 onde o campo zerou); nos jogos decididos nos 90' (J76/J77/J78) o tool o bateu por +12. É
  o perfil que o ENG-32 aposentou — pagou nesta amostra (3/10 KOs foram à prorrogação), sangra se os
  próximos se decidirem nos 90' (~75% histórico). Vigiar: se o monitor de empates cruzar 2σ,
  reavaliar a política anti-empate do ENG-32 para esta Copa. Ação imediata: preencher **sempre** as
  camadas Pror./Pên. do tool no app (+6/acerto; o J82 rendeu +6 hoje por isso).

## Decisões vivas

- **Palpite de campeão (11/07): ESPANHA.** Marcado o **favorito por probabilidade marginal**
  (29,9%), não o campeão do bracket determinístico (Argentina, cenário modal — ENG-52/INV-7). Para
  o slot de campeão do bolão, o que maximiza P(acertar) é o time com maior probabilidade de título,
  não o vencedor da final do caminho mais provável. Números do dia: Espanha 29,9% > França 28,6% >
  Argentina 23,6% > Inglaterra 13,5% > Noruega 2,4% (já pós-fix do blend no campeão, ENG-51).
  **Cuidado:** o palpite jogo a jogo segue o bracket (J101 França vence Espanha) — o slot de campeão
  e os slots de placar são pontuados **separados** pelo bolão, então marcar Espanha campeã e França
  vencendo a J101 não se contradiz (apostas independentes, como no ENG-52).
- `risk = 0.5` **definitivo** — ótimo para a média **e** para o ranking. O botão de
  risco **não é instrumento de variância** neste sistema de pontos: subir o risco baixa o E[pts] sem
  aumentar o SD e, na simulação de campo, **reduz** P(vencer)/P(top-10) — inclusive no mata-mata
  (pesos 2×/4×). **A única alavanca de ranking é acurácia (ENG-19), não ousadia.** Substitui o
  gatilho antigo "subir risco se atrás" (premissa falsa). Modelagem completa
  (campo de 60, KO, números) na entrada **2026-06-17** do Histórico.
- Execução **sob demanda**: o usuário prefere rodar os comandos manualmente; não propor
  cron/agendamento.
- **Regra de endgame v2 (ENG-39, 02/07, substitui a zebra do ENG-36): na manhã da FINAL, se
  estiver atrás, palpite EMPATE nos 90'** (melhor placar de empate por E[pts], hoje ~1×1) **+
  camadas de prorrogação/pênaltis** — a arma do líder, aplicada só onde ela é +EV. Por quê: (1) o
  simulador do ENG-36 era **juiz e parte** (gerador = o próprio modelo), incapaz de punir a
  subestimação de empate em final — **5 das 8 finais desde 1994 empataram nos 90' (~60%) vs ~28%
  no modelo**; (2) com a política `empate-final` adicionada e a sensibilidade
  `--draw-inflate-final`, ela **domina a zebra em TODOS os geradores**: baseline P(top3) 8,4% vs
  5,5% (custo zero de E[pts]; a zebra custa ~8 pts); gerador histórico (60%) P(#1) 4,9% e P(top3)
  14,3% vs 1,2%/3,8% da zebra — e **ganha** E[pts] (+13). `empate-close` (QF/SF apertadas também)
  ≈ empate-final; simplicidade favorece só a final. **Na frente: fiel segue dominante no baseline
  (48% vs 41%)** — refazer a sim na véspera da final com o standing do dia, com e sem
  `--draw-inflate-final 0.45/0.60`, para confirmar o lado. **Execução: `predict --pool-behind`**
  (ENG-40, 02/07 à noite) já gera o empate na final (hoje 0×0 + "vai aos pênaltis" + Argentina);
  `--pool-behind zebra` mantém a política antiga para comparação. A zebra segue como referência
  histórica (entrada 01/07), mas está **superada**.
- **Limiar de poder da regra de endgame — matemática da virada (03/07):** a regra do empate é
  **~grátis** quando atrás (ENG-39/40: custo ~zero de E[pts]) ⇒ **se chegar atrás na final, usar
  sempre**. Mas o **poder de virar** é limitado pelo que UMA final (×4) move em diferencial.
  Base ≈ `1+7,55·log₁₀(1/p)`; final entre fortes (p≈0,10 → base ≈8,5): cravar exato ≈ (8,5+5)×4 ≈
  **54 pts**, só-vencedor ≈ 34, errar vencedor = 0. Swing **diferencial** (você − líder): massa em
  ±0–20; extremos +34 (você vencedor / líder erra) a +54 (você crava / líder zera) são eventos de
  ~1–5% (2–3σ num jogo só). **Limiar:** gap na manhã da final **≤ ~15–20 → a regra decide**;
  ~20–34 → só se cravar e o líder tropeçar (~5–10%); **> ~35 → irrelevante, nenhuma final cobre.**
  **Hoje o gap é −48 (325 vs 373) ⇒ fora do alcance da final.** A virada depende de **erodir ~30
  pts até J102** — não por ousadia (Sistema I não paga risco de placar), mas por (a) **regressão da
  variância de exatos do líder** (ele segue ACIMA do teto do tool, estatisticamente devida) + (b)
  seguir capturando teto (eficiência 90%). Só então a final vira arma. Reavaliar o gap a cada
  rodada; jogos de maior alavancagem restantes (peso × coin-flip): **final J104 (×4)** ≫ J94/J92
  (R16), J99 (QF), J88 (R32, hoje).
- **Palpite de 90' do mata-mata nunca sai empate (ENG-32, 01/07):** o E[pts] puro apostava 0×0/1×1
  em ~25% dos KO e zerava quando o jogo era decidido no tempo normal (te custou J73 e J79). Medido
  nos backtests: a vantagem de E[pts] do empate era ~0,04/jogo
  (e apoiada em super-estimar empate no KO), contra **+70 pts realizados** trocando pelo melhor
  placar com vencedor. Agora as picks de KO já saem com vencedor
  — **não contradiz a decisão de `risk`**
  (aqui reduz variância a custo de E[pts] ~nulo, não troca E[pts] por variância). Jogos de KO já
  disputados (J73–J79) não mudam: você seguiu o tool antigo (0×0); os snapshots arquivados preservam
  aquilo, então a eficiência passada continua justa. **Exceção deliberada (02/07):** o modo endgame
  `--pool-behind` (empate, ENG-39/40) força o empate — só na final e só atrás; a validação do
  ENG-32 foi agregada em R32/R16, onde a regra segue valendo.

## Histórico

- 2026-07-08
  — **Eficiência (96 jogos): 102,6% do teto do tool** (seus 397 / teto 387, as-of risk 0.5 +
  blend 0.8) — **primeira vez acima de 100% de forma mais folgada**, indicando sorte de placar
  exato a seu favor, não só execução em linha. **Caiu para 17º** (de 13º) apesar da eficiência
  subir — sinal de que o resto do bolão também acertou bem as oitavas (J95/96), não que você
  jogou pior. Teto teórico (oráculo) 1045; captura do tool sobre o teórico 37,0% (resto é ruído
  irredutível). **Líder 455 está ACIMA do teto do tool (387)** — nem seguir o tool à risca o
  alcançaria hoje; pegou variância de exatos a favor (regride), não estratégia superior. Gap
  parcialmente **ruído de reconstrução**: no subconjunto arquivado (66 jogos) o as-of
  reconstruído (230) fica +31 acima do snapshot real (199); 30 jogos (R32/R16,
  J1–4/25–35/73–90) sem snapshot → teto não verificável.
- 2026-07-07
  — **Eficiência (94 jogos): 100,5% do teto do tool** (seus 385 / teto 383, as-of risk 0.5 + blend
  0.8). Subiu para **13º** no ranking. Teto teórico (oráculo) 1011; captura do tool sobre o
  teórico 37,9% (resto é ruído irredutível). **Líder 443 está ACIMA do teto do tool (383)** — nem
  seguir o tool à risca o alcançaria hoje; pegou variância de exatos a favor (regride), não
  estratégia superior. Gap parcialmente **ruído de reconstrução**: no subconjunto arquivado (64
  jogos) o as-of reconstruído (226) fica +31 acima do snapshot real (195); 30 jogos (R32/R16,
  J1–4/25–35/73–90) sem snapshot → teto não verificável. Execução em linha com o teto do tool
  (dentro do ruído de ±1/jogo da base).
- 2026-07-06
  — **Eficiência (92 jogos): 100,5% do teto do tool** (seus 375 / teto 373, as-of risk 0.5 + blend
  0.8). Teto teórico (oráculo) 975; captura do tool sobre o teórico 38,3% (resto é ruído
  irredutível). **Líder 433 está ACIMA do teto do tool (373)** — nem seguir o tool à risca o
  alcançaria hoje; pegou variância de exatos a favor (regride), não estratégia superior. Gap
  parcialmente **ruído de reconstrução**: no subconjunto arquivado (62 jogos) o as-of reconstruído
  (216) fica +31 acima do snapshot real (185); 30 jogos (R32/R16, J1–4/25–35/73–90) sem snapshot →
  teto não verificável. Execução em linha com o teto do tool (dentro do ruído de ±1/jogo da base).
- 2026-07-05
  — **Eficiência (90 jogos): 89,9% do teto do tool** (seus 363 / teto 404, as-of risk 0.5 + blend
  0.8). Teto teórico (oráculo) 933; captura do tool sobre o teórico 43,3% (resto é ruído
  irredutível). **Líder 421 está ACIMA do teto do tool (404)** — nem seguir o tool à risca o
  alcançaria hoje; pegou variância de exatos a favor (regride), não estratégia superior. Gap ao teto
  parcialmente **ruído de reconstrução**: no subconjunto arquivado (60 jogos) o as-of reconstruído
  (204) fica +31 acima do snapshot real (173); 30 jogos (todo R32/R16 recente, J73–J90) sem snapshot
  → teto não verificável. Execução sólida, sem erro sistemático. Manter `predict --archive` toda
  manhã torna a métrica exata.
  — **ENG-32 revalidado com dado vivo (não muda nada) + ENG-45 aberto.** Hipótese: os 0-pts recentes
  no KO (J74/J75/J88, empates nos 90') seriam vazamento do `forbid_draw`. Backtest as-of nos 18
  jogos de KO da edição (`scratchpad/eng32_backtest.py`): **ΔE[pts] ex-ante permitir-empate vs
  forbid = +0,8 total (+0,04/jogo)** — idêntico ao veredito histórico do ENG-32 (64 jogos,
  +0,04/jogo). O
  realizado deu +34 a favor de permitir empate, MAS vem de só **2 jogos divergentes** (J75, J88) que
  por acaso empataram — variância pura, não sinal. **Veredito: manter `forbid_draw`; os 0-pts são
  variância + teto estruturalmente baixo do KO (coin-flips), não jogada errada.** Achado colateral
  real: J82 gravado 3×2 mas 2×2 nos 90' (gol na ET) — a eficiência pontua o palpite de 90' contra o
  placar-com-ET e **infla o teto** (credita 12 onde daria ~0). Registrado como **ENG-45** (P2).
  — **Eficiência CORRIGIDA para ~100% (não 89,9%) — o teto estava inflado, não a sua jogada.** Os
  fixes de hoje removeram o inchaço do teto: ENG-45 (J82: 404→392) e sobretudo ENG-34, que **congela
  o teto por jogo** preferindo o **snapshot real** da manhã (o que o tool de fato mostrou) à
  reconstrução volátil — teto foi a **361**, e seus **363 ≈ o teto**. Confirma o que a skill já
  alertava: como você ajusta os palpites toda manhã (= segue o tool), o "gap" era **ruído de
  reconstrução**, não execução. **Sem mudança de estratégia:** `risk 0.5` + `blend 0.8` +
  `forbid_draw` seguem (ENG-32 revalidado). O líder (421) continua acima do teto — variância de
  exatos a favor dele, que regride.
  — **Ferramentas novas que ajudam a campanha daqui pra frente:** (a) **teto estável** (ENG-34): a
  eficiência não oscila mais entre rodagens (o mesmo dia já deu 103% e 88% só pelo refit); mudança
  vira **drift reportado**, não silenciosa. (b) **vigia de staleness** (ENG-43): `predict`/`status`
  avisam se um resultado disputado não entrou no ajuste (a falha que já mordeu em jun/2026). (c) o
  teto de KO passa a usar o snapshot real a partir das **quartas** (ENG-46). Backlog de eng. zerado
  (ENG-25 descartado: tabela de 495 combinações não-verificável com as ferramentas; sem impacto na
  2026 — o override já crava a combinação realizada).
- 2026-07-04 (noite, +tarde)
  — **ENG-44: `edition_boost` calibrado → fixado em 1.0 (sem boost); campeão volta a equilibrar.**
  O sweep `blend-track --boost-sweep` (novo) deu Brier as-of **monotônico crescente** em boost
  (1.0=0,4707 → 6.0=0,4876 → 12.0=0,5035): boostar a forma recente **superajusta e piora** a
  previsão. O peso virou config `edition_boost` no `scoring.toml` (antes era constante 6.0 em
  código) e a 2026 foi para **1.0**. **Campeão calibrado: Argentina 22,7%, Espanha 19,7%, França
  12,9%, Brasil 10,8%, Inglaterra 9,2%** — campo equilibrado, sem a volatilidade do 6.0 (que jogava
  Argentina a 12,9% e Espanha a 29,1%). **Este é o número em uso agora.** Config vigente:
  `risk 0.5` + `blend_weight 0.8` + `edition_boost 1.0`.

- 2026-07-04 (noite)
  — **ENG-42: KO passa a alimentar o ajuste com boost — favorita vira para Espanha.** Os jogos de
  mata-mata guardam slots (`W73`) no fixture e escapavam do boost 6.0, chegando ao modelo só pela
  base histórica a peso 1.0. `build_training_frame` agora resolve os slots dos KO disputados
  (`resolve_live_bracket`) e os alimenta boostados, como os de grupo. **Efeito grande:** Espanha
  **29,1%** (era 20,4%), Argentina **12,9%** (era 24,8%) — a vitória apertada da Argentina (3×2
  Cabo Verde) a peso 6 derruba o rating. ⚠️ A virada expôs que **`CURRENT_EDITION_BOOST`=6.0 nunca
  foi calibrado** (aberto ENG-44 para o sweep de Brier); a correção estrutural está certa, mas o
  valor do peso é questão aberta — **ceticismo com os números de campeão até calibrar.**

- 2026-07-04 (tarde)
  — **Bug de realimentação corrigido: o modelo não estava aprendendo com o mata-mata (ENG-41).**
  A `historical_results.csv` estava congelada em 25/06 e os resultados de KO só chegam ao ajuste
  por ela (os jogos de KO no `fixtures.csv` guardam slots `W##`, escapando do boost 6.0 que os
  jogos de grupo levam). Efeito: o modelo palpitava o mata-mata **sem ter ingerido nenhum
  resultado do mata-mata**. Ao atualizar a base + corrigir o **double-count** dos jogos de grupo
  (entravam a peso 7.0 = base 1.0 + fixture 6.0), a favorita ao título caiu **Argentina 31%→24,8%**
  (número honesto; era inflado por só enxergar a fase de grupos) e 3 palpites futuros mudaram
  (**J96, J99, e a final J104: Argentina→Espanha**). Palpites de hoje (J89/J90) e de grupo
  **inalterados**. Também: **J88 adicionado ao `shootouts.csv`** (Egito nos pênaltis, fonte
  canônica) — o relatório agora mostra prorrogação/pênaltis do jogo. Aberto ENG-42 (unificar os
  dois caminhos de realimentação; KO a peso 1.0) e ENG-43 (métrica que vigie ingestão de
  resultados recentes — hoje o silêncio da staleness não acende vermelho nenhum).

- 2026-07-04
  — **16-avos J86–88 sincronizados; eficiência 91,9%.** Entraram J86 Argentina 3×2 Cabo Verde,
  J87 Colômbia 1×0 Gana, J88 Austrália 1×1 Egito (pênaltis, Egito avança) — o tool acertou
  lado/avanço nos três. **Standing: 351 pts, 15º** (líder **409**) ·
  `efficiency.py --my-points 351 --leader 409 --compare-archive`: teto as-of do tool **382**,
  **eficiência 91,9%**. Líder **ACIMA** do teto (409 > 382) ⇒ variância de exatos no KO, não
  estratégia superior (mesmo padrão recorrente). Gap parcialmente ruído de reconstrução (28 jogos
  sem snapshot real; no verificável a reconstrução ficou +5 acima do arquivo). Bônus de KO de J74,
  J75, J88 ainda fora do teto (sem shootout na fonte). Hoje: J89 Canadá×Marrocos (1×2), J90
  Paraguai×França (0×2).

- 2026-07-02 (noite)
  — **ENG-40 fechado: `predict --pool-behind` agora executa a regra de endgame v2.** O flag ganhou
  valor opcional (`empate`|`zebra`, sem valor ⇒ `empate`): o modo empate palpita os 90' da final
  no melhor placar de empate por E[pts] (hoje **0×0**, camadas "vai aos pênaltis" + Argentina) e
  mantém prorrogação/pênaltis/avanço fiéis; SF/3º lugar (peso ×2) não mudam. Zebra preservada como
  opção para a comparação da véspera. Verificado ponta-a-ponta (J104 0×0 com o modo; `out/` vivo
  restaurado fiel em seguida). Some o risco operacional de aplicar o empate à mão no jogo ×4.

- 2026-07-02 (tarde)
  — **Revisão crítica do projeto rendeu 1 bug real + 2 alavancas; regra de endgame revista.**
  (1) **Bug (blend mudo no R16):** `resolve_live_bracket` só propagava vencedor de KO com
  `ko_outcome`, mas jogo decidido nos 90' registrado à mão fica sem o campo (J77/J78/J79) —
  J90/J91/J92 não casavam odds e rodavam **model-only**. Corrigido + `fetch_odds` agora loga
  eventos não casados. Refetch: `odds.csv` 62→**65**; **J91 Brasil×Noruega despencou de 3×0 (85%
  model-only) para 2×0 (mercado ~50%)** — era o palpite mais frágil da lista. (2) **`blend_weight`
  0,6→0,8 com dado (ENG-38):** novo `blend-track --sweep` em 49 jogos deu Brier **monotônico**
  decrescente em w (0,4420 → 0,4100 em w=1,0); 0,8 captura o grosso hedgeando o extremo. (3)
  **Regra de endgame v2 (ENG-39):** política `empate-final` + sensibilidade `--draw-inflate-final`
  no `eng36_pool_sim` (o gerador padrão é o próprio modelo — juiz e parte — e finais empatam ~60%
  nos 90' historicamente vs ~28% no modelo). `empate-final` domina a zebra em todos os geradores
  (baseline: top3 8,4% vs 5,5% a custo zero; histórico 60%: P(#1) 4,9% / top3 14,3% vs 1,2%/3,8%).
  Decisão viva atualizada: **na final, atrás ⇒ empate nos 90' + camadas** (à mão até o ENG-40).
  Standing do dia: 295 pts, 21º, líder 353; eficiência 88,9% (teto 332).

- 2026-07-02
  — **J81 fechado via `sync-results` (82/104); bug de CLI encontrado e corrigido no processo.**
  `sync-results --archive` quebrava com `AttributeError: 'pool_behind'` — o parser de
  `sync-results` nunca ganhou `--pool-behind` (adicionado ao `predict` no ENG-36), mas
  `cmd_sync_results` delega para `cmd_predict`, que lê `args.pool_behind` direto. Corrigido
  (`cli.py`, espelhando o argumento do `predict`); ruff/mypy/pytest verdes (156 testes). Re-rodado
  o sync com sucesso: J81 **EUA 3×1 Bósnia**. Hoje 02/07: R32 continua com J83 Portugal×Croácia,
  J84 Espanha×Áustria, J85 Suíça×Argélia. **Eficiência: 295 pts vs teto as-of 332 = 88,9%**
  (líder 353, ACIMA do teto — variância de exatos no KO, padrão recorrente).

- 2026-07-01 (fim do dia)
  — **J80/J82 fechados (buscados na internet); 285 pts, 21º, eficiência 88,0%.** A fonte do
  `sync-results` ainda não tinha os jogos de hoje; buscados na web e confirmados em ≥2 fontes:
  **J80 Inglaterra 2×1 RD Congo** (Kane 2× no 2º tempo; englandfootball/Olympics/Outlook)
  e **J82 Bélgica 3×2 Senegal na prorrogação**
  (2×2 nos 90', pênalti de Tielemans aos 125'; ESPN/Outlook/Yahoo).
  J82 registrado **3×2 com `ko_outcome` Belgium** — placar inclui prorrogação, convenção
  martj42/SPEC (registrar 2×2 leria como "foi aos pênaltis", errado). Tool acertou os dois lados
  (J80 palpite 1×0 → 8 pts as-of; J82 palpite 2×1 → 12). `blend-track` n=49: blend 0,418 vs modelo
  0,442 (Δ+0,024, segue melhor); empates 20/72, z=+0,74, sem ação. **Eficiência (81 jogos): 88,0%**
  — 285 pts vs teto as-of **324** (`efficiency.py --my-points 285 --leader 337 --compare-archive`).
  Leitura: a queda vs 103,4% NÃO é piora de execução comprovada — o teto saltou +62 com os 9 jogos
  de R32 **todos sem snapshot real** (teto 100% reconstruído, e a reconstrução diverge: Δ+7 medido
  nos 60 verificáveis; peso ×2 do KO amplifica cada divergência). **Líder 337 > teto 324** ⇒
  inalcançável mesmo seguindo o tool à risca; variância de exatos no KO, regride. Caiu 11º→21º:
  exatos alheios no R32 (mesma variância). Oráculo 797; tool captura 40,7%, usuário 35,8%. Ação:
  manter risk 0,5 + blend
  (subir risco não compra ranking — decisão viva), **ajustar palpites na manhã do jogo**
  (captura flips tipo J78) e manter o `--archive` diário para a eficiência ficar verificável em vez
  de reconstruída.

- 2026-07-01 — **J79 México 2×0 Equador fechado (79/104).** Quiñones 22', Jiménez 31' — decidido nos
  90', México avança (1ª vitória do México em KO em 40 anos). Buscado na internet e confirmado em ≥2
  fontes (FIFA/ESPN/Yahoo/CBS); registrado na ordem do fixture (mandante México). O tool acertou
  o **lado** (avança México) mas o palpite de 90' era 0×0 → pegou a faixa de resultado, não o exato.
  Título praticamente estável: Argentina 28,2%, Espanha 19,9%, França 14,9%, Brasil 13,1%, Portugal
  6,2%. Hoje 01/07: J80–J82. **Eficiência (79 jogos): 103,4%** — seus **271 pts** (líder **327**) vs
  teto as-of do tool **262** (`efficiency.py --my-points 271 --leader 327 --compare-archive`).
  **J79 zerou para você E para o tool:** o palpite de 90' era **0×0**
  (empate, avançar nos pênaltis), mas o México ganhou **2×0** nos 90' → o 0×0 erra o resultado e faz
  0. Como o **teto também não credita J79** (o tool zerou igual), a eficiência fica intacta e o
  zero **não é execução** — é o palpite de KO 0×0 sendo frágil a decisões no tempo normal (mesmo
  padrão de J73 Canadá 0×1; o E[pts] escolhe 0×0 quando espera pênaltis, mas paga 0 quando o
  favorito resolve nos 90'). **Líder 327 está +65 ACIMA do teto** ⇒ variância de exatos no KO
  (peso ×2 amplifica), não estratégia — regride. Oráculo 765; tool captura 34,2%, usuário 35,4%.

- 2026-06-30 (fim do dia)
  — **J77/J78 fechados (buscados na internet); subiu 17º→11º, eficiência 103,4%.** Dois jogos de
  hoje terminaram e foram buscados na web
  (a fonte do `sync-results` já tinha 76; estes dois ainda não): **J77 França 3×0 Suécia**
  (Mbappé 45'/74', Barcola 53' — confirmado FIFA + ESPN) e **J78 Costa do Marfim 1×2 Noruega**
  (Nusa, empate de Amad Diallo 74', Haaland 86' — Yahoo + ESPN). Ambos decididos nos 90',
  registrados via `record` (ordem do fixture = oficial: mandante França / Costa do Marfim).
  **O tool acertou os dois lados** (J77 palpite 3×0 cravado; J78 mudou para "avança Noruega" após
  ENG-28 destravar o blend no KO — acertou). **Standing: 271 pts, 11º/60** (era 17º), líder **313**.
  `efficiency.py --my-points 271 --leader 313 --compare-archive`: **teto do tool as-of = 262**; seus
  271 = **103,4%**
  (acima do teto; inclui ruído de reconstrução Δ+7 nos 60 verificáveis + 18 jogos sem snapshot).
  **Líder 313 está +51 ACIMA do teto** ⇒ variância de exatos no KO (peso ×2), não estratégia —
  regride. Oráculo 747; tool captura 35,1%, usuário 36,3%. Execução segue problema zero.
  **Tela "Pontos por Jogo" confirmou:** J77 pagou **14** e J78 **16**
  (o usuário jogou os exatos do tool, 3×0 e 1×2 — opção (a)); minha estimativa de teto dera 16/18,
  ~2 alto por jogo no KO = a folga de base inobservável (ENG-24/26, ×2 no peso de fase), **não**
  vazamento. Ou seja: no KO o teto as-of real é um pouco menor que o estimado e a eficiência é ainda
  mais colada ao teto. **Processo:** o `fetch_odds` gravou odds inválidas em J77 (home=1.0) →
  removida a linha do `odds.csv` (gitignored; J77 cai para model-only). Falta J79 México×Equador
  (ainda não jogado).

- 2026-06-30 (eficiência)
  — **Caiu para 17º/60 (241 pts, líder 299), MAS execução no teto (105,7%).** Medido por
  `efficiency.py --my-points 241 --leader 299 --compare-archive`
  (já com ENG-27: peso de fase ×2 no KO + bônus de pênaltis onde a fonte confirma).
  **Teto do tool as-of = 228**; seus 241 = **105,7%** (acima do teto — inclui os +6 de pênaltis de
  J74/J75 que o teto não credita por latência do martj42, e ruído de reconstrução Δ+7 nos 60
  verificáveis; 16 jogos sem snapshot). **Líder 299 está +71 ACIMA do teto** ⇒ nem seguir o tool à
  risca chegaria perto; é variância de exatos no KO (peso ×2 amplifica: uma cravada = +16 a +30),
  não estratégia superior. **Queda 4º→17º:** J73–J76 zeraram para o usuário e para o tool
  (1×2 errado em empates/zebras), enquanto o campo cravou exatos. **Veredito:** execução é o
  problema **zero**; o caminho é líder regredir (cravar exato é ~7–10%, insustentável a +71) +
  variância natural nos ~28 jogos restantes. Risco já descartado como alavanca (entrada 29/06).
  Oráculo 713; tool captura 32% (resto é ruído irredutível), usuário 33,8%.

- 2026-06-30 — **R32 de 29/06 fechado: duas zebras de potência (Paraguai e Marrocos avançam).**
  J74 Alemanha **1×1** Paraguai → Paraguai nos pênaltis; J75 Holanda **1×1** Marrocos → Marrocos;
  J76 Brasil **2×1** Japão → Brasil. 76 jogos disputados. O tool acertou o lado de Brasil; Alemanha
  e Holanda eram favoritas no modelo (não captura má fase/upset de potência — limitação conhecida).
  blend-track inalterado (n=49; R32 fora do feed de odds). **Título: Argentina 29,8%, Espanha 19,9%,
  França 13,0%, Brasil 12,3% (salta — bracket abriu), Portugal 7,6%.** Standing do usuário não
  reconsultado nesta sessão (pedido foi só atualizar/mostrar a rodada). Hoje 30/06:
  J77 França×Suécia, J78 Costa do Marfim×Noruega, J79 México×Equador.

- 2026-06-29 — **J73 fechado (Canadá venceu nos 90'); caí para 4º. Cenário de risco rodado: NÃO
  subir o risco.** Resultado: África do Sul **0×1 Canadá** (Canadá 1–0 no tempo normal). O tool
  acertou o **classificado** (Canadá, as-of 28/06) mas o palpite de 90' era **0×0** indo à
  prorrogação → fez **0 pts** no jogo. **Standing: 235 pts, 4º de 60** (era 2º);
  **líder saltou para 275 (+16 num jogo só** = cravou o Canadá 1–0 + bônus de KO). Eficiência
  segue **103,1%** (teto as-of 228) — execução intacta, o gap é variância.
  **Líder está 47 pts ACIMA do teto do tool** ⇒ inalcançável por estratégia; surfa exatos (regride).
  **Cenário risk 0.5 vs alto nos 15 R32 restantes (J74–J88), script `scratchpad/scenario_risk.py`:**
  risk 0.5 → ΣE[pts] **42,4**, Σ P(exato) **2,30**, SD-carteira **11,9**; risk 0.65 → 38,4
  (**−4,0**), P(exato) 2,32, SD 14,8; risk 0.8 → 36,1 (**−6,3**), P(exato) **2,24** (cai!), SD 15,4.
  **Veredito: o botão de risco é a ferramenta errada** — (a) NÃO aumenta a chance de cravar exato
  (Σ P(exato) fica ~2,3 e até cai), só empurra palpites para empates 1×1/0×0; (b) a variância que
  compra é paga **1:1 em E[pts]**, então a caçada dos 40 pts continua a **~2,4 σ** com ou sem risco.
  O que o líder fez (cravar exato não-modal) o risco **não replica**. Mantido **`risk 0.5`**;
  caminho ao título = líder regredir + variância natural dos ~31 jogos restantes, não sabotar o
  E[pts]. Reafirma a decisão viva de risco com quantificação específica do cenário de recuperação.

- 2026-06-28 (correção) — **Bracket do R32 estava com 3 confrontos errados; corrigido (ENG-25).** O
  casamento por restrição dos terceiros (`_assign_thirds`) escolhia um emparelhamento
  válido **porém não-oficial** — divergia da tabela Annex C da FIFA em J74/J77/J81
  (Bósnia/Paraguai/Suécia rodados). Verificado contra 2 fontes oficiais
  (bracket Yahoo/Sky + Wikipedia "row 67"). Correção data-driven: override
  `[group_stage.third_allocation]` no `tournament.toml`
  (oficial: 1E×3D, 1I×3F, 1D×3B, +5 que já batiam), aplicado quando o conjunto de grupos casa. Os 16
  confrontos do R32 agora corretos. Tabela completa de 495 combinações virou item de backlog
  (ENG-25). Repalpitado e re-arquivado o snapshot de hoje. Probabilidades pós-correção: Argentina
  29,8%, Espanha 19,9%, França 11,5%, Brasil 8,8%.

- 2026-06-28 — **Fase de grupos completa (J67–J72 fechados); 72 jogos disputados. Começa o R32.**
  Sincronização pela fonte pública (não foi preciso registro manual desta vez). blend-track n=49:
  Brier modelo 0,442 vs blend 0,418 (Δ+0,024, blend à frente). Empates 20/72 (28%) z=+0,74 —
  variância. **Argentina 29,0%** no título, **Espanha 21,2%** (encosta), França 10,7%, Brasil 8,1%,
  Portugal 7,5%. Chaveamento previsto: campeão **Argentina** (bate Espanha na final, 0×0/pênaltis);
  Brasil cai na semi para a Argentina (J102). Hoje (28/06) abre o mata-mata com
  J73 (África do Sul × Canadá; palpite 0×0, Canadá avança). **Eficiência (72 jogos): 103,1%** —
  seus **235 pts** (2º) vs teto as-of **228** (3,17/jogo). >100% = captura cheia do blend +
  subestimação do teto reconstruído
  (Δ+7 nos 60 verificáveis; 12 jogos sem snapshot: J1–J4, J25–J30, J32, J35).
  **Líder 259 está 31 pts ACIMA do teto** ⇒ variância de exatos a favor dele (regride), não erro de
  execução seu. Oráculo (cravar tudo) = 639; tool perfeito captura só 35,7%
  (resto é ruído irredutível). Sua captura do teórico: 36,8% (à frente do tool). Alavanca segue
  acurácia (blend) + pesos 2×/4× do mata-mata, não ousadia.

- 2026-06-27 — **Rodada J61–J66 fechada (grupos G/H/I); 66 jogos disputados.** Resultados buscados
  na internet (a fonte do `sync-results` ainda estava em 60) e registrados à mão: J61 Cabo Verde 0×0
  Arábia Saudita, J62 Egito 1×1 Irã, J63 Nova Zelândia 1×5 Bélgica, J64 **Noruega 1×4 França**,
  J65 Senegal 5×0 Iraque, J66 Uruguai 0×1 Espanha. **5/6 lados certos**; único furo no empate do
  Cabo Verde (palpite 1×0). blend-track n=43: Brier modelo 0,443 vs blend 0,425
  (Δ+0,019, blend à frente). Empates 18/66 (27%) z=+0,62 — variância. **Espanha salta a 18,9%** no
  título após vencer o grupo H; Argentina 43,5%, França sobe ao top-3 (9,7%), Brasil 7,8%. Hoje
  (27/06) fecham os grupos J/K/L (J67–J72), ainda não jogados. **Eficiência (66 jogos): 103,5%** —
  seus **209 pts** vs teto as-of **202** (3,06/jogo). Acima de 100% = captura cheia do blend
  (você ajusta toda manhã) + subestimação do teto reconstruído (base 1–13 usa prob. interna do app
  inobservável, ±~1/jogo; +7 de ruído de reconstrução nos 54 verificáveis; 12 jogos sem snapshot:
  J1–J4, J25–J30, J32, J35). **Líder 234 está 32 pts ACIMA do teto** ⇒ nem seguir o tool à risca
  alcançaria hoje; é variância de exatos a favor dele (regride), não estratégia superior. Alavanca
  segue sendo acurácia (blend), não ousadia. **Processo:** o J64 foi registrado invertido
  (Noruega 4×1) de uma fonte só e corrigido em seguida — placar errado contamina o refit e o
  chaveamento (mudou o palpite de J78). **Lição: no registro manual (fonte oficial indisponível),
  confirmar o placar em ≥2 fontes antes de
  `record`** — não vale para o `sync-results`, cuja fonte canônica já é a referência.

- 2026-06-26
  — **BUG DE PONTUAÇÃO ENCONTRADO E CORRIGIDO (ENG-23) — retrata a narrativa de eficiência.** As
  telas "Pontos por Jogo" do app revelaram que meu `scoring.points` **somava** os bônus de placar,
  mas o app dá só o **maior nível** (hierárquico): exato +5 > gols do vencedor +3 > saldo +2 > gols
  do perdedor +1. O bug inflava todo placar cravado (Curaçao 0×2 valia 7 no app, eu calculava 13).
  **Validação:** 12 jogos (J43–J54) confrontados com o app — 8 cravam, 4 erram por ≤1 só na base
  (nossa probabilidade ≠ a do app). **Consequências:** (1) **a eficiência estava inflada** — os
  registros de 24/06 (88,8%) e 25/06 (88,4%) e o "você vazou 7 pts em J55–J60" estão **ERRADOS**;
  sua eficiência real é **~100%**: você seguiu o blend e pontuou o que o app deu.
  **Não há vazamento.** (2) O bug **enviesava o `best_prediction` contra empates**
  (jogo decidido somava mais bônus) — explica o "modelo nunca palpita empate" do [ENG-22].
  Corrigido, o modelo **volta a palpitar empates** (hoje J61/J62 saem 0×0 ⚡), relevante numa Copa
  empate-pesada. Repalpitei tudo com o scorer corrigido. Docs
  (SPEC §4, GLOSSARIO, PRD, AGENTS, scoring.toml) atualizadas de "cumulativos" → "hierárquicos".
  **Pendência:** base ~1pt baixa em alguns jogos (probs nossas vs app) — menor, separado, não é o
  bug. **Re-arquivo (fim do dia):** ao trabalhar o ENG-12 rodei `fetch-data`, que refrescou a base
  histórica com resultados mais recentes; o snapshot 26/06 foi **re-arquivado** sobre essa base.
  Mudou 1 pick de hoje (J61 Cabo Verde 0×0→1×0, quase-empate) e alguns de rodadas futuras (J69, J76)
  — ajustes de borda.

- 2026-06-26 — **Rodada J55–J60 fechada; 60 jogos disputados.** Grupos D/E/F encerrados. blend-track
  n=37: Brier modelo 0,477 vs blend 0,446 (Δ+0,031, blend à frente, delta cresce). Empates 16/60
  (27%) z=+0,45 — variância. Argentina 43,0% no título; Espanha 15,8%, Brasil 7,7%. Estado:
  **189 pts, 5º**; líder (Fernanda Polido) 203. Hoje (26/06) fecham os grupos G/H/I (J61–J66).

- 2026-06-25 — **Rodada J49–J54 fechada; 54 jogos disputados.** Grupos A, B e C encerrados.
  blend-track n=31: Brier modelo 0,426 vs blend 0,410 (Δ+0,015, blend à frente). Empates 14/54 (26%)
  z=+0,22 — variância (regime normalizou para ~25%). **Argentina 42,7%** no título; Espanha 15,5%,
  Brasil sobe ao top-3 (7,8%). Hoje (25/06) fecham os grupos D/E/F (J55–J60).
  **Eficiência: 88,4% (168 reais vs teto 190 do tool).** Ritmo mantido vs 24/06 (88,8%): +25 pts em
  J49–J54 contra +29 de teto (~86% de captura na rodada). Teto subiu 161→190 (3,52/jogo) — tool foi
  bem nos 6 jogos novos, o que **levanta a régua**. Caveat de sempre: 12/54 jogos com teto
  reconstruído/não verificável (ver entrada 24/06). O líder de ontem (173) caiu **abaixo** do teto
  novo (190) ⇒ alcançável seguindo o tool (número atual do líder não confirmado).

- 2026-06-24 — **Eficiência ~88% (143 reais vs teto 161 do tool), MAS o teto é parcialmente não
  verificável.** Usuário em **14º com 143 pts**; líder do grupo **173**. Medido por
  `scripts/efficiency.py` (novo): reconstrói a previsão **as-of** de cada manhã
  (mesmo caminho do `predict --as-of`, config real `risk 0.5` + blend `0.6`) e pontua pelo Sistema I
  → teto **161 pts** (3,35/jogo). Usuário diz **ajustar os palpites toda manhã**
  (raramente à noite), ou seja, segue o tool — então o gap **não é "má jogada"**. O
  `--compare-archive` localiza a incerteza: dos 48 jogos, **36 têm snapshot REAL arquivado**
  (a partir de 13/06) e **12 não** (J1–J4, J25–J30, J32, J35) — e esses 12 contêm justamente as
  cravadas de alto valor (J27=14, J30=14, J1=13 ≈ 41 pts), com
  teto **100% reconstruído / não verificável**. Pior:
  **mesmo onde há arquivo, a reconstrução escorrega** — nos 36 jogos verificáveis o tool real
  marcou **103** vs **100** do as-of (Δ−3; divergências em J5/J7/J17/J24 por drift de odds/refit).
  **Conclusão honesta:** "88,8%" repousa sobre um teto ~40% sintético nas partidas que mais pontuam;
  parte do gap é **ruído de reconstrução**, não execução. **Correção:** manter
  o **arquivo da run da manhã completo** (`predict --archive` todo dia) — aí eficiência = seus
  pontos vs `scored(palpite arquivado)`, sem reconstrução. **Ponto que se mantém:** o líder (173)
  está **ACIMA** do teto (161; 164 com arquivo) — nem seguir o tool à risca colocaria em 1º hoje;
  ele pegou variância de exatos a favor (regride no esperado). Reafirma a decisão viva: alavanca é
  acurácia/adesão (+ peso 2× do mata-mata amplificando), não ousadia.

- 2026-06-24 — **Rodada J45–J48 fechada; 48 jogos disputados.** Grupos K e L encerrados. blend-track
  n=25: Brier modelo 0,424 vs blend 0,415 (Δ+0,010, blend à frente). Empates 14/48 (29%) z=+0,74 —
  variância. **Argentina 44,0%** no título; Espanha 16,3%, Portugal sobe ao top-4 (5,5%). Hoje
  (24/06) fecham os grupos A/B/C (J49–J54).

- 2026-06-23 — **Rodada J41–J44 fechada; 44 jogos disputados.** Argentina 2×0 Áustria e França 3×0
  Iraque confirmaram os favoritos; Argélia bateu a Jordânia (1×2) e Noruega 3×2 Senegal
  (jogo aberto). blend-track n=21: Brier modelo 0,424 vs blend 0,408 (Δ+0,016, blend à frente).
  Empates 13/44 (30%) z=+0,74 — variância. **Argentina dispara a 45,5%** no título; Espanha 16,9%.
  Hoje (23/06) fecham os grupos K e L (J45–J48).

- 2026-06-22 — **Rodada J37–J40 fechada; 40 jogos disputados.** Os dois zeros foram empates de novo
  (padrão persistente): J37 Bélgica 0×0 Irã e J40 Uruguai 2×2 Cabo Verde (era o único ⚡). Acertamos
  o lado em J38 (Egito 3×1) e J39 (Espanha 4×0 — goleada maior que o 2×0 palpitado). blend-track
  n=17: Brier modelo 0,479 vs blend 0,456 (Δ+0,023, blend à frente). Empates 13/40 (32%) z=+1,06 —
  variância. **Espanha dispara a 18,4%** no título após o 4×0; Argentina 36,2%.

- 2026-06-21 — **Rodada J33–J36 fechada; 36 jogos disputados.** blend-track n=13: Brier modelo 0,506
  vs blend 0,466 (Δ+0,041, blend à frente). Empates 11/36 (31%) z=+0,73 — variância. Argentina
  36,0%, Espanha 9,3%, Brasil 7,0%. Última rodada de grupos começa hoje (J37–J40).

- 2026-06-20 — **J35 Holanda 5×1 Suécia:** acertamos o lado ✅, palpitamos 2×1 (goleada inesperada).
  odds pós-jogo capturadas com valor inválido (1.0) → linha removida do odds.csv; J35 ficará fora do
  blend-track. Favoritos: Argentina 37,1%, Espanha 10,4%, Brasil 7,9%.

- 2026-06-19 (noite) — **Rodada J29–J32 completa.** 2 placares exatos: Brasil 3×0 Haiti ✅ e Escócia
  0×1 Marrocos ✅. EUA 2×0 Austrália: acertamos o lado (1×0 palpitado). Turquia 0×1 Paraguai: zebra —
  palpitamos Turquia 2×1. blend-track n=10: Brier modelo 0,467 vs blend 0,419
  (Δ+0,048, delta crescendo — blend cada vez mais sólido). Argentina sobe para 37,3%; Brasil volta
  ao top-3 (8,5%).

- 2026-06-19 (tarde) — **J30 Escócia 0×1 Marrocos: palpite exato ✅.** blend-track n=7: Brier modelo
  0,441 vs blend 0,416 (Δ+0,025, blend à frente). Regime de empates: 10/29 (34%) z=+1,01 —
  variância, sem ação. Marrocos entra no top-5 de campeão (5,1%); Brasil sai. Palpite de
  Brasil×Haiti atualizado de 2×0 para 3×0 após reajuste do modelo com o novo resultado.

- 2026-06-19 — **Lição dos 28 jogos: empate é a fraqueza, não a falta de placar exato.** Acerto de
  1×2 = **54%** (15/28); zeros = **46%** (13/28), dos quais **10 são empates**
  (10 empates reais, 0 palpitados; em jogo decidido o tool acerta 80–100% o lado). Cravar placar
  (7%, 2/28) dá os maiores pontos por jogo, mas é evento de ~10% que o
  `best_prediction` **já otimiza dentro do EV** — não é alavanca. A alavanca é **não-zerar**
  (acertar o lado), e os zeros são empates — majoritariamente variância
  (ENG-18: modelo calibrado; 36% vs ~26% = ~1,2σ). **Não forçar empates** (baixa o EV); monitorar
  via [ENG-22]. A acurácia (blend, ENG-19) é a única melhoria real.

- 2026-06-17 — **Trade-off de ranking modelado: risco NÃO é alavanca; acurácia é.** Estado: 44 pts,
  32º de 60, líder 80 (gap +36 = +2,4σ; você ≈ mediana do campo, média≈45/σ≈15). (1) Eficiência
  medida = **100%**: os palpites as-of do tool (risk 0.5) renderiam exatamente os mesmos 44 pts —
  não há ganho jogando diferente sobre este modelo; o teto é o do modelo. (2) Botão de risco ≠
  variância: nos 52 jogos de grupo restantes, SD travado em ~33 em todo risco, E[pts] desaba 191→120
  (0.5→0.8), p95 também cai. (3) Simulação de campo (60 jog., 40k sims): P(vencer)~0–1%, P(top-10)
  ~2–13% (depende de quão diverso o campo palpita — chalk trava o ranking), P(melhorar do 32º)~50%.
  Subir SEU risco reduz P(vencer) e P(top-10). (4) Acurácia é a alavanca: +20 pts de edge de EV →
  P(top-10) 8%→42%. **Decisão revisada (ver Decisões vivas): manter 0.5 definitivo; subida = ENG-19
  (blend odds) + variância natural.** Premissa antiga ("subir risco se atrás") era falsa.

- 2026-06-17 — **Diagnóstico de calibração (ENG-18) nos 20 jogos disputados: variância, sem ação.**
  Brier multiclasse 2026 = **0,637** (≈ uniforme 0,667) vs **0,578** nas 4 Copas passadas
  (256 jogos). Causa única: **8 empates em 20 (40%)** contra ~22–25% normal; o modelo previu 24,9%.
  Desvio de ~1,5σ (binomial, p≈0,25, n=20) — elevado mas dentro do ruído, e na direção **oposta** ao
  viés histórico do modelo (que *superestima* empate levemente: 27,9%→22,3% no pooling). O Brier ≈
  uniforme é mecânico: o modelo nunca dá P(empate) > ~37%, então uma amostra empate-pesada o derruba
  por construção. 7 dos 9 erros de 1×2 foram empates.
  **Veredito: modelo bem calibrado de fundo, não mexer.** Achado de bolão (não de modelo):
  `best_prediction` palpitou empate só **1 vez em 84**; numa Copa empate-pesada isso vira zero
  garantido (ver J3). **Gatilho:** se os empates seguirem agrupando até o fim dos grupos,
  reconsiderar risco/estratégia — não o modelo.

- 2026-06-13 — **Decisão de risco reafirmada (0.5)** após recalibração do motor (ENG-14: a régua de
  pontos do app é logarítmica, não potência — `base = 1 + 7,55·log10(1/p)`; `risk` desacoplado para
  um tilt só na escolha). Efeito nos palpites de hoje a `0.5`: **nenhum** (4 jogos idênticos); a
  `0.7` cravaria as zebras de J5 (Turquia) e J7 (Haiti). Recomendação e decisão: manter `0.5`
  (cedo demais para variância; ver Decisões vivas).

- 2026-06-13 — Usuário em **25º com 14 pts** após 4 jogos. Análise: palpites do modelo (risk 0.5)
  renderiam ~16,4 pts nesses jogos — usuário está colado no ótimo; o "déficit" é variância, não
  estratégia. Zeraram J3 (Canadá 1×1, favorito de 74% empatou) e
  J4 (EUA 4×1, modelo foi de Paraguai/40%). Lição: no Sistema I, errar o 1×2 zera o jogo; eficiência
  mora em acertar o lado, não o placar exato. Decisão: manter risk 0.5 por ora (ver gatilho acima).

- 2026-06-12 — Criado este diário como memória de campanha agnóstica a LLM, referenciado no
  `AGENTS.md`. Estado inicial: nenhum jogo disputado registrado, configuração padrão.
