# BOLAO.md — memória de campanha (Copa 2026)

Memória persistente da campanha do bolão, **agnóstica a ferramenta**: qualquer agente (Claude,
Codex, Gemini, …) deve **ler este arquivo no início da sessão** e **atualizá-lo quando uma decisão
de campanha acontecer** (mudança de `risk`, situação no ranking, regra do bolão alterada, etc.).

Registre aqui **só o que não é rederivável** dos dados e do código:
- estado dos jogos → mora em `fixtures.csv` (e `sync-results` reconstrói da internet);
- palpites vigentes → `out/palpites-2026.{csv,md,html}` (regeneráveis com `predict`);
- decisões e contexto humano da campanha → **aqui**.

Use datas absolutas (AAAA-MM-DD). Entradas novas no topo do histórico.

## Estado atual (atualizado em 2026-06-14)

- A Copa começou em 2026-06-11. 8 de 104 jogos disputados e registrados (J1–J8).
  A fonte martj42 tem só J1–J4; J5–J8 foram registrados manualmente via web search (confirmados).
  Resultados: México 2×0 África do Sul, Coreia do Sul 2×1 Rep. Tcheca, Canadá 1×1 Bósnia,
  EUA 4×1 Paraguai, Austrália 2×0 Turquia, Brasil 1×1 Marrocos, Haiti 0×1 Escócia,
  Catar 1×1 Suíça.
- Próxima rodada a palpitar: 2026-06-14 (J9–J12): Alemanha×Curaçao, Costa do Marfim×Equador,
  Holanda×Japão, Suécia×Tunísia.
- Favorito ao título: Argentina (30,9%), seguido de Brasil (14,2%) e Colômbia (11,0%).
  Brasil caiu de 18,2% após empate com Marrocos.
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
