# Proveniência e licenciamento de dados — worldcup

De onde vêm os dados, sob qual licença, como são processados e o que é versionado. Para uma
validação de IP/conformidade. A **licença do código é MIT** (`LICENSE`); os **dados** têm origem e
termos próprios, tratados aqui.

> ⚠️ **Itens jurídicos a confirmar** estão na §6. São fatos externos (licença do dataset, ToS da API)
> que o mantenedor precisa verificar e fixar — não devem ser presumidos.

---

## 1. Fontes de dados

| Fonte | O que fornece | Acesso | Uso no produto |
|---|---|---|---|
| **martj42 / international_results** | `results.csv` (jogos de seleções desde 1872) + `shootouts.csv` (vencedor em pênaltis) | CSV público no GitHub (raw) | Base de **treino** do modelo |
| **The Odds API** | Odds decimais 1×2 (mercado `h2h`) por jogo | API REST v4 (chave própria) | **Blend** opcional com o mercado (ENG-19) |
| **Specs de edição** (autorais) | Formato do torneio, grupos, fixtures, pontuação | Mantidas no repo | Descrição da edição |

**URLs/parâmetros (canônicos no código):**
- `fetch_data.DEFAULT_URL` → `raw.githubusercontent.com/martj42/international_results/master/results.csv`
  (e `…/shootouts.csv`).
- `scripts/fetch_odds.py` → `api.the-odds-api.com/v4/...`, mercado `h2h`, formato `decimal`, região
  `eu` (tem Pinnacle), casa preferida **Pinnacle** (fallback: mediana das casas).

## 2. Processamento

- **Normalização** (`fetch_data.normalize`): recorte a partir de **2006-01-01**, só jogos disputados,
  nomes mapeados para o **canônico em inglês** (`teams.canonical`), saída em
  `data/historical_results.csv`.
- **Odds** (`scripts/fetch_odds.py`): busca e **mescla** no `odds.csv`, **preservando** os jogos já
  disputados (não sobrescreve histórico de odds). Linhas em branco/ inválidas são ignoradas.
- Nenhum dado é alterado manualmente no cache; correções de resultado entram via `record`/`sync`.

## 3. Cadência de atualização

- **Resultados:** sob demanda, via `fetch-data`/`sync-results` (a fonte atualiza poucas horas após
  cada jogo). Sem agendamento automático (decisão de campanha: execução manual — `BOLAO.md`).
- **Odds:** sob demanda, antes de cada rodada, via `fetch_odds.py`.

## 4. Política de versionamento (o que entra no git)

| Artefato | Versionado? | Porquê |
|---|---|---|
| Specs de edição (`tournament.toml`, `groups.csv`, `fixtures.csv`, `scoring.toml`) | **Sim** | Autorais; definem a edição |
| `odds.csv` (odds **reais** coletadas) | **Sim** | Reprodutibilidade do veredito de blend ⚠️ (ver §6) |
| `history/<data>.{csv,md}` (runs **reais**) | **Sim** | Snapshots imutáveis e não-reproduzíveis |
| `data/historical_results.csv` (cache de treino) | **Não** (`.gitignore`) | Regenerável por `fetch-data` |
| `out/`, `*.reconstruido.*`, caches | **Não** | Regeneráveis |
| Chave da The Odds API | **Nunca** | Segredo — vive no `.env` |

**Regra firme:** nunca versionar odds **inventadas/de teste**, nem a chave de API.

## 5. Atribuição e segredos

- **Atribuição:** o dataset martj42 deve ser **creditado** conforme a licença dele (ver §6). A
  referência já consta em `SPEC.md` §Referências; a atribuição formal completa depende da §6.
- **Segredos:** `ODDS_API_KEY` lida do ambiente ou do `.env` (raiz), nunca commitada. Rotação:
  trocar a chave na conta da The Odds API e atualizar o `.env` local.

## 6. ⚠️ Itens a confirmar (risco de IP/conformidade)

Estes pontos **não estão resolvidos no repo** e são o que uma validação jurídica olharia primeiro:

1. **Licença do dataset martj42.** Confirmar a licença vigente da fonte (a listagem no Kaggle do
   dataset correlato indica **CC BY 4.0**, que exigiria **atribuição**; o repositório GitHub pode não
   carregar um `LICENSE` explícito — *ausência* de licença também é um risco). **Ação:** verificar e
   registrar aqui a licença + a forma de atribuição exigida.
2. **ToS da The Odds API quanto a *redistribuir* odds.** O repo **versiona odds reais** (Pinnacle)
   para reprodutibilidade. É preciso confirmar se os **Termos de Serviço** da The Odds API permitem
   **armazenar e redistribuir** essas odds num repositório público. **Se não permitirem**, parar de
   versionar `odds.csv` (mantê-lo gitignored) e tratar o veredito de blend como reproduzível só
   localmente. **Ação:** ler o ToS e decidir; documentar a conclusão aqui.
3. **Cláusula de atribuição/limite de uso da The Odds API.** Confirmar se há exigência de crédito ou
   restrição de finalidade (uso não-comercial, limite de cota) relevante para o projeto.

> Até a §6 estar resolvida, trate a versionação de `odds.csv` como **provisória**: é uma escolha de
> reprodutibilidade que pode ser revertida se o ToS exigir.

## 7. Referências

[`MODEL_CARD.md`](MODEL_CARD.md) (uso dos dados no modelo) · [`SPEC.md`](SPEC.md) §2 (ingestão) ·
[`PRD.md`](PRD.md) §8 (contratos) · [`AGENTS.md`](../AGENTS.md) (operação) · `LICENSE` (código, MIT).
