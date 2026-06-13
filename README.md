# worldcup — Gerador de palpites de bolão da Copa do Mundo

Gera palpites para **todos os jogos** de uma Copa do Mundo usando um modelo estatístico
(**Poisson / Dixon–Coles**) treinado em resultados históricos de jogos internacionais.
Feito para o app **Bolão de Futebol 2026** (bolaodefutebol.com), mas **agnóstico à edição**:
o formato do torneio e a pontuação vivem em arquivos de dados (`data/editions/<ano>/`), então
em 2030 basta adicionar uma nova pasta.

## Por que isso ajuda a ganhar o bolão

- O bolão deste grupo usa o **Sistema I (probabilístico)**: cravar a **zebra vale muito mais**.
  O app escolhe o placar que **maximiza os pontos esperados**, não só o "mais provável".
- **Peso por fase** (Equilíbrio gradual: grupos 1x, eliminatórias 2x, final 4x) é levado em conta
  para sinalizar onde **arriscar mais compensa**.
- **Realimentação**: conforme os jogos acontecem, o `sync-results` baixa os placares reais da
  internet (ou você registra à mão), o modelo se reajusta e só os jogos que faltam são repalpitados
  (o prazo de cada palpite no app é 5 min antes do jogo).

## Como rodar

```bash
uv sync                                   # cria o ambiente a partir do lockfile
uv run worldcup fetch-data                # baixa e normaliza o histórico (data/historical_results.csv)
uv run worldcup predict --edition 2026    # gera out/palpites-2026.csv e .md
```

Outros comandos:

```bash
uv run worldcup sync-results --edition 2026   # baixa os resultados reais da internet e repalpita
uv run worldcup predict --edition 2026 --archive   # +snapshot versionado do dia (history/)
uv run worldcup record --edition 2026 --match <id> --home 2 --away 1   # registra um placar manualmente
uv run worldcup backtest --edition 2022       # valida o modelo numa Copa passada
uv run pytest        # testes
uv run ruff check .  # lint
```

`sync-results` é a forma automática de realimentar: baixa os placares já disputados (do mesmo
dataset público, atualizado poucas horas após cada jogo), preenche a fase de grupos e o mata-mata
(resolvendo o chaveamento pelos resultados reais, com vencedor nos pênaltis via `shootouts`) e já
roda o `predict`. Use `record` para um ajuste pontual ou se quiser corrigir algo à mão.

Os palpites ficam em `out/palpites-<edição>.md` (tabela pronta para copiar), `.csv` e
`.html` — este último é autocontido (abre no navegador, com barras de probabilidade e destaque
de zebra) e **otimizado para impressão** (Ctrl+P → salvar em PDF, com quebra de página por fase).

`out/` é regenerável (gitignored) e sobrescrito a cada run. Para guardar o **histórico** de como
os palpites evoluem rodada a rodada, use `predict --archive` (ou `--archive AAAA-MM-DD`): grava um
snapshot imutável e **versionado** em `data/editions/<edição>/history/<data>.{csv,md}`. Faz sentido
porque, depois que novos resultados entram e o modelo reajusta, o palpite de um dia não é mais
reproduzível.

Para **reconstruir** a visão de um dia passado (ou semear o histórico retroativamente), use
`predict --as-of AAAA-MM-DD`: reajusta o modelo usando só os resultados conhecidos até a véspera
daquela data e grava `history/<data>.reconstruido.{csv,md}` (marcado como reconstruído, com aviso),
**sem tocar em `out/`** — os palpites vivos da campanha ficam intactos. `--as-of` com a data de hoje
reproduz exatamente o run real do dia.

## Estrutura

- `src/worldcup/` — código (modelo, pontuação, simulação, CLI).
- `data/editions/<ano>/` — spec do formato + jogos + pontuação de cada edição (orientado a dados),
  mais `BOLAO.md`, o diário de campanha do bolão (decisões não rederiváveis dos dados).
- `data/historical_results.csv` — base histórica compartilhada, baixada pelo `fetch-data`.
- `docs/SPEC.md` — **especificação técnica e metodologia** (matemática do modelo, fórmula de
  pontuação, simulação, validação) com derivações e exemplos numéricos.
- `AGENTS.md` (+ symlink `CLAUDE.md`) — guia para quem desenvolve/mantém o projeto.

## Ajustar a pontuação do seu grupo

A pontuação real é configurada pelo admin do grupo. Edite `data/editions/2026/scoring.toml`
para casar com o sistema (I / Simplificado / Só-vencedor) e o peso por fase do seu grupo.
O default já vem calibrado como **Sistema I** (base 1–13 + bônus reais do app) **+ Equilíbrio gradual**.

## Validação e estratégia

Rode `uv run worldcup backtest --edition 2022` para ver quantos pontos o modelo teria feito na
Copa de 2022 (treinando só com jogos anteriores). Lá a estratégia **agressiva** (`risk=1.0`)
fez ~47% mais pontos que a conservadora — coerente com "azarão vale mais". Se quiser arriscar
para subir no ranking, gere com `--risk 0.7` ou `--risk 1.0`.

## Limitações conhecidas

- **Modelo baseado em resultados**: pondera muito os jogos recentes, então favorece quem vem
  bem (seleções da América do Sul aparecem fortes) e pode subestimar potências em má fase
  recente. É o comportamento esperado de um modelo puramente estatístico.
- **Desempates de grupo** são simplificados (pontos → saldo → gols → sorteio); o confronto
  direto oficial não é aplicado.
- **Melhores terceiros**: a alocação aos slots usa casamento por restrição de grupos (Annex C da
  FIFA aproximado). Depois da fase de grupos, com os resultados reais registrados, confira os 8
  confrontos dos 32-avos.

## Licença

[MIT](LICENSE).
