# BOLAO.md — memória de campanha (Copa 2026)

Memória persistente da campanha do bolão, **agnóstica a ferramenta**: qualquer agente (Claude,
Codex, Gemini, …) deve **ler este arquivo no início da sessão** e **atualizá-lo quando uma decisão
de campanha acontecer** (mudança de `risk`, situação no ranking, regra do bolão alterada, etc.).

Registre aqui **só o que não é rederivável** dos dados e do código:
- estado dos jogos → mora em `fixtures.csv` (e `sync-results` reconstrói da internet);
- palpites vigentes → `out/palpites-2026.{csv,md,html}` (regeneráveis com `predict`);
- decisões e contexto humano da campanha → **aqui**.

Use datas absolutas (AAAA-MM-DD). Entradas novas no topo do histórico.

## Estado atual (atualizado em 2026-06-16)

- A Copa começou em 2026-06-11. 16 de 104 jogos disputados e registrados (J1–J16).
  J13–J16 (2026-06-15) entraram **manualmente via web search** (martj42 ainda em 12 jogos):
  **rodada de empates** — Bélgica 1×1 Egito, Irã 2×2 Nova Zelândia, Arábia Saudita 1×1 Uruguai,
  Espanha 0×0 Cabo Verde (zebra: estreante segurou um favorito ao título).
  (J9–J12 via `sync-results`; J1–J8 antes; J5–J8 manualmente.)
- Próxima rodada a palpitar: 2026-06-16 (J17–J20): Argentina×Argélia, Áustria×Jordânia,
  França×Senegal, Iraque×Noruega. Nenhum palpite ousado (⚡) — todos seguem o favorito.
- Favorito ao título: **Argentina (17,5%)**, seguido de Espanha (13,9%), Inglaterra (11,9%),
  Portugal (9,4%) e França (6,0%). O 0×0 derrubou a Espanha de 16,1%→13,9%.
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

- `risk = 0.5` (default, maximiza pontos esperados). **Reafirmado em 2026-06-13** após revisão
  explícita (pós-recalibração ENG-14): é cedo (jogo 5/104), variância domina, e `0.5` é o caminho
  de maior valor acumulado ao longo de ~100 jogos restantes; o "+28%" da estratégia agressiva no
  backtest 2022 é uma Copa só, não vantagem confiável. **Antes de mexer no risco, seguir o E-max do
  tool de forma consistente** — os zeros de J3/J4 vieram de não acompanhar o palpite, não de risco
  baixo. **Gatilho de revisão:** se ainda claramente atrás ao fim da fase de grupos, subir o risco
  **seletivamente nos jogos de peso alto** (mata-mata 2×, final 4×), não global — não no 5º jogo.
- Execução **sob demanda**: o usuário prefere rodar os comandos manualmente; não propor
  cron/agendamento.

## Histórico

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
