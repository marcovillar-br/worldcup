# Copa do Mundo FIFA 2030 — preparação da edição

Diretório-esqueleto. **Ainda não há `tournament.toml`/`groups.csv`/`fixtures.csv` — de propósito.**
O formato do torneio (o dado mais estrutural da edição) **não foi definido pela FIFA**, e escrever
um palpite de formato aqui produziria uma simulação **plausível e errada** — a classe de falha que
o projeto combate (ENG-48/ENG-57: valor plausível + caminho silencioso). Preencha na ordem da
seção *Ordem de preenchimento*, conforme cada fato for publicado.

Nada aqui é lido pelo código enquanto não existir `groups.csv`: `load_edition(2030)` falha alto
(`FileNotFoundError`) e o guardrail de tradução (`tests/test_teams.py`) só enumera edições que já
têm `groups.csv`. O esqueleto é inerte por construção.

## Confirmado (verificado em fonte, 2026-07-20)

- **Sedes principais:** Marrocos, Portugal e Espanha — confirmado pela FIFA em **11/12/2024**.
- **Jogos do centenário:** 1 jogo em cada um de **Uruguai** (Estadio Centenario, Montevidéu — palco
  da final de 1930), **Argentina** (Estadio Monumental, Buenos Aires) e **Paraguai** (Estadio
  Osvaldo Domínguez Dibb, Assunção). As três seleções são **classificadas automáticas** como
  co-anfitriãs do centenário.
- **Janela:** **8 de junho a 21 de julho de 2030**.
- **Escala:** 6 países, 2 confederações, ~21 estádios em ~18 cidades. É a **primeira Copa
  disputada em mais de uma confederação** — e a primeira no norte da África.
- As 6 seleções-sede já têm exibição PT em `teams._PT_DISPLAY` (todas jogaram 2026). Só os
  classificados **novos** exigirão aliases.

## Indefinido — o que bloqueia a edição

| Fato | Situação (2026-07-20) | Bloqueia |
|---|---|---|
| Nº de seleções | **TBA.** 48 é o formato vigente; a CONMEBOL propôs **64** em caráter único | `tournament.toml` inteiro |
| Grupos (nº, tamanho, avanço, melhores 3ºs) | TBA — decorre do nº de seleções | `[group_stage]` |
| Fases do mata-mata | TBA — 64 seleções acrescentariam uma rodada (R64) | `knockout_stages` |
| Sorteio dos grupos | **Não ocorreu** (eliminatórias apenas começando: formato da CONCACAF anunciado em fev/2026; da UEFA em mai/2026) | `groups.csv` |
| Calendário de jogos (datas, sedes, slots) | **Não publicado** | `fixtures.csv` |
| Alocação oficial dos melhores 3ºs (Annex C) | Depende do formato **e** do sorteio | `[group_stage.third_allocation]` |
| Sistema de pontos do bolão | O app de 2030 pode mudar a régua | `scoring.toml` |

## Ordem de preenchimento

1. **Formato confirmado** → `tournament.toml`: `name`, `edition`, `hosts`, `[group_stage]`
   (`num_groups`, `group_size`, `advance_per_group`, `best_thirds`), `tiebreakers`,
   `knockout_stages`. Modelo no fim deste arquivo.
2. **Sorteio dos grupos** → `groups.csv` (`group,team`, nomes canônicos **em inglês**).
3. **Calendário FIFA** → `fixtures.csv`. O chaveamento mora aqui, via slots em `home`/`away`
   (`1A`/`2A`, `3rd` + `third_groups`, `W73`, `L101`). ⚠️ `match_id` é a numeração **interna**;
   ao cruzar com a escala oficial guie-se pelos **nomes das seleções**, nunca pelo número.
   Marque `neutral = false` **só** nos jogos disputados no país de um dos anfitriões.
4. **`scoring.toml`** — confirme a régua do bolão de 2030 antes de copiar a de 2026.
   ⚠️ **Fixe `risk` explicitamente:** o default do campo **ausente** é `0.6`, não `0.5`.
5. **Aliases PT** dos classificados novos em `teams._PT_DISPLAY` — `tests/test_teams.py` acusa.
6. **Rodar** `uv run worldcup predict --edition 2030`. Deve funcionar sem tocar no código, salvo
   os acoplamentos residuais listados abaixo.
7. **Opcionais depois:** `odds.csv` (blend; recalibre `blend_weight` com `blend-track --sweep` —
   o 0,8 de 2026 foi calibrado naquela amostra), `BOLAO.md` novo, `presentation.toml`.

## Cuidados específicos de 2030

- **Mando com 6 sedes.** Ponha as **seis** seleções-sede em `hosts`; quem decide se o mando vale
  em cada jogo é a coluna `neutral` do `fixtures.csv`. Argentina, Paraguai e Uruguai têm **um**
  jogo em casa cada (o do centenário) — todos os demais jogos delas são neutros. Lembre que o
  mando segue quem está em `hosts`, **não** a coluna `home` (a escala oficial às vezes lista o
  anfitrião como visitante — `MatrixCache._host_away`).
- **A Copa será quase toda neutra**, como 2026. O ENG-64 (supressão do visitante, `away_pen`)
  corrigiu justamente o λ dos jogos neutros, que vinha deprimido — a calibração já está do lado
  certo para esta edição.
- **Se o formato de 64 seleções vingar**, o motor é genérico (`format_engine` roda formatos
  arbitrários — há teste com edição sintética de 4 grupos sem melhores terceiros), mas revise:
  `knockout_stages` ganha uma rodada, os `phase_weights` do `scoring.toml` precisam de entrada
  para ela, e a heurística de melhores terceiros pode virar dispensável.

## Acoplamentos residuais a 2026 no código (verificados em 2026-07-20)

O princípio "adicione `data/editions/<ano>/` e o código não muda" vale para o **motor**
(modelo, simulação, pontuação, sincronização), mas há resíduos conhecidos:

- `cli.py` — `--edition` tem **default `2026`** em 5 subcomandos. Rodar 2030 exige passar
  `--edition 2030` sempre. Rastreado em **ENG-65**.
- `scripts/build_presentation.py` — títulos/rótulos de slide com "2026" **em código**, apesar de
  os dados virem de `presentation.toml`. Rastreado em **ENG-66**.
- `backtest._WORLD_CUP_START` / `_WORLD_CUP_HOSTS` — registro de Copas **passadas**; acrescente
  `2030` (data de início + as 6 sedes) só **depois** do torneio, para que ele entre no pool de
  calibração. É registro deliberado, não dívida.
- `.claude/skills/palpites-copa/SKILL.md` — exemplos usam `--edition 2026`; atualize quando 2030
  virar a edição viva.

## Modelo de `tournament.toml` (preencher quando o formato sair)

```toml
name = "Copa do Mundo FIFA 2030"
edition = 2030

# As 6 seleções-sede. O mando por jogo é gated pela coluna `neutral` do fixtures.csv.
hosts = ["Morocco", "Portugal", "Spain", "Argentina", "Paraguay", "Uruguay"]

[group_stage]
num_groups = 0          # TBA — decorre do nº de seleções confirmado
group_size = 0          # TBA
advance_per_group = 0   # TBA
best_thirds = 0         # TBA (0 se o formato não usar melhores terceiros)

tiebreakers = ["points", "goal_difference", "goals_for", "random"]

# TBA — 64 seleções acrescentariam "R64" no início.
knockout_stages = ["R32", "R16", "QF", "SF", "3rd_place", "final"]

# Só após o sorteio, e só se o formato usar melhores terceiros (ver SPEC §7.3).
# [group_stage.third_allocation]
```

**Fontes:** FIFA (anúncio de 11/12/2024 e página do torneio), Wikipédia *2030 FIFA World Cup*.
Reconfirme o formato em ≥2 fontes antes de preencher — este arquivo registra o estado de
**2026-07-20** e o formato é justamente o ponto ainda em aberto.
