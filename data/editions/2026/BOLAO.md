# BOLAO.md — memória de campanha (Copa 2026)

Memória persistente da campanha do bolão, **agnóstica a ferramenta**: qualquer agente (Claude,
Codex, Gemini, …) deve **ler este arquivo no início da sessão** e **atualizá-lo quando uma decisão
de campanha acontecer** (mudança de `risk`, situação no ranking, regra do bolão alterada, etc.).

Registre aqui **só o que não é rederivável** dos dados e do código:
- estado dos jogos → mora em `fixtures.csv` (e `sync-results` reconstrói da internet);
- palpites vigentes → `out/palpites-2026.{csv,md,html}` (regeneráveis com `predict`);
- decisões e contexto humano da campanha → **aqui**.

Use datas absolutas (AAAA-MM-DD). Entradas novas no topo do histórico.

## Estado atual (atualizado em 2026-06-17)

- A Copa começou em 2026-06-11. **20 de 104 jogos disputados e registrados (J1–J20).**
  J17–J20 (2026-06-16) entraram via `sync-results`.
  J13–J16 (2026-06-15) entraram **manualmente via web search** (martj42 ainda em 12 jogos):
  **rodada de empates** — Bélgica 1×1 Egito, Irã 2×2 Nova Zelândia, Arábia Saudita 1×1 Uruguai,
  Espanha 0×0 Cabo Verde (zebra: estreante segurou um favorito ao título).
  (J9–J12 via `sync-results`; J1–J8 antes; J5–J8 manualmente.)
- Próxima rodada a palpitar: 2026-06-17 (J21–J24): Inglaterra×Croácia, Gana×Panamá,
  Portugal×RD Congo, Uzbequistão×Colômbia. **Um palpite ousado (⚡): Gana 0×1 Panamá**
  (jogo aberto, 36%/31%/33% — modelo crava a leve vantagem do visitante).
- Favorito ao título: **Argentina (32,6%)** — saltou de 17,5%, confirmou favoritismo na 2ª rodada.
  Seguida de Espanha (11,5%), Inglaterra (9,8%), França (7,7%) e Portugal (7,4%).
- **Repalpitado 2x em 2026-06-15:** (1) ENG-16 — gradiente analítico fez o fit convergir (antes
  inflava Argentina/Brasil); (2) ENG-17 — defaults recalibrados (meia-vida 2,5→2,0, ridge
  0,05→0,10, +9,2% de pontos no backtest LOO). O shrinkage maior reaproximou Argentina/Espanha na
  ponta. Placares de hoje inalterados (1x0/1x0/0x1/3x0). Snapshot do dia regravado com o modelo
  final (ENG-16+17).
- Palpites vigentes gerados com configuração padrão: `risk 0.5`, Sistema I conforme
  `scoring.toml` (sem customização do admin do bolão até agora).
- Nota operacional: martj42 tem latência de 1-2 dias; quando atrasada, buscar placares via
  web search e registrar com `worldcup record`. Rotina: `sync-results --archive` → se 0 jogos
  novos, buscar manualmente → `predict --archive`.

## Decisões vivas

- `risk = 0.5` **definitivo** — ótimo para a média **e** para o ranking. **Revisado em 2026-06-17**
  com modelagem do trade-off de ranking (substitui o gatilho "subir risco se atrás", que partia de
  premissa errada): o botão de risco **não é instrumento de variância** neste sistema de pontos. Nos
  52 jogos de grupo restantes, o SD do total fica travado em ~33 em qualquer risco, enquanto o E[pts]
  desaba (191→120 de 0.5 a 0.8) — **até a cauda otimista (p95) piora** com risco alto. Na simulação
  de campo (60 jogadores, líder 80, você 44 ≈ mediana), subir o risco **reduz** P(vencer) e P(top-10)
  — inclusive para o objetivo mais agressivo. Causa: o Sistema I já recompensa zebra acertada
  (base→13), então o E-max (0.5) já pega as apostas boas; cranquear só força EV ruim que zera.
  **A única alavanca que sobe o ranking é acurácia, não ousadia:** +20 pts de edge de EV ao longo do
  torneio levam P(top-10) de 8%→42%; risco leva a 0,1%. Daí o [ENG-19] (blend com odds) ser a aposta
  de maior retorno. **Regra:** manter 0.5 sempre; subida vem de acurácia (ENG-19) + da variância
  natural (~50/50 de melhorar, de graça). **Mata-mata testado (2026-06-17): mesma conclusão.** O
  risco só mexe na camada de 90' do palpite de KO (prorrogação/pênaltis são determinísticas em
  `knockout.py`); medido nos 32 jogos do chaveamento, SD ponderado travado em ~58 e E[pts] desaba
  (236→179 de 0.5 a 0.8). O KO é onde a variância vive (SD 58 vs 33 dos grupos, pelos pesos 2×/4×),
  mas você a captura em 0.5 — subir o risco no KO derruba P(top-10) 13,6%→7,8% (0.7)→0% (0.8).
  Restam ~427 pts (SD 67) contra gap de 36 ao líder: posição atual não é destino, mas a alavanca é
  acurácia, não risco.
- Execução **sob demanda**: o usuário prefere rodar os comandos manualmente; não propor
  cron/agendamento.

## Histórico

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
