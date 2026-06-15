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
| [ENG-12](#eng-12) | P2 | scoring | 🟡 | Bônus de prorrogação/pênaltis definidos mas não computados |
| [ENG-13](#eng-13) | P3 | format_engine | ✅ | Default morto `n_sims=8000` em `monte_carlo()` |
| [ENG-14](#eng-14) | P2 | scoring | ✅ | Curva de pontos base não reproduz o app (50%→3, não 2) |
| [ENG-15](#eng-15) | P2 | fetch_data | ✅ | `sync-results` depende de fonte única (martj42) sem fallback |
| [ENG-16](#eng-16) | P2 | model | ✅ | Fit do Dixon-Coles não converge em `maxiter=500` com a base atual |

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
**Bônus de prorrogação/pênaltis definidos mas não computados** · P2 · `scoring.py` · 🟡 fazendo

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
**Commit:** —

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
