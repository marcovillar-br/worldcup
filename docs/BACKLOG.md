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
| [ENG-6](#eng-6) | P3 | cli | 🔴 | Separar camada de render (`render.py`) |
| [ENG-7](#eng-7) | P3 | tipos | ✅ | mypy não cobre `tests/` |
| [ENG-8](#eng-8) | P3 | ci | 🔴 | Sem medição de cobertura |
| [ENG-9](#eng-9) | P3 | tests | ✅ | Guardrail: toda seleção da edição tem tradução PT |
| [ENG-10](#eng-10) | P3 | release | 🔴 | Versão estática, sem CHANGELOG/tags |
| [ENG-11](#eng-11) | P3 | processo | 🔴 | Vigiar proporcionalidade doc/código; consolidar docs |

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
**Separar camada de render (`render.py`)** · P3 · `cli` · 🔴 todo

`cli.py` tem ~500 LOC e mistura argparse, handlers, escrita CSV e ~200 linhas de
`render_markdown`/`render_html`. Coesão/teste isolado da apresentação.

**Correção proposta:** extrair render (MD/HTML/CSV) para `render.py`; `cli.py` só orquestra.
**Aceite:** sem mudança de comportamento; render testável sem a CLI; `ruff`/`mypy`/`pytest` verdes.
**Commit:** —

## ENG-7
**mypy não cobre `tests/`** · P3 · tipos · ✅ feito

`pyproject` tem `files = ["src"]`; os testes não são type-checked.

**Correção proposta:** incluir `tests` no mypy (ou config separada), corrigindo o que aparecer.
**Aceite:** `uv run mypy` passa cobrindo `tests/`.
**Commit:** 4686edf

## ENG-8
**Sem medição de cobertura** · P3 · ci · 🔴 todo

Os testes rodam, mas nada mede o que ficou de fora (ex.: o caso do ENG-1 não tinha teste).

**Correção proposta:** `pytest-cov` + relatório no CI (e, opcional, um piso de cobertura).
**Aceite:** CI reporta cobertura; decisão registrada sobre piso (ou ausência).
**Commit:** —

## ENG-9
**Guardrail: toda seleção da edição tem tradução PT** · P3 · tests · ✅ feito

Seleção sem entrada em `teams._PT_DISPLAY` cai no inglês **silenciosamente**.

**Correção proposta:** teste que afirma que todo time em `groups.csv` de cada edição tem `display`
diferente do canônico (ou entrada explícita no mapa).
**Aceite:** teste cobre a edição 2026; falha se faltar tradução. `pytest` verde.
**Commit:** 593568f

## ENG-10
**Versão estática, sem CHANGELOG/tags** · P3 · release · 🔴 todo

`version = "0.1.0"` fixo, sem `CHANGELOG` nem tags. Para algo agnóstico a edição que sobrevive a
várias Copas, dificulta rastrear o que mudou entre edições.

**Correção proposta:** adotar `CHANGELOG.md` (Keep a Changelog) + tags por marco; avaliar versão
dinâmica via `hatch`.
**Aceite:** CHANGELOG criado com o histórico recente; convenção de tag definida.
**Commit:** —

## ENG-11
**Vigiar proporcionalidade doc/código; consolidar docs** · P3 · processo · 🔴 todo

A camada *meta* (docs/processo/skills) cresceu a ~64% do tamanho do código (1.366 linhas de md vs
~2.135 LOC) e a regra de sincronia de artefatos obriga tocar vários docs por mudança — o andaime
arrisca ficar mais pesado que a casa. Não é bug; é vigilância de proporcionalidade.

**Correção proposta:** tratar "criar novo doc/skill/hook" como decisão que precisa se pagar;
preferir **consolidar a adicionar**. Revisar sobreposição entre `AGENTS.md`, `README.md` e
`docs/SPEC.md` periodicamente e eleger um canônico por assunto (já feito p/ comandos → README).
**Aceite:** revisão de sobreposição registrada; nenhuma seção duplicada entre os três docs sem um
canônico declarado. (Item de vigilância recorrente — fechar quando a revisão for feita; reabrir a
cada salto de doc.)
**Commit:** —
