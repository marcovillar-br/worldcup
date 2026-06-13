---
name: backlog
description: Registra, revisa e resolve itens do backlog de engenharia em docs/BACKLOG.md. Use SEMPRE que o usuário quiser anotar uma melhoria/dívida/bug para depois ("coloca no backlog", "registra um item", "abre um ENG"), revisar/priorizar o que está aberto, ou executar/fechar um item ("resolve o ENG-1", "implementa o próximo do backlog"). Codifica a DINÂMICA (verbos e invariantes); o FORMATO mora em docs/BACKLOG.md (fonte de verdade) — não o reescreva aqui.
---

# Backlog de engenharia

Esta skill define **como** registrar e resolver itens no backlog. A **estrutura** (colunas do
índice, seções de detalhe, legendas) é a do próprio [`docs/BACKLOG.md`](../../../docs/BACKLOG.md) —
leia o cabeçalho dele e **siga o formato que já estiver lá**; nunca duplique/reinvente o formato aqui.

A integridade é garantida por um hook de pre-commit (`scripts/check_backlog.py`): IDs únicos,
índice↔detalhe casados, status do índice == status do detalhe, e item ✅ com ref de commit. Se o
hook reclamar, conserte o que ele apontar — ele é a fonte de verdade das invariantes.

## Registrar um item

1. Leia `docs/BACKLOG.md` para pegar o **prefixo e o maior número** já usados (ex.: `ENG-`) e
   alocar o **próximo ID** sem colisão.
2. Defina **prioridade** (P1 correção/dados · P2 lacuna real · P3 boa prática) e **área**.
3. Escreva **dois lugares de uma vez** (é o que mais desincroniza):
   - uma **linha no índice** (ID com link de âncora, prioridade, área, status 🔴, título curto);
   - uma **seção de detalhe** `## <ID>` com: descrição, refs `arquivo:linha`, correção proposta,
     **critério de aceite** (como verificar) e `**Commit:** —`.
4. Todo item nasce **🔴 todo** e **exige critério de aceite** — sem isso não dá pra saber quando
   está "feito". Confirme a área/refs olhando o código, não de memória.

## Revisar / priorizar

- Mostre o índice (aberto vs feito), agrupando por prioridade. Sugira a ordem de ataque
  (P1 antes de P2 antes de P3) e aponte itens sem critério de aceite ou sem refs.
- Repriorizar = editar a coluna de prioridade no índice. Descartar = status ⚪ + uma linha de
  motivo no detalhe (não apague o item; o histórico vale).

## Resolver um item

Esta é a **disciplina de fechamento** — tudo num **único commit**:

1. Marque o item **🟡 fazendo** (índice **e** detalhe) ao começar, se for demorar.
2. Implemente a correção. **Sempre** com **teste de regressão** que falharia sem o fix
   (especialmente para P1/P2).
3. Rode as checagens de Qualidade do `AGENTS.md`: `uv run ruff check .`, `uv run ruff format`,
   `uv run mypy`, `uv run pytest` — todas verdes.
4. No backlog: status **✅ feito** (índice **e** detalhe) e preencha `**Commit:**` com o hash.
   Como o hash só existe após o commit, use o fluxo: `git commit` → pegue o hash com
   `git rev-parse --short HEAD` → edite o `**Commit:**` → `git commit --amend --no-edit`.
   (ou deixe o `**Commit:** <ID-do-PR>` se preferir rastrear por PR.)
5. O fix e a marcação ✅ andam **no mesmo commit** (regra de sincronia de artefatos do `AGENTS.md`).

## Notas

- Não invente formato: se algo não couber no que está no `BACKLOG.md`, ajuste o `BACKLOG.md`
  (e o cabeçalho dele) — ele é a fonte de verdade, esta skill só descreve o processo.
- O hook `backlog-integrity` **bloqueia** o commit se as invariantes quebrarem; rode
  `python3 scripts/check_backlog.py` para checar antes.
