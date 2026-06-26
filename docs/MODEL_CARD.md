# Model Card — worldcup

Cartão do modelo no padrão *Model Cards for Model Reporting* (Mitchell et al., 2019), adaptado a um
produto preditivo de **bolão**. Consolida, num só lugar, a prova de que o modelo funciona e seus
limites — para uma validação de modelo. Números reproduzidos das fontes canônicas
([`SPEC.md`](SPEC.md) §3, §9; `backtest.py`); termos em [`GLOSSARIO.md`](GLOSSARIO.md).

- **Modelo:** `worldcup` v0.2.0 — Dixon–Coles + otimização de palpite (Sistema I)
- **Atualizado:** 2026-06 · **Mantenedor:** Marco · **Licença (código):** MIT
- **Dados:** ver [`DATA.md`](DATA.md) (proveniência e licenciamento)

---

## 1. Detalhes do modelo

- **Tipo:** modelo de gols **Dixon–Coles** (Poisson bivariada com correção para placares baixos),
  estimado por **máxima verossimilhança ponderada** (`model.DixonColesModel`).
- **Saída primária:** **matriz de placares** `P(i,j)` por jogo; dela derivam 1×2, simulação do
  torneio e o **palpite** ótimo.
- **Camada de decisão (produto):** `scoring.best_prediction` escolhe o placar que maximiza
  `E[pts]·(1/P)^(2·risk−1)` sob a régua do **Sistema I** (SPEC §4–5). O modelo (probabilidades) e a
  estratégia (escolha do palpite) são **desacoplados**.
- **Parâmetros de ajuste** (`FitConfig`): decaimento temporal **meia-vida 2,0 anos**; pesos de
  torneio (Copa 1,0 … amistoso 0,5); **mando** do anfitrião; regularização **ridge 0,10**; recorte de
  treino **≥ 2006-01-01**; mínimo **10 jogos** por seleção; filtra seleções não-FIFA.
- **Blend opcional (ENG-19):** quando há `odds.csv`, funde a matriz com o mercado (des-vig → pool
  logarítmico → reescala), peso `blend_weight` (2026 = **0,6**). Sem odds ⇒ só o modelo.
- **Referência:** Dixon & Coles (1997), *Modelling Association Football Scores…*, Applied Statistics 46(2).

## 2. Uso pretendido

- **Uso primário:** gerar o palpite de cada jogo de uma Copa do Mundo de seleções para **um bolão de
  pontuação probabilística** (Sistema I), maximizando os pontos esperados do participante.
- **Usuários:** o apostador (consome os palpites) e o mantenedor (valida/opera). Ver personas no
  [`PRD.md`](PRD.md).
- **Fora do escopo:** apostas com dinheiro / *value betting*; previsão de ligas de clubes; decisões
  que dependam de causalidade (escalação, lesão, tática) — o modelo é **estatístico e correlacional**.
- **Não é** fonte de verdade sobre futebol; é uma ferramenta de **otimização de pontos** sob incerteza.

## 3. Fatores

- **Subpopulações:** confederações/seleções com históricos de tamanhos diferentes; estreantes e
  seleções de baixo volume são **regredidos à média** pelo ridge (estimativa conservadora).
- **Condições:** **mando** do país-sede (aplicado mesmo quando a escala oficial inverte mandante/
  visitante); **fase** do torneio (peso 1×/2×/4×, afeta estratégia, não a probabilidade).
- **Sensibilidade conhecida:** o decaimento de 2 anos faz o modelo **favorecer quem vem bem** e
  possivelmente **subestimar potência em má fase recente** (SPEC §9.2).

## 4. Métricas

Separa **métricas de modelo** (probabilísticas, independentes de `risk`) de **métricas de produto**
(pontos, dependem da estratégia):

- **Modelo — calibração:** **Brier multiclasse** (0 = perfeito; 0,667 = uniforme) e curva de
  confiabilidade do empate. É a métrica-chave de validação do modelo.
- **Produto — pontos:** total e média/jogo pela **régua fiel do app** (§4.1), além de **% de acerto
  do 1×2** e **% de placar exato**.
- **Acompanhamento prospectivo (campanha):** `blend-track` (Brier blend-vs-modelo) e o **monitor de
  regime de empates** (z-score; gatilho de ação só além de ~2σ).

## 5. Dados de avaliação

- **Backtest:** Copas **2010/2014/2018/2022** (256 jogos), treinando **só** com jogos anteriores ao
  início de cada Copa (sem vazamento). Mando tratado como em produção (`_WORLD_CUP_HOSTS`).
- **Calibração agregada:** `pooled_draw_calibration` sobre as 4 Copas.

## 6. Dados de treino

Resultados de jogos internacionais de seleções (dataset martj42), normalizados a partir de
**2006-01-01**, com `shootouts.csv` para vencedores em pênaltis. Proveniência, licença e cadência em
[`DATA.md`](DATA.md). O treino é **reponderado** (decaimento + torneio + mando), não uniforme.

## 7. Análises quantitativas

**Calibração (256 jogos, 4 Copas) — SPEC §9.1:**
- **Brier multiclasse = 0,578** (< 0,667 ⇒ tem resolução, melhor que o palpite uniforme).
- **P(empate) prevista média 27,9% vs. real 22,3%** ⇒ o modelo **não subestima** empates; se algo, os
  **superestima** levemente (o `rho` do Dixon–Coles já puxa para cima). O baixo acerto de empates num
  punhado de jogos é **variância**, não miscalibração — sem ajuste de modelo a fazer.

**Pontos — backtest Copa 2022 (64 jogos), régua hierárquica corrigida (ENG-23) — SPEC §9.1:**

| risco | pts totais | média/jogo | % acerto 1×2 | % placar exato |
|---|---|---|---|---|
| 0.0 (conservador) | **187,0** | 2,92 | 54,7% | 10,9% |
| 0.5 (fiel) | 159,0 | 2,48 | 46,9% | 9,4% |
| 1.0 (agressivo) | 181,0 | 2,83 | 26,6% | 10,9% |

Resultado **não-monótono e ruidoso** (uma Copa só): o conservador fez mais pontos, o agressivo logo
atrás, o fiel abaixo. A vantagem do agressivo (~28%) que aparecia antes **era artefato do bug de
pontuação cumulativa** (ENG-23, que superrecompensava cravar placar); com a régua hierárquica ela
**some**. **Caveat forte:** é **uma Copa só**; não generaliza. Subir o risco **não** melhora os pontos
de forma confiável.

**Risco como alavanca de *ranking* (não de pontos médios):** a modelagem de campo (60 participantes,
40k simulações — `BOLAO.md`, 2026-06-17) mostra que **subir o `risk` reduz** P(vencer) e P(top-10),
porque trava o E[pts] sem aumentar o desvio-padrão útil. Por isso a configuração de produção é
**`risk = 0.5`** e a alavanca de ranking adotada é **acurácia (blend)**, não ousadia. Métrica de
backtest (pontos médios) e objetivo de campanha (vencer o bolão) **divergem** aqui — documentado de
propósito.

## 8. Considerações éticas e uso responsável

- **Não é aconselhamento de apostas.** O alvo é um bolão de pontos entre amigos; usar para apostar
  dinheiro está fora do escopo e não é recomendado.
- **Incerteza honesta.** As saídas são probabilísticas; um palpite "ótimo" ainda erra com frequência
  (ver % de acerto). O produto **não promete** acerto, e sim **valor esperado** sob a régua.
- **Dados públicos.** Sem dado pessoal (só resultados públicos de jogos). Segredos (chave de odds) no
  `.env`, fora do versionamento.

## 9. Ressalvas e recomendações

- **Vieses estruturais** (SPEC §9.2): favorece forma recente; desempates de grupo simplificados (sem
  confronto direto/fair-play); 8 melhores 3ºs por **aproximação** do Annex C — confira os 32-avos com
  os resultados reais.
- **Empates** são a fraqueza prática: o otimizador raramente crava empate, então numa Copa
  empate-pesada zera mais jogos — **monitorar** via `blend-track`, **não forçar** empate (baixa o E[pts]).
- **Dependências externas:** qualidade do dataset martj42 e disponibilidade/ToS da The Odds API
  ([`DATA.md`](DATA.md)). Sem rede, o produto degrada para o último estado conhecido.
- **Revalidação:** re-rodar `backtest` e revisar este cartão a cada bump de versão que toque
  `model.py`/`scoring.py`/`blend.py`, e ao fim de cada Copa (novos 64 jogos de avaliação).
