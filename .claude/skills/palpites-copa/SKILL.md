---
name: palpites-copa
description: Gera e atualiza os palpites do bolão da Copa do Mundo usando o app worldcup (modelo Dixon-Coles). Use SEMPRE que o usuário pedir palpites da Copa, quiser os palpites da próxima rodada/fase, quiser registrar resultados de jogos já disputados, perguntar quem é o favorito/campeão, quiser repalpitar depois que jogos aconteceram, ou perguntar sobre sua eficiência/desempenho no bolão ("estou indo bem?", "quanto deixei na mesa?") — mesmo que não diga "worldcup" explicitamente. Cobre fase de grupos e mata-mata (90 min, prorrogação e pênaltis).
---

# Palpites da Copa (bolão)

Esta skill orquestra o app `worldcup` (neste repositório) para gerar os palpites do bolão e
mantê-los atualizados conforme a Copa acontece. O modelo é estatístico (Dixon-Coles) treinado em
jogos internacionais; a pontuação é calibrada para o **Sistema I** (probabilístico) do app
Bolão de Futebol 2026, onde **acertar a zebra vale mais**.

## Quando usar
- "me dá os palpites da Copa" / "palpites das oitavas" / "o que palpitar hoje"
- "o Brasil empatou 1x1 com o Marrocos" (registrar resultado) → registre e repalpite
- "quem é o favorito ao título?" → mostre as probabilidades de campeão
- "atualiza os palpites" depois de uma rodada
- "qual minha eficiência?" / "estou indo bem?" / "quanto eu deixei na mesa?" → passo 6

## Passos

### 1. Garantir a base histórica
Se `data/historical_results.csv` não existir, rode primeiro:
```bash
uv run worldcup fetch-data
```

### 2. Atualizar resultados já disputados (realimentação)
**Forma automática (preferida)** — baixa todos os placares reais da internet e já repalpita:
```bash
uv run worldcup sync-results --edition 2026 --archive
```
Use isto quando o usuário disser "atualiza os palpites" ou após uma rodada acontecer. Preenche
grupos e mata-mata sozinho (pênaltis inclusos). Para só sincronizar sem repalpitar: `--no-predict`.
O `--archive` grava o snapshot versionado do dia em `data/editions/2026/history/<hoje>.{csv,md}`
(histórico de como os palpites evoluem); inclua-o na rotina diária. Sem ele, `out/` é sobrescrito
e o palpite do dia se perde.

**Forma manual (pontual)** — se o usuário ditou um placar específico ou quer corrigir algo.
Descubra o `match_id` em `out/palpites-2026.csv` ou `data/editions/2026/fixtures.csv` (pelos nomes
das seleções). Então:
```bash
uv run worldcup record --edition 2026 --match <ID> --home <gols_mandante> --away <gols_visitante>
```
⚠️ **`--home`/`--away` seguem a ordem `mandante,visitante` do fixture**, que
nem sempre é a intuitiva: a escala oficial lista o anfitrião como *visitante* em alguns jogos no
estádio dele (ex.: o fixture do jogo 60 é `Turkey × United States`, não `EUA × Turquia`). **Confira a
ordem do fixture antes de registrar** e mapeie o placar ditado para ela — senão grava invertido.
Para mata-mata empatado nos 90'/prorrogação, acrescente `--ko-winner "<Seleção em inglês>"`
(ex.: `--ko-winner Brazil`). Nomes canônicos em inglês — veja `data/editions/2026/groups.csv`.

### 2.5 Atualizar odds de mercado (blend, ENG-19)
Antes de palpitar a próxima rodada, atualize as odds (a edição 2026 já roda blendada,
`blend_weight = 0.6`):
```bash
uv run python scripts/fetch_odds.py --edition 2026   # busca The Odds API + mescla no odds.csv
```
Mescla preservando jogos já disputados (a chave vive no `.env`). Sem `odds.csv`, os palpites saem
100% modelo. **Depois dos resultados da rodada**, rode o tracking (Brier blend-vs-modelo + monitor
de regime de empates) e anote o veredito no `BOLAO.md`:
```bash
uv run worldcup blend-track --edition 2026
```

### 3. Gerar/atualizar os palpites
```bash
uv run worldcup predict --edition 2026
```
Isso reajusta o modelo (dando peso alto aos jogos já registrados), refaz a simulação e grava
`out/palpites-2026.csv` e `out/palpites-2026.md`. Jogos já disputados saem como `FINAL`; só os
que faltam recebem palpite. Com `odds.csv`, o palpite já sai blendado a `blend_weight`.

Opções úteis:
- `--risk 0.7` → mais agressivo (arrisca mais zebras). **No Sistema I, subir o risco NÃO melhora o
  ranking** — testado (ver `BOLAO.md`); a alavanca de ranking é acurácia (blend), não ousadia.
  `--risk 0.3` → conservador. Default 0.5 (maximiza pontos esperados).
- `--blend-weight W` → sobrescreve o peso do mercado no blend (0 = só modelo).
- `--sims 10000` → mais simulações (probabilidades mais estáveis, roda um pouco mais devagar).

### 4. Apresentar ao usuário
- Mostre primeiro os **candidatos a campeão** (do resumo impresso) e o palpite de campeão sugerido.
- Depois liste os palpites da **próxima rodada/fase ainda não disputada** numa tabela enxuta:
  - Fase de grupos: mandante, palpite (placar), visitante, probabilidades e ⚡ se for ousado.
  - Mata-mata: confronto, palpite dos 90', prorrogação, pênaltis e quem avança.
- Aponte o arquivo `out/palpites-2026.md` (tabela completa, pronta para copiar para o app) e o
  `out/palpites-2026.html` (visualização no navegador; Ctrl+P para imprimir/salvar em PDF).
- Lembre que cada palpite no app fecha **5 minutos antes do jogo**.

### 5. Atualizar a memória de campanha
Após sincronizar/repalpitar, atualize a seção **Estado atual** de `data/editions/<ano>/BOLAO.md`
(quantos jogos preenchidos, configuração em uso) com a data do dia. Se houve **decisão de
campanha** (mudou o `risk`, regra do bolão, situação no ranking), registre-a em **Decisões
vivas**/**Histórico**. É a memória persistente agnóstica a ferramenta — leia-a também no início
da sessão.

### 6. Eficiência da campanha (quando o usuário perguntar "estou indo bem?")
Mede quanto dos pontos que o tool renderia o usuário capturou. **Exige os pontos reais do usuário**
(input dele, não derivável) — pergunte se não souber:
```bash
uv run python scripts/efficiency.py --edition 2026 --my-points <PTS> [--leader <PTS>] --compare-archive
```
Para cada jogo disputado, reconstrói o palpite **as-of** (o que o tool mostrava na manhã do jogo) e
o pontua pelo Sistema I contra o real → o **teto** que seguir o tool à risca renderia;
`eficiência = seus_pontos / teto`.

⚠️ **Regras de interpretação (não pule — é fácil concluir errado):**
1. **Sempre** rode com `--compare-archive`. Ele separa o teto **verificável** (jogos com snapshot
   real em `history/`) do **reconstruído** (dias sem arquivo) — e a reconstrução **diverge** do que
   o tool de fato mostrou (drift de odds/refit). Parte de qualquer gap é **ruído de reconstrução**.
2. **Nunca** afirme "100%" nem culpe a execução do usuário sem checar o item 1 — sobretudo se ele
   diz que **ajusta os palpites toda manhã** (= segue o tool; o gap então é majoritariamente
   reconstrução, não má jogada). Foi o erro cometido na 1ª medição (ver `BOLAO.md` 2026-06-24).
3. Se o **líder** estiver **acima** do teto do tool, diga claramente: nem seguir o tool à risca
   alcançaria; ele pegou variância de exatos a favor (regride), não estratégia superior.
4. Recomende manter o **arquivo da manhã completo** (`predict --archive` todo dia) — só assim a
   eficiência fica exata (seus pontos vs `scored(palpite arquivado)`, sem reconstrução).

Registre o veredito (eficiência, teto, posição) no **Histórico** do `BOLAO.md`.

## Notas
- **Histórico/reconstrução**: `predict --archive` guarda o snapshot do dia em `history/`. Para
  reconstruir um dia passado (ou semear o histórico retroativo), use
  `predict --edition 2026 --as-of AAAA-MM-DD` — gera a visão daquela data (só resultados até a
  véspera), grava `history/<data>.reconstruido.{csv,md}` e **não** mexe no `out/` vivo.
- Para editar a pontuação do bolão (se o admin do grupo usar valores diferentes), ajuste
  `data/editions/2026/scoring.toml`.
- O app é agnóstico à edição: para uma Copa futura, use `--edition <ano>` com os dados em
  `data/editions/<ano>/`.
