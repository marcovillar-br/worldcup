# PRD — worldcup

**Documento de requisitos de produto.** Engenharia-reversa da **implementação atual** (`src/worldcup/`
+ `data/editions/`): descreve *o que o produto faz e por quê*, não como evoluir. Complementa o
[`SPEC.md`](SPEC.md) (matemática/metodologia), o [`C4.md`](C4.md) (arquitetura) e o
[`BACKLOG.md`](BACKLOG.md) (evolução). Termos em **negrito** estão no [`GLOSSARIO.md`](GLOSSARIO.md).

---

## 1. Resumo executivo

O **worldcup** é uma ferramenta de linha de comando que gera o **palpite** de **todos os jogos** de
uma Copa do Mundo para um **bolão**, escolhendo, em cada jogo, o placar que **maximiza os pontos
esperados** sob a régua de pontuação do bolão — não o placar "mais provável". Um **modelo estatístico
Dixon–Coles** estimado em resultados históricos de seleções produz a **matriz de placares**; um
otimizador transforma essa matriz no palpite de maior valor esperado para o **Sistema I** (onde
**acertar a zebra vale mais**). Conforme a Copa acontece, o produto **realimenta** o modelo com os
resultados reais e repalpita só o que falta.

## 2. Problema e contexto

Em um bolão de pontuação probabilística, o palpite ingênuo ("chuto o favorito 2×0") deixa pontos na
mesa: a régua premia acertos improváveis e bônus cumulativos (saldo, gols do vencedor, goleada,
prorrogação, pênaltis). Calcular à mão, para 104 jogos, o placar que maximiza o **valor esperado** sob
essa régua — e refazê-lo a cada rodada conforme o cenário muda — é inviável manualmente. O produto
automatiza esse cálculo e o mantém atualizado.

## 3. Personas

| Persona | Quem é | O que precisa |
|---|---|---|
| **Apostador** (primário) | Participante do bolão (ex.: o mantenedor) | Palpite ótimo por jogo, atualizado por rodada, pronto pra copiar no app; entender o porquê |
| **Admin do bolão** | Quem define as regras de pontuação do grupo | Ajustar o sistema de pontos/pesos sem mexer no código (`scoring.toml`) |
| **Mantenedor/analista** | Quem opera e evolui a ferramenta | Validar o modelo (backtest), medir o blend, reproduzir runs passados |

## 4. Objetivos e não-objetivos

**Objetivos**
- O1 — Maximizar os **pontos esperados** do apostador sob a régua do bolão, jogo a jogo.
- O2 — Manter os palpites **atualizados** à medida que resultados entram, com esforço mínimo.
- O3 — Ser **agnóstico à edição**: uma Copa nova é só dados, sem mudança de código.
- O4 — Ser **honesto e auditável**: decisões rastreáveis, validação por backtest, reprodutibilidade.

**Não-objetivos**
- N1 — Não é casa de apostas nem dá conselho financeiro; o alvo é um bolão de pontos.
- N2 — Não integra com o app do bolão (o apostador transcreve os palpites).
- N3 — Não é um modelo de "verdade absoluta" de futebol; é estatístico e assume suas limitações (§12).
- N4 — Não tem interface gráfica nem serviço web; é CLI + arquivos.

## 5. Princípios de produto

- **P1 — Agnóstico à edição.** Nada específico de um ano no código; cada edição vive em
  `data/editions/<ano>/`. (→ O3)
- **P2 — Valor esperado, não probabilidade.** O palpite ótimo maximiza E[pontos] sob a régua, o que
  pode favorecer a **zebra**. (→ O1)
- **P3 — Degradação graciosa.** Recursos opcionais (blend com odds) somem sem quebrar: sem `odds.csv`
  ⇒ só o modelo.
- **P4 — Reprodutibilidade.** Runs reais são versionados; runs passados são reconstrutíveis
  (`--as-of`). (→ O4)
- **P5 — Honestidade estatística.** Limitações documentadas; calibração e ganho do blend medidos, não
  presumidos. (→ O4)

## 6. Requisitos funcionais

### 6.1 Geração de palpites (núcleo)
- **RF-01** — Gerar o palpite de placar para **cada jogo** da edição (104 na Copa 2026: 72 de grupo +
  32 de mata-mata). Jogos já disputados saem como `FINAL`; só os pendentes recebem palpite. *(cli
  `predict` → `pipeline.run`)*
- **RF-02** — Para cada jogo, estimar a **matriz de placares** `P(i,j)` via **Dixon–Coles** com ajuste
  ponderado por **decaimento temporal** (meia-vida 2,0 anos), **peso de torneio** e **mando** do
  anfitrião. *(`model.DixonColesModel`; SPEC §3)*
- **RF-03** — Escolher o palpite que **maximiza os pontos esperados** sob a régua configurada, com um
  **nível de risco** ajustável: `best_prediction` otimiza `E[pts]·(1/P)^(2·risk−1)`. *(`scoring.Scorer`;
  SPEC §4–5)*
- **RF-04** — Pontuar pelo **Sistema I**: base **1–13** por probabilidade (`base = 1 + 7,55·log10(1/p)`,
  truncada a [1,13]) **+ bônus cumulativos** — exato +5, gols do vencedor +3, saldo +2, gols do
  perdedor +1, goleada (margem ≥3) +1, prorrogação +3, pênaltis +3. *(`scoring.toml [sistema_i]`)*
- **RF-05** — Aplicar **peso por fase** (Equilíbrio gradual: grupos 1×, mata-mata 2×, final 4×) ao
  sinalizar onde arriscar mais decide o ranking. *(`scoring.toml [phase_weights]`)*
- **RF-06** — Para o **mata-mata**, prever em 3 camadas — placar dos 90', prorrogação e pênaltis — e
  **quem avança**. *(`knockout.predict_knockout`; SPEC §6)*
- **RF-07** — Simular o torneio (**Monte Carlo**, 5000 sims default) para produzir **standings**,
  **chaveamento determinístico** e **P(título)** por seleção. *(`format_engine`; SPEC §7)*

### 6.2 Realimentação durante a Copa
- **RF-08** — Baixar **automaticamente** os resultados reais já disputados, preencher grupos e
  mata-mata (resolvendo o chaveamento pelos placares, com vencedor nos pênaltis) e repalpitar.
  *(cli `sync-results` → `sync`)*
- **RF-09** — Registrar um placar **manualmente** (ajuste pontual/correção), com vencedor de mata-mata
  via `--ko-winner`. *(cli `record`)*
- **RF-10** — Ao realimentar, **fixar** o que já aconteceu (resultado entra no treino com peso alto e
  congela o chaveamento) e repalpitar **apenas** os jogos pendentes. *(SPEC §8)*

### 6.3 Blend com mercado (opcional)
- **RF-11** — Quando houver `odds.csv`, **combinar** a matriz do modelo com as odds de mercado:
  **des-vigar** (tirar a margem) → **log opinion pool** (média geométrica ponderada, peso
  `blend_weight`) → **rescale** da matriz ao 1×2-alvo. Aplicado só nos jogos com odds; sem odds ou
  `blend_weight=0` ⇒ matriz do modelo intacta. *(`blend`; SPEC §3.5)*
- **RF-12** — Atualizar/mesclar as odds a partir de uma fonte de mercado, **preservando** os jogos já
  disputados. *(`scripts/fetch_odds.py`)*

### 6.4 Validação e acompanhamento
- **RF-13** — **Backtest** numa Copa passada: reproduzir os palpites com o conhecimento da época e
  somar os pontos do Sistema I. *(cli `backtest`)*
- **RF-14** — **Medir o ganho do blend**: Brier do blend vs. modelo-puro nos jogos disputados com
  odds, e **monitorar o regime de empates** (observado vs esperado, z-score). *(cli `blend-track`;
  ENG-19/ENG-22)*

### 6.5 Saídas, histórico e dados
- **RF-15** — Gerar as saídas em **CSV** (canônico/diffável), **Markdown** (pronto pra copiar no app) e
  **HTML** autocontido e print-friendly (barras de probabilidade, destaque de zebra). *(`render`)*
- **RF-16** — Arquivar um **snapshot diário** versionado dos palpites (`--archive`) em `history/`, e
  **reconstruir** a visão de um dia passado (`--as-of AAAA-MM-DD`) sem tocar nas saídas vivas. *(cli)*
- **RF-17** — Descrever cada edição **por dados**: formato do torneio, grupos, 104 jogos com o
  chaveamento por **slots** (`1A`, `3rd`, `W73`, `L101`), pontuação e odds — validados por schema
  (Pydantic). *(`data/editions/<ano>/`; `edition.py`)*
- **RF-18** — Manter a **memória de campanha** (`BOLAO.md`): decisões não rederiváveis dos dados
  (risco escolhido, situação no ranking, regras do bolão).

## 7. Requisitos não-funcionais

- **RNF-01 — Reprodutibilidade.** Mesmo input ⇒ mesma saída; runs reais versionados; reconstrução
  determinística via `--as-of`. Ambiente travado no `uv.lock` (CI roda `uv sync --locked`).
- **RNF-02 — Qualidade.** Lint (ruff), formatação, tipos (mypy) e testes (pytest) verdes no CI
  (Python 3.11 e 3.13); cobertura mínima (`fail_under = 80`).
- **RNF-03 — Degradação graciosa.** Ausência de odds, de rede ou de resultados não quebra o fluxo
  (cai para só-modelo / só os jogos conhecidos).
- **RNF-04 — Agnóstico à edição.** Adicionar `data/editions/<ano>/` basta; nenhum literal de ano no
  código.
- **RNF-05 — Observabilidade.** `-v/--verbose` expõe avisos da biblioteca (ex.: seleções descartadas,
  não-convergência do ajuste) sem poluir a saída padrão.
- **RNF-06 — Desempenho.** Um `predict` completo (ajuste + 5000 sims + 104 palpites) roda em segundos
  num laptop; `--sims` troca estabilidade por tempo.
- **RNF-07 — Portabilidade & segurança.** Roda local via `uv`; segredos (chave da The Odds API) vivem
  no `.env`, nunca versionados; `odds.csv` é gitignored (ToS — ver [`DATA.md`](DATA.md) §6).

## 8. Contratos de dados de entrada (resumo)

| Arquivo | Papel | Versionado? |
|---|---|---|
| `tournament.toml` | Formato: grupos, avanço, melhores 3ºs, fases, desempates, anfitriões | sim |
| `groups.csv` | `group,team` (nomes canônicos em inglês) | sim |
| `fixtures.csv` | Os 104 jogos + **chaveamento por slots** + colunas de resultado | sim |
| `scoring.toml` | Sistema de pontos, pesos de fase, `blend_weight`, `risk` | sim |
| `odds.csv` | **Opcional**: `match_id,home,draw,away` em odds decimais | não (gitignored, ToS) |
| `historical_results.csv` | Base de treino normalizada (martj42) | não (cache) |

Detalhe canônico dos contratos: [`SPEC.md`](SPEC.md) §contratos de dados e [`AGENTS.md`](../AGENTS.md)
§"Modelo de dados de uma edição".

## 9. Métricas de sucesso

- **M1 — Pontos no bolão** (resultado final): pontos do apostador vs. o campo (a métrica que importa).
- **M2 — Acurácia preditiva**: **Brier multiclasse** do modelo/blend nos jogos disputados (quanto
  menor, melhor); meta operacional: **blend ≤ modelo-puro** (Δ positivo no `blend-track`).
- **M3 — Eficiência do palpite**: pontos colhidos vs. o teto do modelo (palpites as-of renderiam quanto?).
- **M4 — Calibração**: regime de empates observado vs esperado dentro do ruído (sem viés sistemático).

> Achado de campanha (não-objetivo de produto, mas norteia M1): no Sistema I a **alavanca de ranking é
> acurácia (blend), não ousadia** — subir `risk` não melhora o ranking. Ver `BOLAO.md`.

## 10. Restrições e premissas

- **C1** — Fonte histórica: dataset público martj42 (CSV), atualizado horas após cada jogo.
- **C2** — Fonte de odds: The Odds API (cota/chave própria); blend depende dela estar acessível.
- **C3** — Recorte de treino a partir de **2006-01-01**; filtra seleções não-FIFA.
- **C4** — Numeração `match_id` é **interna** (1–104), **não** a oficial da FIFA — cruzar por **nome**.
- **C5** — O apostador transcreve os palpites no app, que **fecha 5 min antes** de cada jogo.

## 11. Fora de escopo

UI gráfica/web; integração direta com o app do bolão; apostas com dinheiro; modelagem de
escalações/lesões/clima (capturadas só indiretamente, via odds); outras modalidades além de Copa do
Mundo de seleções (o motor é genérico, mas só Copa está modelada).

## 12. Limitações conhecidas

Modelo **puramente estatístico** (favorece quem vem bem; pode subestimar potência em má fase);
desempates de grupo **simplificados** (sem confronto direto/fair-play oficiais); alocação dos **8
melhores terceiros** por casamento de restrição (Annex C da FIFA **aproximado**); empates são a
fraqueza estrutural (o otimizador raramente crava empate). Fonte canônica: [`SPEC.md`](SPEC.md) §9.2.

## 13. Evolução

Melhorias e dívidas vivem em [`BACKLOG.md`](BACKLOG.md) (fonte de verdade, com critério de aceite e
commit de fechamento). Marcos recentes: ENG-14 (régua log), ENG-18 (calibração), ENG-19 (blend com
odds), ENG-22 (monitor de regime de empates).

## 14. Referências

[`README.md`](../README.md) (uso) · [`SPEC.md`](SPEC.md) (metodologia) · [`C4.md`](C4.md) (arquitetura)
· [`GLOSSARIO.md`](GLOSSARIO.md) (termos) · [`AGENTS.md`](../AGENTS.md) (guia de manutenção) ·
[`BACKLOG.md`](BACKLOG.md) (evolução).
