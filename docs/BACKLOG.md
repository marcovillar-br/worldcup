# BACKLOG — engenharia

Backlog de engenharia do projeto, **rastreado e vivo**. Fonte de verdade dos itens de melhoria;
o status de um item vira ✅ **no mesmo commit** que o resolve (mesma disciplina de sincronia de
artefatos do `AGENTS.md`). Leia no início da sessão quando for trabalhar em melhorias.

**Prioridade:** P1 (correção/dados) · P2 (lacuna real) · P3 (boa prática incremental).
**Status:** 🔴 todo · 🟡 fazendo · ✅ feito · ⚪ descartado.
**Refs:** aponte para **símbolos** (`módulo.função`), não `arquivo:linha` — número de linha envelhece em silêncio.

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
| [ENG-24](#eng-24) | P2 | scoring | 🔴 | Base (1–13) usa a probabilidade interna do app (inobservável) ⇒ eficiência só aproximada |

---

## ENG-1
**Reencontro de seleções colapsa o resultado indexado por par** · P1 · `sync.py` · ✅ feito

`sync._edition_results` monta `scores[(home, away)]` para todos os jogos da Copa do ano.
Se duas seleções se enfrentam **duas vezes** na mesma Copa com a mesma orientação na fonte
(adversários de grupo que se reencontram no mata-mata — possível no formato 2026), a segunda
partida sobrescreve a primeira no dict, e `_result_for` pode preencher o jogo de grupo com o placar
do mata-mata (ou vice-versa), **sem erro**. O valor inteiro da ferramenta é a fidelidade dos
resultados.

**Correção proposta:** indexar por `(data, par)` (ou desambiguar por estágio/data) — tanto o
`fixtures.csv` quanto a fonte têm `date`. Casar cada fixture pelo seu `date`.
**Aceite:** teste de regressão com um par que joga 2× na mesma Copa (grupo + KO) com a mesma
orientação; o jogo de grupo recebe o placar do grupo e o de KO o placar do KO. `pytest` verde.
**Commit:** 17272f2

## ENG-2
**Mando do anfitrião não aplicado no backtest** · P2 · `backtest.py` · ✅ feito

`backtest.run_backtest` chama `score_matrix(home, away, neutral)` sem `host_away`/`hosts`. A produção usa
`MatrixCache._host_away` + `edition.hosts` (e trata o anfitrião listado como visitante). Logo, jogos
do país-sede (Qatar 2022, África do Sul 2010) são pontuados de forma diferente do caminho real — o
backtest deixa de reproduzir fielmente o que o app faria.

**Correção proposta:** passar o conjunto de anfitriões da edição-alvo ao backtest e reusar a mesma
lógica de `host_away` da produção (idealmente via `MatrixCache`).
**Aceite:** num jogo do anfitrião, a matriz do backtest == a da produção. Teste cobrindo um caso
host-away. `pytest` verde.
**Commit:** 75255bc

## ENG-3
**Convergência do otimizador ignorada** · P2 · `model.py` · ✅ feito

`minimize(...)` em `model.DixonColesModel.fit` roda com `maxiter=500` e descarta `res.success`/`res.status`; usa
`res.x` aconteça o que acontecer. Um fit não-convergido gera previsões ruins sem nenhum sinal.

**Correção proposta:** se `not res.success`, emitir `logger.warning` (depende de [ENG-4]) com
`res.message`; checar `np.isfinite` nos parâmetros. Decidir se vale subir `maxiter` quando a base
crescer.
**Aceite:** teste que força não-convergência (maxiter baixo) e verifica que o aviso é emitido sem
quebrar a saída. `pytest` verde.
**Commit:** f4ffd48

## ENG-4
**`logging` no lugar de `print()` na biblioteca** · P3 · observabilidade · ✅ feito

Tudo é `print()` no `cli.py`; a biblioteca (`model`, `sync`, `pipeline`) não tem como emitir avisos.
Decisões silenciosas hoje invisíveis: seleções descartadas pelo `min_matches` em `DixonColesModel.fit`,
não-convergência (ENG-3), alias/seleção sem tradução.

**Correção proposta:** `logging.getLogger(__name__)` na biblioteca; CLI configura handler/nível
(ex.: `--verbose`). Mantém `print()` só para a saída ao usuário.
**Aceite:** avisos saem por `logging` e são capturáveis em teste (`caplog`). `pytest` verde.
**Commit:** f364ee2

## ENG-5
**Validar schema do CSV baixado** · P3 · `fetch_data` · ✅ feito

`download_raw`/`normalize` (`fetch_data.py`) não checam as colunas da fonte. Se o `martj42` mudar o
schema, o erro estoura adiante, críptico.

**Correção proposta:** após o download, validar presença das colunas esperadas e dar `NetworkError`
(ou erro dedicado) claro e cedo.
**Aceite:** teste com CSV de colunas faltando → erro explícito. `pytest` verde.
**Commit:** 061f223

## ENG-6
**Separar camada de render (`render.py`)** · P3 · `cli` · ✅ feito

`cli.py` tem ~500 LOC e mistura argparse, handlers, escrita CSV e ~200 linhas de
`render_markdown`/`render_html`. Coesão/teste isolado da apresentação.

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
**Decisão:** piso `fail_under = 65` (cobertura medida ~74%) — pega regressões grandes sem fragilidade;
subir conforme `sync`/`pipeline` (hoje 34%/40%) ganharem testes de integração.
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

`version = "0.1.0"` fixo, sem `CHANGELOG` nem tags. Para algo agnóstico a edição que sobrevive a
várias Copas, dificulta rastrear o que mudou entre edições.

**Correção proposta:** adotar `CHANGELOG.md` (Keep a Changelog) + tags por marco; avaliar versão
dinâmica via `hatch`.
**Aceite:** CHANGELOG criado com o histórico recente; convenção de tag definida.
**Resolução (2026-06-13):** adiado e reaberto no mesmo dia (a pedido) — implementado em escopo
**enxuto**: `CHANGELOG.md` (Keep a Changelog) semeado com o marco `0.2.0`, bump de versão em
`pyproject`/`__init__`, convenção de tag `vX.Y.Z` documentada e tag `v0.2.0` criada. Versão dinâmica
via `hatch` ficou de fora (baixo valor p/ mantenedor único); revisitar se a manutenção do bump
manual em dois arquivos incomodar.
**Commit:** 94fe954

## ENG-11
**Vigiar proporcionalidade doc/código; consolidar docs** · P3 · processo · ✅ feito

A camada *meta* (docs/processo/skills) cresceu a ~64% do tamanho do código (1.366 linhas de md vs
~2.135 LOC) e a regra de sincronia de artefatos obriga tocar vários docs por mudança — o andaime
arrisca ficar mais pesado que a casa. Não é bug; é vigilância de proporcionalidade.

**Correção proposta:** tratar "criar novo doc/skill/hook" como decisão que precisa se pagar;
preferir **consolidar a adicionar**. Revisar sobreposição entre `AGENTS.md`, `README.md` e
`docs/SPEC.md` periodicamente e eleger um canônico por assunto (já feito p/ comandos → README).
**Aceite:** revisão de sobreposição registrada; nenhuma seção duplicada entre os três docs sem um
canônico declarado. (Item de vigilância recorrente — fechar quando a revisão for feita; reabrir a
cada salto de doc.)
**Revisão (2026-06-13):** canônicos declarados — comandos → `README.md`; arquitetura/convenções →
`AGENTS.md`; metodologia/matemática → `docs/SPEC.md`; **limitações → `docs/SPEC.md` §9.2** (era a
única duplicada sem canônico: estava nos três docs; README mantém resumo ao usuário, AGENTS aponta
para o SPEC). Demais sobreposições são audiências distintas (ex.: README §Estrutura ≠ AGENTS
§Arquitetura). Reabrir a cada salto de doc/skill.
**Commit:** 8e4616d

## ENG-12
**Bônus de prorrogação/pênaltis definidos mas não computados** · P2 · `scoring.py` · ✅ feito

`scoring.toml` define `extra_time = 3.0` e `penalties = 3.0` (bônus oficiais do app, confirmados nas
telas de regras), mas `Scorer.points()` nunca lê esses parâmetros — só computa base + exact +
goal_diff + winner_goals + loser_goals + goleada. Consequências: (a) o **backtest subestima** os
pontos em jogos de mata-mata decididos na prorrogação/pênaltis; (b) a config tem valores mortos que
enganam quem for ajustar a pontuação. (Para a escolha do placar de 90' é neutro: o bônus de ET/pên
independe do placar escolhido.)

**Correção proposta:** método `Scorer.knockout_bonus()` que pontua os palpites de prorrogação/
pênaltis (`KnockoutPrediction.extra_time`/`penalty_winner`) contra o desfecho real, e integrá-lo ao
backtest onde o desfecho é determinável (ex.: `shootouts.csv` indica ida a pênaltis e vencedor).
Cuidado: o histórico nem sempre separa placar de 90' vs prorrogação (ver SPEC §9.2) — escopo e
limites a definir.
**Aceite:** teste cobrindo um KO decidido nos pênaltis → bônus +3 concedido; backtest usa o desfecho
real. `pytest` verde.
**Progresso (c00dc93):** método `Scorer.knockout_bonus()` implementado e testado (config não está
mais morta). **Bloqueio descoberto:** o `historical_results.csv` local (saída do `fetch_data.normalize`)
não tem coluna de **fase** nem dados de **pênaltis** (`shootouts`), então o backtest não identifica
jogos de KO nem o desfecho ET/pênaltis. Fechar exige estender o pipeline: persistir `shootouts` no
histórico + inferir/rotular a fase. Sub-tarefa de dados antes de wirar no backtest.
**Resolução (0df13f6):** `fetch_data` agora **mescla** `shootouts.csv` na base histórica como coluna
`penalty_winner` (canônico, casado por `date+home+away`; `OUTPUT_COLUMNS`, `_merge_penalty_winner`,
`fetch` baixa best-effort, `load_historical` compat com bases antigas). O `backtest._knockout_bonus_for`
concede os bônus de KO (`Scorer.knockout_bonus`: +3 ida aos pênaltis, +3 vencedor) nos jogos com
`penalty_winner`, via `predict_knockout` sobre a matriz as-of; o relatório conta os jogos de pênaltis.
Testes: merge no `normalize` (com/sem shootouts) + bônus de KO no backtest (jogo de pênaltis → 6/3/0).
Validado end-to-end: **Copa 2022 reconhece 5 jogos de pênaltis** e soma o bônus. **Limitação aceita
(não é o bug, é a fonte):** o martj42 não traz a **fase** nem separa 90' de prorrogação, então jogos
decididos **dentro da prorrogação** não são identificáveis e **não** recebem bônus de ET (documentado
em SPEC §9.2). A edição **viva** não sofre disso — `sync` resolve o bracket real com os shootouts.
**Commit:** 0df13f6

## ENG-13
**Default morto `n_sims=8000` em `monte_carlo()`** · P3 · `format_engine.py` · ✅ feito

`format_engine.monte_carlo()` tem assinatura `n_sims: int = 8000`, mas o caminho real (CLI/pipeline)
sempre passa `5000`, e o SPEC §7.1 diz "padrão 5000". O default da assinatura nunca é exercitado e
diverge da documentação — confunde quem lê a função isolada.

**Correção proposta:** alinhar o default da assinatura a 5000 (fonte única do default no
`pipeline`/CLI) ou remover o default e exigir o parâmetro. Verificar se algum teste depende de 8000.
**Aceite:** default coerente com o caminho real e com o SPEC; `pytest` verde.
**Commit:** e4b23bb

## ENG-15
**`sync-results` depende de fonte única (martj42) sem fallback** · P2 · `fetch_data.py` · ✅ feito

`fetch_data.DEFAULT_URL` aponta exclusivamente para o CSV do repositório `martj42/international_results`.
Na Copa 2026, a latência típica da fonte é de 1-2 dias — os placares de J5–J8 (2026-06-13) não
estavam disponíveis no dia seguinte, forçando busca manual na web e registro via `worldcup record`.
Conforme a Copa avança (vários jogos por dia), o risco de ficarem defasados é alto e o custo manual
cresce.

**Correção proposta:** suportar lista ordenada de fontes em `fetch_data.fetch()`. Candidatos:
- Fonte primária: martj42 (já existente, histórico completo).
- Fonte secundária: CSV público de resultado da Copa atual (ex.: API-football, football-data.org,
  ou outro dataset que atualize no mesmo dia). Alternativamente, expor `--source-url` na CLI para
  que o operador passe uma URL alternativa sem mudar o código.
A lógica: tentar a primária; se falhar ou se os jogos esperados não aparecerem, tentar a próxima.
**Aceite:** `fetch-data` (ou `sync-results`) obtém os placares do dia corrente sem intervenção
manual quando martj42 estiver atrasada; teste de unidade cobre o fallback (mock de URLs).
`pytest` verde.
**Resolução:** `download_from_urls(urls)` em `fetch_data.py` tenta cada URL em cascata
(`NetworkError`/`DataSourceError` dispara o próximo); `fetch()` e `sync_results()` aceitam
a lista; CLI expõe `--source-url` (appendável) em `fetch-data` e `sync-results`. 3 testes novos.
**Commit:** 7e2f360

## ENG-14
**Curva de pontos base não reproduz o app (50%→3, não 2)** · P2 · `scoring.py` · ✅ feito

A tela do "Simulador de Pontos" do app mostra **50% de chance → 3 pts** (base, sem bônus). A fórmula
do projeto, `_base_points`, no risco "fiel" 0.5 usa `base = (1/p)^(2·risk) = 1/p`, que em p=0,5 dá
**2 pts**. Os extremos batem (p→1 → 1 pt = `base_min`; zebra → 13 = `base_max`), mas o **meio da
curva** não. Implicação: a curva real do app é mais íngreme que `1/p` (γ "fiel" implícito ≈ log2(3)
≈ 1,585 → equivaleria a `risk ≈ 0,8`), ou seja **o projeto sub-recompensa zebra** vs. o app — afeta
`best_prediction` e a estratégia de risco.

**Correção proposta:** coletar 3–4 pontos `(probabilidade, pontos)` do Simulador do app (ex.: 50/40/
30/20/10%), ajustar a forma de `_base_points` (expoente/curva) para reproduzi-los, e **desacoplar**
a curva-base-do-app do knob `risk` (hoje os dois são o mesmo γ — conceitualmente distintos: a curva
é fixa do app, `risk` é estratégia do palpiteiro). Revisar a calibração de "risk=0.5 = fiel".
**Aceite:** `_base_points` reproduz os pontos observados do app dentro de ±0,5 pt nos pontos
coletados; teste com os pares observados. `pytest` verde. **Bloqueado por:** coleta dos dados do
Simulador (depende do usuário).
**Resolução (43f2be2):** dados do Simulador coletados (80%→2, 50%→3, 15%→7, 5%→11). Curva trocada
para log-linear `base = 1 + 7.55·log10(1/p)` (reproduz os 4 pontos ±0.5) e `risk` **desacoplado** da
régua → migrou para um tilt na escolha (`best_prediction`), preservando "0.5 = E-max puro". Backtest
2022 recalculado. **Refinar depois:** com mais pontos do Simulador (ex.: 40/30%) dá para apertar o
coeficiente; o teto de 13 e o arredondamento são hipóteses a confirmar.
**Commit:** 43f2be2

## ENG-16
**Fit do Dixon-Coles não converge em `maxiter=500` com a base atual** · P2 · `model.py` · ✅ feito

Desde que os resultados da Copa 2026 passaram a realimentar o ajuste (jogos registrados recebem
peso alto), `model.DixonColesModel.fit` emite o aviso de não-convergência do ENG-3 em todo run de
`sync-results`/`predict`: `ajuste do modelo não convergiu (maxiter=500): STOP: TOTAL NO. OF F,G
EVALUATIONS EXCEEDS LIMIT`. O guardrail do ENG-3 está funcionando (o aviso aparece e a saída segue
usável), mas a **causa** não foi tratada: o otimizador esgota o orçamento de avaliações antes de
convergir. Com a base crescendo (mais seleções/parâmetros + pesos altos nos jogos recentes), o
`res.x` retornado pode estar longe do ótimo — previsões potencialmente piores sem sinal além do
aviso. Observado em 2026-06-15 (12 jogos registrados).

**Correção proposta:** investigar a não-convergência — (a) subir `maxiter`/`maxfun` do `minimize`
e medir se converge e quanto custa em tempo; (b) avaliar escala/normalização dos parâmetros ou um
chute inicial melhor (warm start) para acelerar; (c) checar se o peso alto dos jogos da Copa
desequilibra a verossimilhança. Decidir um teto de iterações que convirja na base típica de uma
Copa em andamento sem regredir o tempo de run de forma relevante.
**Aceite:** em um run representativo com ~12+ jogos da edição 2026 registrados, `fit` converge
(`res.success`/sem aviso) dentro de um tempo aceitável; teste/medição registrando o antes/depois
(iterações até convergir ou ausência do warning). `pytest` verde.
**Diagnóstico:** o limite que mordia era o `maxfun` default do scipy (15000), **não** o `maxiter`.
Sem `jac`, o gradiente saía por diferenças finitas (~2n+1 = ~448 avaliações por gradiente nos 447
params), esgotando o maxfun em **27 iterações**. Subir `maxiter` sozinho não muda nada. Medições na
base real (19.677 jogos): atual = não-converge, 17s, nfev≈15.2k; força bruta (`maxfun=500k`) =
converge mas **233s**; **jac analítico = converge em 1.7s**, mesmo ótimo (neg_ll 3306.37 vs 3306.39).
Impacto comprovado nos palpites: Δxg de até **0,36 gol** entre o fit não-convergido e o convergido
(ex.: Brasil×Croácia 1.88→1.53), `max|Δataque|`≈1,5 — não era cosmético.
**Resolução (0934fcc):** gradiente analítico da log-verossimilhança (Poisson + correção
Dixon-Coles `tau` + ridge, com máscara na região do `clip`) passado via `jac=grad` ao `minimize`.
Teste de regressão valida o jac contra diferenças centrais nos 4 ramos de placar baixo do `tau`; o
fixture sintético ganhou sinal de mando real (era simétrico → `home_adv` convergido ~0, deixava os
testes de mando no fio da navalha — falso-passe por não-convergência).
**Validação (backtest, mesmo código alternando só o gradiente, determinístico):** o fit convergido
melhora os pontos do bolão (Sistema I, risk 0.5, 64 jogos/Copa) em **todas** as 4 Copas, nunca pior —
2010 +2 (303→305), 2014 +14 (205→219), 2018 +14 (257→271), **2022 +37 (170→207)**. A `% resultado`
(acerto de vencedor/empate) fica **estável em 56%** com o fit convergido, vs. 42–56% oscilando com o
não-convergido (a não-convergência parava a distâncias variáveis do ótimo — ruído, pior caso 2022:
42%→56%). O `% placar exato` quase não muda — o ganho vem de acertar o lado certo.
**Commit:** 0934fcc

## ENG-17
**Defaults do `FitConfig` (meia-vida/ridge) subótimos no backtest** · P2 · `model.py` · ✅ feito

Os defaults `halflife_years=2.5` e `ridge=0.05` (`model.FitConfig`) ficam perto do **pior** ponto
de uma varredura de hiperparâmetros no backtest das 4 Copas (2010/14/18/22, 256 jogos). Quase toda
config da grade bate o atual. Surgiu da análise dos 12 jogos da Copa 2026: o motivo do baixo acerto
não é a régua de empate (`best_prediction` é E-max ótimo; nunca palpitar empate é correto sob o
sistema de pontos), e sim a calibração das forças.

**Correção proposta:** retunar os defaults para `halflife_years=2.0`, `ridge=0.10` (mais shrinkage
regulariza forças com poucos dados; meia-vida menor pesa um pouco mais a forma recente). Atualizar
`docs/SPEC.md` (cita "meia-vida padrão 2,5 anos"). Refino futuro: grade mais fina + incluir pesos
de torneio/`max_xg`.
**Aceite:** validação **leave-one-World-Cup-out** (escolhe a config nas outras 3 Copas, avalia na de
fora) com ganho positivo — não pode ser overfit in-sample. Teste documenta os defaults escolhidos.
**Evidência (LOO-CV):** a config `hl=2.0, rg=0.10` vence em **todas as 4 dobras** (não é overfit:
generaliza para a Copa de fora) — 2010 +20, 2014 +40, 2018 +25, 2022 +7; total **+92 pts em 256
jogos (+9,2%)** vs. os defaults atuais. Combina com o ganho do [ENG-16] (mesmo motor).
**Resolução (57bb420):** `FitConfig.halflife_years` 2.5→2.0 e `ridge` 0.05→0.10; SPEC.md atualizado
(meia-vida 2,0) e teste `test_fitconfig_calibrated_defaults` trava a calibração (mudança deve
re-rodar o LOO-CV).
**Refino (grade fina + pesos de torneio):** varredura 3D `halflife×ridge×tournament_gamma`
(gamma = expoente de nitidez `peso^gamma` aplicado só à verossimilhança, não ao `is_major`),
hl∈{1.5,2.0,2.5,3.0} × rg∈{0.08,0.10,0.15} × gamma∈{0.5,1.0,1.5,2.0,2.5}, validada LOO-CV.
**Resultado negativo:** `hl=2.0, rg=0.10, gamma=1.0` é o melhor in-sample **e nas 4 dobras** —
gamma=1.0 (identidade) ótimo, afiar/achatar pesos de torneio não ganha nada; os `_TOURNAMENT_WEIGHTS`
já estão bem calibrados. Ótimo é interior na grade (não é borda). O hook `tournament_gamma` foi
prototipado e **revertido** (config morta — ENG-11). Os defaults do 57bb420 ficam confirmados.
**Commit:** 57bb420

## ENG-18
**Backtest mede só acerto de 1×2, não calibração probabilística** · P2 · `backtest.py` · ✅ feito

`backtest.run_backtest` reporta `result_pct` (acertou vencedor/empate) e `exact_pct` (cravou o
placar), mas **não mede se as probabilidades P(mandante)/P(empate)/P(visitante) são calibradas** —
i.e., se em jogos a que o modelo deu ~30% de empate, ~30% de fato empatam. Acerto de 1×2 é uma
métrica de classificação (depende do argmax); calibração é uma métrica de probabilidade
(depende da massa). São independentes: o modelo pode acertar 56% dos resultados com P(empate)
sistematicamente baixa, e isso enviesaria a régua de pontos base (que escala com `1/p`), as
sims de campeão/avanço e a própria decisão de quando vale arriscar.

Surgiu da análise dos 16 primeiros jogos da Copa 2026: 8/16 empates reais (50%) vs. P(empate)
média de 25,8% que o modelo atribuiu, e 0/16 empates palpitados. Em 16 jogos isso é variância
(~2σ; o backtest de 256 jogos fixa o acerto de 1×2 em ~56%), **não** evidência de defeito —
mas é exatamente a pergunta que um diagnóstico de calibração responde com base estatística, em
vez de reagir a uma amostra pequena. Decide, com evidência, se há algo a corrigir (ex.: limite do
`rho` da correção Dixon-Coles, hoje `model.rho`≈−0,078, ou termo específico de empate) ou se a
calibração já está boa e os 38% de 2026 são só azar.

**Correção proposta:** estender `backtest.run_backtest`/`BacktestResult` para computar, sobre os
jogos de teste (agregável nas 4 Copas via `_WORLD_CUP_START`), a partir do `outcome_probs_from_matrix`
de cada confronto:
- **Brier score multiclasse** sobre o vetor (P_mandante, P_empate, P_visitante) vs. o resultado
  one-hot — métrica única de calibração+resolução;
- **curva de confiabilidade** por faixa de probabilidade prevista (bins, ex.: 0–10%,…,90–100%):
  frequência observada vs. prevista, **por classe de resultado** (com foco no empate, a suspeita).
Reportar no `_print_report`. Independe de `risk` (é do modelo, não da estratégia de escolha).

**Aceite:** (1) teste de regressão valida o Brier num caso sintético de probabilidade conhecida
(ex.: previsão determinística certa → 0; uniforme → valor fechado) e a atribuição de bins da
reliability; (2) rodar o diagnóstico nas 4 Copas e **registrar aqui** o veredito — P(empate) é
calibrada ou não? — fechando a dúvida levantada na Copa 2026. Se miscalibrada, abrir item-filho
para o ajuste do modelo (não fazê-lo neste item — aqui é só medição).
**Evidência (veredito, 256 jogos · 2010/14/18/22 · `pooled_draw_calibration`):** Brier multiclasse
**0,578** (< 0,667 uniforme → o modelo tem resolução). Confiabilidade do empate, faixas povoadas:
20–30% (144 jogos) previsto 26,4% vs observado 20,8%; 30–40% (92 jogos) previsto 32,5% vs observado
26,1%. Global: P(empate) prevista média **27,9%** vs. frequência real **22,3%**. **Veredito: o
modelo NÃO subestima empates — se algo, os superestima levemente** (a correção Dixon-Coles `rho`,
hoje ≈−0,078, já puxa a massa para cima). Logo o 0/8 em empates no início da Copa 2026 (P(empate)
média de 25,8% naqueles 16 jogos vs 50% observado) é **variância**, não miscalibração. **Não há
ajuste de modelo a fazer; nenhum item-filho aberto.** O diagnóstico fica como métrica permanente do
backtest para reabrir a questão com base estatística, não com punhado de jogos.
**Resolução (8652360):** `multiclass_brier` + `reliability_curve` (puras, testadas),
`pooled_draw_calibration` agrega as 4 Copas; `BacktestResult` ganha `brier`/`reliability_draw` e o
`_print_report` os exibe. Testes de regressão cobrem caso determinístico (0), uniforme (2/3), pior
caso (2), atribuição de bins e o limite `p=1.0`. SPEC §9.1 registra a métrica e o veredito.
**Commit:** 8652360

## ENG-19
**Blendar probabilidades do Dixon-Coles com odds de mercado (des-vigadas)** · P2 · `model`/`scoring` · ✅ feito

O modelo é puramente estatístico: ajusta forças a partir de resultados passados e é **cego a
escalações, lesões, suspensões, motivação e dinheiro**. As **odds de fechamento** de uma casa
sharp (ex.: Pinnacle) são o melhor preditor público *calibrado* de resultado justamente porque
incorporam essa informação. Diagnóstico que motivou o item (2026-06-17, 20 jogos): a eficiência do
palpiteiro já é **100% do tool** (seguir o `best_prediction` rende exatamente os mesmos 44 pts que o
usuário fez) — ou seja, **não há ganho a extrair jogando diferente sobre este modelo**; o teto de
acurácia é o do próprio modelo. Para subir o teto, a alavanca de maior valor é uma **fonte de
probabilidade externa** blendada, não um refino interno (ver ENG-17: afiar pesos de torneio não
ganhou nada; o `rho` da correção Dixon-Coles já calibra empate — ENG-18). **Não é** sobre "prever
mais empates" (o modelo já os superestima levemente no agregado — ENG-18); é sobre probabilidades
melhores em todos os resultados.

**Refs:** `scoring.outcome_probs_from_matrix` (saída P(mandante/empate/visitante) do modelo, hoje
única fonte), `pipeline.run`/`MatrixCache.matrix` (onde a matriz de placares é consumida),
`backtest.multiclass_brier`/`pooled_draw_calibration` (a régua de validação do ENG-18, baseline
DC-only = **Brier 0,578**).

**Correção proposta:** introduzir uma fonte de odds e um *blend* de probabilidades, mantendo o
código agnóstico à edição (odds entram como **dados** por jogo, não hardcode):
- des-vigar as odds (remover a margem da casa → probabilidades implícitas normalizadas);
- combinar com as do modelo via *logarithmic opinion pool* (média geométrica ponderada renormalizada)
  ou média linear; peso `w∈[0,1]` entre modelo e mercado como único hiperparâmetro;
- o blend produz a tripla (mandante/empate/visitante); decidir se ele **reescala a matriz de
  placares** (preserva o `best_prediction`/bônus de placar exato) ou só substitui o 1×2. Preferir
  reescalar a matriz para não quebrar a camada de scoring.
- onde armazenar as odds por jogo no modelo de dados da edição (ex.: coluna opcional em
  `fixtures.csv` ou arquivo `odds.csv` paralelo); ausência de odds ⇒ cai para DC-only (degradação
  graciosa, sem travar a Copa).

**Aceite (revisado 2026-06-17 — o LOO-CV multi-Copa original era inviável por falta de dados, ver Decisão):**
três gates; teste de regressão sempre verde.
- *Gate 1 — mecanismo + testes unitários:* devig/pool/rescale/blend + carga de `odds.csv`, com
  `w=0`⇒modelo e `w=1`⇒mercado. **✅ (a26cfa8).**
- *Gate 2 — default de `w` por prior de princípio:* `blend_weight` default documentado (~0,6,
  ancorado na calibração quase-ótima de odds de fechamento na literatura), **não** tunado em dados
  de seleção (que não existem grátis). Teste trava o default.
- *Gate 3 — validação prospectiva 2026:* harness que, com odds em `odds.csv` por rodada, compara o
  **Brier multiclasse** do blend(`w`) vs. modelo-puro (as-of) nos jogos disputados, acumulando um
  tally; `w` **pré-registrado** ⇒ out-of-sample por construção. Veredito registrado no `BOLAO.md`
  conforme acumula; re-tunar `w` se 2026 discordar forte.

**Decisão (2026-06-17 — fonte de dados):** pesquisa de fontes confirmou que **odds 1X2 de jogos de
seleção das Copas 2010–2018, grátis e legais, não existem** (só scraping de OddsPortal/checkbestodds
contra o ToS; The Odds API cobre só 2022, pago ~$29–99/mês; football-data.co.uk é só ligas de
clube). Logo o **LOO-CV histórico multi-Copa foi descartado**. Alternativas avaliadas e preteridas:
(a) tunar em ligas de clube e transferir — esforço alto (ingestão + desligar o filtro FIFA) + gap
clube→seleção; (b) comprar odds da Copa 2022 — 1 torneio, sem fold para tunar, custa. **Escolhido**
(decisão do usuário): **prior de princípio + tracking prospectivo** — mais barato e a evidência
in-domain (jogos de seleção reais) acumula sozinha ao longo da própria Copa 2026.
**Progresso (a26cfa8):** **mecanismo implementado e testado**, item segue 🟡 só pela validação
empírica. Novo `blend.py` puro: `devig` (des-vig proporcional) → `log_opinion_pool` (média
geométrica ponderada, peso `w`) → `rescale_matrix` (reescala a matriz ao 1×2-alvo preservando a
forma condicional e a massa total — `best_prediction`/bônus intactos). Decisões tomadas: odds em
`odds.csv` paralelo (`match_id,home,draw,away`, decimais; **não** em `fixtures.csv` para não
poluir o arquivo canônico/hook de sync), opção **reescalar a matriz** (não só o 1×2), `w` via
`scoring.toml::blend_weight` + override `--blend-weight` (espelha o padrão do `risk`). `pipeline.run`
aplica só nos jogos com odds; sim de campeão/avanço segue DC-only. Ausência de odds ou `w=0` ⇒
intacto. 13 testes (devig margem/erro, pool `w=0/1/0.5`, rescale alvo/massa/forma, blend e2e
`w=0/1/parcial`, carga de `odds.csv` + ausência graciosa); e2e manual confirmou o shift dos palpites
(J21 50→55% mandante; J24 14→32% após odds equilibradas).
**Resolução (7124554) — Gates 2–3:** *Gate 2:* `blend_weight = 0.6` no `scoring.toml` da 2026
(prior de princípio), travado por `test_2026_blend_weight_prior`. *Gate 3:*
`backtest.prospective_blend_report(edition, w)` + CLI `worldcup blend-track` — para cada jogo de
grupo já disputado com odds, reajusta o modelo **as-of** e compara o Brier multiclasse do
modelo-puro vs. do blend(`w`); `w` pré-registrado ⇒ out-of-sample. Degradação graciosa (n=0 sem
`odds.csv`). Testes: empty path (roda em CI) + invariante `w=0 ⇒ Brier(blend)==Brier(modelo)` (skipif
sem `historical_results.csv`, roda local). Docs: README (`blend-track` + prior), SPEC §3.5
(validação prospectiva substitui o LOO-CV), BOLAO (alavanca armada, dorme até `odds.csv`).
**Operacional, não bloqueia o ✅:** o veredito empírico só acumula quando houver `odds.csv` + jogos
disputados (hoje n=0); registrar no BOLAO conforme rodar `blend-track`. Re-tunar `w` se 2026
discordar forte do prior.
**Commit:** 7124554

## ENG-20
**Pipeline `predict` não roda no CI; `sync`/`pipeline` com cobertura baixa (34%/43%)** · P2 · `tests`/`ci` · ✅ feito

A cobertura agregada (77%) esconde que os módulos de **orquestração e correção** mais arriscados são
os menos testados: `sync.py` **34%**, `pipeline.py` **43%** — contra `model` 96%, `scoring` 93%,
`blend` 98%. Pior: o único teste que exercita o caminho real `fit→monte_carlo→deterministic_bracket→
predict` é `skipif`-guardado por `historical_results.csv` (gerado, gitignored, **ausente no CI**), então
o **CI nunca roda o pipeline de ponta a ponta**. Uma regressão na fiação de `pipeline.run` ou na
resolução de bracket de `sync` passaria **verde** no CI — e foi justamente `sync` o [ENG-1] (placar
trocado, sem teste à época). É o ponto cego que separa o projeto de uma nota mais alta.

**Refs:** `pipeline.run`, `sync.sync_results`/`sync._edition_results`, `format_engine.deterministic_bracket`,
e os `skipif` de `historical` em `tests/test_backtest.py`/`tests/test_blend.py`.
**Correção proposta:** versionar um **fixture histórico mínimo/sintético** (subconjunto pequeno ou
gerado) em `tests/fixtures/`, suficiente para ajustar o modelo de uma edição reduzida. Com ele:
(a) **teste e2e de fumaça** que roda `pipeline.run` numa edição-fixture e afirma invariantes (nº de
linhas = nº de jogos; P(mandante)+P(empate)+P(visitante)=100; todo jogo previsto tem placar; o KO
resolve `avanca`); (b) testes de integração direcionados de `sync` (resolução de bracket por resultados
reais, incluindo o caso do [ENG-1]) e de `pipeline` (realimentação; blend só onde há odds). Remover o
`skipif` desses caminhos para rodarem no CI.
**Aceite:** `sync` e `pipeline` ≥ ~75% de cobertura; o caminho e2e do `predict` roda no CI (sem
`skipif`); CI verde em Python 3.11 e 3.13.
**Resolução (3372d97):** `conftest.mini_historical` gera um histórico **sintético** (round-robin
ida/volta entre 14 seleções reais da 2026, competitivo p/ passar o filtro do fit) — destrava o
caminho real sem o `historical_results.csv` (gitignored). Testes novos: **e2e** `test_pipeline_run_e2e_invariants`
(injeta o fixture, roda `pipeline.run` pré-torneio, afirma 104 linhas, P(1×2) somam 100, todo grupo
tem placar, KO resolve `avanca`, título normaliza); **integração de sync** — `_resolve_real_bracket`
resolve a R32 com seleções reais, `sync_results` preenche jogos num **clone temp** da edição (sem
tocar no real), `_edition_results` guarda reencontro como lista e filtra não-Copa + lê pênaltis.
Removidos todos os `skipif` de `historical` (o blend e2e do ENG-19 agora roda no CI). **Cobertura:
`pipeline` 43%→90%, `sync` 34%→90%, total 86%**; piso `fail_under` 65→80 (trava o ganho — fecha o
gancho deixado no ENG-8). Decisão: fixture **gerado em código** (não CSV versionado) — sem arquivo
binário a envelhecer.
**Commit:** 3372d97

## ENG-21
**Podar/consolidar a camada meta pós-ENG-19 (extensão recorrente do ENG-11)** · P3 · processo · ✅ feito

O [ENG-11] é o item recorrente de proporcionalidade doc/código ("reabrir a cada salto de doc"). O
trabalho do [ENG-19] nesta sessão foi um salto: blend + odds + tracking adicionaram material em
`README`/`AGENTS`/`SPEC §3.5`/`BOLAO`, um script novo (`scripts/fetch_odds.py`) e várias entradas de
`BOLAO`. A camada meta (~1.210 linhas md + backlog + skills + hooks) está em ~44% das ~2.772 LOC de
`src` — para um mantenedor único, o andaime arrisca custar mais que a casa. Não é bug; é dívida de
proporcionalidade a revisar.

**Refs:** `README.md`, `AGENTS.md`, `docs/SPEC.md`, `data/editions/2026/BOLAO.md`, `.claude/skills/`.
**Correção proposta:** revisar a sobreposição introduzida pelo ENG-19 — a explicação do blend aparece
em README, AGENTS, SPEC §3.5 **e** BOLAO; confirmar que cada uma serve audiência distinta e declarar um
canônico (como o ENG-11 fez para "limitações → SPEC §9.2"); consolidar o que duplicou; podar entradas
obsoletas do BOLAO (a memória higieniza-se por revisão). Preferir **consolidar a adicionar**.
**Aceite:** revisão de sobreposição registrada (canônico por assunto declarado para o material de
blend/odds); nenhuma seção duplicada sem canônico; `BOLAO` sem entradas obsoletas. (Vigilância
recorrente — fechar quando a revisão for feita; reabrir a cada novo salto, como o ENG-11.)
**Resolução (7540ab7):** **Canônicos do material de blend/odds declarados por audiência** (estende o
esquema do [ENG-11]): *uso/como-fazer* (formato do `odds.csv`, `fetch_odds.py`, `blend-track`,
`blend_weight`) → **README**; *arquitetura/dados/convenções* (módulo `blend.py`, data-model do
`odds.csv`, "acrescentar não sobrescrever", não versionar odds falsas, chave no `.env`) → **AGENTS**;
*metodologia/matemática* (des-vig → pool log → reescala) → **SPEC §3.5**; *registro de engenharia* →
**ENG-19**; *estado de campanha* (config ativa, veredito do tracking) → **BOLAO** (só estado, sem
how-to). As três aparições do "porquê o blend ajuda" (README/SPEC/ENG-19) são **audiências
distintas**, não duplicação — cada uma é canônica no seu doc. **Poda do `BOLAO` (112→79 linhas):**
"Estado atual" deixou de ser log de resultados (deriváveis do `fixtures.csv`) e virou snapshot; o
how-to do blend saiu (aponta p/ README); a decisão de risco foi condensada (modelagem completa só no
Histórico, sem duplicar); menções a martj42 unificadas; a lição dos empates foi para o Histórico
(lugar canônico). Nenhuma decisão/fato não-derivável perdido. **Vigilância recorrente: reabrir ao
próximo salto de doc/skill.**
**Commit:** 7540ab7

## ENG-22
**Monitor de regime de empates na edição viva (tilt só se estatisticamente significativo)** · P3 · `backtest` · ✅ feito

Dados da Copa 2026 até J28 (medido com o modelo as-of): **10 de 28 jogos de grupo foram empates
(36%)** contra ~26% que o modelo espera (~1,2σ binomial — variância, não sinal, coerente com o
veredito do [ENG-18] de que o modelo é **bem calibrado** em empates sobre 256 jogos, até os
superestima). Sob E-max + Sistema I o `best_prediction` **nunca palpita empate** (palpitou 0 em 28),
então **todo empate real zera** — **10 dos 13 zeros são empates**; é a fraqueza dominante (em jogo
decidido o tool acerta 80%/100% o lado). Risco dos dois lados: **agir agora** (forçar empates) é
overfit à variância e baixa os pontos esperados; **não ter detector** deixaria passar um regime real
de empates se ele existir. Falta um monitor que separe os dois com base estatística, não com punhado
de jogos — exatamente o espírito do ENG-18, mas na **edição viva**.

**Refs:** `backtest.prospective_blend_report` (irmão: diagnóstico as-of na edição viva),
`backtest.multiclass_brier`/`reliability_curve`, `scoring.outcome_probs_from_matrix`; veredito do
[ENG-18] (modelo calibrado em empate; `model.rho`≈−0,078 já puxa massa pra empate).
**Correção proposta:** função (vizinha de `prospective_blend_report`) que, sobre os jogos de grupo já
disputados, compara a **frequência observada de empates** com a **soma das P(empate) do modelo
as-of** e devolve o desvio padronizado (z-score binomial / p-valor). Expor via CLI (ou no
`blend-track`). **Gatilho de ação:** só quando o desvio for **≥2σ sustentado** é que um *tilt* de
empate passa a ser justificado por dados — e aí abre-se um **item-filho** para a correção do modelo
(ex.: termo específico de empate ou ajuste do `rho` para a edição). Até lá: **reportar e não agir**.
**Aceite:** função + teste em caso sintético (probabilidades/resultados conhecidos → z fechado);
roda sobre os jogos da 2026 e reporta observado/esperado/z; documenta o gatilho de 2σ e a postura
"não agir sobre variância". A correção em si **não** entra aqui (medição-só, como o ENG-18) — vira
item-filho se e quando o gatilho disparar.
**Resolução (f1c0da6):** `backtest.draw_regime_report(edition)` → `DrawRegime(n, observed, expected, z)`
com `.significant` (|z|≥2σ). A estatística pura `draw_regime_stats(p_draws, is_draw)` calcula o
z-score **Poisson-binomial** `(observado − Σp)/sqrt(Σ p(1−p))` (cada jogo é um Bernoulli com seu
P(empate)). Surge no CLI `blend-track` (sobre **todos** os jogos de grupo disputados, não só os com
odds), com veredito "variância (não agir)" vs "⚠️ SINAL ≥2σ — abrir item-filho de tilt". O loop as-of
foi extraído para `_as_of_group_matrices` (helper compartilhado com `prospective_blend_report` — dedup,
no espírito do ENG-21). 4 testes (z conhecido = 1,549; gatilho >2σ; vazio; report na 2026 com
`observed` = empates reais). **Veredito ao vivo (28 jogos): 10 obs vs 7,3 esp, z=+1,19 → variância,
não agir** — confirma o ENG-18. O item-filho de correção só abre se o z cruzar 2σ até o fim dos grupos.
**Commit:** f1c0da6

## ENG-23
**Bônus de placar somados em vez de hierárquicos (inflam pontos, enviesam contra empate)** · P1 · `scoring` · ✅ feito

`scoring.points` somava os bônus de placar do Sistema I — no placar exato dava `base + exato(5) +
saldo(2) + gols_vencedor(3) + gols_perdedor(1)` = base+11 — mas o app concede **só o maior nível
atingido** (hierárquico): **exato +5 > gols do vencedor +3 > saldo +2 > gols do perdedor +1**; a
goleada (+1) é um extra que empilha. Descoberto ao confrontar as telas "Pontos por Jogo" do app
(rodadas J43–J60, 23–25/06): Curaçao 0×2 cravado pontuou **7** (= base 2 + exato 5), não os 13 que o
código dava; Paraguai 0×0 cravado = **9** (base 4 + 5). Prova de que não era cumulativo: 7 é
impossível somando (base mínima 1 + 11 = 12). Dois efeitos graves: (1) **toda eficiência calculada
ficou inflada** (teto superestimado); (2) **`best_prediction` enviesado contra empates** — jogo
decidido acumulava mais bônus que empate, então o E-max quase nunca escolhia empate (ligado ao
sintoma do [ENG-18]/[ENG-22], "0 empates palpitados").

**Refs:** `scoring.Scorer.points` (a régua), `scoring.Scorer.best_prediction`/`expected_points`
(consumidores; mudam de comportamento), `docs/SPEC.md` §4 (tabela + pseudocódigo + exemplos).
**Correção:** os quatro níveis de placar viram uma **hierarquia** (`if/elif` pelo maior atingido),
não somas; os três níveis "decididos" são mutuamente exclusivos com o exato (acertar dois ⇒ exato),
o que torna a hierarquia natural. Goleada (+1) mantida como extra que empilha (sem exemplo no app —
marcado no teste). **Validação:** confronto dos 12 jogos J43–J54 com o app — **8 cravam exato, 4
erram por ≤1 só na base** (probabilidade nossa ≠ a do app; resíduo separado, não o bug). Casos de
ouro travados em `tests/test_scoring.py` (`test_app_golden_points_per_game`,
`test_exact_score_is_base_plus_five_only`, `test_placar_bonus_levels_are_exclusive`). Docs de "bônus
cumulativos" → "hierárquicos" em SPEC/GLOSSARIO/PRD/AGENTS/scoring.toml. Edição repalpitada: o modelo
**volta a palpitar empates** (J61/J62 de 26/06 saem 0×0). **Pendência (não-bloqueante):** base ~1pt
baixa em ~1/3 dos jogos por divergência de probabilidade modelo×app — vira item-filho se incomodar.
**Commit:** 5017468

## ENG-24
**Base (1–13) usa a probabilidade interna do app (inobservável) ⇒ eficiência só aproximada** · P2 · `scoring` · 🔴 todo

O Sistema I tem **duas partes**: o **bônus de placar** (exato/vencedor/saldo/perdedor — hierárquico,
[ENG-23]) é **determinístico** e reconstrutível com exatidão; a **base variável "Acertar o vencedor ou
empate" (1–13)** é função da **probabilidade que o app calcula internamente** para o resultado. Essa
probabilidade **difere da nossa** (modelo Dixon-Coles + blend) e **não é exposta** pelo app. Logo, mesmo
com a curva de base perfeita, alimentamos a *nossa* `p` e a base sai com **±~1 ponto por jogo** sempre
que nosso bucket cruza a fronteira de arredondamento do app. **Evidência:** o Simulador de Pontos do app
(telas de 26/06/2026) dá `0.80→2, 0.45→3, 0.15→7, 0.10→9, 0.05→11`; nossa fórmula erra em `0.45` (dá 4),
e **nenhuma** curva log+arredondamento passa por `0.45→3` e `0.10→9` ao mesmo tempo. Na validação do
[ENG-23] (12 jogos vs app), os 4 desvios foram **todos ±1 só na base** — exatamente este efeito, não bug.

**Impacto:** `scripts/efficiency.py` (teto/eficiência) é **aproximado** (±~1/jogo), nunca exato — não
ler o `%` como cravado. Já houve auto-engano por causa disso (BOLAO 24–26/06: "eficiência 86,7%" e "você
vazou pts" eram artefato do scorer somado — corrigido em ENG-23; o resíduo da base é este item).
**Mitigação aplicada (não resolve):** documentado em `docs/SPEC.md` §4 (tabela + nota de
observabilidade) e na docstring de `scripts/efficiency.py`; o script agora **imprime o caveat** de que
teto/eficiência são estimativas ±~1/jogo.
**Refs:** `scoring.Scorer._base_points`, `scripts/efficiency.py` (`asof_scores`/`archive_scores`),
`docs/SPEC.md` §4.1.
**Resolução possível (aberta):** (a) capturar as **probabilidades exibidas pelo app** por jogo (entrada
manual num CSV opcional, à la `odds.csv`) e usá-las na base do `efficiency.py` → base exata onde houver;
(b) ou aceitar o limite e sempre **reportar faixa** em vez de ponto. **Aceite:** quando (a) existir,
a eficiência dos jogos com probabilidade do app registrada bate o app dentro de ±0 na base; até lá, o
item fica como **limitação conhecida documentada** (não há fix puramente algorítmico — é dado que falta).
