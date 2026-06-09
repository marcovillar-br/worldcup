---
name: palpites-copa
description: Gera e atualiza os palpites do bolão da Copa do Mundo usando o app worldcup (modelo Dixon-Coles). Use SEMPRE que o usuário pedir palpites da Copa, quiser os palpites da próxima rodada/fase, quiser registrar resultados de jogos já disputados, perguntar quem é o favorito/campeão, ou quiser repalpitar depois que jogos aconteceram — mesmo que não diga "worldcup" explicitamente. Cobre fase de grupos e mata-mata (90 min, prorrogação e pênaltis).
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

## Passos

### 1. Garantir a base histórica
Se `data/historical_results.csv` não existir, rode primeiro:
```bash
uv run worldcup fetch-data
```

### 2. Atualizar resultados já disputados (realimentação)
**Forma automática (preferida)** — baixa todos os placares reais da internet e já repalpita:
```bash
uv run worldcup sync-results --edition 2026
```
Use isto quando o usuário disser "atualiza os palpites" ou após uma rodada acontecer. Preenche
grupos e mata-mata sozinho (pênaltis inclusos). Para só sincronizar sem repalpitar: `--no-predict`.

**Forma manual (pontual)** — se o usuário ditou um placar específico ou quer corrigir algo.
Descubra o `match_id` em `out/palpites-2026.csv` ou `data/editions/2026/fixtures.csv` (pelos nomes
das seleções). Então:
```bash
uv run worldcup record --edition 2026 --match <ID> --home <gols_mandante> --away <gols_visitante>
```
Para mata-mata empatado nos 90'/prorrogação, acrescente `--ko-winner "<Seleção em inglês>"`
(ex.: `--ko-winner Brazil`). Nomes canônicos em inglês — veja `data/editions/2026/groups.csv`.

### 3. Gerar/atualizar os palpites
```bash
uv run worldcup predict --edition 2026
```
Isso reajusta o modelo (dando peso alto aos jogos já registrados), refaz a simulação e grava
`out/palpites-2026.csv` e `out/palpites-2026.md`. Jogos já disputados saem como `FINAL`; só os
que faltam recebem palpite.

Opções úteis:
- `--risk 0.7` → mais agressivo (arrisca mais zebras; útil para diferenciar e subir no ranking
  quando se está atrás). `--risk 0.3` → mais conservador. Default 0.5 (maximiza pontos esperados).
- `--sims 10000` → mais simulações (probabilidades mais estáveis, roda um pouco mais devagar).

### 4. Apresentar ao usuário
- Mostre primeiro os **candidatos a campeão** (do resumo impresso) e o palpite de campeão sugerido.
- Depois liste os palpites da **próxima rodada/fase ainda não disputada** numa tabela enxuta:
  - Fase de grupos: mandante, palpite (placar), visitante, probabilidades e ⚡ se for ousado.
  - Mata-mata: confronto, palpite dos 90', prorrogação, pênaltis e quem avança.
- Aponte o arquivo `out/palpites-2026.md` (tabela completa, pronta para copiar para o app) e o
  `out/palpites-2026.html` (visualização no navegador; Ctrl+P para imprimir/salvar em PDF).
- Lembre que cada palpite no app fecha **5 minutos antes do jogo**.

## Notas
- Para editar a pontuação do bolão (se o admin do grupo usar valores diferentes), ajuste
  `data/editions/2026/scoring.toml`.
- O app é agnóstico à edição: para uma Copa futura, use `--edition <ano>` com os dados em
  `data/editions/<ano>/`.
