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

## Estado atual (atualizado em 2026-07-02)

- **82 de 104 jogos disputados (J1–J82).** J81 EUA 3×1 Bósnia fechado via `sync-results`. Hoje
  (02/07): **J83 Portugal×Croácia, J84 Espanha×Áustria, J85 Suíça×Argélia** (ainda pendentes,
  palpites 2×0/2×0/2×1). **Standing (02/07): 295 pts, 21º** (líder **353**) ·
  **eficiência 88,9%** (teto as-of do tool 332;
  `efficiency.py --my-points 295 --leader 353 --compare-archive`). Líder **ACIMA** do teto de novo
  ⇒ variância de exatos no KO, não estratégia superior (mesmo padrão das entradas anteriores).
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
