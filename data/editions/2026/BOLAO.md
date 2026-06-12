# BOLAO.md — memória de campanha (Copa 2026)

Memória persistente da campanha do bolão, **agnóstica a ferramenta**: qualquer agente (Claude,
Codex, Gemini, …) deve **ler este arquivo no início da sessão** e **atualizá-lo quando uma decisão
de campanha acontecer** (mudança de `risk`, situação no ranking, regra do bolão alterada, etc.).

Registre aqui **só o que não é rederivável** dos dados e do código:
- estado dos jogos → mora em `fixtures.csv` (e `sync-results` reconstrói da internet);
- palpites vigentes → `out/palpites-2026.{csv,md,html}` (regeneráveis com `predict`);
- decisões e contexto humano da campanha → **aqui**.

Use datas absolutas (AAAA-MM-DD). Entradas novas no topo do histórico.

## Estado atual (atualizado em 2026-06-12)

- A Copa começou em 2026-06-11. Resultados sincronizados até a 1ª rodada do grupo A
  (2 de 104 jogos preenchidos): México 2x0 África do Sul, Coreia do Sul 2x1 Rep. Tcheca.
- Palpites vigentes gerados com configuração padrão: `risk 0.5`, Sistema I conforme
  `scoring.toml` (sem customização do admin do bolão até agora).
- Rotina diária (sob demanda, sem agendamento): `uv run worldcup sync-results --edition 2026`
  → conferir a próxima rodada em `out/palpites-2026.md`.

## Decisões vivas

- `risk = 0.5` (default, maximiza pontos esperados). Revisitar se ficar atrás no ranking —
  `--risk 0.7` arrisca mais zebras para diferenciar.
- Execução **sob demanda**: o usuário prefere rodar os comandos manualmente; não propor
  cron/agendamento.

## Histórico

- 2026-06-12 — Criado este diário como memória de campanha agnóstica a LLM, referenciado no
  `AGENTS.md`. Estado inicial: nenhum jogo disputado registrado, configuração padrão.
