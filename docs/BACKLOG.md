# BACKLOG — engenharia

Backlog de engenharia do projeto, **rastreado e vivo**. Fonte de verdade dos itens de melhoria;
o status de um item vira ✅ **no mesmo commit** que o resolve
(mesma disciplina de sincronia de artefatos do `AGENTS.md`). Leia no início da sessão quando for
trabalhar em melhorias.

**Prioridade:** P1 (correção/dados) · P2 (lacuna real) · P3 (boa prática incremental).
**Status:** 🔴 todo · 🟡 fazendo · ✅ feito · ⚪ descartado.
**Refs:** aponte para **símbolos** (`módulo.função`), não `arquivo:linha` — número de linha
envelhece em silêncio.

Semeado em 2026-06-13 a partir da avaliação de engenharia do projeto.

## Índice

| ID | Pri | Área | Status | Item |
|----|-----|------|--------|------|
| [ENG-1](#eng-1) | P1 | sync | ✅ | Reencontro de seleções colapsa resultado indexado por par |
| [ENG-2](#eng-2) | P2 | backtest | ✅ | Mando do anfitrião não aplicado no backtest |
| [ENG-3](#eng-3) | P2 | model | ✅ | Convergência do otimizador ignorada |
| [ENG-4](#eng-4) | P3 | observabilidade | ✅ | `logging` no lugar de `print()` na biblioteca |
| [ENG-5](#eng-5) | P3 | fetch_data | ✅ | Validar schema do CSV baixado |
| [ENG-6](#eng-6) | P3 | cli | ✅ | Separar camada de render (`render.py`) |
| [ENG-7](#eng-7) | P3 | tipos | ✅ | mypy não cobre `tests/` |
| [ENG-8](#eng-8) | P3 | ci | ✅ | Sem medição de cobertura |
| [ENG-9](#eng-9) | P3 | tests | ✅ | Guardrail: toda seleção da edição tem tradução PT |
| [ENG-10](#eng-10) | P3 | release | ✅ | Versão estática, sem CHANGELOG/tags |
| [ENG-11](#eng-11) | P3 | processo | ✅ | Vigiar proporcionalidade doc/código; consolidar docs |
| [ENG-12](#eng-12) | P2 | scoring | ✅ | Bônus de prorrogação/pênaltis definidos mas não computados |
| [ENG-13](#eng-13) | P3 | format_engine | ✅ | Default morto `n_sims=8000` em `monte_carlo()` |
| [ENG-14](#eng-14) | P2 | scoring | ✅ | Curva de pontos base não reproduz o app (50%→3, não 2) |
| [ENG-15](#eng-15) | P2 | fetch_data | ✅ | `sync-results` depende de fonte única (martj42) sem fallback |
| [ENG-16](#eng-16) | P2 | model | ✅ | Fit do Dixon-Coles não converge em `maxiter=500` com a base atual |
| [ENG-17](#eng-17) | P2 | model | ✅ | Defaults do `FitConfig` (meia-vida/ridge) subótimos no backtest |
| [ENG-18](#eng-18) | P2 | backtest | ✅ | Backtest mede só acerto de 1×2, não calibração probabilística (Brier/reliability) |
| [ENG-19](#eng-19) | P2 | model | ✅ | Blendar probabilidades do Dixon-Coles com odds de mercado (des-vigadas) |
| [ENG-20](#eng-20) | P2 | tests/ci | ✅ | Pipeline `predict` não roda no CI; `sync`/`pipeline` com cobertura baixa (34%/43%) |
| [ENG-21](#eng-21) | P3 | processo | ✅ | Podar/consolidar a camada meta pós-ENG-19 (extensão recorrente do ENG-11) |
| [ENG-22](#eng-22) | P3 | backtest | ✅ | Monitor de regime de empates na edição viva (tilt só se estatisticamente significativo) |
| [ENG-23](#eng-23) | P1 | scoring | ✅ | Bônus de placar somados em vez de hierárquicos (inflam pontos, enviesam contra empate) |
| [ENG-24](#eng-24) | P2 | scoring | ⚪ | Base (1–13) usa a probabilidade interna do app (inobservável) ⇒ eficiência só aproximada |
| [ENG-25](#eng-25) | P3 | format_engine | ⚪ | Tabela oficial completa (495 combinações) da alocação de terceiros (Annex C) |
| [ENG-26](#eng-26) | P2 | scoring | ⚪ | Recalibrar `base_log_coeff` (7,55→~8,4) com telas reais de jogo; ordem de arredondamento na fase ×2 |
| [ENG-27](#eng-27) | P2 | scoring/efficiency | ✅ | Peso de fase (×2/×4) nunca aplicado ⇒ teto de mata-mata subcontado, eficiência infla no KO |
| [ENG-28](#eng-28) | P2 | blend/odds | ✅ | `fetch_odds` só casa jogos de grupo ⇒ blend DESLIGADO em todo o mata-mata (peso 2×/4×) |
| [ENG-29](#eng-29) | P3 | knockout | ✅ | Palpite de prorrogação/pênaltis por heurística de limiar, não E[pts] (ignora P(ET empatada)) |
| [ENG-30](#eng-30) | P3 | pipeline/render | ✅ | Jogos de KO FINAL não mostram prorrogação/pênaltis/quem avançou (dados existem) |
| [ENG-31](#eng-31) | P3 | cli | ✅ | `worldcup status`: briefing read-only de start-of-day (rehidrata contexto em 1 saída) |
| [ENG-32](#eng-32) | P3 | scoring/knockout | ✅ | Palpite de 90' no KO tende a 0×0 (empate→pênaltis) e zera quando o favorito vence nos 90' — é E[pts]-ótimo ou artefato? |
| [ENG-33](#eng-33) | P1 | cli/history | ✅ | Re-arquivar depois de registrar resultados sobrescreve o snapshot do dia e perde os palpites da manhã |
| [ENG-34](#eng-34) | P2 | efficiency | ✅ | Teto reconstruído do `efficiency.py` não é estável entre rodagens — eficiência muda sem o usuário mudar nada |
| [ENG-35](#eng-35) | P2 | blend/odds | ✅ | Blend só corrige o 1×2 — a forma do placar (totals) fica 100% modelo; mercado de over/under não é usado |
| [ENG-36](#eng-36) | P2 | scoring/estratégia | ✅ | Modo endgame consciente de bolão: otimizar P(top-k) contra o pelotão nos jogos de peso ×2/×4, não E[pts] |
| [ENG-37](#eng-37) | P3 | processo/docs | ✅ | Padrão de largura de linha nos `.md`: régua definida (100 caracteres) + scripts on-demand |
| [ENG-38](#eng-38) | P2 | blend/backtest | ✅ | `blend_weight` fixado por prior (0,6), nunca otimizado com dado — sweep de Brier por peso |
| [ENG-39](#eng-39) | P2 | scoring/estratégia | ✅ | Simulador de endgame é juiz e parte: gerador = modelo, cego à subestimação de empate em final |
| [ENG-40](#eng-40) | P2 | knockout/cli | ✅ | Expor a política `empate-final` (ENG-39) no `predict` — `--pool-behind` ainda gera a zebra superada |
| [ENG-41](#eng-41) | P1 | pipeline/model | ✅ | Jogos da edição contados em dobro no ajuste quando a base histórica já os contém (peso 7.0) |
| [ENG-42](#eng-42) | P2 | pipeline/model | ✅ | Resultados de KO alimentam o fit sem o boost (peso 1.0 via base), pois o fixture guarda slots |
| [ENG-43](#eng-43) | P3 | observabilidade | ✅ | Nenhuma métrica vigia se o modelo ingeriu os resultados recentes (staleness da base é silenciosa) |
| [ENG-44](#eng-44) | P2 | model/backtest | ✅ | `CURRENT_EDITION_BOOST` (6.0) é constante mágica nunca calibrada — sweep out-of-sample de Brier |
| [ENG-45](#eng-45) | P2 | efficiency/scoring | ✅ | KO decidido por gol na prorrogação é gravado com ET ⇒ palpite de 90' pontuado contra o placar errado (teto infla) |
| [ENG-46](#eng-46) | P3 | efficiency/pipeline | ✅ | `archive_scores` é só de grupo ⇒ teto de KO congela da reconstrução (menos fiel que o snapshot real) |
| [ENG-47](#eng-47) | P3 | apresentação | ✅ | Números da campanha 2026 hardcoded em `build_presentation.py` — exigia editar código a cada rodada |
| [ENG-48](#eng-48) | P1 | eficiência | ✅ | `efficiency.py` nunca creditava o bônus de ET/pênaltis: chave de data `datetime64` vs `str` ⇒ teto subestimado, eficiência inflada |
| [ENG-49](#eng-49) | P2 | eficiência/dados | ✅ | Fontes redundantes do desfecho de KO (`shootouts.csv` vs `penalty_winner`) são escolhidas, não comparadas — redundância sem detector |
| [ENG-50](#eng-50) | P2 | eficiência | ✅ | Anomalia numérica (eficiência > 100%) vira narrativa em vez de gatilho: sem limiar nem ação prescrita, ao contrário do monitor de empates |

---

## ENG-1
**Reencontro de seleções colapsa o resultado indexado por par** · P1 · `sync.py` · ✅ feito

`sync._edition_results` monta `scores[(home, away)]` para todos os jogos da Copa do ano. Se duas
seleções se enfrentam **duas vezes** na mesma Copa com a mesma orientação na fonte
(adversários de grupo que se reencontram no mata-mata — possível no formato 2026), a segunda partida
sobrescreve a primeira no dict, e `_result_for` pode preencher o jogo de grupo com o placar
do mata-mata (ou vice-versa), **sem erro**. O valor inteiro da ferramenta é a fidelidade
dos resultados.

**Correção proposta:** indexar por `(data, par)` (ou desambiguar por estágio/data) — tanto
o `fixtures.csv` quanto a fonte têm `date`. Casar cada fixture pelo seu `date`.
**Aceite:** teste de regressão com um par que joga 2× na mesma Copa (grupo + KO) com a mesma
orientação; o jogo de grupo recebe o placar do grupo e o de KO o placar do KO. `pytest` verde.
**Commit:** 17272f2

## ENG-2
**Mando do anfitrião não aplicado no backtest** · P2 · `backtest.py` · ✅ feito

`backtest.run_backtest` chama `score_matrix(home, away, neutral)` sem `host_away`/`hosts`.
A produção usa `MatrixCache._host_away` + `edition.hosts`
(e trata o anfitrião listado como visitante). Logo, jogos do país-sede
(Qatar 2022, África do Sul 2010) são pontuados de forma diferente do caminho real — o backtest deixa
de reproduzir fielmente o que o app faria.

**Correção proposta:** passar o conjunto de anfitriões da edição-alvo ao backtest e reusar a mesma
lógica de `host_away` da produção (idealmente via `MatrixCache`).
**Aceite:** num jogo do anfitrião, a matriz do backtest == a da produção. Teste cobrindo um caso
host-away. `pytest` verde.
**Commit:** 75255bc

## ENG-3
**Convergência do otimizador ignorada** · P2 · `model.py` · ✅ feito

`minimize(...)` em `model.DixonColesModel.fit` roda com `maxiter=500` e descarta
`res.success`/`res.status`; usa `res.x` aconteça o que acontecer. Um fit não-convergido gera
previsões ruins sem nenhum sinal.

**Correção proposta:** se `not res.success`, emitir `logger.warning` (depende de [ENG-4])
com `res.message`; checar `np.isfinite` nos parâmetros. Decidir se vale subir `maxiter` quando
a base crescer.
**Aceite:** teste que força não-convergência (maxiter baixo) e verifica que o aviso é emitido sem
quebrar a saída. `pytest` verde.
**Commit:** f4ffd48

## ENG-4
**`logging` no lugar de `print()` na biblioteca** · P3 · observabilidade · ✅ feito

Tudo é `print()` no `cli.py`; a biblioteca (`model`, `sync`, `pipeline`) não tem como emitir avisos.
Decisões silenciosas hoje invisíveis: seleções descartadas pelo `min_matches`
em `DixonColesModel.fit`, não-convergência (ENG-3), alias/seleção sem tradução.

**Correção proposta:** `logging.getLogger(__name__)` na biblioteca; CLI configura handler/nível
(ex.: `--verbose`). Mantém `print()` só para a saída ao usuário.
**Aceite:** avisos saem por `logging` e são capturáveis em teste (`caplog`). `pytest` verde.
**Commit:** f364ee2

## ENG-5
**Validar schema do CSV baixado** · P3 · `fetch_data` · ✅ feito

`download_raw`/`normalize` (`fetch_data.py`) não checam as colunas da fonte. Se o `martj42` mudar
o schema, o erro estoura adiante, críptico.

**Correção proposta:** após o download, validar presença das colunas esperadas e dar `NetworkError`
(ou erro dedicado) claro e cedo.
**Aceite:** teste com CSV de colunas faltando → erro explícito. `pytest` verde.
**Commit:** 061f223

## ENG-6
**Separar camada de render (`render.py`)** · P3 · `cli` · ✅ feito

`cli.py` tem ~500 LOC e mistura argparse, handlers, escrita CSV e ~200 linhas
de `render_markdown`/`render_html`. Coesão/teste isolado da apresentação.

**Correção proposta:** extrair render (MD/HTML/CSV) para `render.py`; `cli.py` só orquestra.
**Aceite:** sem mudança de comportamento; render testável sem a CLI; `ruff`/`mypy`/`pytest` verdes.
**Commit:** 51f24a5

## ENG-7
**mypy não cobre `tests/`** · P3 · tipos · ✅ feito

`pyproject` tem `files = ["src"]`; os testes não são type-checked.

**Correção proposta:** incluir `tests` no mypy (ou config separada), corrigindo o que aparecer.
**Aceite:** `uv run mypy` passa cobrindo `tests/`.
**Commit:** 4686edf

## ENG-8
**Sem medição de cobertura** · P3 · ci · ✅ feito

Os testes rodam, mas nada mede o que ficou de fora (ex.: o caso do ENG-1 não tinha teste).

**Correção proposta:** `pytest-cov` + relatório no CI (e, opcional, um piso de cobertura).
**Aceite:** CI reporta cobertura; decisão registrada sobre piso (ou ausência).
**Decisão:** piso `fail_under = 65` (cobertura medida ~74%) — pega regressões grandes sem
fragilidade; subir conforme `sync`/`pipeline` (hoje 34%/40%) ganharem testes de integração.
**Commit:** 43bcacb

## ENG-9
**Guardrail: toda seleção da edição tem tradução PT** · P3 · tests · ✅ feito

Seleção sem entrada em `teams._PT_DISPLAY` cai no inglês **silenciosamente**.

**Correção proposta:** teste que afirma que todo time em `groups.csv` de cada edição tem `display`
diferente do canônico (ou entrada explícita no mapa).
**Aceite:** teste cobre a edição 2026; falha se faltar tradução. `pytest` verde.
**Commit:** 593568f

## ENG-10
**Versão estática, sem CHANGELOG/tags** · P3 · release · ✅ feito

`version = "0.1.0"` fixo, sem `CHANGELOG` nem tags. Para algo agnóstico a edição que sobrevive
a várias Copas, dificulta rastrear o que mudou entre edições.

**Correção proposta:** adotar `CHANGELOG.md` (Keep a Changelog) + tags por marco; avaliar versão
dinâmica via `hatch`.
**Aceite:** CHANGELOG criado com o histórico recente; convenção de tag definida.
**Resolução (2026-06-13):** adiado e reaberto no mesmo dia (a pedido) — implementado
em escopo **enxuto**: `CHANGELOG.md` (Keep a Changelog) semeado com o marco `0.2.0`, bump de versão
em `pyproject`/`__init__`, convenção de tag `vX.Y.Z` documentada e tag `v0.2.0` criada. Versão
dinâmica via `hatch` ficou de fora (baixo valor p/ mantenedor único); revisitar se a manutenção
do bump manual em dois arquivos incomodar.
**Commit:** 94fe954

## ENG-11
**Vigiar proporcionalidade doc/código; consolidar docs** · P3 · processo · ✅ feito

A camada *meta* (docs/processo/skills) cresceu a ~64% do tamanho do código
(1.366 linhas de md vs ~2.135 LOC) e a regra de sincronia de artefatos obriga tocar vários docs
por mudança — o andaime arrisca ficar mais pesado que a casa. Não é bug; é vigilância
de proporcionalidade.

**Correção proposta:** tratar "criar novo doc/skill/hook" como decisão que precisa se pagar;
preferir **consolidar a adicionar**. Revisar sobreposição entre `AGENTS.md`, `README.md`
e `docs/SPEC.md` periodicamente e eleger um canônico por assunto (já feito p/ comandos → README).
**Aceite:** revisão de sobreposição registrada; nenhuma seção duplicada entre os três docs sem
um canônico declarado. (Item de vigilância recorrente — fechar quando a revisão for feita; reabrir
a cada salto de doc.)
**Revisão (2026-06-13):** canônicos declarados — comandos → `README.md`; arquitetura/convenções →
`AGENTS.md`; metodologia/matemática → `docs/SPEC.md`; **limitações → `docs/SPEC.md` §9.2** (era
a única duplicada sem canônico: estava nos três docs; README mantém resumo ao usuário, AGENTS aponta
para o SPEC). Demais sobreposições são audiências distintas
(ex.: README §Estrutura ≠ AGENTS §Arquitetura). Reabrir a cada salto de doc/skill.
**Commit:** 8e4616d

## ENG-12
**Bônus de prorrogação/pênaltis definidos mas não computados** · P2 · `scoring.py` · ✅ feito

`scoring.toml` define `extra_time = 3.0` e `penalties = 3.0`
(bônus oficiais do app, confirmados nas telas de regras), mas `Scorer.points()` nunca lê esses
parâmetros — só computa base + exact + goal_diff + winner_goals + loser_goals + goleada.
Consequências: (a) o **backtest subestima** os pontos em jogos de mata-mata decididos
na prorrogação/pênaltis; (b) a config tem valores mortos que enganam quem for ajustar a pontuação.
(Para a escolha do placar de 90' é neutro: o bônus de ET/pên independe do placar escolhido.)

**Correção proposta:** método `Scorer.knockout_bonus()` que pontua os palpites de prorrogação/
pênaltis (`KnockoutPrediction.extra_time`/`penalty_winner`) contra o desfecho real, e integrá-lo
ao backtest onde o desfecho é determinável (ex.: `shootouts.csv` indica ida a pênaltis e vencedor).
Cuidado: o histórico nem sempre separa placar de 90' vs prorrogação (ver SPEC §9.2) — escopo
e limites a definir.
**Aceite:** teste cobrindo um KO decidido nos pênaltis → bônus +3 concedido; backtest usa o desfecho
real. `pytest` verde.
**Progresso (c00dc93):** método `Scorer.knockout_bonus()` implementado e testado
(config não está mais morta).
**Bloqueio descoberto:** o `historical_results.csv` local (saída do `fetch_data.normalize`) não tem
coluna de **fase** nem dados de **pênaltis** (`shootouts`), então o backtest não identifica jogos
de KO nem o desfecho ET/pênaltis. Fechar exige estender o pipeline: persistir `shootouts`
no histórico + inferir/rotular a fase. Sub-tarefa de dados antes de wirar no backtest.
**Resolução (0df13f6):** `fetch_data` agora **mescla** `shootouts.csv` na base histórica como coluna
`penalty_winner` (canônico, casado por `date+home+away`; `OUTPUT_COLUMNS`, `_merge_penalty_winner`,
`fetch` baixa best-effort, `load_historical` compat com bases antigas).
O `backtest._knockout_bonus_for` concede os bônus de KO
(`Scorer.knockout_bonus`: +3 ida aos pênaltis, +3 vencedor) nos jogos com `penalty_winner`, via
`predict_knockout` sobre a matriz as-of; o relatório conta os jogos de pênaltis. Testes: merge
no `normalize` (com/sem shootouts) + bônus de KO no backtest (jogo de pênaltis → 6/3/0). Validado
end-to-end: **Copa 2022 reconhece 5 jogos de pênaltis** e soma o bônus.
**Limitação aceita (não é o bug, é a fonte):** o martj42 não traz a **fase** nem separa 90'
de prorrogação, então jogos decididos **dentro da prorrogação** não são identificáveis e **não**
recebem bônus de ET (documentado em SPEC §9.2). A edição **viva** não sofre disso — `sync` resolve
o bracket real com os shootouts.
**Commit:** 0df13f6

## ENG-13
**Default morto `n_sims=8000` em `monte_carlo()`** · P3 · `format_engine.py` · ✅ feito

`format_engine.monte_carlo()` tem assinatura `n_sims: int = 8000`, mas o caminho real (CLI/pipeline)
sempre passa `5000`, e o SPEC §7.1 diz "padrão 5000". O default da assinatura nunca é exercitado
e diverge da documentação — confunde quem lê a função isolada.

**Correção proposta:** alinhar o default da assinatura a 5000
(fonte única do default no `pipeline`/CLI) ou remover o default e exigir o parâmetro. Verificar
se algum teste depende de 8000.
**Aceite:** default coerente com o caminho real e com o SPEC; `pytest` verde.
**Commit:** e4b23bb

## ENG-15
**`sync-results` depende de fonte única (martj42) sem fallback** · P2 · `fetch_data.py` · ✅ feito

`fetch_data.DEFAULT_URL` aponta exclusivamente para o CSV do repositório
`martj42/international_results`. Na Copa 2026, a latência típica da fonte é de 1-2 dias —
os placares de J5–J8 (2026-06-13) não estavam disponíveis no dia seguinte, forçando busca manual
na web e registro via `worldcup record`. Conforme a Copa avança (vários jogos por dia), o risco
de ficarem defasados é alto e o custo manual cresce.

**Correção proposta:** suportar lista ordenada de fontes em `fetch_data.fetch()`. Candidatos:
- Fonte primária: martj42 (já existente, histórico completo).
- Fonte secundária: CSV público de resultado da Copa atual
  (ex.: API-football, football-data.org, ou outro dataset que atualize no mesmo dia).
  Alternativamente, expor `--source-url` na CLI para que o operador passe uma URL alternativa sem
  mudar o código.
A lógica: tentar a primária; se falhar ou se os jogos esperados não aparecerem, tentar a próxima.
**Aceite:** `fetch-data` (ou `sync-results`) obtém os placares do dia corrente sem intervenção
manual quando martj42 estiver atrasada; teste de unidade cobre o fallback (mock de URLs). `pytest`
verde.
**Resolução:** `download_from_urls(urls)` em `fetch_data.py` tenta cada URL em cascata
(`NetworkError`/`DataSourceError` dispara o próximo); `fetch()` e `sync_results()` aceitam a lista;
CLI expõe `--source-url` (appendável) em `fetch-data` e `sync-results`. 3 testes novos.
**Commit:** 7e2f360

## ENG-14
**Curva de pontos base não reproduz o app (50%→3, não 2)** · P2 · `scoring.py` · ✅ feito

A tela do "Simulador de Pontos" do app mostra **50% de chance → 3 pts** (base, sem bônus). A fórmula
do projeto, `_base_points`, no risco "fiel" 0.5 usa `base = (1/p)^(2·risk) = 1/p`, que em p=0,5
dá **2 pts**. Os extremos batem (p→1 → 1 pt = `base_min`; zebra → 13 = `base_max`), mas
o **meio da curva** não. Implicação: a curva real do app é mais íngreme que `1/p` (γ "fiel"
implícito ≈ log2(3) ≈ 1,585 → equivaleria a `risk ≈ 0,8`),
ou seja **o projeto sub-recompensa zebra** vs. o app — afeta `best_prediction` e a estratégia
de risco.

**Correção proposta:** coletar 3–4 pontos `(probabilidade, pontos)` do Simulador do app
(ex.: 50/40/ 30/20/10%), ajustar a forma de `_base_points` (expoente/curva) para reproduzi-los,
e **desacoplar** a curva-base-do-app do knob `risk` (hoje os dois são o mesmo γ — conceitualmente
distintos: a curva é fixa do app, `risk` é estratégia do palpiteiro). Revisar a calibração
de "risk=0.5 = fiel".
**Aceite:** `_base_points` reproduz os pontos observados do app dentro de ±0,5 pt nos pontos
coletados; teste com os pares observados. `pytest` verde.
**Bloqueado por:** coleta dos dados do Simulador (depende do usuário).
**Resolução (43f2be2):** dados do Simulador coletados (80%→2, 50%→3, 15%→7, 5%→11). Curva trocada
para log-linear `base = 1 + 7.55·log10(1/p)` (reproduz os 4 pontos ±0.5) e `risk` **desacoplado**
da régua → migrou para um tilt na escolha (`best_prediction`), preservando "0.5 = E-max puro".
Backtest 2022 recalculado.
**Refinar depois:** com mais pontos do Simulador (ex.: 40/30%) dá para apertar o coeficiente; o teto
de 13 e o arredondamento são hipóteses a confirmar.
**Commit:** 43f2be2

## ENG-16
**Fit do Dixon-Coles não converge em `maxiter=500` com a base atual** · P2 · `model.py` · ✅ feito

Desde que os resultados da Copa 2026 passaram a realimentar o ajuste
(jogos registrados recebem peso alto), `model.DixonColesModel.fit` emite o aviso de não-convergência
do ENG-3 em todo run de `sync-results`/`predict`:
`ajuste do modelo não convergiu (maxiter=500): STOP: TOTAL NO. OF F,G EVALUATIONS EXCEEDS LIMIT`.
O guardrail do ENG-3 está funcionando (o aviso aparece e a saída segue usável), mas a **causa** não
foi tratada: o otimizador esgota o orçamento de avaliações antes de convergir. Com a base crescendo
(mais seleções/parâmetros + pesos altos nos jogos recentes), o `res.x` retornado pode estar longe
do ótimo — previsões potencialmente piores sem sinal além do aviso. Observado em 2026-06-15
(12 jogos registrados).

**Correção proposta:** investigar a não-convergência — (a) subir `maxiter`/`maxfun` do `minimize`
e medir se converge e quanto custa em tempo; (b) avaliar escala/normalização dos parâmetros
ou um chute inicial melhor (warm start) para acelerar; (c) checar se o peso alto dos jogos da Copa
desequilibra a verossimilhança. Decidir um teto de iterações que convirja na base típica de uma Copa
em andamento sem regredir o tempo de run de forma relevante.
**Aceite:** em um run representativo com ~12+ jogos da edição 2026 registrados, `fit` converge
(`res.success`/sem aviso) dentro de um tempo aceitável; teste/medição registrando o antes/depois
(iterações até convergir ou ausência do warning). `pytest` verde.
**Diagnóstico:** o limite que mordia era o `maxfun` default do scipy (15000), **não** o `maxiter`.
Sem `jac`, o gradiente saía por diferenças finitas
(~2n+1 = ~448 avaliações por gradiente nos 447 params), esgotando o maxfun em **27 iterações**.
Subir `maxiter` sozinho não muda nada. Medições na base real (19.677 jogos): atual = não-converge,
17s, nfev≈15.2k; força bruta (`maxfun=500k`) = converge mas **233s**;
**jac analítico = converge em 1.7s**, mesmo ótimo (neg_ll 3306.37 vs 3306.39). Impacto comprovado
nos palpites: Δxg de até **0,36 gol** entre o fit não-convergido e o convergido
(ex.: Brasil×Croácia 1.88→1.53), `max|Δataque|`≈1,5 — não era cosmético.
**Resolução (0934fcc):** gradiente analítico da log-verossimilhança
(Poisson + correção Dixon-Coles `tau` + ridge, com máscara na região do `clip`) passado via
`jac=grad` ao `minimize`. Teste de regressão valida o jac contra diferenças centrais nos 4 ramos
de placar baixo do `tau`; o fixture sintético ganhou sinal de mando real (era simétrico → `home_adv`
convergido ~0, deixava os testes de mando no fio da navalha — falso-passe por não-convergência).
**Validação (backtest, mesmo código alternando só o gradiente, determinístico):** o fit convergido
melhora os pontos do bolão (Sistema I, risk 0.5, 64 jogos/Copa) em **todas** as 4 Copas, nunca pior
— 2010 +2 (303→305), 2014 +14 (205→219), 2018 +14 (257→271), **2022 +37 (170→207)**. A `% resultado`
(acerto de vencedor/empate) fica **estável em 56%** com o fit convergido, vs. 42–56% oscilando
com o não-convergido
(a não-convergência parava a distâncias variáveis do ótimo — ruído, pior caso 2022: 42%→56%).
O `% placar exato` quase não muda — o ganho vem de acertar o lado certo.
**Commit:** 0934fcc

## ENG-17
**Defaults do `FitConfig` (meia-vida/ridge) subótimos no backtest** · P2 · `model.py` · ✅ feito

Os defaults `halflife_years=2.5` e `ridge=0.05` (`model.FitConfig`) ficam perto do **pior** ponto
de uma varredura de hiperparâmetros no backtest das 4 Copas (2010/14/18/22, 256 jogos). Quase toda
config da grade bate o atual. Surgiu da análise dos 12 jogos da Copa 2026: o motivo do baixo acerto
não é a régua de empate
(`best_prediction` é E-max ótimo; nunca palpitar empate é correto sob o sistema de pontos), e sim
a calibração das forças.

**Correção proposta:** retunar os defaults para `halflife_years=2.0`, `ridge=0.10` (mais shrinkage
regulariza forças com poucos dados; meia-vida menor pesa um pouco mais a forma recente). Atualizar
`docs/SPEC.md` (cita "meia-vida padrão 2,5 anos"). Refino futuro: grade mais fina + incluir pesos
de torneio/`max_xg`.
**Aceite:** validação **leave-one-World-Cup-out**
(escolhe a config nas outras 3 Copas, avalia na de fora) com ganho positivo — não pode ser overfit
in-sample. Teste documenta os defaults escolhidos.
**Evidência (LOO-CV):** a config `hl=2.0, rg=0.10` vence em **todas as 4 dobras**
(não é overfit: generaliza para a Copa de fora) — 2010 +20, 2014 +40, 2018 +25, 2022 +7;
total **+92 pts em 256 jogos (+9,2%)** vs. os defaults atuais. Combina com o ganho do [ENG-16]
(mesmo motor).
**Resolução (57bb420):** `FitConfig.halflife_years` 2.5→2.0 e `ridge` 0.05→0.10; SPEC.md atualizado
(meia-vida 2,0) e teste `test_fitconfig_calibrated_defaults` trava a calibração
(mudança deve re-rodar o LOO-CV).
**Refino (grade fina + pesos de torneio):** varredura 3D `halflife×ridge×tournament_gamma`
(gamma = expoente de nitidez `peso^gamma` aplicado só à verossimilhança, não ao `is_major`),
hl∈{1.5,2.0,2.5,3.0} × rg∈{0.08,0.10,0.15} × gamma∈{0.5,1.0,1.5,2.0,2.5}, validada LOO-CV.
**Resultado negativo:** `hl=2.0, rg=0.10, gamma=1.0` é o melhor in-sample **e nas 4 dobras** —
gamma=1.0 (identidade) ótimo, afiar/achatar pesos de torneio não ganha nada;
os `_TOURNAMENT_WEIGHTS` já estão bem calibrados. Ótimo é interior na grade (não é borda). O hook
`tournament_gamma` foi prototipado e **revertido** (config morta — ENG-11). Os defaults do 57bb420
ficam confirmados.
**Commit:** 57bb420

## ENG-18
**Backtest mede só acerto de 1×2, não calibração probabilística** · P2 · `backtest.py` · ✅ feito

`backtest.run_backtest` reporta `result_pct` (acertou vencedor/empate) e `exact_pct`
(cravou o placar),
mas **não mede se as probabilidades P(mandante)/P(empate)/P(visitante) são calibradas** — i.e.,
se em jogos a que o modelo deu ~30% de empate, ~30% de fato empatam. Acerto de 1×2 é uma métrica
de classificação (depende do argmax); calibração é uma métrica de probabilidade (depende da massa).
São independentes: o modelo pode acertar 56% dos resultados com P(empate) sistematicamente baixa,
e isso enviesaria a régua de pontos base (que escala com `1/p`), as sims de campeão/avanço
e a própria decisão de quando vale arriscar.

Surgiu da análise dos 16 primeiros jogos da Copa 2026: 8/16 empates reais (50%) vs. P(empate) média
de 25,8% que o modelo atribuiu, e 0/16 empates palpitados. Em 16 jogos isso é variância
(~2σ; o backtest de 256 jogos fixa o acerto de 1×2 em ~56%), **não** evidência de defeito — mas é
exatamente a pergunta que um diagnóstico de calibração responde com base estatística, em vez
de reagir a uma amostra pequena. Decide, com evidência, se há algo a corrigir (ex.: limite do `rho`
da correção Dixon-Coles, hoje `model.rho`≈−0,078, ou termo específico de empate) ou se a calibração
já está boa e os 38% de 2026 são só azar.

**Correção proposta:** estender `backtest.run_backtest`/`BacktestResult` para computar, sobre
os jogos de teste (agregável nas 4 Copas via `_WORLD_CUP_START`), a partir
do `outcome_probs_from_matrix` de cada confronto:
- **Brier score multiclasse** sobre o vetor (P_mandante, P_empate, P_visitante) vs. o resultado
  one-hot — métrica única de calibração+resolução;
- **curva de confiabilidade** por faixa de probabilidade prevista (bins, ex.: 0–10%,…,90–100%):
  frequência observada vs. prevista, **por classe de resultado** (com foco no empate, a suspeita).
Reportar no `_print_report`. Independe de `risk` (é do modelo, não da estratégia de escolha).

**Aceite:** (1) teste de regressão valida o Brier num caso sintético de probabilidade conhecida
(ex.: previsão determinística certa → 0; uniforme → valor fechado) e a atribuição de bins
da reliability; (2) rodar o diagnóstico nas 4 Copas e **registrar aqui** o veredito — P(empate) é
calibrada ou não? — fechando a dúvida levantada na Copa 2026. Se miscalibrada, abrir item-filho
para o ajuste do modelo (não fazê-lo neste item — aqui é só medição).
**Evidência (veredito, 256 jogos · 2010/14/18/22 · `pooled_draw_calibration`):** Brier
multiclasse **0,578** (< 0,667 uniforme → o modelo tem resolução). Confiabilidade do empate, faixas
povoadas: 20–30% (144 jogos) previsto 26,4% vs observado 20,8%; 30–40% (92 jogos) previsto 32,5% vs
observado 26,1%. Global: P(empate) prevista média **27,9%** vs. frequência real **22,3%**.
**Veredito: o modelo NÃO subestima empates — se algo, os superestima levemente**
(a correção Dixon-Coles `rho`, hoje ≈−0,078, já puxa a massa para cima). Logo o 0/8 em empates
no início da Copa 2026 (P(empate) média de 25,8% naqueles 16 jogos vs 50% observado)
é **variância**, não miscalibração. **Não há ajuste de modelo a fazer; nenhum item-filho aberto.**
O diagnóstico fica como métrica permanente do backtest para reabrir a questão com base estatística,
não com punhado de jogos.
**Resolução (8652360):** `multiclass_brier` + `reliability_curve` (puras, testadas),
`pooled_draw_calibration` agrega as 4 Copas; `BacktestResult` ganha `brier`/`reliability_draw`
e o `_print_report` os exibe. Testes de regressão cobrem caso determinístico (0), uniforme (2/3),
pior caso (2), atribuição de bins e o limite `p=1.0`. SPEC §9.1 registra a métrica e o veredito.
**Commit:** 8652360

## ENG-19
**Blendar probabilidades do Dixon-Coles com odds de mercado (des-vigadas)** · P2 · `model`/`scoring`
· ✅ feito

O modelo é puramente estatístico: ajusta forças a partir de resultados passados
e é **cego a escalações, lesões, suspensões, motivação e dinheiro**. As **odds de fechamento**
de uma casa sharp (ex.: Pinnacle) são o melhor preditor público *calibrado* de resultado justamente
porque incorporam essa informação. Diagnóstico que motivou o item (2026-06-17, 20 jogos):
a eficiência do palpiteiro já é **100% do tool**
(seguir o `best_prediction` rende exatamente os mesmos 44 pts que o usuário fez) —
ou seja, **não há ganho a extrair jogando diferente sobre este modelo**; o teto de acurácia é
o do próprio modelo. Para subir o teto, a alavanca de maior valor é
uma **fonte de probabilidade externa** blendada, não um refino interno (ver ENG-17: afiar pesos
de torneio não ganhou nada; o `rho` da correção Dixon-Coles já calibra empate — ENG-18). **Não é**
sobre "prever mais empates" (o modelo já os superestima levemente no agregado — ENG-18); é sobre
probabilidades melhores em todos os resultados.

**Refs:** `scoring.outcome_probs_from_matrix` (saída P(mandante/empate/visitante) do modelo, hoje
única fonte), `pipeline.run`/`MatrixCache.matrix` (onde a matriz de placares é consumida),
`backtest.multiclass_brier`/`pooled_draw_calibration`
(a régua de validação do ENG-18, baseline DC-only = **Brier 0,578**).

**Correção proposta:** introduzir uma fonte de odds e um *blend* de probabilidades, mantendo
o código agnóstico à edição (odds entram como **dados** por jogo, não hardcode):
- des-vigar as odds (remover a margem da casa → probabilidades implícitas normalizadas);
- combinar com as do modelo via *logarithmic opinion pool*
  (média geométrica ponderada renormalizada) ou média linear; peso `w∈[0,1]` entre modelo e mercado
  como único hiperparâmetro;
- o blend produz a tripla (mandante/empate/visitante); decidir
  se ele **reescala a matriz de placares** (preserva o `best_prediction`/bônus de placar exato)
  ou só substitui o 1×2. Preferir reescalar a matriz para não quebrar a camada de scoring.
- onde armazenar as odds por jogo no modelo de dados da edição
  (ex.: coluna opcional em `fixtures.csv` ou arquivo `odds.csv` paralelo); ausência de odds ⇒ cai
  para DC-only (degradação graciosa, sem travar a Copa).

**Aceite (revisado 2026-06-17 — o LOO-CV multi-Copa original era inviável por falta de dados, ver
Decisão):** três gates; teste de regressão sempre verde.
- *Gate 1 — mecanismo + testes unitários:* devig/pool/rescale/blend + carga de `odds.csv`,
  com `w=0`⇒modelo e `w=1`⇒mercado. **✅ (a26cfa8).**
- *Gate 2 — default de `w` por prior de princípio:* `blend_weight` default documentado
  (~0,6, ancorado na calibração quase-ótima de odds de fechamento na literatura), **não** tunado
  em dados de seleção (que não existem grátis). Teste trava o default.
- *Gate 3 — validação prospectiva 2026:* harness que, com odds em `odds.csv` por rodada, compara
  o **Brier multiclasse** do blend(`w`) vs. modelo-puro (as-of) nos jogos disputados, acumulando
  um tally; `w` **pré-registrado** ⇒ out-of-sample por construção. Veredito registrado no `BOLAO.md`
  conforme acumula; re-tunar `w` se 2026 discordar forte.

**Decisão (2026-06-17 — fonte de dados):** pesquisa de fontes confirmou
que **odds 1X2 de jogos de seleção das Copas 2010–2018, grátis e legais, não existem** (só scraping
de OddsPortal/checkbestodds contra o ToS; The Odds API cobre só 2022, pago ~$29–99/mês;
football-data.co.uk é só ligas de clube). Logo o **LOO-CV histórico multi-Copa foi descartado**.
Alternativas avaliadas e preteridas: (a) tunar em ligas de clube e transferir — esforço alto
(ingestão + desligar o filtro FIFA) + gap clube→seleção; (b) comprar odds da Copa 2022 — 1 torneio,
sem fold para tunar, custa. **Escolhido**
(decisão do usuário): **prior de princípio + tracking prospectivo** — mais barato e a evidência
in-domain (jogos de seleção reais) acumula sozinha ao longo da própria Copa 2026.
**Progresso (a26cfa8):** **mecanismo implementado e testado**, item segue 🟡 só pela validação
empírica. Novo `blend.py` puro: `devig` (des-vig proporcional) → `log_opinion_pool`
(média geométrica ponderada, peso `w`) → `rescale_matrix` (reescala a matriz ao 1×2-alvo preservando
a forma condicional e a massa total — `best_prediction`/bônus intactos). Decisões tomadas: odds
em `odds.csv` paralelo (`match_id,home,draw,away`, decimais; **não** em `fixtures.csv` para não
poluir o arquivo canônico/hook de sync), opção **reescalar a matriz** (não só o 1×2), `w` via
`scoring.toml::blend_weight` + override `--blend-weight` (espelha o padrão do `risk`).
`pipeline.run` aplica só nos jogos com odds; sim de campeão/avanço segue DC-only. Ausência de odds
ou `w=0` ⇒ intacto. 13 testes (devig margem/erro, pool `w=0/1/0.5`, rescale alvo/massa/forma, blend
e2e `w=0/1/parcial`, carga de `odds.csv` + ausência graciosa); e2e manual confirmou o shift
dos palpites (J21 50→55% mandante; J24 14→32% após odds equilibradas).
**Resolução (7124554) — Gates 2–3:** *Gate 2:* `blend_weight = 0.6` no `scoring.toml` da 2026
(prior de princípio), travado por `test_2026_blend_weight_prior`. *Gate 3:*
`backtest.prospective_blend_report(edition, w)` + CLI `worldcup blend-track` — para cada jogo
de grupo já disputado com odds, reajusta o modelo **as-of** e compara o Brier multiclasse
do modelo-puro vs. do blend(`w`); `w` pré-registrado ⇒ out-of-sample. Degradação graciosa
(n=0 sem `odds.csv`). Testes: empty path (roda em CI) + invariante
`w=0 ⇒ Brier(blend)==Brier(modelo)` (skipif sem `historical_results.csv`, roda local). Docs: README
(`blend-track` + prior), SPEC §3.5 (validação prospectiva substitui o LOO-CV), BOLAO
(alavanca armada, dorme até `odds.csv`).
**Operacional, não bloqueia o ✅:** o veredito empírico só acumula quando houver `odds.csv` + jogos
disputados (hoje n=0); registrar no BOLAO conforme rodar `blend-track`. Re-tunar `w` se 2026
discordar forte do prior.
**Commit:** 7124554

## ENG-20
**Pipeline `predict` não roda no CI; `sync`/`pipeline` com cobertura baixa (34%/43%)** · P2 ·
`tests`/`ci` · ✅ feito

A cobertura agregada (77%) esconde que os módulos de **orquestração e correção** mais arriscados são
os menos testados: `sync.py` **34%**, `pipeline.py` **43%** — contra `model` 96%, `scoring` 93%,
`blend` 98%. Pior: o único teste que exercita o caminho real
`fit→monte_carlo→deterministic_bracket→ predict` é `skipif`-guardado por `historical_results.csv`
(gerado, gitignored, **ausente no CI**), então o **CI nunca roda o pipeline de ponta a ponta**.
Uma regressão na fiação de `pipeline.run` ou na resolução de bracket de `sync` passaria **verde**
no CI — e foi justamente `sync` o [ENG-1] (placar trocado, sem teste à época). É o ponto cego
que separa o projeto de uma nota mais alta.

**Refs:** `pipeline.run`, `sync.sync_results`/`sync._edition_results`,
`format_engine.deterministic_bracket`, e os `skipif` de `historical`
em `tests/test_backtest.py`/`tests/test_blend.py`.
**Correção proposta:** versionar um **fixture histórico mínimo/sintético**
(subconjunto pequeno ou gerado) em `tests/fixtures/`, suficiente para ajustar o modelo de uma edição
reduzida. Com ele: (a) **teste e2e de fumaça** que roda `pipeline.run` numa edição-fixture e afirma
invariantes (nº de linhas = nº de jogos; P(mandante)+P(empate)+P(visitante)=100; todo jogo previsto
tem placar; o KO resolve `avanca`); (b) testes de integração direcionados de `sync`
(resolução de bracket por resultados reais, incluindo o caso do [ENG-1]) e de `pipeline`
(realimentação; blend só onde há odds). Remover o `skipif` desses caminhos para rodarem no CI.
**Aceite:** `sync` e `pipeline` ≥ ~75% de cobertura; o caminho e2e do `predict` roda no CI
(sem `skipif`); CI verde em Python 3.11 e 3.13.
**Resolução (3372d97):** `conftest.mini_historical` gera um histórico **sintético** (round-robin
ida/volta entre 14 seleções reais da 2026, competitivo p/ passar o filtro do fit) — destrava
o caminho real sem o `historical_results.csv` (gitignored). Testes novos: **e2e**
`test_pipeline_run_e2e_invariants` (injeta o fixture, roda `pipeline.run` pré-torneio, afirma 104
linhas, P(1×2) somam 100, todo grupo tem placar, KO resolve `avanca`, título
normaliza); **integração de sync** — `_resolve_real_bracket` resolve a R32 com seleções reais,
`sync_results` preenche jogos num **clone temp** da edição (sem tocar no real), `_edition_results`
guarda reencontro como lista e filtra não-Copa + lê pênaltis. Removidos todos os `skipif`
de `historical` (o blend e2e do ENG-19 agora roda no CI).
**Cobertura: `pipeline` 43%→90%, `sync` 34%→90%, total 86%**; piso `fail_under` 65→80
(trava o ganho — fecha o gancho deixado no ENG-8). Decisão: fixture **gerado em código**
(não CSV versionado) — sem arquivo binário a envelhecer.
**Commit:** 3372d97

## ENG-21
**Podar/consolidar a camada meta pós-ENG-19 (extensão recorrente do ENG-11)** · P3 · processo · ✅
feito

O [ENG-11] é o item recorrente de proporcionalidade doc/código ("reabrir a cada salto de doc").
O trabalho do [ENG-19] nesta sessão foi um salto: blend + odds + tracking adicionaram material
em `README`/`AGENTS`/`SPEC §3.5`/`BOLAO`, um script novo (`scripts/fetch_odds.py`) e várias entradas
de `BOLAO`. A camada meta (~1.210 linhas md + backlog + skills + hooks) está em ~44% das ~2.772 LOC
de `src` — para um mantenedor único, o andaime arrisca custar mais que a casa. Não é bug; é dívida
de proporcionalidade a revisar.

**Refs:** `README.md`, `AGENTS.md`, `docs/SPEC.md`, `data/editions/2026/BOLAO.md`,
`.claude/skills/`.
**Correção proposta:** revisar a sobreposição introduzida pelo ENG-19 — a explicação do blend
aparece em README, AGENTS, SPEC §3.5 **e** BOLAO; confirmar que cada uma serve audiência distinta
e declarar um canônico (como o ENG-11 fez para "limitações → SPEC §9.2"); consolidar o que duplicou;
podar entradas obsoletas do BOLAO (a memória higieniza-se por revisão).
Preferir **consolidar a adicionar**.
**Aceite:** revisão de sobreposição registrada
(canônico por assunto declarado para o material de blend/odds); nenhuma seção duplicada sem
canônico; `BOLAO` sem entradas obsoletas. (Vigilância recorrente — fechar quando a revisão for
feita; reabrir a cada novo salto, como o ENG-11.)
**Resolução (7540ab7):** **Canônicos do material de blend/odds declarados por audiência**
(estende o esquema do [ENG-11]): *uso/como-fazer*
(formato do `odds.csv`, `fetch_odds.py`, `blend-track`, `blend_weight`) → **README**;
*arquitetura/dados/convenções* (módulo `blend.py`, data-model do `odds.csv`, "acrescentar não
sobrescrever", não versionar odds falsas, chave no `.env`) → **AGENTS**; *metodologia/matemática*
(des-vig → pool log → reescala) → **SPEC §3.5**; *registro de engenharia* → **ENG-19**; *estado
de campanha* (config ativa, veredito do tracking) → **BOLAO** (só estado, sem how-to). As três
aparições do "porquê o blend ajuda" (README/SPEC/ENG-19) são **audiências distintas**, não
duplicação — cada uma é canônica no seu doc.
**Poda do `BOLAO` (112→79 linhas):** "Estado atual" deixou de ser log de resultados
(deriváveis do `fixtures.csv`) e virou snapshot; o how-to do blend saiu (aponta p/ README);
a decisão de risco foi condensada (modelagem completa só no Histórico, sem duplicar); menções
a martj42 unificadas; a lição dos empates foi para o Histórico (lugar canônico). Nenhuma
decisão/fato não-derivável perdido.
**Vigilância recorrente: reabrir ao próximo salto de doc/skill.**
**Commit:** 7540ab7

## ENG-22
**Monitor de regime de empates na edição viva (tilt só se estatisticamente significativo)** · P3 ·
`backtest` · ✅ feito

Dados da Copa 2026 até J28
(medido com o modelo as-of): **10 de 28 jogos de grupo foram empates (36%)** contra ~26%
que o modelo espera (~1,2σ binomial — variância, não sinal, coerente com o veredito do [ENG-18]
de que o modelo é **bem calibrado** em empates sobre 256 jogos, até os superestima). Sob E-max +
Sistema I o `best_prediction` **nunca palpita empate** (palpitou 0 em 28),
então **todo empate real zera** — **10 dos 13 zeros são empates**; é a fraqueza dominante
(em jogo decidido o tool acerta 80%/100% o lado). Risco dos dois lados: **agir agora**
(forçar empates) é overfit à variância e baixa os pontos esperados; **não ter detector** deixaria
passar um regime real de empates se ele existir. Falta um monitor que separe os dois com base
estatística, não com punhado de jogos — exatamente o espírito do ENG-18, mas na **edição viva**.

**Refs:** `backtest.prospective_blend_report` (irmão: diagnóstico as-of na edição viva),
`backtest.multiclass_brier`/`reliability_curve`, `scoring.outcome_probs_from_matrix`; veredito
do [ENG-18] (modelo calibrado em empate; `model.rho`≈−0,078 já puxa massa pra empate).
**Correção proposta:** função (vizinha de `prospective_blend_report`) que, sobre os jogos de grupo
já disputados, compara a **frequência observada de empates**
com a **soma das P(empate) do modelo as-of** e devolve o desvio padronizado
(z-score binomial / p-valor). Expor via CLI (ou no `blend-track`).
**Gatilho de ação:** só quando o desvio for **≥2σ sustentado** é que um *tilt* de empate passa a ser
justificado por dados — e aí abre-se um **item-filho** para a correção do modelo
(ex.: termo específico de empate ou ajuste do `rho` para a edição). Até lá: **reportar e não agir**.
**Aceite:** função + teste em caso sintético (probabilidades/resultados conhecidos → z fechado);
roda sobre os jogos da 2026 e reporta observado/esperado/z; documenta o gatilho de 2σ e a postura
"não agir sobre variância". A correção em si **não** entra aqui (medição-só, como o ENG-18) — vira
item-filho se e quando o gatilho disparar.
**Resolução (f1c0da6):** `backtest.draw_regime_report(edition)` →
`DrawRegime(n, observed, expected, z)` com `.significant` (|z|≥2σ). A estatística pura
`draw_regime_stats(p_draws, is_draw)` calcula o z-score **Poisson-binomial**
`(observado − Σp)/sqrt(Σ p(1−p))` (cada jogo é um Bernoulli com seu P(empate)). Surge no CLI
`blend-track` (sobre **todos** os jogos de grupo disputados, não só os com odds), com veredito
"variância (não agir)" vs "⚠️ SINAL ≥2σ — abrir item-filho de tilt". O loop as-of foi extraído
para `_as_of_group_matrices`
(helper compartilhado com `prospective_blend_report` — dedup, no espírito do ENG-21). 4 testes
(z conhecido = 1,549; gatilho >2σ; vazio; report na 2026 com `observed` = empates reais).
**Veredito ao vivo (28 jogos): 10 obs vs 7,3 esp, z=+1,19 → variância, não agir** — confirma
o ENG-18. O item-filho de correção só abre se o z cruzar 2σ até o fim dos grupos.
**Commit:** f1c0da6

## ENG-23
**Bônus de placar somados em vez de hierárquicos (inflam pontos, enviesam contra empate)** · P1 ·
`scoring` · ✅ feito

`scoring.points` somava os bônus de placar do Sistema I — no placar exato dava
`base + exato(5) + saldo(2) + gols_vencedor(3) + gols_perdedor(1)` = base+11 — mas o app
concede **só o maior nível atingido**
(hierárquico): **exato +5 > gols do vencedor +3 > saldo +2 > gols do perdedor +1**; a goleada (+1) é
um extra que empilha. Descoberto ao confrontar as telas "Pontos por Jogo" do app
(rodadas J43–J60, 23–25/06): Curaçao 0×2 cravado pontuou **7** (= base 2 + exato 5), não os 13
que o código dava; Paraguai 0×0 cravado = **9** (base 4 + 5). Prova de que não era cumulativo: 7 é
impossível somando (base mínima 1 + 11 = 12). Dois efeitos graves:
(1) **toda eficiência calculada ficou inflada** (teto superestimado);
(2) **`best_prediction` enviesado contra empates** — jogo decidido acumulava mais bônus que empate,
então o E-max quase nunca escolhia empate
(ligado ao sintoma do [ENG-18]/[ENG-22], "0 empates palpitados").

**Refs:** `scoring.Scorer.points` (a régua), `scoring.Scorer.best_prediction`/`expected_points`
(consumidores; mudam de comportamento), `docs/SPEC.md` §4 (tabela + pseudocódigo + exemplos).
**Correção:** os quatro níveis de placar viram uma **hierarquia** (`if/elif` pelo maior atingido),
não somas; os três níveis "decididos" são mutuamente exclusivos com o exato (acertar dois ⇒ exato),
o que torna a hierarquia natural. Goleada (+1) mantida como extra que empilha
(sem exemplo no app — marcado no teste).
**Validação:** confronto dos 12 jogos J43–J54 com o app
— **8 cravam exato, 4 erram por ≤1 só na base**
(probabilidade nossa ≠ a do app; resíduo separado, não o bug). Casos de ouro travados
em `tests/test_scoring.py` (`test_app_golden_points_per_game`,
`test_exact_score_is_base_plus_five_only`, `test_placar_bonus_levels_are_exclusive`). Docs de "bônus
cumulativos" → "hierárquicos" em SPEC/GLOSSARIO/PRD/AGENTS/scoring.toml. Edição repalpitada:
o modelo **volta a palpitar empates** (J61/J62 de 26/06 saem 0×0).
**Pendência (não-bloqueante):** base ~1pt baixa em ~1/3 dos jogos por divergência de probabilidade
modelo×app — vira item-filho se incomodar.
**Commit:** 5017468

## ENG-24
**Base (1–13) usa a probabilidade interna do app (inobservável) ⇒ eficiência só aproximada** · P2 ·
`scoring` · ⚪ descartado (limitação aceita)

O Sistema I tem **duas partes**: o **bônus de placar**
(exato/vencedor/saldo/perdedor — hierárquico, [ENG-23]) é **determinístico** e reconstrutível
com exatidão; a **base variável "Acertar o vencedor ou empate" (1–13)** é função
da **probabilidade que o app calcula internamente** para o resultado. Essa
probabilidade **difere da nossa** (modelo Dixon-Coles + blend) e **não é exposta** pelo app. Logo,
mesmo com a curva de base perfeita, alimentamos a *nossa* `p` e a base sai
com **±~1 ponto por jogo** sempre que nosso bucket cruza a fronteira de arredondamento do app.
**Evidência:** o Simulador de Pontos do app (telas de 26/06/2026) dá
`0.80→2, 0.45→3, 0.15→7, 0.10→9, 0.05→11`; nossa fórmula erra em `0.45` (dá 4), e **nenhuma** curva
log+arredondamento passa por `0.45→3` e `0.10→9` ao mesmo tempo. Na validação do [ENG-23]
(12 jogos vs app), os 4 desvios foram **todos ±1 só na base** — exatamente este efeito, não bug.
**Confirmação adicional (tela "Editar Palpite" do J61, 26/06):** o app mostra suas
probabilidades **39/28/33** (Cabo Verde/empate/Arábia) vs. as nossas **41/31/28** — distribuições
diferentes — e a base `0.28→6`, onde nossa fórmula dá **5** (−1). Somado ao `0.45→3`
(nossa dá 4, +1), o erro da curva vai **nos dois sentidos**: o app usa régua própria, não uma log
simples. Ou seja, o resíduo tem **duas causas independentes** — probabilidade de entrada
diferente **e** curva de base diferente.

**Impacto:** `scripts/efficiency.py` (teto/eficiência) é **aproximado** (±~1/jogo), nunca exato —
não ler o `%` como cravado. Já houve auto-engano por causa disso (BOLAO 24–26/06: "eficiência 86,7%"
e "você vazou pts" eram artefato do scorer somado — corrigido em ENG-23; o resíduo da base é este
item).
**Mitigação aplicada (não resolve):** documentado em `docs/SPEC.md` §4
(tabela + nota de observabilidade) e na docstring de `scripts/efficiency.py`; o script
agora **imprime o caveat** de que teto/eficiência são estimativas ±~1/jogo.
**Refs:** `scoring.Scorer._base_points`, `scripts/efficiency.py` (`asof_scores`/`archive_scores`),
`docs/SPEC.md` §4.1.
**Decisão (26/06/2026 — ⚪ descartado, limitação aceita):** **não** resolver; manter o **cálculo**
(nossa `p` + fórmula) com o **caveat de ±~1/jogo** já aplicado. Razões:
- **Captura manual descartada** — inviável registrar a prob/base do app por jogo a cada rodada
  (o usuário rejeitou, com razão).
- **Calcular melhor tem retorno decrescente** — há **duas fontes de erro independentes**: (1)
  a probabilidade de entrada (nossa ≠ a do app — **irredutível** sem a prob do app) e (2) a curva (o
  app não usa log; os desvios `0.45`/`0.28` vão em **sentidos opostos**, então nenhum coeficiente
  conserta). Refinar a fórmula poliria só a fonte menor (2) e deixaria a dominante (1).
- **O tripwire de bug já existe** — o papel de "pegar divergência absurda"
  (que teria flagrado o ENG-23) está coberto pelos **testes de ouro**
  `test_app_golden_points_per_game` (valores do app travados como regressão). Não precisa de check
  em runtime.
- **A calibração que importa já é monitorada** — divergência vs o app é modelo-vs-modelo;
  a divergência útil (nossa prob vs realidade) é o `blend-track` (Brier) + monitor de empates
  [ENG-22].

**Mitigação que fica no lugar:** caveat impresso no `efficiency.py` + nota de observabilidade
em `docs/SPEC.md` §4. A eficiência é **curiosidade de campanha** (não entra em decisão), então
o nível de aproximação atual basta. Reabrir só se a base virar insumo de decisão e houver fonte
automática das probabilidades do app.

## ENG-25
**Tabela oficial completa (495 combinações) da alocação de terceiros (Annex C)** · P3 ·
`format_engine` · ⚪ descartado

O casamento por restrição do `_assign_thirds` (backtracking) aproxima o Annex C da FIFA,
mas **não é único**: para uma dada combinação dos 8 grupos cujos terceiros se classificam podem
existir vários emparelhamentos válidos slot→grupo, e a FIFA escolhe **um** específico via tabela
predeterminada. O backtracking devolve o primeiro válido — que pode **divergir** do oficial.
Aconteceu em 2026 (após a fase de grupos, combinação B/D/E/F/I/J/K/L = "row 67"): J74/J77/J81 saíam
com Bósnia/Paraguai/Suécia **rodados** em relação ao bracket oficial.

**Mitigação já no lugar (não é este item):** override por edição
em `tournament.toml::[group_stage.third_allocation]` (`match_id → grupo`), aplicado quando
o conjunto de grupos bate com os terceiros classificados — crava a alocação oficial
da combinação **realizada**. Resolve o caso vivo (2026), mas exige preencher a tabela **após**
a fase de grupos e cobre **uma** combinação.

**Este item:** ingerir a tabela oficial **completa** das 495 combinações (C(12,8)) como dado
da edição (CSV/TOML), indexada pelo conjunto de grupos classificados, e fazer o `_assign_thirds`
consultá-la sempre (não só na combinação cravada). Aí o bracket sai **sempre** oficial, inclusive
nas ramificações do Monte Carlo (hoje aproximadas pelo backtracking).
**Refs:** `format_engine._assign_thirds`, `docs/SPEC.md` §7.3/§9.2-§9.3.
**Critério de aceite:** dado qualquer conjunto de 8 grupos válido, a alocação bate com a tabela
FIFA; teste com ≥3 combinações conhecidas (inclui a row 67 de 2026).
**Fonte:** Wikipedia "2026 FIFA World Cup knockout stage" + documento oficial FIFA (Annex). Trabalho
sobretudo de **transcrição confiável** da tabela.
**Descartado (2026-07-05).** A fonte existe e é bem estruturada
(Wikipedia `Template:2026 FIFA World Cup third-place table`, 495 linhas inline; colunas =
grupos-vencedores; a row 67 confere com o override atual). Mas o item é **transcrição de dado que
não dá para verificar** com as ferramentas disponíveis: o WebFetch **resume** via modelo pequeno
(não reproduz 495 linhas verbatim de forma garantida) e não há segunda fonte independente para o
cross-check de ≥2 fontes que o projeto exige. Invariantes estruturais (cada linha é permutação dos 8
grupos; um terceiro nunca enfrenta o vencedor do próprio grupo) pegam erros grosseiros mas **não**
uma troca sutil — e uma tabela silenciosamente errada é **pior** que a aproximação honesta de hoje
(contaminaria os brackets do Monte Carlo com confiança). Custo/benefício: **P3, zero impacto na
2026** — o override `third_allocation` já crava a combinação realizada; a tabela completa só serve a
edições futuras e ramos hipotéticos do Monte Carlo. **Desbloqueio:** uma fonte **machine-readable**
oficial (CSV/JSON) — aí o mecanismo (ingestão + `_assign_thirds` consulta a tabela, validado por
invariantes + linhas conhecidas) é uma mudança pequena e verificável. Reabrir se ela aparecer.

## ENG-26
**Recalibrar `base_log_coeff` (7,55→~8,4) com telas reais de jogo; investigar ordem
de arredondamento na fase ×2** · P2 · `scoring` · ⚪ descartado
(subdeterminado, converge com [ENG-24])

A curva de base do app, `base = 1 + a·log10(1/p)`, foi calibrada no [ENG-14] em `a=7.55` a partir
de **4 pontos do Simulador de Pontos** (tela "e se"). Três telas **reais de jogo** do R32
(Copa 2026, 30/06) — "Pontos por Jogo"/"Editar Palpite" do **J74 Alemanha×Paraguai**,
**J78 Costa do Marfim×Noruega** e **J79 México×Equador**, todas peso **×2**, base ponderada / 2 =
base unitária — dão **9 pontos** que implicam um coeficiente **maior**:

| Jogo | Resultado | p exibido | base unit (app) | a implícito |
|------|-----------|-----------|------------------|-------------|
| J74 | Paraguai | 11% | 9 | 8,35 |
| J74 | Empate | 19% | 7 | 8,32 |
| J78 | Costa do Marfim | 26% | 6 | 8,55 |
| J79 | Equador | 26% | 6 | 8,55 |
| J78 | Empate | 27% | 6 | 8,79 |
| J79 | Empate | 32% | 5 | 8,08 |
| J79 | México | 42% | 4 | 7,96 |
| J78 | Noruega | 47% | 3 | 6,10 ⚠️ favorito (ruidoso) |
| J74 | Alemanha | 70% | 3 | 12,91 ⚠️ favorito (ruidoso) |

Os **7 pontos informativos** (p≤45%) ajustam **a=8,40** com **SSE=0,12**
(vs 2,16 do 7,55 atual — 18× pior) e **a=8,40 reproduz a base ponderada 7 de 9 na mosca** — todos
com p≤45%. Só erram os dois **favoritos** (47%→prev 8/app 6; 70%→prev 5/app 6):
provável **piso na base do favorito** (ambos dão unit 3 para p bem diferentes) ou arredondamento
do "%" exibido — faixa que **menos** importa para o `best_prediction`
(o favorito é escolhido de qualquer jeito). Consistência confirmada: J78 CdM e J79
Equador, **ambos p=26% → base 6** (o app é determinístico em p). Com **a=7,55 atual erram os 9**
(sempre para baixo, −1 a −2 ponderado); no J74 o nosso teto sai 29 vs **30** do app
("Máximo possível"). **Coeficiente essencialmente fixado em ≈8,40** — falta só
a implementação/validação (abaixo).

**Por que não é o [ENG-24] (⚪ descartado) nem o [ENG-14] (✅):** o ENG-24 tratou
da **probabilidade de entrada** inobservável (fonte de erro irredutível) e concluiu que a curva erra
"nos dois sentidos"; este item é sobre a **curva** (fonte 2),
com **evidência nova de telas reais de jogo** (não Simulador) que mostra
erro **sistemático para baixo** na faixa que decide picks. O ENG-14 antecipou exatamente isto
("com mais pontos dá para apertar o coeficiente").
**Consequência que o ENG-24 não pesou:** base de zebra baixa **rebaixa o E[pts] do palpite-zebra**
vs. favorito (a base escala com a raridade do resultado, e o `best_prediction` escolhe entre 1/X/2
por E[pts]) — logo pode **enviesar a escolha contra upsets**, o que é **decisão**, não só
contabilidade de eficiência.

**Sub-questão nova (fase ×2/×4):** determinar se o app arredonda
a base **no unitário e depois multiplica** pelo peso, ou **multiplica e depois arredonda** — muda
o valor em jogos de mata-mata e a contabilidade de teto. As telas do R32 (peso ×2) permitem
distinguir: ex. Paraguai p=0,11 dá 18 ponderado; unit-round-then-×2 (9→18) e fit-then-×2 (≈18,1→18)
coincidem aqui, mas pontos de fronteira resolvem a ambiguidade — coletar um caso onde as duas ordens
divergem.

**Refs:** `scoring.Scorer._base_points` (`base_log_coeff`), `data/editions/2026/scoring.toml`
(`[sistema_i].base_log_coeff = 7.55`), `scripts/efficiency.py` (teto/eficiência consomem a base),
[ENG-14] (curva original), [ENG-23] (bônus hierárquicos), [ENG-24] (erro de prob. de entrada).
**Correção proposta (coleta essencialmente concluída — a≈8,40 fixado em 7/7 pontos p≤45%):** trocar
`base_log_coeff` 7,55→**8,40**; decidir se a log pura basta ou se há **piso no favorito**
(p≥47% → unit 3; opcional, faixa de baixo impacto); decidir a **ordem de arredondamento**
(unit-round -then-×2 vs ×2-then-round) — os 9 pontos atuais não a desempatam
(coincidem na faixa coletada), precisa de **um** ponto de fronteira; medir o impacto
no `best_prediction` (algum pick muda? fica mais ousado em zebra?); re-rodar backtest/LOO-CV
(não regredir os pontos do bolão); re-rodar `efficiency.py`
(teto sobe ~1/jogo, eficiência cai do >100% — **interage com o [ENG-27]**, fazer junto).
**Aceite:** `_base_points` reproduz a base das telas reais dentro de **±0,5 pt**
(já satisfeito a 8,40 nos 7 informativos; favorito documentado como resíduo/piso); ordem
de arredondamento decidida e testada; teste de regressão trava o novo coeficiente
(mudança re-roda o LOO-CV, como o [ENG-17]); SPEC §4 atualizado.
**Coleta — restrição descoberta (30/06):** a base detalhada
(tela "Pontos por Jogo"/"Editar Palpite") só aparece em jogos **ainda não realizados**; **não** há
pontuação detalhada retroativa no app. Logo a coleta de pontos de calibração
é **só na janela pré-jogo** — capturar nos confrontos do dia/véspera, não depois.
**Decisão (30/06 — ⚪ descartado, subdeterminado):** com os 9 pontos, o ajuste é **confundido**:
`a≈8,40` com arredondamento *round* e `a=7,55` com arredondamento *ceil* explicam
o live **igualmente bem** (≈7/8), e **as duas hipóteses quebram** os pontos do Simulador
(`0.50→3`, `0.15→7`) — nenhuma combinação (coeficiente, arredondamento) concilia as duas fontes
do app. Somado à probabilidade de entrada inobservável ([ENG-24]), a curva é **subdeterminada**
pelos dados. Mantém-se `a=7,55` + round; o resíduo ±1/jogo é **limitação aceita**, igual ao [ENG-24]
(este item **converge** com aquele). Registrado em SPEC §4.1. **Reabrir só** se um ponto
de **fronteira** pré-jogo desempatar ceil vs round de forma limpa
(baixo valor — o resíduo é da ordem do ruído da base). Prints em `tmp/` (não versionar).
**Commit:** —
**Commit:** —

## ENG-27
**Peso de fase (×2/×4) nunca aplicado na pontuação ⇒ teto de mata-mata subcontado, eficiência infla
no KO** · P2 · `scoring`/`efficiency` · ✅ feito

O app pontua o mata-mata com **peso de fase**: R32–SF **×2**, final **×4** (grupos ×1) — sobre
a **partida inteira** (base + bônus de placar + bônus de prorrogação/pênaltis). Confirmado nas telas
do app (J74 30/06: "PONTOS POR ACERTAR O VENCEDOR · PESO: ×2 · valores já incluem o peso", base
6/14/18 = unit 3/7/9 ×2; tutorial "E se tiver prorrogação e pênaltis?": Prorrogação +6 / Pênaltis +6
com seletor Peso 1/**2**/4). Nosso modelo **define** esse peso
(`scoring.toml::[phase_weights]` group=1, R32=R16=QF=SF=2, "3rd_place"=2, final=4) e expõe
`ScoringConfig.weight(stage)` (`edition.py:86`) — **mas nada o chama**: `grep '\.weight('` em `src/`
e `scripts/` retorna só a definição. A pontuação (`scoring.Scorer.points`/`knockout_bonus`) devolve
valores **unitários** e nenhum consumidor multiplica pela fase.

**Impacto (material agora — R32 em curso, J73–J76 disputados):**
- `scripts/efficiency.py` (`asof_scores`, linha ~119) pontua o KO com `scorer.points(...)` **a ×1**
  e ainda **descarta o bônus de prorrogação/pênaltis** (comentário "mata-mata: sem bônus"). Logo
  o **teto** de cada jogo de mata-mata é subcontado (×1 em vez de ×2/×4, e sem os +6/+6).
- Os **pontos reais do usuário** (`--my-points`, vindos do app) **já são ponderados** (×2 no R32).
  Então a eficiência = (real ponderado) / (teto não-ponderado) **infla** conforme o mata-mata avança
  — viés sistemático, não ruído. É a mesma classe de auto-engano do [ENG-23]
  (eficiência inflada por bug de pontuação → conclusão falsa de "deixou pontos na mesa"). O "~103%"
  do BOLAO já começa a carregar esse componente.

**Refs:** `edition.ScoringConfig.weight` (definido, nunca chamado),
`data/editions/2026/scoring.toml` `[phase_weights]`,
`scripts/efficiency.py::asof_scores`/`archive_scores`, `scoring.Scorer.points`/ `knockout_bonus`,
`backtest.run_backtest` (loop de pontos, linha ~161 — também não pondera, **mas** o martj42 não traz
a fase: ponderar o backtest é inviável/fora de escopo, ver [ENG-12]/SPEC §9.2).
**Correção proposta:**
1. *(limpo, alto valor)* aplicar `edition.scoring.weight(f.stage)` ao pontuar cada jogo
   no `efficiency.py` (a fase vem do `fixtures.csv` na edição viva — trivial). O teto do KO passa
   a refletir ×2/×4. Centralizar o peso num único ponto (ex.: helper `weighted_points(stage, …)`)
   para não espalhar a multiplicação.
2. *(limitado por dado — igual [ENG-12]/SPEC §9.2)* somar o `knockout_bonus` ao teto onde o desfecho
   é determinável: jogos a **pênaltis** (via `penalty_winner` do fixture/`ko_outcome`) recebem
   o bônus ponderado; jogos decididos **dentro da prorrogação** não são separáveis (sem flag de ET)
   e ficam de fora, documentado. Decididos nos **90'** não recebem bônus de KO
   (correto — não houve ET/pênaltis).
**Aceite:** num jogo de R32, o teto de `efficiency.py` == 2× o teto unitário (e ×4 na final); teste
de regressão com um jogo de KO ponderado (inclui um caso a pênaltis com o bônus +6/+6 ponderado);
re-rodar a eficiência da 2026 e registrar no BOLAO o número **corrigido** (deve cair do ">100%").
A ponderação do backtest fica explicitamente fora de escopo (sem fase no martj42). `pytest` verde.
**Progresso (working tree, 30/06):** parte 1 (peso de fase) **implementada**:
`Scorer.weighted_points` (`points()` × peso, fonte única `ScoringConfig.weight`); `efficiency.py`
pondera o placar dos 90' do KO no `asof_scores`, no oráculo e no `archive_scores`. Testes novos:
`test_weighted_points_applies_phase_weight` (×1/×2/×4 e zero ponderado segue zero) +
`test_2026_phase_weights` (trava grupos×1/R32–SF×2/final×4 da config, antes código morto). 107
testes verdes; ruff/mypy ok. Smoke: teto 2026 = 228
(os 4 KO atuais zeraram o 1×2, ×2 não muda; passa a valer quando o tool acertar um KO). Docs:
CHANGELOG, SPEC §4.1, docstring/avisos do `efficiency.py`.
**Parte 2 (bônus de prorrogação/pênaltis no teto) — IMPLEMENTADA** (working tree, 30/06): reavaliada
após a pergunta sobre a fonte — o desfecho ET/pênaltis **é** recuperável do martj42
(placar 90' + `shootouts`; empate-90'-sem-shootout ⇒ decidido na prorrogação) para a edição viva,
ao contrário do escopo inicial. `efficiency.py`: `_penalty_lookup`
(mapa data+par → vencedor dos pênaltis, presença = na fonte) + `_actual_ko_outcome`
(regulação/pênaltis/ET/latência) → soma `knockout_bonus` ×peso ao teto
e ao oráculo; **guarda de latência**
(jogo empatado nos 90' fora da fonte é pulado e listado, nunca inferido). 5 testes
em `tests/test_efficiency.py` (regulação, pênaltis, ET, latência, bônus ×2 no R32). Smoke 2026:
J74/J75 (a pênaltis, fonte ainda em 25/06) corretamente pulados por latência; pontuam quando
o martj42 alcançar.
**Commit:** bd8a4c0

## ENG-28
**`fetch_odds` só casa jogos de grupo ⇒ blend desligado em todo o mata-mata** · P2 · `blend`/`odds`
· ✅ feito

O blend com odds (ENG-19) é a única alavanca de acurácia **validada**
(Brier 0,418 vs 0,442 do modelo puro). Mas `scripts/fetch_odds.py::map_to_fixtures` casa
eventos→fixtures **só** com jogos de grupo:
`unplayed = {... for f in edition.fixtures if f.is_group and not f.played}`. Logo `odds.csv`
tem **0 match_id de mata-mata** (verificado: 49 grupo, 0 KO) e **todo** o R32→final
sai **100% modelo**, sem o mercado — justamente nos **31 jogos de peso 2×/4×**, onde acurázia rende
mais. Hoje o `fetch_odds` puxou 13 eventos (os R32) e mesclou **0**. Causa estrutural: (a) o filtro
`is_group`; (b) os fixtures de KO guardam **slots** (`1A`, `W73`), não times — casar com o feed
(nomes reais) exige **resolver o bracket** dos confrontos já determinados pelos resultados reais.

**Refs:** `fetch_odds.map_to_fixtures` (filtro `is_group`, alinhamento `price[f.home]`),
`sync._resolve_real_bracket` (resolução do bracket por resultados reais), `pipeline.run`
(consome `odds.csv` por match_id, alinhado à orientação home/away).
**Correção proposta:** resolver os confrontos de KO a partir
dos **resultados reais do próprio fixture** (standings de grupo + `ko_outcome` dos KO disputados —
sem rede, sem modelo, mais fresco que o martj42, que tem latência) e incluir no casamento de odds
os jogos de KO **não disputados** cujos dois times já estão determinados; alinhar as odds
pelos **times resolvidos** (não pelos slots). Função `sync.resolve_live_bracket(edition)` reusável.
**Aceite:** com odds disponíveis para um confronto de R32 já definido (ex.: França×Suécia),
`fetch_odds` grava o match_id de KO em `odds.csv` com as odds alinhadas à orientação do fixture;
`predict` blenda esse jogo (matriz ≠ modelo puro). Teste do resolvedor
(bracket real → confrontos esperados) + do casamento de um evento de KO. `pytest` verde.
**Progresso (working tree, 30/06) — IMPLEMENTADO:** `sync.resolve_live_bracket(edition)` resolve
o bracket pelos resultados reais do fixture
(standings + `ko_outcome`; sem rede/modelo, mais fresco que o martj42);
`fetch_odds._matchable_fixtures` inclui os confrontos de KO definidos e alinha as odds
pelos **times resolvidos**. Testes: `test_resolve_live_bracket_resolves_r32_from_real_results`
(16 confrontos, times reais, J77=France×Sweden) +
`test_map_to_fixtures_matches_resolved_knockout_game`
(odds de KO alinhadas, robusto à orientação do feed). Validado ao vivo: `fetch_odds`
mesclou **+13 jogos de KO** (odds.csv 49→62) e o `predict` re-rodado blendou os KO
— **J78 mudou o avanço de Costa do Marfim para Noruega** (segue o mercado). 114 testes verdes;
ruff/mypy ok.
**Commit:** bd8a4c0

## ENG-29
**Palpite de prorrogação/pênaltis por heurística de limiar, não E[pts]** · P3 · `knockout` · ✅ feito

`knockout.predict_knockout` escolhe a **camada 2** (quem vence a prorrogação / vai aos pênaltis)
por um **limiar fixo** sobre a probabilidade condicional: `extra_time = "home"`
se `cond_home ≥ 0.58`, `"away"` se `≤ 0.42`, senão `"penalties"` (`_ET_DECISIVE_THRESHOLD = 0.58`).
Não modela a probabilidade de a **prorrogação terminar empatada** (→ pênaltis): como a ET são 30 min
(~1/3 do jogo), uma fração grande termina nivelada, então "vai aos pênaltis" costuma ser
o desfecho **mais provável**, e o limiar 0,58 só o escolhe numa banda estreita de `cond_home`.
Para um favorito moderado (`cond_home`≈0,62) crava "vence na prorrogação" quando o modal real talvez
seja pênaltis — escolha **sub-ótima em E[pts]**. Idem a camada 3 (vencedor dos pênaltis), hoje só
"lado mais forte" — para uma aposta binária é o argmax certo, então menos crítico.
**Relevância confirmada:** o bônus vale **+6/+12/+24** (×2 R32, ×4 final) e o usuário pontua nele
(capturou +6 em 29/06, J74/J75 a pênaltis).

**Refs:** `knockout.predict_knockout` (camadas 2 e 3, `_ET_DECISIVE_THRESHOLD`),
`scoring.Scorer.knockout_bonus` (a régua que se quer maximizar), `model.score_matrix`
(taxas de 90').
**Correção proposta:** modelo explícito de gols da **prorrogação** — Poisson com taxa ≈ taxa de 90'
× (30/90) por lado (reusando as forças do `score_matrix`), computar `P(home vence ET)`,
`P(ET empatada → pênaltis)`, `P(away vence ET)` e escolher a camada 2 por **E[pts]**
(argmax da probabilidade do desfecho, já que o bônus é fixo). Camada 3: P(vencedor dos pênaltis) ~
moeda com leve viés à força — manter argmax. Validar contra desfechos reais de mata-mata
(Copas passadas via `shootouts` + jogos não-decididos nos 90').
**Aceite:** a camada 2 passa a escolher por E[pts] (teste: distribuição de ET conhecida → escolha
esperada, incl. caso favorito-moderado→pênaltis que o limiar erra); sem regressão no avanço previsto
(`advancer`). `pytest` verde.
**Resolução (0f91d63):** `knockout._extra_time_probs(lam_home, lam_away)` modela a prorrogação como
Poisson independente (taxa de 90' × 30/90, taxas via `_expected_goals` da matriz)
e `predict_knockout` escolhe a camada 2 pelo **argmax** das três probabilidades
(= E[pts], bônus fixo). Removido `_ET_DECISIVE_THRESHOLD`. Camada 3 (pênaltis) e `advancer` mantidos
no `cond_home`. 7 testes novos (`tests/test_knockout.py`): recupera λ da matriz, probs de ET
simétricas/normalizadas, favorito-moderado (cond_home≥0.58) → **penalties**
(o caso que o limiar errava), favorito-forte → home, equilibrado → penalties, camada 3/avanço
inalterados.
**Efeito ao vivo:** dos R32, só J77 França×Suécia (favorito forte) crava um lado; os demais saem
"vai aos pênaltis" — coerente com a estatística real
(~metade dos jogos que chegam à ET vão a pênaltis). Validação contra Copas passadas ficou de fora
(escopo); a aproximação Poisson-independente (DC ignorado na ET) é documentada no SPEC §6. 121
testes verdes.
**Commit:** 0f91d63

## ENG-30
**Jogos de mata-mata FINAL não mostram prorrogação/pênaltis/quem avançou** · P3 ·
`pipeline`/`render` · ✅ feito

Para um jogo de KO **já disputado** (`status=FINAL`), o `pipeline.run` preenche só o placar dos 90'
(`palpite`/`placar_real`) e deixa **`prorrogacao`/`penaltis`/`avanca` vazios**
(o ramo que os preenche é `not f.played`). O `avanca` real **existe**
(`Fixture.ko_outcome` = quem avançou; J73 Canadá, J74 Paraguai, J75 Marrocos, J76 Brasil) — é só não
estar sendo usado nos FINAL. O desfecho real prorrogação/pênaltis é parcial: placar 90' decidido ⇒
não houve; 90' empate ⇒ foi a prorrogação/pênaltis, mas a **fonte (martj42) tem latência**
(ENG-15/ENG-27), então o ET-vs-pênaltis não vem automático na hora.

**Refs:** `pipeline.run` (ramo `not f.played`, linhas ~150/168), `render`
(colunas já existem: `CSV_COLUMNS`, tabelas MD/HTML), `Fixture.ko_outcome`, `Edition.odds`
(padrão de arquivo opcional por edição a espelhar), `efficiency._actual_ko_outcome`
(mesma lógica de desfecho real do ENG-27).
**Correção proposta:**
1. preencher `avanca` dos jogos de KO FINAL com o classificado real (`ko_outcome`) — ganho limpo.
2. desfecho prorrogação/pênaltis nos FINAL: 90' decidido ⇒ "—"; 90' empate + shootout conhecido ⇒
   "vai aos pênaltis" + vencedor; senão vazio (não afirmar ET sob incerteza).
3. **captura/armazenamento** dos shootouts da edição viva (latência da fonte): arquivo opcional
   `data/editions/<ano>/shootouts.csv` (`match_id,winner`), carregado em `Edition.shootouts`
   (espelha `odds.csv`); preenchido de **fontes confiáveis verificadas em ≥2** quando a fonte
   oficial ainda não tem (regra de `confirmar-placares-multiplas-fontes`).
**Aceite:** um jogo de KO FINAL decidido nos pênaltis mostra `avanca`/prorrogação/pênaltis corretos;
um decidido nos 90' mostra avanço + "—"; teste cobre os dois + a carga do `shootouts.csv`. `pytest`
verde.
**Resolução (01e0ba9):** `Edition.shootouts`
(campo + `_load_shootouts`, espelha `odds.csv`; `as_of` descarta os de jogos futuros)
e `pipeline._final_ko_layers(f, shootouts)` preenchem os FINAL de KO: `avanca` sempre
do `ko_outcome`; prorrogação/pênaltis = "—" (90' decidido) / "Vai aos pênaltis" + vencedor
(empate + shootout conhecido) / vazio (empate sem shootout — não afirma sob latência). As colunas já
existiam no `render` (CSV/MD/HTML). Captura: `data/editions/2026/shootouts.csv` com J74 Paraguai
e J75 Marrocos, **verificados em ≥2 fontes**
(ESPN/Sky/Al Jazeera/NBC/CBS: Paraguai 4-3, Marrocos 3-2 nos pênaltis). 4 testes
(`_final_ko_layers` reg/pênaltis/incerto + carga do shootouts.csv + edição 2026). Saída ao vivo: J73
—/—/Canadá, J74/J75 pênaltis+vencedor, J76 —/—/Brasil.
**Limitação aceita:** jogos decididos **dentro da prorrogação** (sem pênaltis) seguem vazios até
captura/fonte (nenhum em 2026 até agora). 124 testes verdes.
**Commit:** 01e0ba9

## ENG-31
**`worldcup status`: briefing read-only de start-of-day** · P3 · `cli`/`status` · ✅ feito

Reidratar o contexto da campanha no início de uma sessão custava N comandos
(`sync-results`, `predict`, `blend-track`, `efficiency`) + leitura do `BOLAO.md` inteiro + saídas
verbosas — enchia o contexto de ruído antes da primeira pergunta.
Faltava **uma foto compacta, read-only e idempotente** do estado: jogos disputados/total, fase
atual, fixtures de hoje (✓ disputado / ⏳ pendente), próximos palpites, standing (do `BOLAO.md`)
e o que **depende do usuário** (pontos p/ a eficiência; jogos atrasados que a fonte ainda não tem).
"Ver" separado de "fazer": o `status` só relata; a mutação (`sync`/`predict`) segue na skill
`palpites-copa`.

**Refs:** `status.build_status`/`format_status` (lógica pura), `cli.cmd_status`, `Edition`
(`fixtures`/`scoring`), `out/palpites-<ano>.csv` (nomes resolvidos + palpite por `match_id`),
`BOLAO.md` (linha de standing). Espelha o padrão de subcomando read-only do `blend-track`.
**Correção:** subcomando `worldcup status --edition 2026` (read-only, edition-agnóstico): lê
a edição + o último `out/` + a linha de standing do `BOLAO.md`; detecta atraso
(`fixture` não disputado com `date < hoje`) e descompasso `out/` vs `fixtures` (pede `predict`).
`--date` sobrescreve "hoje" (teste).
**Aceite:** `worldcup status` imprime o bloco compacto com hoje/próximos/standing/pendências; testes
cobrem a montagem (disputado vs pendente, atraso, out/ obsoleto, hoje vazio). `pytest` verde.
**Resolução:** `status.py` (`build_status`/`format_status`, funções puras) + `cli.cmd_status`/
`main_status` (alias `ws` em `pyproject.toml`); 7 testes em `test_status.py` (hoje
disputado/pendente, atraso, out/ obsoleto, sem picks, hoje vazio, palpite de grupo sem seta, pede
pontos). Docs sincronizados (README/CHANGELOG/AGENTS/skill). 131 testes verdes.
**Commit:** 5ffd667

## ENG-32
**Palpite de 90' no mata-mata tende a 0×0 e zera quando o favorito vence no tempo normal** · P3 ·
`scoring`/`knockout` · ✅ feito

O placar de 90' de um jogo de KO sai de `scorer.best_prediction(matrix)`
(camada 1 do `knockout.predict_knockout`), a **mesma** maximização de E[pts] da fase de grupos.
Quando o modelo dá alta P(empate) num confronto que ele espera resolver nos pênaltis, o palpite
de 90' sai **0×0** (empate é o resultado mais raro ⇒ base 1–13 maior no Sistema I; entre os empates,
0×0 costuma ser o modal). O problema
prático: **um palpite 0×0 pontua 0 sempre que o jogo é decidido no tempo normal**, que é o caso
da maioria dos jogos de KO. Já mordeu em campo: **J73**
(palpite 0×0, real Canadá 0×1 nos 90' → 0 pts) e **J79** (palpite 0×0, real México 2×0 → 0 pts).
Como no KO o peso de fase é **×2/×4**, um zero desses custa caro.

**A pergunta é se isto é bug ou variância:** se 0×0 **de fato** maximiza E[pts]
(empate raro = base alta), então o zero é variância realizada e a escolha é risk-neutra correta —
mexer **baixaria** o E[pts] (mesma lição do `risk`, ver `data/editions/2026/BOLAO.md` 2026-06-17).
Mas pode haver **artefato**: (a) o modelo super-estima P(empate) em confrontos desequilibrados
de KO; (b) a base do empate está inflada vs. o app; (c) sob peso ×2/×4 e num objetivo de **ranking**
(não E[pts] médio), um palpite de "placar mínimo do favorito" (ex.: 1×0) domina 0×0 por ter
P(não-zerar) muito maior. Distinto do ENG-29
(que corrigiu a camada de **prorrogação/pênaltis**, não o placar de 90').

**Refs:** `knockout.predict_knockout` (camada 1 = `scorer.best_prediction`),
`scoring.best_prediction`, `pipeline.run` (ramo de KO), `backtest.run_backtest`
(medir nos KO das 4 Copas passadas). Relacionado: ENG-29, ENG-18 (calibração de empates), decisão
de `risk` no BOLAO (2026-06-17).
**Correção proposta (investigação, depois decisão):**
1. **Medir**: nos jogos de KO das 4 Copas passadas (`backtest`), quantas vezes o `best_prediction`
   de 90' sai empate/0×0, e o E[pts] realizado do 0×0 vs. o do "placar mínimo do favorito"
   (1×0/0×1).
2. Se 0×0 for E[pts]-ótimo e também melhor em P(top-k) simulado ⇒ **⚪ descartar**
   (é variância; registrar o número). Se um objetivo alternativo no KO pontua mais **sem** baixar
   o E[pts] médio de forma material ⇒ propor a mudança
   (flag de política de palpite de KO, agnóstica à edição).
**Aceite:** um relatório (número, não opinião) do comportamento do palpite de 90' de KO
nos backtests + veredito manter/mudar; se mudar, teste de regressão que falharia sem o fix. `pytest`
verde. **Resolução (veredito: MUDAR).** Investigação nos **64 jogos de KO** das 4 Copas passadas
(últimos 16 por data = mata-mata): o `best_prediction` escolhia **empate em 16/64 (25%)**,
e **12 desses foram decididos nos 90'** (palpite de empate = 0 pts). Números: Σ E[pts]
atual **179,49** vs. melhor não-empate **177,16**
(Δ **+2,32** ≈ +0,04/jogo — o empate é ótimo só por um fio); Σ **realizados** (peso ×2/×4)
atual **384** vs. não-empate **454** (Δ **−70**, todo no subconjunto de empates: 56 vs 126).
A "vantagem" repousa em **super-estimação de empate no KO**
(P̄ modelo 0,278 vs real 0,234; nos jogos onde apostou empate, 0,330 vs 0,250). Não é o `risk`
(aqui **reduz** variância a custo de E[pts] ~nulo, não troca E[pts] por variância).
**Fix:** `Scorer.best_prediction(forbid_draw=…)`, usado na camada 1 de `knockout.predict_knockout`
(grupos e camadas ET/pênaltis/avanço inalterados). Regressão em `test_scoring`
(forbid_draw nunca empata / no-op quando já há vencedor) e `test_knockout`
(camada 1 nunca empata no KO). 134 testes verdes. Relatório reproduzível:
`scratchpad/eng32_ko_pick.py`.
**Commit:** 6e5f4e2

## ENG-33
**Re-arquivar depois de registrar resultados sobrescreve o snapshot do dia e perde os palpites
da manhã** · P1 · `cli`/`history` · ✅ feito

`cli.archive_outputs` grava `history/<data>.csv` **sobrescrevendo sem olhar o que já existe**.
A rotina diária tem dois momentos de archive no mesmo dia: o da manhã (palpites da rodada)
e o pós-resultado (`sync-results --archive` ou `predict --archive` depois de um `record`). O segundo
grava os jogos do dia como `FINAL` **em cima** do palpite da manhã — exatamente
o dado **não-reprodutível** que o snapshot existe para preservar
(é a justificativa de versionar `history/`, ver docstring de `archive_outputs`). Mordeu
em 2026-07-01: o snapshot da manhã tinha os palpites de J80–J82; após registrar J80/J82
e re-arquivar, viraram `FINAL` — e J80/J82 caíram no bucket "sem snapshot real"
do `efficiency.py --compare-archive`
(teto reconstruído, não verificável; ver ENG-34, mesmo episódio).

**Refs:** `cli.archive_outputs` (sobrescrita incondicional), `cli.cmd_sync_results`/`cmd_predict`
(chamadores com `--archive`), `scripts/efficiency.py::archive_scores`
(consumidor que exige o palpite da manhã). Relacionado: ENG-34.
**Correção proposta:** merge por jogo ao re-arquivar no mesmo dia: se o snapshot existente
tem **palpite** para um `match_id` e o run novo o traria como `FINAL`, **preserva a linha antiga**
(o palpite da manhã); linhas novas/ainda-pendentes atualizam normalmente. Alternativa mais simples:
recusar sobrescrita quando ela rebaixaria palpite→FINAL, exigindo `--force`. Em ambas, logar
o que foi preservado.
**Aceite:** teste de regressão — arquiva com palpite em J_x, registra o resultado de J_x, arquiva
de novo (mesma data): o snapshot mantém o palpite da manhã de J_x (não `FINAL`) e os demais jogos
atualizam. `pytest` verde.
**Resolução:** merge por jogo em `cli.archive_outputs` (helper `_merge_preserved_rows`): linha
`PREVISTO` do snapshot existente que o run novo traria como `FINAL` é **preservada**
(e logada no console, com os jogos); pendentes/novas atualizam; o MD é rerenderizado das linhas
mescladas. Snapshots **reconstruídos** (`--as-of`) ficam fora do merge — são regeneráveis
por definição (re-rodar após corrigir um placar **deve** sobrescrever). Optou-se pelo merge
(não pelo `--force`) por ser à prova de esquecimento na rotina diária. Testes: o do aceite +
repalpite intradiário de jogo ainda pendente atualiza normalmente. Docs: README (`--archive`),
AGENTS (`history/`), CHANGELOG.
**Commit:** e5b9748

## ENG-34
**Teto reconstruído do `efficiency.py` não é estável entre rodagens — eficiência muda sem o usuário
mudar nada** · P2 · `scripts/efficiency.py` · ✅ feito

O teto por jogo sai de `efficiency.asof_scores`: re-roda o modelo
`as_of(data)` **com os arquivos de hoje**
(base histórica re-baixada pelo `sync-results`, `odds.csv` atual, código atual). Nada congela
a medição: a cada rodagem o "palpite que o tool teria mostrado" de um jogo **já medido** pode mudar.
Mordeu em 2026-07-01, duas rodagens no mesmo dia: de manhã J79 reconstruiu **0×0 → 0 pts**
(teto 262, eficiência 103,4%); à noite, após o sync atualizar a base, o mesmo J79 as-of
reconstruiu **1×0 → 10 pts** — teto dos mesmos 79 jogos foi a 304 (+42 de drift) e a "eficiência"
caiu a 88,0% **sem o usuário ter feito nada**. Conclusão de execução errada quase saiu duas vezes
(cf. regra de interpretação da skill `palpites-copa` e `BOLAO.md` 2026-06-24/07-01).
O `--compare-archive` já separa verificável de reconstruído, mas o **headline** (teto/eficiência)
usa o reconstruído volátil.

**Refs:** `scripts/efficiency.py::asof_scores` (reconstrução volátil), `::archive_scores`
(fonte estável quando há snapshot), `::main` (headline usa o as-of),
`cli.archive_outputs`/`Edition.as_of`. Relacionado: ENG-33
(garante o snapshot da manhã — a fonte estável), ENG-24/ENG-27 (aproximações já conhecidas do teto).
**Correção proposta:** hierarquia de fontes por jogo no teto headline: (1) snapshot real
de `history/` quando existe; (2) senão, teto reconstruído **persistido na primeira medição**
(cache por `match_id` em arquivo rastreado, estilo tally do `blend-track`), para o número não mudar
retroativamente; (3) reconstrução viva só para jogo ainda sem medição —
e o script **reporta o drift** quando uma reconstrução nova diverge da persistida
(em vez de substituí-la em silêncio).
**Aceite:** duas rodagens consecutivas (com `sync-results`/`fetch_odds` entre elas) mantêm o teto
dos jogos já medidos idêntico e destacam qualquer drift por jogo; teste de regressão do cache
(jogo medido não re-pontua diferente). `pytest` verde.
**Resolução.** Novo `ceiling.csv` (`match_id,pts,palpite,real,source`, na pasta da edição,
rastreado) congela o teto por jogo na 1ª medição. `efficiency.load_ceiling`/`save_ceiling` e a
função pura `reconcile_ceiling(recon, archive, cache)` implementam a hierarquia: (1) snapshot real
de `history/` (`source=archive`) quando existe; (2) senão a reconstrução as-of (`source=asof`); o
`main` usa o **congelado** no headline (total/eficiência) e só semeia jogos ainda não medidos.
Divergência da reconstrução viva vira **drift reportado** — mas **só p/ congelados `asof`** (os
`archive` divergem da reconstrução por natureza = ruído, não drift temporal; isso fica no
`--compare-archive`). `--reset-ceiling` recongela do zero (ex.: após um fix de scoring). O `archive`
passou a ser computado **sempre** (não só com `--compare-archive`), para servir de fonte preferida.
Efeito: 2026 com 60/90 jogos vindo do snapshot real ⇒ teto 392→**361**, eficiência ~100% (a leitura
correta p/ quem segue o tool; a reconstrução inflava). Limitação restante: `archive_scores` ainda é
só de grupo, então jogos de **KO** congelam da reconstrução (fidelidade menor — extensão futura).
Testes: `reconcile_ceiling` (freeze/drift/preferência/asof) + round-trip do cache. 176 verdes.
**Commit:** c0d49bf

## ENG-35
**Blend só corrige o 1×2 — a forma do placar (totals) fica 100% modelo** · P2 · `blend`/`odds` · ✅
feito

O blend (ENG-19) faz `devig` → `log_opinion_pool` → `rescale_matrix`: ajusta a matriz de placares
ao 1×2-alvo **preservando a forma condicional**. Ou seja: o mercado corrige *quem ganha*, mas
os **gols esperados** — onde vivem o exato (+5) e o `winner_goals` (+3), a maior fatia dos pontos
do Sistema I — continuam 100% Dixon-Coles. A The Odds API oferece o mercado de **totals**
(over/under) para os mesmos eventos que o `fetch_odds.py` já busca (hoje só `markets=h2h`); a linha
de gols do mercado embute escalação/fadiga/clima que o modelo não vê. Corrigir a taxa total de gols
da matriz para a linha do mercado tornaria o *placar* palpitado tão informado quanto o *lado* —
a melhoria de acurácia mais barata disponível (mesma infra, mesmo fetch, mesma chave).

**Refs:** `blend.rescale_matrix`/`blend_matrix_with_odds` (só 1×2 hoje), `scripts/fetch_odds.py`
(`markets=h2h` → acrescentar `totals`), `data/editions/<ano>/odds.csv`
(schema ganharia colunas de totals, opcionais/retrocompatíveis), `pipeline.run`
(aplicação por jogo). Relacionado: ENG-19, ENG-28.
**Correção proposta:** (1) `fetch_odds` passa a pedir `h2h,totals` e grava `total_line,over,under`
(opcionais; linhas antigas seguem válidas); (2) novo passo no blend: des-vigar o over/under, inferir
o λ-total implícito do mercado na linha (Poisson: resolver P(gols > linha) = p_over)
e **reescalar a taxa total da matriz** para o pool modelo×mercado (mesmo `blend_weight`),
preservando a partição home/away e depois reaplicando o rescale de 1×2; (3) degradação graciosa
idêntica à do 1×2: sem totals ⇒ matriz intacta. Validar com `blend-track` estendido
(Brier de faixa de gols ou log-loss do placar exato, modelo vs blendado).
**Aceite:** teste de regressão: matriz com λ conhecido + totals sintéticos ⇒ taxa total blendada
converge ao alvo e o 1×2 final continua batendo com o pool; sem colunas de totals, output byte-igual
ao atual. Métrica prospectiva no `blend-track` mostrando o efeito. `pytest`/`mypy` verdes.
**Resolução:** `blend.devig_pair`/`implied_total_rate` (bissecção na Poisson) /
`expected_total_goals`/`tilt_matrix_to_total` (tilting `c^(i+j)`; num produto de Poissons escala
as duas taxas por `c`, preservando a partição mandante/visitante) + pool geométrico de taxas
(pool logarítmico de Poissons é Poisson na média geométrica), iterado 3× com o `rescale_matrix`
(1×2 exato por vir por último). `odds.csv` com colunas opcionais `total_line,over,under`
(`edition._load_totals` → `Edition.totals`; legado válido); `fetch_odds.py` busca `h2h,totals`
(fallback: mediana na linha modal); `blend-track` com Brier binário do over/under. 17 testes novos
(inversão do λ, invariância do share sob tilting, alvos do pool, schema legado, extração/fallback).
150 testes verdes. Efeito real em 01/07 (8 jogos com totals): J81 3×1→2×0, J86/J87 1×0→2×0, J89
0×1→1×2; sem totals ⇒ caminho antigo byte-idêntico.
**Commit:** 61a6d78

## ENG-36
**Modo endgame consciente de bolão: otimizar P(top-k) contra o pelotão, não E[pts]** · P2 ·
`scoring`/`estratégia` · ✅ feito

`Scorer.best_prediction` maximiza E[pts] contra a verdade — ótimo para acumular pontos, mas bolão é
jogo **diferencial** contra N humanos: ranking só muda quando o palpite **diverge** do pelotão
e a divergência acerta. Humanos aglomeram no favorito com placar redondo; seguir o E[pts]-máximo
em jogo claro ≈ palpitar igual a todo mundo ≈ preservar a posição atual. Em 2026-07-01 ficou nítido:
98% de captura do teto (execução perfeita) e mesmo assim 11º→21º — captura perfeita do consenso não
redistribui posições. O botão de `risk` não resolve (perturba o placar, não o lado, e é cego
a adversários — decisão viva de 2026-06-17 no `BOLAO.md`). A alavanca real: nos jogos de peso ×2/×4
(QF→final), divergência barata e deliberada — zebra em 1×2 apertado, placar exato fora do modal —
onde um único acerto descorrelacionado ≈ 40–50 pts (final ×4) enquanto o pelotão zera junto.

**Refs:** `scoring.Scorer.best_prediction` (objetivo atual), `format_engine.monte_carlo`
(infra de simulação reaproveitável), `scoring.toml::phase_weights` (onde a alavanca mora),
`BOLAO.md` (decisão do risk 2026-06-17; standing/gap como inputs). Relacionado: ENG-32
(mesma tensão E[pts]-vs-realizado no KO), ⚪ENG-24
(base aproximada limita a precisão do E[pts] absoluto, não do diferencial).
**Correção proposta (investigação primeiro, como no ENG-32):** (1) modelar o pelotão como
apostadores de consenso (palpite = favorito do mercado com placar modal; sensibilidade: % do pelotão
que segue o consenso); (2) Monte Carlo dos jogos restantes (reusa `monte_carlo`/matrizes): para cada
política no jogo-alvo (E[pts]-máximo vs alternativas divergentes), simular a distribuição de pontos
meus vs pelotão e estimar **P(top-k | gap atual, jogos restantes)**; (3) se a política divergente
dominar em P(top-k) sem custo material de E[pts] nos cenários de gap real, expor como modo opt-in
da CLI (ex.: `predict --pool-gap <pts> --pool-size <n>`), edition-agnóstico; senão, ⚪ descartar
com o número.
**Aceite:** relatório reproduzível (script em `scratchpad/` ou `scripts/`) com P(top-k) por política
em ≥2 cenários de gap (atrás/na frente), e decisão numérica manter/expor; se expor, teste cobrindo
a seleção divergente (jogo apertado ⇒ lado zebra escolhido quando o modo ativo) e docs
sincronizados. `pytest` verde. **Resolução (veredito: EXPOR, escopo mínimo).** Simulador rastreado
`scripts/eng36_pool_sim.py` (3000 torneios restantes via modelo+blend; pelotão de 60 sintéticos
consenso/ruidoso/caça-empate ancorado no standing real 285/337/21º; políticas fiel / exato-alt /
zebra-final / zebra-sf / zebra-qf; comparação pareada — gerador compartilhado). Números: **atrás**,
fiel P(#1)=0,7% e zebra **só na final** P(#1)=**4,0%** (~6×; top-3 2,2%→8,5%) a custo de ~7 pts
esperados; divergir antes (SF 3,7% / QF 3,5%) não adiciona P(#1) e custa mais; **exato-alt ≈ fiel**
(0,8%) ⇒ a correlação com o pelotão mora no **lado**, não no placar; **na frente**, fiel domina
(47,1% vs 35,1%) ⇒ regra condicional ao standing. Exposto como `predict --pool-behind` (não
`--pool-gap`: a simulação mostrou que a regra é binária — atrás ⇒ zebra no peso máximo — sem
dependência fina de gap/tamanho): `knockout.predict_knockout(pool_behind=)` palpita a zebra nas 3
camadas (90' por E[pts] dentro do lado azarão; ET/pên. na zebra); `pipeline.run`/`_max_ko_weight`
restringe aos estágios de peso **máximo** da edição (a final no Equilíbrio gradual) —
edition-agnóstico. Regra de campanha nas Decisões vivas do `BOLAO.md`
(refazer a sim na véspera da final com o standing do dia). Testes: zebra nas 3 camadas, E[pts]-ótimo
dentro do lado, `pool_behind=False` inalterado, flag no parser. 154 verdes; docs sincronizados
(README/AGENTS/CHANGELOG/BOLAO).
**Commit:** 931be03

## ENG-37
**Padrão de largura de linha nos `.md`: régua definida (100 caracteres) + scripts on-demand** · P3 ·
processo/docs · ✅ feito

Não existe regra de formatação para markdown no repo
(o pre-commit só tem ruff/`bolao-sync`/ `backlog-integrity`); a convenção observável é quebra suave
em ~100 caracteres, mas ela é violada em vários pontos antigos: os links de docs no topo
do `AGENTS.md` (~125), entradas do `CHANGELOG.md` (~106) e entradas do histórico do `BOLAO.md`
em linha única (~260). Decisão do usuário (2026-07-01): manter um padrão. A régua deve ser
em **caracteres**, não bytes — em UTF-8 acento vale 2 bytes e travessão 3, então uma linha de 95
caracteres em português "estoura" 100 bytes sem estar longa.

**Refs:** `.pre-commit-config.yaml` (onde o hook entra), `scripts/check_backlog.py`
(modelo de hook local em Python), `AGENTS.md` §Convenções e cuidados (onde documentar a régua).
**Correção proposta:** (1) fixar a régua em **100 caracteres** e documentá-la no `AGENTS.md`; (2)
hook de pre-commit (markdownlint `MD013` ou script local no padrão do `check_backlog`)
com **isenções**: `data/editions/*/history/*.md` (snapshots imutáveis — não se reescreve registro),
linhas de tabela, URLs/links longos e blocos de código; (3) varredura única reembrulhando os `.md`
de prosa (`AGENTS.md`, `README.md`, `CHANGELOG.md`, `docs/`, `BOLAO.md`) para conformar o legado.
**Aceite:** hook bloqueia linha nova >100 caracteres em `.md` fora das isenções; varredura única
aplicada (repo conforme); régua documentada no `AGENTS.md`; `pre-commit run --all-files` e `pytest`
verdes.
**Resolução:** ferramenta on-demand (não hook no pre-commit) — reflow automático `textwrap.fill`
cru é frágil: quebra em qualquer espaço sem noção de rótulo+número, parênteses ou chamadas de
função, produzindo fragmentos órfãos (ex.: `Espanha\n**19,2%**,`, `(+13\nKO)`). Implementado
`scripts/check_markdown_line_length.py` (detecta violações; isenções automáticas: tabelas, URLs,
`uv run`, diagramas C4, blocos de código). O `scripts/reformat_markdown_lines.py` inicial
(`textwrap.fill` cru) foi **removido** — causou justamente os fragmentos órfãos que a régua
deveria evitar; não há substituto automático, revisão é manual/por agente. Régua (100 caracteres
UTF-8) documentada no `AGENTS.md` §Convenções e cuidados. Todos os 12 `.md` de prosa do repo
(`AGENTS.md`, `README.md`, `CHANGELOG.md`, `BOLAO.md`, `docs/*.md`, skill `palpites-copa`)
passaram por revisão criteriosa linha a linha (rejunta fragmento → rewrap respeitando unidades
semânticas, verificado por `git diff --word-diff` sem alteração de palavra alguma). A revisão
também achou e corrigiu 2 bugs reais introduzidos pelo reflow automático anterior: um parágrafo
do `AGENTS.md` **triplicado** por um `sed` malformado, e duas linhas de blockquote no `C4.md`/
`PRD.md` que haviam perdido o marcador `>` (quebraria a renderização, não só estética).
Resultado: **100% compliance técnica** (zero violações) + qualidade semântica revisada arquivo
por arquivo, sem fragmentos órfãos remanescentes (exceto sintaxe de diagrama Mermaid, que não é
prosa).
**Commit:** 53518c9

## ENG-38
**`blend_weight` fixado por prior (0,6), nunca otimizado com dado** · P2 · `blend`/`backtest` ·
✅ feito

O peso do mercado no blend (ENG-19) foi fixado em 0,6 por prior de princípio ("odds de fechamento
são quase-otimamente calibradas") e nunca revisitado, apesar de o `blend-track` acumular jogos
disputados com odds — em 02/07 já eram 49, amostra suficiente para uma escolha direcional. Como o
peso multiplica **todos** os jogos com odds (inclusive o KO de peso ×2/×4), qualquer subotimalidade
é paga em cada palpite.

**Refs:** `backtest.prospective_blend_report` (avalia 1 peso por chamada, re-fitando tudo),
`scoring.toml::blend_weight` (o prior), `cli.cmd_blend_track`. Relacionado: ENG-19 (o blend),
ENG-35 (totals).
**Correção:** `blend_weight_sweep` — refatora o report em coleta (`_collect_blend_games`, 1 fit/dia,
o custo caro) + tally por peso (`_tracking_for_weight`, barato), e varre a grade numa passada só.
Exposto como `blend-track --sweep` (grade 0,0..1,0, passo 0,1, marca mínimo e peso em uso).
**Aceite:** sweep roda numa passada as-of (Brier do modelo idêntico em todos os pesos da grade —
testado); w=0 reproduz o modelo-puro; sem odds ⇒ n=0 sem quebrar. Docs (README/CHANGELOG/AGENTS)
sincronizadas. **Resolução:** Brier **monotônico decrescente** em w nos 49 jogos — 0,4420
(modelo-puro) → 0,4179 (0,6) → 0,4100 (w=1,0): o mercado foi estritamente melhor que o modelo
nesta Copa. `blend_weight` da edição 2026 elevado a **0,8** (captura o grosso do ganho sem abraçar
o extremo w*=1,0 em amostra pequena; teste de trava atualizado com a justificativa). Limitação
honesta: só jogos de **grupo** — no KO a convenção martj42 (placar inclui prorrogação) torna o
desfecho de 90' ambíguo e corromperia o Brier em silêncio.
**Commit:** c9fd4a7

## ENG-39
**Simulador de endgame é juiz e parte: gerador = modelo, cego à subestimação de empate em final**
· P2 · `scoring`/`estratégia` · ✅ feito

O `eng36_pool_sim` amostra os placares "reais" das MESMAS matrizes usadas para palpitar (premissa
declarada). Consequência estrutural: ele **não pode punir o modelo por estar errado** — e o modelo
está errado justamente onde a regra de endgame decide: P(empate 90') de uma final entre parelhos
sai ~28% no DC (treinado em eliminatórias/amistosos de ritmo normal), contra **~60% empírico**
(5 das 8 finais desde 1994 empatadas nos 90': 1994, 2006, 2010, 2014, 2022). A conclusão do ENG-36
("zebra na final") foi tirada dentro dessa circularidade, e a política do líder (caça-empate) era
subavaliada pela mesma razão.

**Refs:** `scripts/eng36_pool_sim.py` (gerador compartilhado; políticas), `blend.rescale_matrix`
(reusado para o tilt do gerador), `knockout.predict_knockout` (forbid_draw do ENG-32 — validado
agregado em R32/R16, não por fase). Relacionado: ENG-36 (regra superada), ENG-32 (proíbe o palpite
modal do próprio modelo na final), ENG-40 (expor no predict).
**Correção:** (a) políticas `empate-final`/`empate-close` — empate nos 90' com o melhor placar da
diagonal por E[pts] + camadas ET/pênaltis (a arma do líder, cirúrgica no peso ×4); (b)
`--draw-inflate-final P` — infla P(empate 90') **só do gerador** da final via `rescale_matrix`
(palpites seguem cegos), separando crença de realidade para o teste de sensibilidade.
**Aceite:** relatório reproduzível com as novas políticas em ≥2 geradores (modelo puro e inflado)
e decisão registrada no `BOLAO.md`. **Resolução:** `empate-final` **domina** `zebra-final` em
TODOS os geradores — baseline (juiz = o próprio modelo cético): P(top3) 8,4% vs 5,5% a **custo
zero** de E[pts] (a zebra custa ~8); gerador 45%: 10,4% vs 5,2%; gerador histórico 60%: P(#1)
4,9% / P(top3) 14,3% vs 1,2%/3,8%, **ganhando** E[pts] (+13). Na frente, fiel segue dominante no
baseline (48% vs 41%) ⇒ regra continua condicional ao standing. Decisão viva atualizada no
`BOLAO.md` (final atrás ⇒ empate nos 90' + camadas; refazer a sim na véspera com o standing do
dia, com e sem inflação).
**Commit:** c9fd4a7

## ENG-40
**Expor a política `empate-final` (ENG-39) no `predict` — `--pool-behind` ainda gera a zebra
superada** · P2 · `knockout`/`cli` · ✅ feito

A regra de endgame v2 (ENG-39) é "na final, atrás ⇒ empate nos 90' + camadas", mas o único modo
endgame da CLI (`predict --pool-behind`, ENG-36) palpita a **zebra** nas 3 camadas — política
dominada em todos os geradores testados. Até a final (19/07), o palpite de empate precisa ser
aplicado à mão no app, com risco de erro operacional exatamente no jogo de peso ×4.

**Refs:** `knockout.predict_knockout(pool_behind=…)` (onde a zebra mora),
`knockout._zebra_prediction` (análogo a substituir/parametrizar), `pipeline.run`/`_max_ko_weight`
(restrição aos estágios de peso máximo), `scripts/eng36_pool_sim.empate_pick` (a política de
referência já implementada na sim).
**Correção proposta:** trocar o comportamento do `--pool-behind` de zebra para empate-final
(mesma restrição de peso máximo e mesma condicionalidade ao standing), OU parametrizar
(`--pool-behind {zebra,empate}` com default empate). Antes de trocar, re-rodar a sim na véspera
da final com o standing real para confirmar que a dominância se mantém.
**Aceite:** com o modo ativo, o palpite da final sai empate nos 90' (melhor placar da diagonal
por E[pts]) + camadas ET/pênaltis; jogos de peso não-máximo inalterados; teste cobrindo a seleção;
docs (README/AGENTS/CHANGELOG/BOLAO/skill) sincronizadas; `pytest` verde.
**Resolução (parametrizado, default empate):** `predict_knockout(pool_behind=)` vira
`None|"empate"|"zebra"` (valor inválido ⇒ ValueError); o modo `empate` usa
`_empate_prediction` (melhor placar da diagonal por E[pts]) e mantém camadas ET/pênaltis e
avanço fiéis; `zebra` preserva o ENG-36 para a comparação da véspera (a reavaliação
com o standing do dia segue na decisão viva do `BOLAO.md`). CLI: `--pool-behind [empate|zebra]`
em `predict` e `sync-results` (sem valor ⇒ `empate`). Verificado ponta-a-ponta: J104 sai 0×0
+ "vai aos pênaltis" com o modo; J101–J103 (peso ×2) inalterados; `out/` vivo restaurado
fiel. Testes: empate força a melhor diagonal, camadas/avanço idênticos ao fiel, `None`
inalterado, valor inválido levanta, parser dos 2 subcomandos. 162 verdes.
**Commit:** f04c73b

## ENG-41
**Jogos da edição contados em dobro no ajuste quando a base histórica já os contém (peso 7.0)**
· P1 · `pipeline`/`model` · ✅ feito

`pipeline.build_training_frame` concatena a base histórica **inteira** com os jogos disputados da
edição, estes com `CURRENT_EDITION_BOOST` (6.0). O código assume **implicitamente** que a base não
contém a edição corrente — mas `fetch-data` baixa o martj42, que traz o torneio **em andamento**.
Quando a base é atualizada no meio da Copa, cada jogo de grupo disputado entra **duas vezes**: uma
pela base (peso 1.0) e outra pelo boost (6.0) ⇒ peso efetivo 7.0. Isso infla o peso dos resultados
recentes e distorce as probabilidades (o argmax dos palpites é robusto, então o sintoma é
silencioso — só aparece nas probabilidades de campeão, que não têm gabarito diário). Não há
filtro nem dedup; nenhum teste cobria a composição da base.

**Refs:** `pipeline.build_training_frame`, `pipeline.CURRENT_EDITION_BOOST`,
`fetch_data.load_historical`.
**Correção proposta:** antes de concatenar, remover da base os jogos que já entram via fixtures
(casar por data + par não-ordenado de seleções; o resultado autoritativo da edição é o do
`fixtures.csv`). Teste de regressão que falharia com o double-count.
**Aceite:** jogo da edição presente na base entra **uma vez só**, com o boost (não também a 1.0);
placar da base descartado em favor do fixture; linhas de outros dias intactas; `pytest` verde.
**Resolução:** `build_training_frame` chama `_drop_edition_games`, que remove da base as linhas
casando (data, {mandante,visitante}) com os jogos disputados antes do append. Coberto por
`test_build_training_frame_no_double_count`. Efeito na edição 2026: favorita Argentina 31%→24,8%.
**Commit:** 70c1d83

## ENG-42
**Resultados de KO alimentam o fit sem o boost (peso 1.0 via base), pois o fixture guarda slots**
· P2 · `pipeline`/`model` · ✅ feito

A realimentação com boost (`build_training_frame`) usa `f.home`/`f.away`, mas os jogos de
mata-mata no `fixtures.csv` guardam **slots** (`W73`, `2D`), não nomes de seleção — então o filtro
`.isin(edition.teams)` os descarta e eles **não recebem o boost 6.0**. Na prática os resultados de
KO só chegam ao modelo pela `historical_results.csv` (peso 1.0), e **só se ela estiver atualizada**.
Consequências: (a) resultados de KO — os mais recentes e de maior peso de fase — entram
subponderados frente aos de grupo; (b) a realimentação de KO fica **refém da atualidade da base
histórica** (ver ENG-41: base congelada ⇒ modelo cego ao mata-mata inteiro). São **dois caminhos
de realimentação com comportamentos diferentes**, o que já produziu falha silenciosa.

**Refs:** `pipeline.build_training_frame` (filtro `.isin(edition.teams)` que barra os slots),
`sync`/`format_engine` (onde o bracket resolve slot→seleção), `edition.Fixture`.
**Correção proposta:** resolver os slots dos jogos de KO **disputados** para os nomes reais das
seleções (o bracket já sabe quem jogou) e alimentá-los pelo mesmo caminho com boost — unificando as
duas rotas de realimentação. Alternativa: derivar os nomes do próprio `ko_outcome`/resultado real.
**Aceite:** jogo de KO disputado entra no treino com `CURRENT_EDITION_BOOST` (nomes reais),
uma única vez; teste afirmando que um resultado de KO disputado está no frame de treino com o
boost; `pytest` verde.
**Resolução:** `build_training_frame` chama `sync.resolve_live_bracket` (resolve slots→seleções só
com resultados reais) e usa os nomes resolvidos para os jogos de KO disputados; assim passam pelo
filtro `.isin(edition.teams)` e entram com o boost, uma vez (o dedup do ENG-41 remove a cópia da
base). Coberto por `test_build_training_frame_feeds_knockout_with_boost`. **Efeito:** favorita
Argentina 24,8%→12,9%, Espanha 20,4%→29,1% — a virada expôs que o boost 6.0 nunca foi calibrado
(ENG-44); a correção estrutural (unificar rotas) está certa, o valor do peso é a questão aberta.
**Commit:** 3c8a424

## ENG-44
**`CURRENT_EDITION_BOOST` (6.0) é constante mágica nunca calibrada — sweep out-of-sample de Brier**
· P2 · `model`/`backtest` · ✅ feito

`pipeline.CURRENT_EDITION_BOOST` (6.0) multiplica o peso dos jogos disputados da edição no ajuste.
Foi fixado a olho quando só havia jogos de grupo e **nunca validado por backtest**. O ENG-42, ao
levar o boost também ao mata-mata, revelou o quanto ele domina: a favorita ao título virou de
Argentina para Espanha (24,8%→12,9% vs 20,4%→29,1%) — uma vitória apertada da Argentina a peso 6
derruba o rating. Com o decaimento temporal do modelo, os jogos recentes já pesam muito; 6.0 pode
estar superajustando a forma recentíssima. Não há evidência de que 6.0 seja bom nem ruim — falta
medir.

**Refs:** `pipeline.CURRENT_EDITION_BOOST`, `pipeline.build_training_frame`,
`backtest._as_of_group_matrices` (fit as-of por dia, base do sweep), `backtest.multiclass_brier`,
`blend-track --sweep` (padrão de sweep já existente, a espelhar).
**Correção proposta:** sweep out-of-sample do boost (ex.: 1..10) medindo Brier/log-loss multiclasse
dos jogos disputados da edição viva, reajustando as-of (1 fit/dia por valor), análogo ao
`blend-track --sweep`. Escolher o mínimo; se ≠ 6.0, atualizar — de preferência tornando o boost
**configurável por edição** (`scoring.toml`, como `risk`/`blend_weight`), não constante de código.
Considerar também se KO merece peso distinto de grupo (é o sinal mais recente/decisivo).
**Aceite:** comando/flag que imprime Brier por valor de boost numa passada as-of; boost escolhido
com base no mínimo (documentado no `BOLAO.md`); se virar config, defaults por edição fixados e
teste cobrindo a leitura; `pytest` verde.
**Resolução:** novo `blend-track --boost-sweep` (`backtest.boost_sweep`, `BoostTracking`) mede o
Brier as-of do modelo puro por valor de boost (só grupo, 1 fit/dia). Na 2026 deu **monotônico
crescente** (1.0=0,4707 → 6.0=0,4876 → 12.0=0,5035) ⇒ boost superajusta. O peso virou config
`ScoringConfig.edition_boost` (default 1.0) lido por `build_training_frame`; a constante
`CURRENT_EDITION_BOOST` foi removida; a 2026 fixou `edition_boost = 1.0` no `scoring.toml`.
Cobertura: `test_blend_track_boost_sweep` + os testes de `build_training_frame` passam boost
explícito. Campeão calibrado: Argentina 22,7% / Espanha 19,7% (vs 12,9%/29,1% no 6.0).
**Commit:** 4a792de

## ENG-43
**Nenhuma métrica vigia se o fit ingeriu os resultados recentes (staleness da base é silenciosa)**
· P3 · `observabilidade` · ✅ feito

Não há nenhum sinal que acenda vermelho quando a base de treino está desatualizada ou quando um
resultado recente **não** entrou no ajuste. `blend-track` mede Brier do blend; `efficiency.py` mede
usuário-vs-teto — nenhum vigia "o fit ingeriu os N últimos jogos disputados?". A staleness que
motivou ENG-41/42 passou despercebida por semanas justamente por ser silenciosa (o caminho de
grupo funcionava, mascarando o de KO quebrado).

**Refs:** `pipeline.build_training_frame`, `status.build_status` (candidato natural a exibir o
sinal no briefing de start-of-day), `backtest`/`blend-track`.
**Correção proposta:** um check barato — comparar o conjunto de jogos disputados da edição com o
que efetivamente entrou no frame de treino (com boost) e alertar os ausentes; expor no
`worldcup status` (ex.: "⚠️ N jogos disputados fora do ajuste") e/ou como aviso no `predict`.
**Aceite:** rodar `status`/`predict` com um resultado disputado ausente do treino emite alerta
identificando os jogos; sem ausências, silêncio; teste cobrindo os dois casos; `pytest` verde.
**Resolução.** `pipeline.ingestion_gaps(edition)` devolve os `match_id`s de jogos **disputados** que
não entram no fit — mesmo critério do filtro `.isin(edition.teams)` de `build_training_frame` (após
`resolve_live_bracket`; KO com slot órfão ⇒ fora). Barato (só resultados reais, sem histórico).
`cli.cmd_predict` avisa no caminho vivo; `cli.cmd_status` passa o resultado a `build_status`
(`fit_gaps`), e `format_status` emite uma linha ⚠️ logo abaixo dos stats. Base em dia ⇒ silêncio
(verificado: `ingestion_gaps` na 2026 = `[]`). Testes: `ingestion_gaps` saudável + KO não resolvido
(monkeypatch do bracket) e o alerta/silêncio no `format_status`. 183 verdes.
**Commit:** e49038f

## ENG-45
**KO decidido por gol na prorrogação é gravado com ET ⇒ palpite de 90' pontuado contra o placar
errado** · P2 · `efficiency`/`scoring` · ✅ feito

A convenção martj42/`fixtures.csv` grava o **placar final com prorrogação** nos jogos de KO. Para
os decididos por **gol na prorrogação** (não pênaltis), o `home_goals`/`away_goals` gravado inclui
o(s) gol(s) da ET e **difere do placar real dos 90'**. Mas no app o slot *"placar dos 90'"* é
julgado contra o placar do **tempo normal**. Consequências no lado da **medição**:
1. `efficiency.asof_scores`, o oráculo e o `backtest` pontuam o palpite de 90' contra o placar
   **com ET** ⇒ **super-creditam**. Caso concreto: **J82 Bélgica gravado 3×2, mas 2×2 nos 90'**
   (pênalti... gol de Tielemans na ET, 125'). O `asof_scores` credita **12 pts** a um palpite 2×1
   que, contra o 2×2 real dos 90', daria **~0** — o "teto do tool" fica inflado nesses jogos.
2. `efficiency._actual_ko_outcome` trata `home != away` como *decidido nos 90' → (None, None)*,
   então um jogo de gol-na-ET **não recebe o bônus de ET** E é tratado como tempo normal — erro
   duplo (base errada + bônus perdido).
3. Distinto dos jogos de **pênaltis puros** (empate nos 90', `home == away` preservado), que **são**
   tratados via `shootouts.csv`. A lacuna é **específica de gol na prorrogação** — e contradiz a
   nota do ENG-27 *"a edição viva não sofre disso"*, que só vale para o subcaso de pênaltis.

**Raiz (dado):** nada em `fixtures`/`shootouts` distingue um jogo de gol-na-ET de um resolvido nos
90' — ambos têm `home != away`. Falta um sinal (placar de 90' separado, ou flag `aet`) para pontuar
o slot de 90' corretamente. Verificado no backtest do ENG-32 (`scratchpad/eng32_backtest.py`, com
override manual de J82→2×2): sem o override, o mesmo jogo pontua 12 em vez de 0.

**Refs:** `efficiency.asof_scores`, `efficiency._actual_ko_outcome`, `backtest` (teto de KO),
schema de `Edition.fixtures` (`home_goals`/`away_goals`/`ko_outcome`), `shootouts.csv`, ENG-27
(limitação aceita), SPEC §9.2.
**Correção proposta:** (a) registrar o **placar dos 90'** separado do placar-com-ET nos KO decididos
na prorrogação — coluna opcional no fixture (`reg_home`/`reg_away`) ou flag `aet` + placar de 90',
captura manual sob a regra `confirmar-placares-multiplas-fontes`; (b) `efficiency`/`backtest` usam o
placar de 90' quando presente e reconhecem a ET (base **e** bônus corretos); (c) sem o dado, ao
menos **não** conceder exato/saldo em jogo marcado `aet`.
**Aceite:** um KO decidido por gol na prorrogação (J82) é pontuado contra o placar de 90' (2×2) e
recebe o bônus de ET; teste de regressão que **falha** com a lógica atual (usa 3×2 e trata como
90'); `pytest` verde.
**Resolução (via arquivo companheiro).** Novo `regulation.csv` (`match_id,reg_home,reg_away`,
opcional, versionado) guarda o placar de **90'** dos KO decididos por gol na ET — escolhido em vez
de coluna no `fixtures.csv` para **não** tocar o caminho de escrita do `sync.write_fixtures_atomic`
(mesmo padrão do `shootouts.csv`). `edition._load_regulation` → `Edition.regulation`; `as_of`
descarta entradas futuras. `efficiency.regulation_90(edition, fixture)` devolve o 90' (reg quando
presente, senão o gravado); `asof_scores` passa a pontuar o slot de 90' e o oráculo contra ele, e o
jogo cai no caminho de ET (`_actual_ko_outcome` inalterado — recebe o 90' já corrigido). **J82**
(gravado 3×2, 90' 2×2) semeado; o teto do tool as-of da 2026 caiu **404→392** (−12, o super-crédito)
e a eficiência subiu de 89,9%→92,6%. O `backtest` das Copas passadas **não** muda (o martj42 não
separa 90'/ET — limitação aceita, SPEC §9.2). Escopo: só a **medição** (efficiency); o ajuste do
modelo segue no placar gravado. **Captura futura** de outros jogos gol-na-ET é manual (≥2 fontes),
como os shootouts sob latência. Testes: `test_load_regulation`,
`test_as_of_drops_future_regulation`, `test_regulation_90_*`,
`test_eng45_et_goal_scored_against_90_and_gets_bonus`. 171 testes verdes.
**Commit:** 43006e7

## ENG-46
**`archive_scores` só de grupo ⇒ teto de KO congela da reconstrução, não do snapshot real** · P3 ·
`efficiency`/`pipeline` · ✅ feito

Extensão do ENG-34: no teto congelado, a hierarquia prefere o snapshot real de `history/`
(`archive_scores`), mas `archive_scores` **pulava** o mata-mata (`if not f.is_group: continue`) —
então todo jogo de KO congelava da **reconstrução** (menos fiel: o placar de 90' reconstruído
diverge do que o tool mostrou naquela manhã; ver os +31 de ruído do `--compare-archive`). Como o KO
carrega o peso de fase **×2/×4**, é onde a fidelidade mais importa.

Dois blockers levantados na investigação (2026-07-05): (a) o snapshot guardava, para KO,
`P_mandante = P(avança)` com `P_empate`/`P_visitante` **vazios** — **sem o 1×2 do 90'** que a base
do palpite de 90' exige; (b) o palpite de ET/pênaltis vive como **string renderizada** no snapshot.

**Refs:** `efficiency.archive_scores`, `efficiency.reconcile_ceiling` (ENG-34),
`pipeline.run` (ramo de KO), `pipeline._ko_layer_text`, `efficiency.regulation_90` (ENG-45).
**Resolução.** (1) `pipeline` passa a gravar o **1×2 do 90'** (de `outcome_probs_from_matrix`) em
`P_mandante`/`P_empate`/`P_visitante` do KO — uniformiza a semântica (P_* = 1×2 do 90' p/ todos) e é
seguro (essas colunas de KO são CSV-only: não exibidas nem lidas no ramo KO; o avanço fica em
`avanca`). (2) `archive_scores(edition, asof)` pontua o KO de snapshot **novo formato**
(`P_empate`/`P_visitante` preenchidos): placar de 90' (palpite arquivado vs `regulation_90`, base
pelo 1×2 do snapshot) ×peso + bônus de ET/pênaltis, **reusando o desfecho real do `asof`**
(`act_et`/`act_pen`) — só o palpite vem do snapshot. `_parse_ko_layers` inverte o
`_ko_layer_text` (robusto: usa os nomes de exibição do próprio snapshot). `_archive_ko_points`
(puro) isola a pontuação, testável.
**Limitação honesta:** só ajuda KO **arquivado a partir de agora** — snapshots passados de KO
(R32/R16 já jogados) têm o formato antigo e **não** têm o 1×2 do 90', então continuam congelando da
reconstrução. Para a 2026, beneficia QF em diante (os jogos de maior peso). O snapshot de 05/07 foi
re-arquivado no novo formato (91–104 PREVISTO), então os R16 de hoje já entram por `archive` quando
disputados.
**Aceite:** um KO de snapshot novo formato é pontuado pelo palpite arquivado (placar de 90' + bônus)
e vira `source=archive` no `ceiling.csv`; KO de formato antigo é pulado; testes de
`_parse_ko_layers` e `_archive_ko_points`. `pytest` verde (179).
**Commit:** 108bdfe

## ENG-47
**Números da campanha 2026 hardcoded em `build_presentation.py`** · P3 · apresentação · ✅ feito

`scripts/build_presentation.py` guardava os números vivos da campanha (jogos disputados, pontos,
favoritos ao título, bracket em andamento, Brier) como constantes hardcoded no código
(`AS_OF`, `champ_bars()` default, `stat(...)` das slides 9/9b/10/12) — cada rodada exigia editar o
script à mão (3 vezes em uma única sessão, 06–08/07). Violava o princípio central do projeto:
"nada específico de um ano fica no código".

**Refs:** `scripts/build_presentation.py` (constantes removidas),
`scripts/update_presentation_data.py` (novo).
**Resolução.** Os números viram dado em `data/editions/2026/presentation.toml`
(`load_presentation_data(edition)`, `--edition` seleciona a edição). `update_presentation_data.py`
atualiza os campos **deriváveis** desse TOML a partir do estado atual: jogos disputados e
favoritos ao título (`out/palpites-2026.{csv,md}`), Brier modelo-vs-blend
(`worldcup.backtest.prospective_blend_report`, mesma métrica do `blend-track`) e a contagem de
melhorias do backlog (`docs/BACKLOG.md`). **Preserva** (não deriva) `campanha.pontos`/
`eficiencia_pct` — só existem no placar real do usuário, informação externa ao repo — e
`campanha.fase`/`bracket_destaque.*` — curadoria editorial (qual seleção acompanhar, qual jogo
destacar), não cálculo. Cablado na skill `palpites-copa` (passo 5.5): roda logo após repalpitar,
fechando o loop de "atualizar a apresentação" sem pedido separado do usuário.
**Aceite:** `update_presentation_data.py --edition 2026` recalcula `jogos_disputados`, `favoritos`,
`validacao.*` e `evolucao.melhorias_entregues` sem tocar em `pontos`/`eficiencia_pct`/`fase`/
`bracket_destaque`; `build_presentation.py --edition 2026 --docs` gera o HTML a partir do TOML
atualizado; ruff/mypy/pytest verdes (187 testes).
**Commit:** ba1d532

## ENG-48
**`efficiency.py` nunca creditava o bônus de prorrogação/pênaltis (chave de data incompatível)** ·
P1 · eficiência · ✅ feito

`_penalty_lookup` indexava a fonte martj42 por `str(r["date"])` sobre uma coluna `datetime64` ⇒
chave `'2026-06-29 00:00:00'`. O consumidor `_actual_ko_outcome` procurava por `str(f.date)`, e
`Fixture.date` é `str` ⇒ `'2026-06-29'`. As chaves **nunca** batiam: todo KO empatado nos 90' caía
no ramo "a fonte ainda não confirmou (latência) — não inferir" e **perdia o bônus** de ET/pênaltis
(+3/+3 ×peso de fase). O aviso "N jogos empatados nos 90' ainda sem shootout na fonte" não
reportava latência da fonte — reportava o próprio bug.

Efeito: o **teto** do tool saía subestimado e a **eficiência** superestimada. Em 10/07 (97 jogos):
teto 399 → **423** (+24), eficiência 102,5% → **96,7%**. Os dois "acima do teto" (08/07 e 10/07)
eram artefato. **Não afetava palpites**: `scripts/efficiency.py` é isolado — nada em `src/` o
importa, e ele só escreve `ceiling.csv`.

Por que passou: `tests/test_efficiency.py` montava o `pens` **à mão**, no formato do consumidor
(`_pens(date, ...)` com `"2026-06-29"`), e nunca exercitava `_penalty_lookup`. Produtor e consumidor
tinham cobertura, a **costura** entre eles não.

**Refs:** `scripts/efficiency.py` (`_date_key`, `_penalty_lookup`, `_actual_ko_outcome`),
`tests/test_efficiency.py::test_penalty_lookup_casa_com_a_data_do_fixture`.
**Resolução.** `_date_key(date) -> str(date)[:10]` normaliza os dois lados (aceita `str` da edição e
`datetime64` do pandas). Teste de regressão passa pelo `_penalty_lookup` **real**, com um frame
`datetime64`, em vez de fabricar a chave — falha sem o fix (verificado). Teto recongelado com
`--reset-ceiling` (ENG-34: o congelamento protege contra drift, não contra bug — corrigir exige
reset explícito).
**Aceite:** `_actual_ko_outcome(1, 1, "2026-06-29", ...)` devolve `("penalties", "away")` para J74
via lookup real; latentes caem de 5 (J74, J75, J82, J88, J96) para 1 (J96, latência genuína — a
base martj42 termina em 03/07); ruff/mypy/pytest verdes (188 testes).
**Commit:** 39a150a

## ENG-49
**Fontes redundantes do desfecho de KO são escolhidas, não comparadas** · P2 · eficiência/dados ·
✅ feito

O repo conhece o desfecho de um KO (prorrogação vs pênaltis, e quem venceu) por **duas vias
independentes**: `data/editions/<ano>/shootouts.csv` (curado à mão, ≥2 fontes) e a coluna
`penalty_winner` da base martj42. O ENG-27 decidiu que o `efficiency.py` lê **só** a martj42 — o
que é defensável (a base é a referência do ajuste) — mas o outro lado passou a ser ignorado em vez
de conferido. Resultado: redundância existe e **não vira detector**.

Custo concreto: o ENG-48 (chave de data incompatível) sobreviveu a ≥2 rodadas de medição
imprimindo "5 jogos empatados nos 90' ainda sem shootout na fonte". Três deles (J74, J75, J88)
estavam no `shootouts.csv` da edição, e o J82 no `regulation.csv`. Uma comparação cruzada teria
gritado "a edição afirma pênaltis no J74; a fonte não confirma" e o bug cairia na primeira
rodagem, sem depender de questionamento humano.

**Refs:** `scripts/efficiency.py` (`_penalty_lookup`, `_actual_ko_outcome`),
`data/editions/2026/shootouts.csv`, `data/editions/2026/regulation.csv`, ENG-27, ENG-48.
**Proposta.** Ao montar a lista de "latentes", cruzar com `Edition.shootouts`/`Edition.regulation`
e classificar cada jogo em: (a) **latência genuína** — ausente das duas fontes (ex.: J96, cuja data
é posterior ao fim da base); (b) **contradição** — a edição afirma um desfecho que a fonte não
confirma ⇒ **erro**, não latência: avisar alto (o caso do ENG-48). Não é preciso mudar de quem se
lê: basta que discordância seja **ruidosa**.
**Resolução.** `cross_source_ko_check(edition, scores) -> (latência, contradição)` cruza as duas
fontes para todo KO empatado nos 90' e classifica: **latência** (ninguém afirma o desfecho — a base
ainda não ingeriu o jogo) vs **contradição** (a edição afirma e a fonte não confirma, ou confirma
diferente). Contradição imprime `🚨 CONTRADIÇÃO DE FONTE` e diz explicitamente que **não é
latência**. Continua lendo da martj42 (ENG-27 intacto); só a discordância virou ruidosa.
**Aceite:** ✅ com o bug do ENG-48 reintroduzido a sonda acusa `[74, 75, 82, 88]` como contradição e
só `[96]` como latência; sem o bug, contradição = `[]` e J96 segue latência (a base termina em
03/07). Testes: um jogo em cada classe + um contra a `Edition` **real** (guarda a chave `int` do
`shootouts.csv`, a mesma família de bug do ENG-48, um nível acima).
**Commit:** 5da25ff

## ENG-50
**Anomalia numérica vira narrativa em vez de gatilho** · P2 · eficiência · ✅ feito

Eficiência = `seus_pontos / teto_do_tool`. Um valor **> 100%** significa que o usuário superou o
palpite que maximiza pontos esperados — possível (variância de exatos), mas **anômalo**. Hoje o
script imprime o número sem limiar nem ação prescrita, e a interpretação fica por conta de quem lê
— que tipicamente produz uma explicação plausível (*"variância"*, *"ruído de reconstrução"*) e
encerra a investigação. Foi exatamente o que aconteceu em 08/07 e 10/07: **dois** "acima do teto"
seguidos, ambos artefato do ENG-48, ambos racionalizados.

O `blend-track` já faz o oposto e serve de modelo: o monitor de regime de empates tem **limiar**
(z ≥ 2σ) e **ação prescrita** ("gatilho não atingido — não agir"). A eficiência não tem nenhum dos
dois.

**Refs:** `scripts/efficiency.py` (saída final), `worldcup.backtest.pooled_draw_calibration`
(monitor de empates, o padrão a imitar), ENG-48.
**Proposta.** Definir limiares e a ação de cada faixa na própria saída: eficiência > 100% ⇒ avisar
que o teto pode estar subestimado e listar as suspeitas mecânicas primeiro (bônus de KO não
creditado, jogos fora do teto, `ceiling.csv` congelado antes de um fix) **antes** de oferecer a
leitura estatística. Mesma ideia para o líder acima do teto. O objetivo não é proibir a explicação
por variância — é **exigir que a checagem mecânica venha antes dela**.
**Resolução (em duas levas).** 1ª leva (5da25ff): **canário de caminho morto**
(`dead_path_canary`) — se há KOs empatados nos 90' e o bônus de ET/pênaltis foi creditado em
**zero** deles, o script grita que a hipótese mecânica vem antes da estatística. É uma checagem de
**população**, não de caso: não precisa saber o desfecho de nenhum jogo. Teria pego o ENG-48 na
primeira rodagem. 2ª leva (8a116dc): (a) `ceiling_anomalies` dispara quando os pontos do usuário
**ou** do líder passam do teto, e `mechanical_suspects` imprime as sondas **antes** de qualquer
leitura estatística
— a frase pré-escrita "líder pegou variância de exatos" saiu do código; a variância só é oferecida
depois que todas as sondas voltam limpas. (b) Procedência: `code_fingerprint` (sha256 de
`efficiency.py` + `scoring.py` + `knockout.py`, pega até alteração não commitada) vai para a coluna
`code` do `ceiling.csv`; `provenance_split` separa **desatualizado** (recongele) de **desconhecido**
(pré-ENG-50). CSV antigo sem a coluna segue carregando. (c) A skill `palpites-copa` (passo 6) teve
as explicações pré-escritas expurgadas: **documento fornece checagens, não explicações** — um doc
que antecipa a explicação de uma anomalia a imuniza contra investigação, e foi ele que me entregou
"ruído de reconstrução" e "variância de exatos" prontas em 08/07 e 10/07.
**Aceite:** ✅ com o teto do ENG-48 (399) a saída acusa as duas anomalias (409 e 471 > 399) e 5
sondas sujas; com o teto correto (423) sobra a anomalia do líder e 2 sondas sujas honestas (J96 sem
bônus por latência; 30 jogos só reconstruídos). Recongelamento com procedência **não mudou nenhum
teto** (diff do `ceiling.csv` = só a coluna `code`); 199 testes verdes.
**Commit:** 8a116dc
