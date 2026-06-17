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
uv run worldcup blend-track --edition 2026     # Brier do blend vs modelo nos jogos com odds (ENG-19)
uv run pytest        # testes
uv run ruff check .  # lint
```

Flag global `-v`/`--verbose` (antes do subcomando) desce o nível de log para `INFO` e mostra os
avisos informativos da biblioteca em `stderr` — ex.: quais seleções o `min_matches` descartou no
ajuste. Por padrão só avisos de nível `WARNING` aparecem (ex.: ajuste do modelo não-convergido).

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

**Blend com odds de mercado (opcional):** crie `data/editions/<edição>/odds.csv` com
`match_id,home,draw,away` em odds decimais (**acrescente** os jogos de cada rodada — não
sobrescreva: o `blend-track` acumula o tally sobre todos os jogos passados com odds). A ferramenta
tira a margem da casa, combina as odds com as probabilidades do modelo (média geométrica ponderada,
peso `blend_weight`) e ajusta o palpite. A edição 2026 já vem com `blend_weight = 0.6` no
`scoring.toml` (prior de princípio: odds de fechamento são bem calibradas); `--blend-weight 0` ou a
ausência de `odds.csv` ⇒ só o modelo, sem mudança. Por que ajuda: o modelo é estatístico e cego a
escalações/lesões/motivação, que as odds capturam. Para medir se o blend está de fato ajudando,
rode `worldcup blend-track` conforme registra odds + resultados — compara o Brier do blend vs. o do
modelo-puro nos jogos já disputados com odds.

Para **reconstruir** a visão de um dia passado, use `predict --as-of AAAA-MM-DD`: reajusta o modelo
usando só os resultados conhecidos até a véspera daquela data e grava
`history/<data>.reconstruido.{csv,md}` (marcado como reconstruído, com aviso), **sem tocar em
`out/`** — os palpites vivos da campanha ficam intactos. `--as-of` com a data de hoje reproduz
exatamente o run real do dia. Os reconstruídos são **regeneráveis sob demanda**, então ficam fora
do git (`.gitignore`); só os runs reais (`--archive`) são versionados em `history/`.

## Estrutura

- `src/worldcup/` — código (modelo, pontuação, simulação, CLI).
- `data/editions/<ano>/` — spec do formato + jogos + pontuação de cada edição (orientado a dados),
  mais `BOLAO.md`, o diário de campanha do bolão (decisões não rederiváveis dos dados).
- `data/historical_results.csv` — base histórica compartilhada, baixada pelo `fetch-data`.
- `docs/SPEC.md` — **especificação técnica e metodologia** (matemática do modelo, fórmula de
  pontuação, simulação, validação) com derivações e exemplos numéricos.
- `AGENTS.md` (+ symlink `CLAUDE.md`) — guia para quem desenvolve/mantém o projeto.
- `CHANGELOG.md` — mudanças relevantes por versão (Keep a Changelog); tags `vX.Y.Z` marcam marcos.

## Ajustar a pontuação do seu grupo

A pontuação real é configurada pelo admin do grupo. Edite `data/editions/2026/scoring.toml`
para casar com o sistema (I / Simplificado / Só-vencedor) e o peso por fase do seu grupo.
O default já vem calibrado como **Sistema I** (base 1–13 + bônus reais do app) **+ Equilíbrio gradual**.

## Validação e estratégia

Rode `uv run worldcup backtest --edition 2022` para ver quantos pontos o modelo teria feito na
Copa de 2022 (treinando só com jogos anteriores). Lá a estratégia **agressiva** (`risk=1.0`)
fez ~28% mais pontos que a fiel (`0.5`) — coerente com "azarão vale mais", ao custo de acertar menos
o 1×2. Se quiser arriscar para subir no ranking, gere com `--risk 0.7` ou `--risk 1.0`.

## Limitações conhecidas

(Resumo para o usuário; a fonte canônica, com o detalhamento técnico, é [`docs/SPEC.md`](docs/SPEC.md) §9.2.)

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
