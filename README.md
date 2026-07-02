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
uv run worldcup status --edition 2026         # briefing read-only do estado (start-of-day); alias: `uv run ws`
uv run worldcup sync-results --edition 2026   # baixa os resultados reais da internet e repalpita
uv run worldcup predict --edition 2026 --archive   # +snapshot versionado do dia (history/)
uv run worldcup record --edition 2026 --match <id> --home 2 --away 1   # registra um placar manualmente
uv run worldcup backtest --edition 2022       # valida o modelo numa Copa passada
uv run worldcup blend-track --edition 2026     # Brier blend vs modelo (ENG-19) + monitor de empates (ENG-22)
uv run pytest        # testes
uv run ruff check .  # lint
```

Flag global `-v`/`--verbose` (antes do subcomando) desce o nível de log para `INFO` e mostra os
avisos informativos da biblioteca em `stderr` — ex.: quais seleções o `min_matches` descartou no
ajuste. Por padrão só avisos de nível `WARNING` aparecem (ex.: ajuste do modelo não-convergido).

`status` (alias `ws`) é um **briefing read-only** para reidratar o contexto no início da sessão:
numa saída só mostra jogos disputados/total, fase atual, os jogos de hoje (disputado ✓ / pendente ⏳),
os próximos palpites, o standing (do `BOLAO.md`) e o que depende de você (seus pontos para a
eficiência, jogos atrasados que a fonte ainda não tem). Não muta nada — a atualização de fato
(`sync-results`/`predict`) continua nos comandos próprios. `--date AAAA-MM-DD` sobrescreve "hoje".

`sync-results` é a forma automática de realimentar: baixa os placares já disputados (do mesmo
dataset público, atualizado poucas horas após cada jogo), preenche a fase de grupos e o mata-mata
(resolvendo o chaveamento pelos resultados reais, com vencedor nos pênaltis via `shootouts`) e já
roda o `predict`. Use `record` para um ajuste pontual ou se quiser corrigir algo à mão.

Os palpites ficam em `out/palpites-<edição>.md` (tabela pronta para copiar), `.csv` e
`.html` — este último é autocontido (abre no navegador, com barras de probabilidade e destaque
de zebra) e **otimizado para impressão** (Ctrl+P → salvar em PDF, com quebra de página por fase).

`out/` é regenerável (gitignored) e sobrescrito a cada run. Para guardar o **histórico** de como
os palpites evoluem rodada a rodada, use `predict --archive` ou `sync-results --archive` (ambos
aceitam `--archive AAAA-MM-DD`): grava um
snapshot imutável e **versionado** em `data/editions/<edição>/history/<data>.{csv,md}`. Faz sentido
porque, depois que novos resultados entram e o modelo reajusta, o palpite de um dia não é mais
reproduzível. Re-arquivar na mesma data (ex.: pós-`record`) faz **merge por jogo**: o palpite da
manhã de um jogo que já virou `FINAL` é preservado, nunca sobrescrito.

**Blend com odds de mercado (opcional):** `data/editions/<edição>/odds.csv` com
`match_id,home,draw,away` em odds decimais e, opcionalmente, `total_line,over,under` (o mercado de
**over/under** — ENG-35). A forma prática de preencher é
`uv run python scripts/fetch_odds.py` (busca 1×2 **e totals** da The Odds API com a chave em `.env` e
**mescla** no `odds.csv`, preservando os jogos já disputados — o `blend-track` acumula o tally sobre
todos eles). Para editar à mão, **acrescente** os jogos de cada rodada (não sobrescreva). A ferramenta
tira a margem da casa, combina as odds com as probabilidades do modelo (média geométrica ponderada,
peso `blend_weight`) e ajusta o palpite; com totals, também ancora a **taxa de gols** do placar no
mercado (sem totals num jogo, só o 1×2 é corrigido). A edição 2026 já vem com `blend_weight = 0.6` no
`scoring.toml` (prior de princípio: odds de fechamento são bem calibradas); `--blend-weight 0` ou a
ausência de `odds.csv` ⇒ só o modelo, sem mudança. Por que ajuda: o modelo é estatístico e cego a
escalações/lesões/motivação, que as odds capturam. Para medir se o blend está de fato ajudando,
rode `worldcup blend-track` conforme registra odds + resultados — compara o Brier do blend vs. o do
modelo-puro nos jogos já disputados com odds (e, havendo totals, o Brier binário do over/under).

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
- `docs/C4.md` — **arquitetura no modelo C4** (Contexto → Container → Componentes → Dinâmica),
  em diagramas Mermaid derivados do grafo de imports real.
- `docs/PRD.md` — **requisitos de produto** (o quê e por quê), com glossário em `docs/GLOSSARIO.md`.
- `docs/MODEL_CARD.md` — **cartão do modelo** (uso pretendido, métricas, calibração, limitações).
- `docs/DATA.md` — **proveniência e licenciamento dos dados** (fontes, versionamento, itens de IP).
- `AGENTS.md` (+ symlink `CLAUDE.md`) — guia para quem desenvolve/mantém o projeto.
- `CHANGELOG.md` — mudanças relevantes por versão (Keep a Changelog); tags `vX.Y.Z` marcam marcos.

## Ajustar a pontuação do seu grupo

A pontuação real é configurada pelo admin do grupo. Edite `data/editions/2026/scoring.toml`
para casar com o sistema (I / Simplificado / Só-vencedor) e o peso por fase do seu grupo.
O default já vem calibrado como **Sistema I** (base 1–13 + bônus reais do app) **+ Equilíbrio gradual**.

## Validação e estratégia

Rode `uv run worldcup backtest --edition 2022` para ver quantos pontos o modelo teria feito na
Copa de 2022 (treinando só com jogos anteriores). Com a régua de pontos **corrigida** (bônus de placar
hierárquicos, não somados), subir o risco **não** melhora os pontos de forma confiável: no backtest de
2022 o conservador (`risk=0.0`) faz mais que o agressivo (`1.0`), e o fiel (`0.5`) fica no meio — um
resultado ruidoso de uma Copa só. A alavanca de ranking é **acurácia** (blend de odds), não ousadia; o
default `0.5` (maximiza pontos esperados) é o recomendado.

**Eficiência da sua campanha** — quanto dos pontos que o tool renderia você capturou:

```bash
uv run python scripts/efficiency.py --edition 2026 --my-points 143 --leader 173 [--compare-archive]
```

Para cada jogo já disputado, reconstrói o palpite **as-of** (o que o tool mostrava na manhã do jogo)
e o pontua contra o resultado real — a soma é o **teto** que seguir o tool à risca renderia;
`eficiência = seus_pontos / teto`. `--compare-archive` confronta com os snapshots reais de
`history/` e lista onde a reconstrução diverge (quanto do gap é ruído de reconstrução vs. dias sem
snapshot arquivado). Cobre a fase de grupos com pontuação exata; no mata-mata pontua os 90' **com o
peso de fase** (R32–SF ×2, final ×4) e soma os bônus de prorrogação/pênaltis (±3 ×peso) quando a fonte
(`shootouts.csv`) confirma o desfecho; jogos empatados nos 90' ainda sem shootout na fonte são pulados
(ENG-27).

**Endgame de bolão (ENG-36)** — bolão é jogo **diferencial**: seguir o E[pts]-máximo pontua junto
com o pelotão (que aglomera no favorito) e **preserva** sua posição; ranking só muda quando o
palpite diverge e a divergência acerta. A simulação de pelotão quantifica:

```bash
uv run python scripts/eng36_pool_sim.py --edition 2026 --my-points 285 --leader 337 --pool-size 60
```

Compara políticas (fiel / placar alternativo / zebra na final / SF / QF) em P(#1), P(top-3) e
E[pts]. Resultado (01/07, 3000 torneios): **atrás**, zebra só na final multiplica P(#1) por ~6
(0,7%→4,0%) custando ~7 pts esperados; divergir antes (SF/QF) não adiciona nada; **na frente**,
fiel domina (47% vs 35%). Para aplicar na prática: `worldcup predict --pool-behind` palpita a
**zebra** (90' + prorrogação + pênaltis) **só nos jogos de peso máximo** (a final) — use apenas
na manhã da final e apenas se estiver **atrás** no ranking.

**Apresentação do projeto** — um deck HTML autocontido (tema "Placar Noturno", 16:9, navegável) que
explica o projeto para leigos (conceitos, diferenciais, resultados e futuro):

```bash
uv run python scripts/build_presentation.py --docs   # gera out/ e docs/apresentacao.html
```

Abra o HTML no navegador (← → navegam; `Ctrl+P` salva um PDF/handout). É self-contained (sem CDN;
imagens CC embutidas em base64). A versão pronta vive versionada em
[`docs/apresentacao.html`](docs/apresentacao.html); ao editar o script, **regenere com `--docs`** e
inclua o HTML no mesmo commit.

## Limitações conhecidas

(Resumo para o usuário; a fonte canônica, com o detalhamento técnico, é [`docs/SPEC.md`](docs/SPEC.md) §9.2.)

- **Modelo baseado em resultados**: pondera muito os jogos recentes, então favorece quem vem
  bem (seleções da América do Sul aparecem fortes) e pode subestimar potências em má fase
  recente. É o comportamento esperado de um modelo puramente estatístico.
- **Desempates de grupo** são simplificados (pontos → saldo → gols → sorteio); o confronto
  direto oficial não é aplicado.
- **Melhores terceiros**: a alocação aos slots usa casamento por restrição de grupos (Annex C da
  FIFA aproximado) e **pode divergir** da tabela oficial — há mais de um emparelhamento válido. Dá
  para cravar a alocação oficial da combinação realizada via `[group_stage.third_allocation]` no
  `tournament.toml` (feito em 2026). Depois da fase de grupos, **confira os 8 confrontos dos 16-avos**
  com o bracket oficial.

## Licença

[MIT](LICENSE).
