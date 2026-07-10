---
name: palpites-copa
description: Gera e atualiza os palpites do bolão da Copa do Mundo usando o app worldcup (modelo
Dixon-Coles). Use SEMPRE que o usuário pedir palpites da Copa, quiser os palpites da próxima
rodada/fase, quiser registrar resultados de jogos já disputados, perguntar quem é o
favorito/campeão, quiser repalpitar depois que jogos aconteceram, ou perguntar sobre sua
eficiência/desempenho no bolão ("estou indo bem?", "quanto deixei na mesa?") — mesmo que não diga
"worldcup" explicitamente. Cobre fase de grupos e mata-mata (90 min, prorrogação e pênaltis).
---

# Palpites da Copa (bolão)

Esta skill orquestra o app `worldcup` (neste repositório) para gerar os palpites do bolão e
mantê-los atualizados conforme a Copa acontece. O modelo é estatístico (Dixon-Coles) treinado em
jogos internacionais; a pontuação é calibrada para o **Sistema I** (probabilístico) do app Bolão
de Futebol 2026, onde **acertar a zebra vale mais**.

## Quando usar
- "me dá os palpites da Copa" / "palpites das oitavas" / "o que palpitar hoje"
- "o Brasil empatou 1x1 com o Marrocos" (registrar resultado) → registre e repalpite
- "quem é o favorito ao título?" → mostre as probabilidades de campeão
- "atualiza os palpites" depois de uma rodada
- "qual minha eficiência?" / "estou indo bem?" / "quanto eu deixei na mesa?" → passo 6

## Start-of-Day (reidratar contexto — rode primeiro)

Para retomar a campanha no início de uma sessão sem rodar a pipeline, comece pelo briefing
**read-only** (ENG-31) — uma saída só com estado, jogos de hoje, próximos palpites, standing e o
que depende do usuário:
```bash
uv run worldcup status --edition 2026   # alias: uv run ws
```
Não muta nada. Use-o para decidir o que fazer a seguir (se há jogos atrasados → passo 2; se vai
mostrar a rodada → passos 3–4). A **mutação** (sync/predict) continua nos passos abaixo.

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
Descubra o `match_id` em `out/palpites-2026.csv` ou `data/editions/2026/fixtures.csv`
(pelos nomes das seleções). Então:
```bash
uv run worldcup record --edition 2026 --match <ID> --home <gols_mandante> --away <gols_visitante>
```
⚠️ **`--home`/`--away` seguem a ordem `mandante,visitante` do fixture**, que nem sempre é a
intuitiva: a escala oficial lista o anfitrião como *visitante* em alguns jogos no estádio dele
(ex.: o fixture do jogo 60 é `Turkey × United States`, não `EUA × Turquia`). **Confira a ordem do
fixture antes de registrar** e mapeie o placar ditado para ela — senão grava invertido.

⚠️ **No registro manual** (quando a fonte oficial do `sync-results` ainda não tem o jogo e você
busca o placar na internet): **confirme em ≥2 fontes independentes antes de `record`** (ESPN,
FIFA, Yahoo, Olympics, etc.) — placar **e** ordem mandante×visitante. **Nunca** registre a partir
de uma única busca/resumo. (Isso **não** se aplica ao `sync-results`: a fonte canônica dele já é
a referência.) O resultado realimenta o ajuste do modelo (e o placar real congela o chaveamento),
então um placar errado/invertido **contamina o refit inteiro**: favoritos ao título, regime de
empates e o chaveamento do mata-mata. Já aconteceu (2026-06-27): J64 gravado como
`Noruega 4×1 França` de uma fonte só — o correto era França 4×1; o erro mudava o favorito e o
palpite de jogos futuros (J78). Se as fontes divergirem, **não registre** — pergunte ao usuário.
Para mata-mata empatado nos 90'/prorrogação, acrescente `--ko-winner "<Seleção em inglês>"`
(ex.: `--ko-winner Brazil`). Nomes canônicos em inglês — veja `data/editions/2026/groups.csv`.

### 2.5 Atualizar odds de mercado (blend, ENG-19)
Antes de palpitar a próxima rodada, atualize as odds (a edição 2026 já roda blendada,
`blend_weight = 0.8` — escolhido com dado via `blend-track --sweep`, ENG-38):
```bash
uv run python scripts/fetch_odds.py --edition 2026   # busca The Odds API + mescla no odds.csv
```
Mescla preservando jogos já disputados (a chave vive no `.env`). Sem `odds.csv`, os palpites
saem 100% modelo. **Depois dos resultados da rodada**, rode o tracking (Brier blend-vs-modelo +
monitor de regime de empates) e anote o veredito no `BOLAO.md`:
```bash
uv run worldcup blend-track --edition 2026
```

### 3. Gerar/atualizar os palpites
```bash
uv run worldcup predict --edition 2026
```
Isso reajusta o modelo (incorporando os jogos já registrados; peso `edition_boost` — a 2026 usa
1.0, sem boost, ENG-44), refaz a simulação e grava
`out/palpites-2026.csv` e `out/palpites-2026.md`. Jogos já disputados saem como `FINAL`; só os
que faltam recebem palpite. Com `odds.csv`, o palpite já sai blendado a `blend_weight`.

Opções úteis:
- `--risk 0.7` → mais agressivo (arrisca mais zebras). **No Sistema I, subir o risco NÃO melhora
  o ranking** — testado (ver `BOLAO.md`); a alavanca de ranking é acurácia (blend), não ousadia.
  `--risk 0.3` → conservador. Default 0.5 (maximiza pontos esperados).
- `--blend-weight W` → sobrescreve o peso do mercado no blend (0 = só modelo).
- `--sims 10000` → mais simulações (probabilidades mais estáveis, roda um pouco mais devagar).

### 4. Apresentar ao usuário
- Mostre primeiro os **candidatos a campeão** (do resumo impresso) e o palpite de campeão
  sugerido.
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

### 5.5 Atualizar os dados da apresentação (deriváveis)
Depois de repalpitar (passo 3), atualize os campos deriváveis do deck `docs/apresentacao.html` e
regenere-o — assim "atualiza os palpites" já deixa a apresentação em dia, sem pedido separado:
```bash
uv run python scripts/update_presentation_data.py --edition 2026
uv run python scripts/build_presentation.py --edition 2026 --docs
```
O primeiro script reescreve `data/editions/2026/presentation.toml` com o que é **derivável de
dado**: jogos disputados e favoritos ao título (via `out/palpites-2026.{csv,md}`), Brier
modelo-vs-blend (mesma métrica do `blend-track`, chamada direto da lib) e a contagem de melhorias
do backlog. Ele **preserva** (não sobrescreve) os campos que exigem dado externo ou curadoria:
- `campanha.pontos`/`eficiencia_pct` — só existem no seu placar real do bolão; atualize-os quando
  rodar o passo 6 (eficiência).
- `campanha.fase`/`bracket_destaque.*` (seleção em destaque, rival de QF/SF, jogos para ficar de
  olho) — é escolha editorial, não cálculo; revise à mão quando o bracket mudar de forma relevante
  (eliminação, zebra que muda o adversário de quem você acompanha).
O segundo comando regenera `out/apresentacao.html` + `docs/apresentacao.html` a partir do TOML
atualizado — inclua o HTML e o TOML no mesmo commit da rodada.

### 6. Eficiência da campanha (quando o usuário perguntar "estou indo bem?")
Mede quanto dos pontos que o tool renderia o usuário capturou. **Exige os pontos reais do
usuário** (input dele, não derivável) — pergunte se não souber:
```bash
uv run python scripts/efficiency.py --edition 2026 --my-points <PTS> [--leader <PTS>] --compare-archive
```
Para cada jogo disputado, pontua pelo Sistema I contra o real o palpite que o tool mostrava na
manhã do jogo → o **teto** que seguir o tool à risca renderia. O teto por jogo é **congelado**
na 1ª medição em `ceiling.csv` (ENG-34): snapshot real de `history/` primeiro, reconstrução as-of
só sem arquivo (`--reset-ceiling` recongela, ex.: após fix de scoring). No mata-mata o placar dos
90' entra com o **peso de fase** (R32–SF ×2, final ×4), contra o tempo normal (`regulation.csv`,
ENG-45) se houve gol na ET; o bônus de prorrogação/pênaltis é somado quando a base **martj42**
(`penalty_winner`; não o `shootouts.csv` da edição) confirma o desfecho (ENG-27) — jogo empatado
nos 90' sem shootout na fonte pontua o 90' e só fica sem esse bônus.
`eficiência = seus_pontos / teto`.

O script também imprime um **teto teórico (oráculo)** — cravar o placar exato de todo jogo — e
duas capturas complementares: `tool / oráculo` (qualidade do modelo+blend) e `seus_pontos /
oráculo` (sua distância da perfeição). **A eficiência (vs teto do tool) é a métrica de execução;
o oráculo é só diagnóstico de teto.** O oráculo é dominado por ruído irredutível (ninguém crava
placar exato com consistência: o tool perfeito captura ~34% do teórico), então **não** o use
para avaliar a jogada do usuário — serve para dimensionar "quanto teto ainda existe".

⚠️ **Regras de interpretação — checar antes de explicar (ENG-50).**
Este bloco fornece **checagens**, não explicações. É deliberado: um documento que já traz a
explicação de uma anomalia a **imuniza contra investigação** — quem lê pega a explicação pronta,
acha plausível, e para de procurar. Foi assim que o ENG-48 (bônus de KO nunca creditado ⇒ teto
subestimado ⇒ eficiência inflada) sobreviveu a duas medições: a skill dizia "é ruído de
reconstrução" e "o líder pegou variância de exatos", e as duas frases couberam perfeitamente no
sintoma de um bug. **Nunca** ofereça uma leitura estatística de um número anômalo antes de as
sondas mecânicas voltarem limpas.

1. **Sempre** rode com `--compare-archive`. Ele separa o teto **verificável** (jogos com snapshot
   real em `history/`) do **reconstruído** (dias sem arquivo).
2. **Leia as sondas do próprio script antes de interpretar.** Se os pontos do usuário ou os do
   líder passam do teto, ele imprime `🚨 ANOMALIA` seguido das sondas mecânicas (bônus de KO
   creditado, contradição de fonte, latência, procedência do congelamento, jogos só reconstruídos).
   **Sonda suja ⇒ o teto pode estar subestimado: investigue.** Só com todas limpas a variância de
   placares exatos passa a ser leitura legítima — e aí o script diz isso sozinho.
3. **Nunca** culpe a execução do usuário sem checar o item 1 — sobretudo se ele **ajusta os palpites
   toda manhã** (= segue o tool). Erro cometido na 1ª medição (`BOLAO.md` 2026-06-24).
4. Recomende manter o **arquivo da manhã completo** (`predict --archive` todo dia) — só assim a
   eficiência fica exata (seus pontos vs `scored(palpite arquivado)`, sem reconstrução).
5. **Teto congelado (ENG-34)**: o teto por jogo é **congelado na 1ª medição** em `ceiling.csv`
   (rastreado) — o headline não muda mais retroativamente entre rodagens. Se código/odds/base
   mudarem depois (ex.: um fix de scoring), o script **reporta drift** dos jogos afetados sem
   sobrescrever; para recongelar na medição atual, rode com `--reset-ceiling`. O `ceiling.csv`
   guarda a coluna `code` (ENG-50): a impressão digital do código que decidiu aquele teto. Mudou o
   pontuador ⇒ o script acusa "congelado sob código diferente" — recongele; o congelamento protege
   contra **drift**, não contra **bug**.

Registre o veredito (eficiência, teto, posição) no **Histórico** do `BOLAO.md` e atualize
`campanha.pontos`/`eficiencia_pct` em `data/editions/2026/presentation.toml` (único jeito de
manter esses dois campos em dia — o passo 5.5 não os deriva). Se editou o TOML, regenere o deck
(`build_presentation.py --edition 2026 --docs`).

## Notas
- **Histórico/reconstrução**: `predict --archive` guarda o snapshot do dia em `history/`. Para
  reconstruir um dia passado (ou semear o histórico retroativo), use
  `predict --edition 2026 --as-of AAAA-MM-DD` — gera a visão daquela data (só resultados até a
  véspera), grava `history/<data>.reconstruido.{csv,md}` e **não** mexe no `out/` vivo.
- Para editar a pontuação do bolão (se o admin do grupo usar valores diferentes), ajuste
  `data/editions/2026/scoring.toml`.
- O app é agnóstico à edição: para uma Copa futura, use `--edition <ano>`
  com os dados em `data/editions/<ano>/`.
