# BOLAO.md — memória de campanha (Copa 2026)

Memória persistente da campanha do bolão, **agnóstica a ferramenta**: qualquer agente (Claude,
Codex, Gemini, …) deve **ler este arquivo no início da sessão** e **atualizá-lo quando uma decisão
de campanha acontecer** (mudança de `risk`, situação no ranking, regra do bolão alterada, etc.).

Registre aqui **só o que não é rederivável** dos dados e do código:
- estado dos jogos → mora em `fixtures.csv` (e `sync-results` reconstrói da internet);
- palpites vigentes → `out/palpites-2026.{csv,md,html}` (regeneráveis com `predict`);
- decisões e contexto humano da campanha → **aqui**.

Use datas absolutas (AAAA-MM-DD). Entradas novas no topo do histórico.

## Estado atual (atualizado em 2026-06-25)

- **54 de 104 jogos disputados (J1–J54).** Última rodada de grupos em andamento: J55–J60 hoje (25/06,
  grupos D/E/F); demais J61–J72 até 27/06.
- **`blend-track` n=31:** Brier modelo **0,426** vs blend **0,410** — Δ=**+0,015**; blend
  segue melhor. Regime de empates: 14/54 (26%) z=+0,22 — variância, sem ação.
- Favorito ao título: **Argentina (42,7%)**; Espanha 15,5%, Brasil 7,8%, França 5,6%, Portugal 5,2%.
- **Config em uso:** `risk 0.5` + `blend_weight 0.6` (blend com odds **ATIVO** — ENG-19; odds
  refrescadas em 25/06: 18 jogos atualizados, 49 no total); admin do bolão usa Sistema I sem customização. **Rotina por rodada e formato do
  `odds.csv`: no README** (`fetch_odds.py` → `predict` → `blend-track`); a chave da The Odds API vive no `.env`.

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
