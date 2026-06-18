# BOLAO.md — memória de campanha (Copa 2026)

Memória persistente da campanha do bolão, **agnóstica a ferramenta**: qualquer agente (Claude,
Codex, Gemini, …) deve **ler este arquivo no início da sessão** e **atualizá-lo quando uma decisão
de campanha acontecer** (mudança de `risk`, situação no ranking, regra do bolão alterada, etc.).

Registre aqui **só o que não é rederivável** dos dados e do código:
- estado dos jogos → mora em `fixtures.csv` (e `sync-results` reconstrói da internet);
- palpites vigentes → `out/palpites-2026.{csv,md,html}` (regeneráveis com `predict`);
- decisões e contexto humano da campanha → **aqui**.

Use datas absolutas (AAAA-MM-DD). Entradas novas no topo do histórico.

## Estado atual (atualizado em 2026-06-18)

- A Copa começou em 2026-06-11. **24 de 104 jogos disputados e registrados (J1–J24).**
  J22 (Gana **1×0** Panamá — zebra, Gana venceu) e J24 (Uzbequistão **1×3** Colômbia) entraram via
  `sync-results` (martj42 alcançou). J21/J23 (2026-06-17) entraram manualmente: Inglaterra **4×2**
  Croácia e Portugal **1×1** RD Congo (1º ponto da RDC em Copas). Na rodada J21–J24 o tool acertou
  o lado em J21 e J24, e **zerou J22 (zebra do Gana) e J23 (empate)** — padrão de zebra/empate
  seguindo a punir.
  J17–J20 (2026-06-16) via `sync-results`; J13–J16 (2026-06-15) manualmente (rodada de empates:
  Bélgica 1×1 Egito, Irã 2×2 Nova Zelândia, Arábia Saudita 1×1 Uruguai, Espanha 0×0 Cabo Verde).
  (J9–J12 via `sync-results`; J1–J8 antes; J5–J8 manualmente.)
- Rodada de hoje (J25–J28, 18/06): todos favoritos, blend e modelo concordam — Canadá 2×0 Catar
  (70%), Tchéquia 1×0 África do Sul (52%), México 1×0 Coreia do Sul (47%), Suíça 1×0 Bósnia (59%).
- **1º veredito do `blend-track` (n=2, J22+J24):** Brier modelo **0,441** vs blend **0,465** —
  modelo levemente melhor (Δ −0,024), mas **n=2 é ruído**. Detalhe: blend ganhou no J24 (mais
  confiante na Colômbia, certo), perdeu no J22 (puxou pro empate, mas Gana venceu). Acompanhar até
  ~20 jogos pra ler sinal. (Nota: o J22 que o usuário não conseguiu retravar não custou ponto — Gana
  venceu, modelo e blend zerariam igual.)
- Favorito ao título: **Argentina (35,5%)**. Espanha 11,7%; Inglaterra 8,5%; França 8,0%.
- **Repalpitado 2x em 2026-06-15:** (1) ENG-16 — gradiente analítico fez o fit convergir (antes
  inflava Argentina/Brasil); (2) ENG-17 — defaults recalibrados (meia-vida 2,5→2,0, ridge
  0,05→0,10, +9,2% de pontos no backtest LOO). O shrinkage maior reaproximou Argentina/Espanha na
  ponta. Placares de hoje inalterados (1x0/1x0/0x1/3x0). Snapshot do dia regravado com o modelo
  final (ENG-16+17).
- Palpites vigentes gerados com configuração padrão: `risk 0.5`, Sistema I conforme
  `scoring.toml` (sem customização do admin do bolão até agora).
- **Alavanca de acurácia ATIVA (ENG-19, 2026-06-17):** `blend_weight = 0.6` no `scoring.toml` e
  `odds.csv` com odds **Pinnacle** (via The Odds API) de **50 jogos de grupo** — os palpites vigentes
  em `out/` já saem **blendados** (peso 0.6). Efeito notável da 1ª carga: J32 EUA×Austrália virou
  (modelo 29/30/41 → blend 47/26/27, palpite 0x1→1x0); J24/J25/J28 ficaram mais firmes no favorito.
  (J21/J23 sem odds — já tinham começado quando a chave entrou.) **Rotina a cada rodada** (única
  alavanca que sobe o ranking, ver Decisões vivas): `uv run python scripts/fetch_odds.py` (busca +
  mescla as odds, preservando jogos já disputados); palpitar; depois dos resultados rodar
  `worldcup blend-track` e anotar aqui se o blend está ganhando do modelo (Brier). Fonte de odds em
  uso: **The Odds API** (free tier, `soccer_fifa_world_cup`); a chave é segredo (não versionar).
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
