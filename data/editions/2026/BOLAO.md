# BOLAO.md — memória de campanha (Copa 2026)

Memória persistente da campanha do bolão, **agnóstica a ferramenta**: qualquer agente (Claude,
Codex, Gemini, …) deve **ler este arquivo no início da sessão** e **atualizá-lo quando uma decisão
de campanha acontecer** (mudança de `risk`, situação no ranking, regra do bolão alterada, etc.).

Registre aqui **só o que não é rederivável** dos dados e do código:
- estado dos jogos → mora em `fixtures.csv` (e `sync-results` reconstrói da internet);
- palpites vigentes → `out/palpites-2026.{csv,md,html}` (regeneráveis com `predict`);
- decisões e contexto humano da campanha → **aqui**.

Use datas absolutas (AAAA-MM-DD). Entradas novas no topo do histórico.

## Estado atual (atualizado em 2026-06-30)

- **76 de 104 jogos disputados (J1–J76).** Fase de grupos completa + J73–J76 do mata-mata
  sincronizados pela fonte pública do `sync-results`. **16-avos (R32)** em andamento: hoje
  30/06 são **J77 França × Suécia**, **J78 Costa do Marfim × Noruega** e **J79 México × Equador**; o
  resto do R32 vai até 03/07.
- **Ontem (29/06): duas zebras no R32.** J74 Alemanha **1×1** Paraguai → **Paraguai avança** nos
  pênaltis (eliminou a Alemanha); J75 Holanda **1×1** Marrocos → **Marrocos avança** (eliminou a
  Holanda); J76 Brasil **2×1** Japão → **Brasil avança**. O tool pegou o lado do Brasil; as duas
  zebras de potência eram improváveis no modelo (favorece quem vem bem).
- **Standing: 17º de 60 · 241 pts** (líder **299**) · **eficiência 105,7%** (teto as-of 228). Caiu de
  4º→17º com o R32: J73–J76 zeraram para o usuário **e para o tool** (empates/zebras, 1×2 errado), e o
  campo cravou exatos de KO (peso ×2 → +16 a +30 num jogo). **Líder está +71 ACIMA do teto do tool** ⇒
  inalcançável por estratégia, é variância de exatos (regride). Execução intacta (>100%: pegou os +6 de
  pênaltis que o teto nem credita por latência). Detalhe na entrada 2026-06-30 do Histórico.
- **`blend-track` n=49:** Brier modelo **0,442** vs blend **0,418** — Δ=**+0,024**; blend segue
  melhor. Regime de empates: 20/72 (28%) z=+0,74 — variância, sem ação.
- **Blend AGORA cobre o mata-mata (ENG-28, 30/06):** o `fetch_odds` só casava jogos de grupo — o
  blend estava **desligado em todos os 31 jogos de KO (peso 2×/4×)**. Corrigido: resolve o bracket
  pelos resultados reais e casa os confrontos de KO definidos. `odds.csv` foi de 49→**62 jogos** (+13
  KO). Efeito imediato: **J78 mudou de "avança Costa do Marfim" para "avança Noruega"** (mercado tem
  Noruega favorita, 2.17). Os palpites de KO agora saem blendados; a sim de campeão segue DC-only.
- Favorito ao título (30/06): **Argentina (29,8%)**; Espanha **19,9%**, França 13,0%, **Brasil 12,3%**
  (sobe forte — bracket abriu com Alemanha/Holanda fora), Portugal 7,6%.
- **Bracket R32 corrigido (ENG-25, 28/06):** a alocação dos terceiros divergia da tabela oficial da
  FIFA — J74/J77/J81 saíam com Bósnia/Paraguai/Suécia rodados. Cravada a alocação oficial (row 67,
  grupos B/D/E/F/I/J/K/L) em `tournament.toml`. Agora: J74 Alemanha×**Paraguai**, J77 França×**Suécia**,
  J81 EUA×**Bósnia**. Os 16 confrontos batem com o oficial (Yahoo/Sky/Wikipedia).
- **Config em uso:** `risk 0.5` + `blend_weight 0.6` (blend com odds **ATIVO** — ENG-19). Scorer
  hierárquico (ENG-23). Admin do bolão usa Sistema I sem customização. **Rotina por rodada e formato
  do `odds.csv`: no README** (`fetch_odds.py` → `predict` → `blend-track`); a chave da The Odds API
  vive no `.env`. Odds em 30/06: **62 jogos** no `odds.csv` (49 grupo + 13 KO, após ENG-28 destravar o
  casamento do mata-mata).

## Decisões vivas

- `risk = 0.5` **definitivo** — ótimo para a média **e** para o ranking. O botão de risco **não é
  instrumento de variância** neste sistema de pontos: subir o risco baixa o E[pts] sem aumentar o SD
  e, na simulação de campo, **reduz** P(vencer)/P(top-10) — inclusive no mata-mata (pesos 2×/4×).
  **A única alavanca de ranking é acurácia (ENG-19), não ousadia.** Substitui o gatilho antigo
  "subir risco se atrás" (premissa falsa). Modelagem completa (campo de 60, KO, números) na entrada
  **2026-06-17** do Histórico.
- Execução **sob demanda**: o usuário prefere rodar os comandos manualmente; não propor
  cron/agendamento.

## Histórico

- 2026-06-30 (eficiência) — **Caiu para 17º/60 (241 pts, líder 299), MAS execução no teto (105,7%).**
  Medido por `efficiency.py --my-points 241 --leader 299 --compare-archive` (já com ENG-27: peso de fase
  ×2 no KO + bônus de pênaltis onde a fonte confirma). **Teto do tool as-of = 228**; seus 241 = **105,7%**
  (acima do teto — inclui os +6 de pênaltis de J74/J75 que o teto não credita por latência do martj42, e
  ruído de reconstrução Δ+7 nos 60 verificáveis; 16 jogos sem snapshot). **Líder 299 está +71 ACIMA do
  teto** ⇒ nem seguir o tool à risca chegaria perto; é variância de exatos no KO (peso ×2 amplifica: uma
  cravada = +16 a +30), não estratégia superior. **Queda 4º→17º:** J73–J76 zeraram para o usuário e para
  o tool (1×2 errado em empates/zebras), enquanto o campo cravou exatos. **Veredito:** execução é o
  problema **zero**; o caminho é líder regredir (cravar exato é ~7–10%, insustentável a +71) + variância
  natural nos ~28 jogos restantes. Risco já descartado como alavanca (entrada 29/06). Oráculo 713; tool
  captura 32% (resto é ruído irredutível), usuário 33,8%.

- 2026-06-30 — **R32 de 29/06 fechado: duas zebras de potência (Paraguai e Marrocos avançam).** J74
  Alemanha **1×1** Paraguai → Paraguai nos pênaltis; J75 Holanda **1×1** Marrocos → Marrocos; J76
  Brasil **2×1** Japão → Brasil. 76 jogos disputados. O tool acertou o lado de Brasil; Alemanha e
  Holanda eram favoritas no modelo (não captura má fase/upset de potência — limitação conhecida).
  blend-track inalterado (n=49; R32 fora do feed de odds). **Título: Argentina 29,8%, Espanha 19,9%,
  França 13,0%, Brasil 12,3% (salta — bracket abriu), Portugal 7,6%.** Standing do usuário não
  reconsultado nesta sessão (pedido foi só atualizar/mostrar a rodada). Hoje 30/06: J77 França×Suécia,
  J78 Costa do Marfim×Noruega, J79 México×Equador.

- 2026-06-29 — **J73 fechado (Canadá venceu nos 90'); caí para 4º. Cenário de risco rodado: NÃO subir
  o risco.** Resultado: África do Sul **0×1 Canadá** (Canadá 1–0 no tempo normal). O tool acertou o
  **classificado** (Canadá, as-of 28/06) mas o palpite de 90' era **0×0** indo à prorrogação → fez **0
  pts** no jogo. **Standing: 235 pts, 4º de 60** (era 2º); **líder saltou para 275 (+16 num jogo só** =
  cravou o Canadá 1–0 + bônus de KO). Eficiência segue **103,1%** (teto as-of 228) — execução intacta, o
  gap é variância. **Líder está 47 pts ACIMA do teto do tool** ⇒ inalcançável por estratégia; surfa
  exatos (regride). **Cenário risk 0.5 vs alto nos 15 R32 restantes (J74–J88), script
  `scratchpad/scenario_risk.py`:** risk 0.5 → ΣE[pts] **42,4**, Σ P(exato) **2,30**, SD-carteira **11,9**;
  risk 0.65 → 38,4 (**−4,0**), P(exato) 2,32, SD 14,8; risk 0.8 → 36,1 (**−6,3**), P(exato) **2,24** (cai!),
  SD 15,4. **Veredito: o botão de risco é a ferramenta errada** — (a) NÃO aumenta a chance de cravar
  exato (Σ P(exato) fica ~2,3 e até cai), só empurra palpites para empates 1×1/0×0; (b) a variância que
  compra é paga **1:1 em E[pts]**, então a caçada dos 40 pts continua a **~2,4 σ** com ou sem risco. O que
  o líder fez (cravar exato não-modal) o risco **não replica**. Mantido **`risk 0.5`**; caminho ao título
  = líder regredir + variância natural dos ~31 jogos restantes, não sabotar o E[pts]. Reafirma a decisão
  viva de risco com quantificação específica do cenário de recuperação.

- 2026-06-28 (correção) — **Bracket do R32 estava com 3 confrontos errados; corrigido (ENG-25).** O
  casamento por restrição dos terceiros (`_assign_thirds`) escolhia um emparelhamento válido **porém
  não-oficial** — divergia da tabela Annex C da FIFA em J74/J77/J81 (Bósnia/Paraguai/Suécia rodados).
  Verificado contra 2 fontes oficiais (bracket Yahoo/Sky + Wikipedia "row 67"). Correção data-driven:
  override `[group_stage.third_allocation]` no `tournament.toml` (oficial: 1E×3D, 1I×3F, 1D×3B, +5 que
  já batiam), aplicado quando o conjunto de grupos casa. Os 16 confrontos do R32 agora corretos.
  Tabela completa de 495 combinações virou item de backlog (ENG-25). Repalpitado e re-arquivado o
  snapshot de hoje. Probabilidades pós-correção: Argentina 29,8%, Espanha 19,9%, França 11,5%,
  Brasil 8,8%.

- 2026-06-28 — **Fase de grupos completa (J67–J72 fechados); 72 jogos disputados. Começa o R32.**
  Sincronização pela fonte pública (não foi preciso registro manual desta vez). blend-track n=49:
  Brier modelo 0,442 vs blend 0,418 (Δ+0,024, blend à frente). Empates 20/72 (28%) z=+0,74 —
  variância. **Argentina 29,0%** no título, **Espanha 21,2%** (encosta), França 10,7%, Brasil 8,1%,
  Portugal 7,5%. Chaveamento previsto: campeão **Argentina** (bate Espanha na final, 0×0/pênaltis);
  Brasil cai na semi para a Argentina (J102). Hoje (28/06) abre o mata-mata com J73 (África do Sul ×
  Canadá; palpite 0×0, Canadá avança).
  **Eficiência (72 jogos): 103,1%** — seus **235 pts** (2º) vs teto as-of **228** (3,17/jogo). >100% =
  captura cheia do blend + subestimação do teto reconstruído (Δ+7 nos 60 verificáveis; 12 jogos sem
  snapshot: J1–J4, J25–J30, J32, J35). **Líder 259 está 31 pts ACIMA do teto** ⇒ variância de exatos a
  favor dele (regride), não erro de execução seu. Oráculo (cravar tudo) = 639; tool perfeito captura só
  35,7% (resto é ruído irredutível). Sua captura do teórico: 36,8% (à frente do tool). Alavanca segue
  acurácia (blend) + pesos 2×/4× do mata-mata, não ousadia.

- 2026-06-27 — **Rodada J61–J66 fechada (grupos G/H/I); 66 jogos disputados.** Resultados buscados na
  internet (a fonte do `sync-results` ainda estava em 60) e registrados à mão: J61 Cabo Verde 0×0 Arábia
  Saudita, J62 Egito 1×1 Irã, J63 Nova Zelândia 1×5 Bélgica, J64 **Noruega 1×4 França**, J65 Senegal 5×0
  Iraque, J66 Uruguai 0×1 Espanha. **5/6 lados certos**; único furo no empate do Cabo Verde (palpite 1×0).
  blend-track n=43: Brier modelo 0,443 vs blend 0,425 (Δ+0,019, blend à frente). Empates 18/66 (27%)
  z=+0,62 — variância. **Espanha salta a 18,9%** no título após vencer o grupo H; Argentina 43,5%,
  França sobe ao top-3 (9,7%), Brasil 7,8%. Hoje (27/06) fecham os grupos J/K/L (J67–J72), ainda não
  jogados.
  **Eficiência (66 jogos): 103,5%** — seus **209 pts** vs teto as-of **202** (3,06/jogo). Acima de 100%
  = captura cheia do blend (você ajusta toda manhã) + subestimação do teto reconstruído (base 1–13 usa
  prob. interna do app inobservável, ±~1/jogo; +7 de ruído de reconstrução nos 54 verificáveis; 12 jogos
  sem snapshot: J1–J4, J25–J30, J32, J35). **Líder 234 está 32 pts ACIMA do teto** ⇒ nem seguir o tool
  à risca alcançaria hoje; é variância de exatos a favor dele (regride), não estratégia superior. Alavanca
  segue sendo acurácia (blend), não ousadia. **Processo:** o J64 foi registrado invertido (Noruega 4×1) de uma fonte só e corrigido em
  seguida — placar errado contamina o refit e o chaveamento (mudou o palpite de J78). **Lição: no registro manual
  (fonte oficial indisponível), confirmar o placar em ≥2 fontes antes de `record`** — não vale para o
  `sync-results`, cuja fonte canônica já é a referência.

- 2026-06-26 — **BUG DE PONTUAÇÃO ENCONTRADO E CORRIGIDO (ENG-23) — retrata a narrativa de eficiência.**
  As telas "Pontos por Jogo" do app revelaram que meu `scoring.points` **somava** os bônus de placar,
  mas o app dá só o **maior nível** (hierárquico): exato +5 > gols do vencedor +3 > saldo +2 > gols do
  perdedor +1. O bug inflava todo placar cravado (Curaçao 0×2 valia 7 no app, eu calculava 13).
  **Validação:** 12 jogos (J43–J54) confrontados com o app — 8 cravam, 4 erram por ≤1 só na base
  (nossa probabilidade ≠ a do app). **Consequências:** (1) **a eficiência estava inflada** — os
  registros de 24/06 (88,8%) e 25/06 (88,4%) e o "você vazou 7 pts em J55–J60" estão **ERRADOS**; sua
  eficiência real é **~100%**: você seguiu o blend e pontuou o que o app deu. **Não há vazamento.**
  (2) O bug **enviesava o `best_prediction` contra empates** (jogo decidido somava mais bônus) — explica
  o "modelo nunca palpita empate" do [ENG-22]. Corrigido, o modelo **volta a palpitar empates** (hoje
  J61/J62 saem 0×0 ⚡), relevante numa Copa empate-pesada. Repalpitei tudo com o scorer corrigido.
  Docs (SPEC §4, GLOSSARIO, PRD, AGENTS, scoring.toml) atualizadas de "cumulativos" → "hierárquicos".
  **Pendência:** base ~1pt baixa em alguns jogos (probs nossas vs app) — menor, separado, não é o bug.
  **Re-arquivo (fim do dia):** ao trabalhar o ENG-12 rodei `fetch-data`, que refrescou a base histórica
  com resultados mais recentes; o snapshot 26/06 foi **re-arquivado** sobre essa base. Mudou 1 pick de
  hoje (J61 Cabo Verde 0×0→1×0, quase-empate) e alguns de rodadas futuras (J69, J76) — ajustes de borda.

- 2026-06-26 — **Rodada J55–J60 fechada; 60 jogos disputados.** Grupos D/E/F encerrados. blend-track
  n=37: Brier modelo 0,477 vs blend 0,446 (Δ+0,031, blend à frente, delta cresce). Empates 16/60 (27%)
  z=+0,45 — variância. Argentina 43,0% no título; Espanha 15,8%, Brasil 7,7%. Estado: **189 pts, 5º**;
  líder (Fernanda Polido) 203. Hoje (26/06) fecham os grupos G/H/I (J61–J66).

- 2026-06-25 — **Rodada J49–J54 fechada; 54 jogos disputados.** Grupos A, B e C encerrados.
  blend-track n=31: Brier modelo 0,426 vs blend 0,410 (Δ+0,015, blend à frente). Empates 14/54 (26%)
  z=+0,22 — variância (regime normalizou para ~25%). **Argentina 42,7%** no título; Espanha 15,5%,
  Brasil sobe ao top-3 (7,8%). Hoje (25/06) fecham os grupos D/E/F (J55–J60).
  **Eficiência: 88,4% (168 reais vs teto 190 do tool).** Ritmo mantido vs 24/06 (88,8%): +25 pts
  em J49–J54 contra +29 de teto (~86% de captura na rodada). Teto subiu 161→190 (3,52/jogo) — tool
  foi bem nos 6 jogos novos, o que **levanta a régua**. Caveat de sempre: 12/54 jogos com teto
  reconstruído/não verificável (ver entrada 24/06). O líder de ontem (173) caiu **abaixo** do teto
  novo (190) ⇒ alcançável seguindo o tool (número atual do líder não confirmado).

- 2026-06-24 — **Eficiência ~88% (143 reais vs teto 161 do tool), MAS o teto é parcialmente não
  verificável.** Usuário em **14º com 143 pts**; líder do grupo **173**. Medido por
  `scripts/efficiency.py` (novo): reconstrói a previsão **as-of** de cada manhã (mesmo caminho do
  `predict --as-of`, config real `risk 0.5` + blend `0.6`) e pontua pelo Sistema I → teto **161 pts**
  (3,35/jogo). Usuário diz **ajustar os palpites toda manhã** (raramente à noite), ou seja, segue o
  tool — então o gap **não é "má jogada"**. O `--compare-archive` localiza a incerteza: dos 48 jogos,
  **36 têm snapshot REAL arquivado** (a partir de 13/06) e **12 não** (J1–J4, J25–J30, J32, J35) — e
  esses 12 contêm justamente as cravadas de alto valor (J27=14, J30=14, J1=13 ≈ 41 pts), com teto
  **100% reconstruído / não verificável**. Pior: **mesmo onde há arquivo, a reconstrução escorrega** —
  nos 36 jogos verificáveis o tool real marcou **103** vs **100** do as-of (Δ−3; divergências em
  J5/J7/J17/J24 por drift de odds/refit). **Conclusão honesta:** "88,8%" repousa sobre um teto ~40%
  sintético nas partidas que mais pontuam; parte do gap é **ruído de reconstrução**, não execução.
  **Correção:** manter o **arquivo da run da manhã completo** (`predict --archive` todo dia) — aí
  eficiência = seus pontos vs `scored(palpite arquivado)`, sem reconstrução. **Ponto que se mantém:**
  o líder (173) está **ACIMA** do teto (161; 164 com arquivo) — nem seguir o tool à risca colocaria
  em 1º hoje; ele pegou variância de exatos a favor (regride no esperado). Reafirma a decisão viva:
  alavanca é acurácia/adesão (+ peso 2× do mata-mata amplificando), não ousadia.

- 2026-06-24 — **Rodada J45–J48 fechada; 48 jogos disputados.** Grupos K e L encerrados. blend-track
  n=25: Brier modelo 0,424 vs blend 0,415 (Δ+0,010, blend à frente). Empates 14/48 (29%) z=+0,74 —
  variância. **Argentina 44,0%** no título; Espanha 16,3%, Portugal sobe ao top-4 (5,5%). Hoje (24/06)
  fecham os grupos A/B/C (J49–J54).

- 2026-06-23 — **Rodada J41–J44 fechada; 44 jogos disputados.** Argentina 2×0 Áustria e França 3×0
  Iraque confirmaram os favoritos; Argélia bateu a Jordânia (1×2) e Noruega 3×2 Senegal (jogo aberto).
  blend-track n=21: Brier modelo 0,424 vs blend 0,408 (Δ+0,016, blend à frente). Empates 13/44 (30%)
  z=+0,74 — variância. **Argentina dispara a 45,5%** no título; Espanha 16,9%. Hoje (23/06) fecham os
  grupos K e L (J45–J48).

- 2026-06-22 — **Rodada J37–J40 fechada; 40 jogos disputados.** Os dois zeros foram empates de
  novo (padrão persistente): J37 Bélgica 0×0 Irã e J40 Uruguai 2×2 Cabo Verde (era o único ⚡).
  Acertamos o lado em J38 (Egito 3×1) e J39 (Espanha 4×0 — goleada maior que o 2×0 palpitado).
  blend-track n=17: Brier modelo 0,479 vs blend 0,456 (Δ+0,023, blend à frente). Empates 13/40
  (32%) z=+1,06 — variância. **Espanha dispara a 18,4%** no título após o 4×0; Argentina 36,2%.

- 2026-06-21 — **Rodada J33–J36 fechada; 36 jogos disputados.** blend-track n=13: Brier modelo
  0,506 vs blend 0,466 (Δ+0,041, blend à frente). Empates 11/36 (31%) z=+0,73 — variância.
  Argentina 36,0%, Espanha 9,3%, Brasil 7,0%. Última rodada de grupos começa hoje (J37–J40).

- 2026-06-20 — **J35 Holanda 5×1 Suécia:** acertamos o lado ✅, palpitamos 2×1 (goleada inesperada). odds pós-jogo capturadas com valor inválido (1.0) → linha removida do odds.csv; J35 ficará fora do blend-track. Favoritos: Argentina 37,1%, Espanha 10,4%, Brasil 7,9%.

- 2026-06-19 (noite) — **Rodada J29–J32 completa.** 2 placares exatos: Brasil 3×0 Haiti ✅ e Escócia
  0×1 Marrocos ✅. EUA 2×0 Austrália: acertamos o lado (1×0 palpitado). Turquia 0×1 Paraguai: zebra —
  palpitamos Turquia 2×1. blend-track n=10: Brier modelo 0,467 vs blend 0,419 (Δ+0,048, delta
  crescendo — blend cada vez mais sólido). Argentina sobe para 37,3%; Brasil volta ao top-3 (8,5%).

- 2026-06-19 (tarde) — **J30 Escócia 0×1 Marrocos: palpite exato ✅.** blend-track n=7: Brier modelo
  0,441 vs blend 0,416 (Δ+0,025, blend à frente). Regime de empates: 10/29 (34%) z=+1,01 — variância,
  sem ação. Marrocos entra no top-5 de campeão (5,1%); Brasil sai. Palpite de Brasil×Haiti atualizado
  de 2×0 para 3×0 após reajuste do modelo com o novo resultado.

- 2026-06-19 — **Lição dos 28 jogos: empate é a fraqueza, não a falta de placar exato.** Acerto de
  1×2 = **54%** (15/28); zeros = **46%** (13/28), dos quais **10 são empates** (10 empates reais, 0
  palpitados; em jogo decidido o tool acerta 80–100% o lado). Cravar placar (7%, 2/28) dá os maiores
  pontos por jogo, mas é evento de ~10% que o `best_prediction` **já otimiza dentro do EV** — não é
  alavanca. A alavanca é **não-zerar** (acertar o lado), e os zeros são empates — majoritariamente
  variância (ENG-18: modelo calibrado; 36% vs ~26% = ~1,2σ). **Não forçar empates** (baixa o EV);
  monitorar via [ENG-22]. A acurácia (blend, ENG-19) é a única melhoria real.

- 2026-06-17 — **Trade-off de ranking modelado: risco NÃO é alavanca; acurácia é.** Estado: 44 pts,
  32º de 60, líder 80 (gap +36 = +2,4σ; você ≈ mediana do campo, média≈45/σ≈15). (1) Eficiência
  medida = **100%**: os palpites as-of do tool (risk 0.5) renderiam exatamente os mesmos 44 pts —
  não há ganho jogando diferente sobre este modelo; o teto é o do modelo. (2) Botão de risco ≠
  variância: nos 52 jogos de grupo restantes, SD travado em ~33 em todo risco, E[pts] desaba
  191→120 (0.5→0.8), p95 também cai. (3) Simulação de campo (60 jog., 40k sims): P(vencer)~0–1%,
  P(top-10) ~2–13% (depende de quão diverso o campo palpita — chalk trava o ranking), P(melhorar do
  32º)~50%. Subir SEU risco reduz P(vencer) e P(top-10). (4) Acurácia é a alavanca: +20 pts de edge
  de EV → P(top-10) 8%→42%. **Decisão revisada (ver Decisões vivas): manter 0.5 definitivo; subida =
  ENG-19 (blend odds) + variância natural.** Premissa antiga ("subir risco se atrás") era falsa.

- 2026-06-17 — **Diagnóstico de calibração (ENG-18) nos 20 jogos disputados: variância, sem ação.**
  Brier multiclasse 2026 = **0,637** (≈ uniforme 0,667) vs **0,578** nas 4 Copas passadas (256 jogos).
  Causa única: **8 empates em 20 (40%)** contra ~22–25% normal; o modelo previu 24,9%. Desvio de
  ~1,5σ (binomial, p≈0,25, n=20) — elevado mas dentro do ruído, e na direção **oposta** ao viés
  histórico do modelo (que *superestima* empate levemente: 27,9%→22,3% no pooling). O Brier ≈
  uniforme é mecânico: o modelo nunca dá P(empate) > ~37%, então uma amostra empate-pesada o derruba
  por construção. 7 dos 9 erros de 1×2 foram empates. **Veredito: modelo bem calibrado de fundo, não
  mexer.** Achado de bolão (não de modelo): `best_prediction` palpitou empate só **1 vez em 84**;
  numa Copa empate-pesada isso vira zero garantido (ver J3). **Gatilho:** se os empates seguirem
  agrupando até o fim dos grupos, reconsiderar risco/estratégia — não o modelo.

- 2026-06-13 — **Decisão de risco reafirmada (0.5)** após recalibração do motor (ENG-14: a régua
  de pontos do app é logarítmica, não potência — `base = 1 + 7,55·log10(1/p)`; `risk` desacoplado
  para um tilt só na escolha). Efeito nos palpites de hoje a `0.5`: **nenhum** (4 jogos idênticos);
  a `0.7` cravaria as zebras de J5 (Turquia) e J7 (Haiti). Recomendação e decisão: manter `0.5`
  (cedo demais para variância; ver Decisões vivas).

- 2026-06-13 — Usuário em **25º com 14 pts** após 4 jogos. Análise: palpites do modelo (risk 0.5)
  renderiam ~16,4 pts nesses jogos — usuário está colado no ótimo; o "déficit" é variância, não
  estratégia. Zeraram J3 (Canadá 1×1, favorito de 74% empatou) e J4 (EUA 4×1, modelo foi de
  Paraguai/40%). Lição: no Sistema I, errar o 1×2 zera o jogo; eficiência mora em acertar o lado,
  não o placar exato. Decisão: manter risk 0.5 por ora (ver gatilho acima).

- 2026-06-12 — Criado este diário como memória de campanha agnóstica a LLM, referenciado no
  `AGENTS.md`. Estado inicial: nenhum jogo disputado registrado, configuração padrão.
