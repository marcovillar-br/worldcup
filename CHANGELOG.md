# Changelog

Todas as mudanças relevantes deste projeto. Formato baseado em
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento
[SemVer](https://semver.org/lang/pt-BR/).

**Convenção de tag:** cada marco recebe uma tag `vX.Y.Z` apontando para o commit do release;
a seção correspondente aqui sai de `[Não lançado]` para `[X.Y.Z] - AAAA-MM-DD`. A versão é
mantida em `pyproject.toml` e `src/worldcup/__init__.py` (bump manual nos dois).

## [Não lançado]

## [0.2.0] - 2026-06-13

Leva de endurecimento de engenharia (backlog `docs/BACKLOG.md`, ENG-1..ENG-9 e ENG-11).

### Adicionado
- Flag global `-v`/`--verbose` e `logging` na biblioteca: avisos antes silenciosos agora são
  visíveis e capturáveis em teste (seleções descartadas pelo `min_matches`, fit não-convergido). (ENG-4)
- Validação de schema do CSV da fonte pública: falha cedo e clara (`DataSourceError`) se o
  formato mudar, em vez de um `KeyError` críptico adiante. (ENG-5)
- Medição de cobertura no CI (`pytest-cov`) com piso `fail_under = 65` (cobertura ~74%). (ENG-8)
- Guardrail de tradução: toda seleção de cada edição precisa ter exibição em PT, senão o teste
  falha (evita cair no inglês silenciosamente). (ENG-9)
- `mypy` passa a cobrir `tests/`. (ENG-7)

### Corrigido
- `sync`: o reencontro do mesmo par de seleções na mesma Copa (grupo + mata-mata) não colapsa mais
  num único placar — desambiguação por data; corrige risco de preencher um jogo com o placar do
  outro. (ENG-1)
- `backtest`: aplica o mando do anfitrião pela mesma `MatrixCache` da produção (antes ignorava,
  pontuando jogos do país-sede de forma diferente do caminho real). (ENG-2)
- `model`: avisa quando o otimizador não converge (antes usava o resultado silenciosamente). (ENG-3)

### Mudado
- Camada de apresentação extraída para `render.py`; `cli.py` passou a só orquestrar (520 → 285
  linhas). Sem mudança de comportamento. (ENG-6)
- Documentação: `docs/SPEC.md` §9.2 declarado canônico para "Limitações conhecidas" (antes
  duplicada nos três docs sem dono). (ENG-11)

## [0.1.0]

- Versão inicial: modelo Dixon–Coles, pontuação Sistema I, simulação Monte Carlo + chaveamento,
  realimentação por resultados reais (`sync-results`/`record`), saídas CSV/MD/HTML, orientação a
  dados por edição (`data/editions/<ano>/`) e backtest.
