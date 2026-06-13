# BOLAO.md — memória de campanha (Copa 2026)

Memória persistente da campanha do bolão, **agnóstica a ferramenta**: qualquer agente (Claude,
Codex, Gemini, …) deve **ler este arquivo no início da sessão** e **atualizá-lo quando uma decisão
de campanha acontecer** (mudança de `risk`, situação no ranking, regra do bolão alterada, etc.).

Registre aqui **só o que não é rederivável** dos dados e do código:
- estado dos jogos → mora em `fixtures.csv` (e `sync-results` reconstrói da internet);
- palpites vigentes → `out/palpites-2026.{csv,md,html}` (regeneráveis com `predict`);
- decisões e contexto humano da campanha → **aqui**.

Use datas absolutas (AAAA-MM-DD). Entradas novas no topo do histórico.

## Estado atual (atualizado em 2026-06-13)

- A Copa começou em 2026-06-11. Resultados sincronizados até 2026-06-12
  (4 de 104 jogos preenchidos): México 2x0 África do Sul, Coreia do Sul 2x1 Rep. Tcheca,
  Canadá 1x1 Bósnia, EUA 4x1 Paraguai.
- Próxima rodada a palpitar: 2026-06-13 (J5–J8): Austrália×Turquia, Brasil×Marrocos,
  Haiti×Escócia, Catar×Suíça.
- Favorito ao título: Argentina (29,4%), seguido de Brasil (18,2%) e Colômbia (10,7%).
- Palpites vigentes gerados com configuração padrão: `risk 0.5`, Sistema I conforme
  `scoring.toml` (sem customização do admin do bolão até agora).
- Rotina diária (sob demanda, sem agendamento): `uv run worldcup sync-results --edition 2026 --archive`
  → conferir a próxima rodada em `out/palpites-2026.md`. O `--archive` guarda o snapshot do dia
  versionado em `history/` (histórico da evolução dos palpites).

## Decisões vivas

- `risk = 0.5` (default, maximiza pontos esperados). **Mantido em 2026-06-13** mesmo estando
  em 25º — é cedo (4/104 jogos), variância domina. **Gatilho de revisão:** se ainda atrás ao
  fim da fase de grupos, subir para `--risk 0.7` (arrisca zebras para diferenciar). Guardar a
  ousadia para o mata-mata, que pesa 2× (e final 4×) no `scoring.toml`.
- Execução **sob demanda**: o usuário prefere rodar os comandos manualmente; não propor
  cron/agendamento.

## Histórico

- 2026-06-13 — Usuário em **25º com 14 pts** após 4 jogos. Análise: palpites do modelo (risk 0.5)
  renderiam ~16,4 pts nesses jogos — usuário está colado no ótimo; o "déficit" é variância, não
  estratégia. Zeraram J3 (Canadá 1×1, favorito de 74% empatou) e J4 (EUA 4×1, modelo foi de
  Paraguai/40%). Lição: no Sistema I, errar o 1×2 zera o jogo; eficiência mora em acertar o lado,
  não o placar exato. Decisão: manter risk 0.5 por ora (ver gatilho acima).

- 2026-06-12 — Criado este diário como memória de campanha agnóstica a LLM, referenciado no
  `AGENTS.md`. Estado inicial: nenhum jogo disputado registrado, configuração padrão.
