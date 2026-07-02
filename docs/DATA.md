# Proveniência e licenciamento de dados — worldcup

De onde vêm os dados, sob qual licença, como são processados e o que é versionado. Para uma
validação de IP/conformidade. A **licença do código é MIT** (`LICENSE`); os **dados** têm origem e
termos próprios, tratados aqui.

> **Itens de IP/conformidade** (licença do dataset, ToS da API) estão **resolvidos** na §6
> (verificado em 2026-06 contra as fontes primárias).

---

## 1. Fontes de dados

| Fonte | O que fornece | Acesso | Uso no produto |
|---|---|---|---|
| **martj42 / international_results** | `results.csv` (jogos de seleções desde 1872) + `shootouts.csv` (vencedor em pênaltis) | CSV público no GitHub (raw) · **licença CC0-1.0** (domínio público) | Base de **treino** do modelo |
| **The Odds API** | Odds decimais 1×2 (`h2h`) + over/under (`totals`) por jogo | API REST v4 (chave própria, **tier gratuito**) | **Blend** opcional com o mercado (ENG-19/ENG-35) |
| **Specs de edição** (autorais) | Formato do torneio, grupos, fixtures, pontuação | Mantidas no repo | Descrição da edição |

**URLs/parâmetros (canônicos no código):**
- `fetch_data.DEFAULT_URL` →
  `raw.githubusercontent.com/martj42/international_results/master/results.csv`
  (e `…/shootouts.csv`).
- `scripts/fetch_odds.py` → `api.the-odds-api.com/v4/...`, mercados `h2h,totals`, formato `decimal`,
  região `eu` (tem Pinnacle), casa preferida **Pinnacle** (fallback: mediana das casas; no totals, a
  mediana é tirada na **linha modal** entre as casas, para não misturar preços de linhas
  diferentes).

## 2. Processamento

- **Normalização** (`fetch_data.normalize`): recorte a partir de **2006-01-01**, só jogos
  disputados, nomes mapeados para o **canônico em inglês** (`teams.canonical`), saída em
  `data/historical_results.csv` com 8 colunas (`fetch_data.OUTPUT_COLUMNS`):
  `date, home_team, away_team, home_score, away_score, tournament, neutral, penalty_winner`. As 7
  primeiras vêm do `results.csv`; **`penalty_winner`** é **mesclada** do `shootouts.csv`
  (`_merge_penalty_winner`, casando por `date+home+away`): nome canônico do vencedor da disputa, ou
  `""` se o jogo não foi a pênaltis. É o **único desfecho de mata-mata determinável da fonte**
  (o martj42 não traz a fase); o `backtest` a usa para os bônus de prorrogação/pênaltis (ENG-12).
- **Odds** (`scripts/fetch_odds.py`): busca e **mescla** no `odds.csv`, **preservando** os jogos já
  disputados (não sobrescreve histórico de odds). Linhas em branco/ inválidas são ignoradas. As
  colunas `total_line,over,under` são **opcionais** (ENG-35): arquivos antigos (só 1×2) seguem
  válidos; jogo sem totals fica com as colunas em branco (blend só de 1×2 nele).
- Nenhum dado é alterado manualmente no cache; correções de resultado entram via `record`/`sync`.

## 3. Cadência de atualização

- **Resultados:** sob demanda, via `fetch-data`/`sync-results` (a fonte atualiza poucas horas após
  cada jogo). Sem agendamento automático (decisão de campanha: execução manual — `BOLAO.md`).
- **Odds:** sob demanda, antes de cada rodada, via `fetch_odds.py`.

## 4. Política de versionamento (o que entra no git)

| Artefato | Versionado? | Porquê |
|---|---|---|
| Specs de edição (`tournament.toml`, `groups.csv`, `fixtures.csv`, `scoring.toml`) | **Sim** | Autorais; definem a edição |
| `odds.csv` (odds **reais** coletadas) | **Não** (`.gitignore`) | ToS não permite redistribuir odds em repo público (§6); vive só local |
| `shootouts.csv` (vencedores de pênaltis da edição, ENG-30) | **Sim** | Fato público e durável; captura manual da edição viva sob latência da fonte, verificada em ≥2 fontes. Distinto do `shootouts.csv` baixado do martj42 (ingestão, embutido no `historical_results.csv` gitignored) |
| `history/<data>.{csv,md}` (runs **reais**) | **Sim** | Snapshots imutáveis e não-reproduzíveis |
| `data/historical_results.csv` (cache de treino) | **Não** (`.gitignore`) | Regenerável por `fetch-data` |
| `out/`, `*.reconstruido.*`, caches | **Não** | Regeneráveis |
| Chave da The Odds API | **Nunca** | Segredo — vive no `.env` |

**Regra firme:** `odds.csv` é gitignored (§6); **nunca** versionar odds (reais, inventadas ou de
teste), nem a chave de API.

## 5. Atribuição e segredos

- **Atribuição:** o dataset martj42 é **CC0-1.0** (domínio público) — atribuição **não é legalmente
  exigida**. Mantemos o crédito por cortesia/boa prática (referência em `SPEC.md` §Referências); o
  próprio README do martj42 credita Wikipedia, RSSSF e associações como origem dos dados.
- **Segredos:** `ODDS_API_KEY` lida do ambiente ou do `.env` (raiz), nunca commitada. Rotação:
  trocar a chave na conta da The Odds API e atualizar o `.env` local.

## 6. Decisões de IP/conformidade

Verificado em **2026-06** contra as fontes primárias:

1. **Licença do dataset martj42 — RESOLVIDO.** O repositório
   `github.com/martj42/international_results` declara **CC0-1.0** (dedicação a domínio público): uso
   irrestrito, **sem atribuição obrigatória**. O README do martj42 credita Wikipedia, RSSSF e
   associações como origem — mantemos o crédito por cortesia. **Sem risco de IP no treino.**
2. **Redistribuição de odds (The Odds API) — RESOLVIDO: não versionar.** O ToS **permite** usar odds
   em ferramentas analíticas voltadas ao usuário, mas **proíbe redistribuí-las como produto de dados
   autônomo** (feeds/arquivos crus para terceiros); o tier gratuito é descrito como "para
   desenvolvimento e teste". Um `odds.csv` num repo público é zona cinzenta. **Decisão:** `odds.csv`
   é **gitignored** (`data/editions/*/odds.csv`) — vive só local; o veredito de blend permanece
   reproduzível localmente. Remove o risco sem custo prático relevante.
3. **Cota/uso da The Odds API — OK.** Uso dentro do **tier gratuito** (limite de requisições), sem
   uso comercial e sem revenda de dados.

## 7. Referências

[`MODEL_CARD.md`](MODEL_CARD.md) (uso dos dados no modelo) · [`SPEC.md`](SPEC.md) §2 (ingestão) ·
[`PRD.md`](PRD.md) §8 (contratos) · [`AGENTS.md`](../AGENTS.md) (operação) · `LICENSE` (código,
MIT).
