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
uv run worldcup predict --edition 2026    # gera out/palpites-2026.{csv,md,html}
```

Outros comandos:

```bash
uv run worldcup status --edition 2026         # briefing read-only do estado (start-of-day); alias: `uv run ws`
uv run worldcup sync-results --edition 2026   # baixa os resultados reais da internet e repalpita
uv run worldcup predict --edition 2026 --archive   # +snapshot versionado do dia (history/)
uv run worldcup record --edition 2026 --match <id> --home 2 --away 1   # registra um placar manualmente
uv run worldcup record --edition 2026 --match <id> --home 1 --away 1 --ko-winner Brazil   # KO empatado nos 90'
uv run worldcup backtest --edition 2022       # valida o modelo numa Copa passada
uv run worldcup blend-track --edition 2026     # Brier blend vs modelo (ENG-19) + monitor de empates (ENG-22)
uv run worldcup blend-track --edition 2026 --sweep   # varre blend_weight 0.0..1.0 e mostra o Brier de cada peso (ENG-38)
uv run worldcup blend-track --edition 2026 --boost-sweep   # varre o peso dos jogos da edição (edition_boost) e mostra o Brier as-of do modelo (ENG-44)
uv run pytest        # testes
uv run ruff check .  # lint
```

Flags menos usados (todos com default sensato — só mexa se souber por quê): `predict`/
`sync-results` aceitam `--sims N` (simulações Monte Carlo, default 5000), `--seed` (default 12345),
`--risk R` (sobrescreve o `risk` da edição) e `--pool-behind [empate|zebra]` (modo endgame, ver
seção do bolão); `sync-results` tem ainda `--no-predict` (só sincroniza) e `--source-url`;
`fetch-data` tem `--cutoff` e `--source-url`; `backtest` tem `--sims` (default 2000); `blend-track`
tem `--blend-weight W` (avalia um peso arbitrário fora do sweep).

Flag global `-v`/`--verbose` (antes do subcomando) desce o nível de log para `INFO` e mostra os
avisos informativos da biblioteca em `stderr` — ex.: quais seleções o `min_matches` descartou no
ajuste. Por padrão só avisos de nível `WARNING` aparecem (ex.: ajuste do modelo não-convergido).

`status` (alias `ws`) é um **briefing read-only** para reidratar o contexto no início da sessão:
numa saída só mostra jogos disputados/total, fase atual, os jogos de hoje
(disputado ✓ / pendente ⏳), os próximos palpites, o standing (do `BOLAO.md`) e o que depende de você
(seus pontos para a eficiência, jogos atrasados que a fonte ainda não tem).
Não muta nada — a atualização de fato (`sync-results`/`predict`) continua nos comandos
próprios. `--date AAAA-MM-DD` sobrescreve "hoje".

`sync-results` é a forma automática de realimentar: baixa os placares já disputados
(do mesmo dataset público, atualizado poucas horas após cada jogo), preenche a fase de grupos
e o mata-mata (resolvendo o chaveamento pelos resultados reais, com vencedor nos pênaltis via
`shootouts`) e já roda o `predict`. Use `record` para um ajuste pontual ou se quiser corrigir
algo à mão.

Os palpites ficam em `out/palpites-<edição>.md` (tabela pronta para copiar), `.csv` e `.html` — este
último é autocontido (abre no navegador, com barras de probabilidade e destaque de zebra) e
**otimizado para impressão** (Ctrl+P → salvar em PDF, com quebra de página por fase).

`out/` é regenerável (gitignored) e sobrescrito a cada run. Para guardar o **histórico**
de como os palpites evoluem rodada a rodada, use `predict --archive` ou `sync-results --archive`
(ambos aceitam `--archive AAAA-MM-DD`): grava snapshot imutável e **versionado** em
`data/editions/<edição>/history/<data>.{csv,md}`. Faz sentido porque, depois que novos resultados
entram e o modelo reajusta, o palpite de um dia não é mais reproduzível. Re-arquivar na mesma data
(ex.: pós-`record`) faz **merge por jogo**: o palpite da manhã de um jogo que já virou `FINAL` é
preservado, nunca sobrescrito.

**Blend com odds de mercado (opcional):** `data/editions/<edição>/odds.csv`
com `match_id,home,draw,away` em odds decimais e, opcionalmente, `total_line,over,under`
(o mercado de **over/under** — ENG-35). A forma prática de preencher é
`uv run python scripts/fetch_odds.py` (busca 1×2 e totals da The Odds API com chave em `.env`,
**mescla** no `odds.csv`, preservando jogos já disputados — `blend-track` acumula tally).
Para editar à mão, **acrescente** jogos de cada rodada (não sobrescreva). Ferramenta tira
margem da casa, combina odds com probabilidades do modelo (média geométrica ponderada, peso
`blend_weight`) e ajusta palpite; com totals, também ancora **taxa de gols** do placar
no mercado (sem totals num jogo, só 1×2 corrigido). Edição 2026 usa `blend_weight = 0.8`
no `scoring.toml` (escolhido com dado via `blend-track --sweep`, ENG-38 — o Brier caiu
monotonicamente com mais peso de mercado); `--blend-weight 0` ou ausência
de `odds.csv` ⇒ só modelo, sem mudança. Por que ajuda: o modelo é estatístico e cego a
escalações/lesões/motivação, que as odds capturam. Para medir se o blend está de fato
ajudando, rode `worldcup blend-track` conforme registra odds + resultados — compara o
Brier do blend vs. o do modelo-puro nos jogos já disputados com odds (e, havendo totals,
o Brier binário do over/under).

Para **reconstruir** a visão de um dia passado, use `predict --as-of AAAA-MM-DD`: reajusta o modelo
usando só os resultados conhecidos até a véspera daquela data e grava
`history/<data>.reconstruido.{csv,md}` (marcado como reconstruído, com aviso),
**sem tocar em `out/`** — os palpites vivos da campanha ficam intactos. `--as-of` com a data de hoje
reproduz exatamente o run real do dia. Os reconstruídos são **regeneráveis sob demanda**, então
ficam fora do git (`.gitignore`); só os runs reais (`--archive`) são versionados em `history/`.

## Estrutura

- `src/worldcup/` — código (modelo, pontuação, simulação, CLI).
- `data/editions/<ano>/` — spec do formato + jogos + pontuação de cada edição (orientado a dados),
  mais `BOLAO.md`, o diário de campanha do bolão (decisões não rederiváveis dos dados).
- `data/historical_results.csv` — base histórica compartilhada, baixada pelo `fetch-data`.
- `docs/SPEC.md` — **especificação técnica e metodologia**
  (matemática do modelo, fórmula de pontuação, simulação, validação) com derivações e exemplos
  numéricos.
- `docs/C4.md` — **arquitetura no modelo C4** (Contexto → Container → Componentes → Dinâmica),
  em diagramas Mermaid derivados do grafo de imports real.
- `docs/PRD.md` — **requisitos de produto** (o quê e por quê), com glossário em `docs/GLOSSARIO.md`.
- `docs/MODEL_CARD.md` — **cartão do modelo** (uso pretendido, métricas, calibração, limitações).
- `docs/DATA.md` — **proveniência e licenciamento dos dados** (fontes, versionamento, itens de IP).
- `AGENTS.md` (+ symlink `CLAUDE.md`) — guia para quem desenvolve/mantém o projeto.
- `CHANGELOG.md` — mudanças relevantes por versão (Keep a Changelog); tags `vX.Y.Z` marcam marcos.

## Ajustar a pontuação do seu grupo

A pontuação real é configurada pelo admin do grupo. Edite `data/editions/2026/scoring.toml` para
casar com o sistema (I / Simplificado / Só-vencedor) e o peso por fase do seu grupo. O default já
vem calibrado como **Sistema I** (base 1–13 + bônus reais do app) **+ Equilíbrio gradual**.

## Validação e estratégia

Rode `uv run worldcup backtest --edition 2022` para ver quantos pontos o modelo teria feito na Copa
de 2022 (só com jogos anteriores). Com régua de pontos **corrigida**
(bônus hierárquicos, não somados), subir risco **não** melhora pontos confiavelmente: no backtest
2022 o conservador (`risk=0.0`) faz mais que agressivo (`1.0`), fiel (`0.5`) fica no meio —
resultado ruidoso de uma Copa. Alavanca de ranking é **acurácia** (blend de odds), não ousadia;
a edição 2026 fixa `risk = 0.5` no `scoring.toml` (fiel, maximiza pontos esperados). ⚠️ O default
do campo **ausente** é `0.6`, não `0.5` — fixe o valor explicitamente em cada edição.

**Eficiência da sua campanha** — quanto dos pontos que o tool renderia você capturou:

```bash
uv run python scripts/efficiency.py --edition 2026 --my-points 143 --leader 173 [--compare-archive]
```

Para cada jogo já disputado, pontua contra o resultado real o palpite que o tool mostrava na manhã
do jogo — a soma é o **teto** que seguir o tool à risca renderia; `eficiência = seus_pontos / teto`.
O teto de cada jogo é **congelado** na primeira medição em `ceiling.csv` (ENG-34), preferindo o
snapshot real de `history/` e caindo na reconstrução as-of só sem arquivo — assim o número não
oscila entre rodagens; `--reset-ceiling` recongela do zero (ex.: após um fix de scoring).
`--compare-archive` confronta com os snapshots reais de `history/` e lista onde a reconstrução
diverge (quanto do gap é ruído de reconstrução vs. dias sem snapshot arquivado). Cobre a fase de
grupos com pontuação exata; no mata-mata pontua os 90' **com o peso de fase** (R32–SF ×2, final ×4)
— contra o placar do tempo normal (`regulation.csv`, ENG-45) quando houve gol na prorrogação — e
soma os bônus de prorrogação/pênaltis (+3 ×peso) quando a base martj42 (`penalty_winner`) confirma
o desfecho; em jogo empatado nos 90' ainda sem shootout na fonte, só esse bônus fica de fora do
teto (ENG-27).

**Endgame de bolão (ENG-36)** — bolão é jogo **diferencial**: seguir o E[pts]-máximo pontua junto
com o pelotão (que aglomera no favorito) e **preserva** sua posição; ranking só muda quando o
palpite diverge e a divergência acerta. A simulação de pelotão quantifica:

```bash
uv run python scripts/eng36_pool_sim.py --edition 2026 --my-points 285 --leader 337 --pool-size 60
```

Compara políticas (fiel / placar alternativo / zebra na final / SF / QF / **empate na final** —
ENG-39) em P(#1), P(top-3) e E[pts]. Resultado (02/07, 3000 torneios, standing 295/353/21º):
**atrás**, `empate-final` (empata os 90' da final com o melhor placar por E[pts] + camadas
prorrogação/pênaltis) domina a zebra — P(top-3) 8,4% vs 5,5% **a custo zero de E[pts]** — e a
vantagem cresce sob o gerador realista: `--draw-inflate-final P` infla P(empate 90') **só do
gerador** da final (5 das 8 finais desde 1994 empataram nos 90', ~60%, vs ~28% no modelo) e a
0,60 dá P(#1) 4,9% / P(top-3) 14,3% contra 1,2%/3,8% da zebra; **na frente**, fiel domina.
Para aplicar na prática: `worldcup predict --pool-behind` gera o **empate** nos 90' (melhor
placar da diagonal por E[pts] + camadas de prorrogação/pênaltis) **só nos jogos de peso máximo**
(a final) — ENG-40; `--pool-behind zebra` mantém a política antiga do ENG-36 para comparação na
véspera. Use apenas na manhã da final e apenas se estiver **atrás** no ranking.

**Apresentação do projeto** — um deck HTML autocontido (tema "Placar Noturno", 16:9, navegável) que
explica o projeto para leigos (conceitos, diferenciais, resultados e futuro):

```bash
uv run python scripts/build_presentation.py --docs   # gera out/ e docs/apresentacao.html
```

Abra o HTML no navegador (← → navegam; `Ctrl+P` salva um PDF/handout). É self-contained
(sem CDN; imagens CC embutidas em base64). A versão pronta vive versionada em
[`docs/apresentacao.html`](docs/apresentacao.html); ao editar o script, **regenere com `--docs`**
e inclua o HTML no mesmo commit. Os números da campanha (jogos, pontos, favoritos, bracket,
Brier) vivem em `data/editions/<edição>/presentation.toml` — agnóstico à edição, como o resto dos
dados; atualize o TOML (não o script) a cada rodada.

`scripts/update_presentation_data.py --edition 2026` atualiza os campos **deriváveis** desse
TOML (jogos disputados, favoritos ao título, Brier do blend, melhorias do backlog) a partir do
estado atual — parte da rotina diária da skill `palpites-copa` (passo 5.5), logo após repalpitar.
Só `campanha.pontos`/`eficiencia_pct` (seu placar real) e `campanha.fase`/`bracket_destaque.*`
(curadoria editorial) continuam manuais.

## Limitações conhecidas

(Resumo para o usuário; a fonte canônica, com o detalhamento técnico, é
[`docs/SPEC.md`](docs/SPEC.md) §9.2.)

- **Modelo baseado em resultados**: pondera muito os jogos recentes, então favorece quem vem
  bem (seleções da América do Sul aparecem fortes) e pode subestimar potências em má fase
  recente. É o comportamento esperado de um modelo puramente estatístico.
- **Desempates de grupo** são simplificados (pontos → saldo → gols → sorteio); o confronto direto
  oficial não é aplicado.
- **Melhores terceiros**: a alocação aos slots usa casamento por restrição de grupos
  (Annex C da FIFA aproximado) e **pode divergir** da tabela oficial — há mais de um emparelhamento
  válido. Dá para cravar a alocação oficial da combinação realizada via
  `[group_stage.third_allocation]` no `tournament.toml` (feito em 2026). Depois da fase de grupos,
  **confira os 8 confrontos dos 16-avos** com o bracket oficial.

## Licença

[MIT](LICENSE).
