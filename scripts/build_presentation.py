#!/usr/bin/env python3
"""Gera a apresentação HTML do projeto worldcup (deck autocontido, tema "Placar Noturno").

Um único arquivo `.html` self-contained (CSS + JS inline, sem CDN/libs) que explica o projeto para
leigos: conceitos, diferenciais, resultados da campanha 2026, a evolução/lições ao longo da Copa e a
visão de futuro. Espelha a filosofia de `worldcup.render.render_html` (offline, print-friendly).

Características:
  - Palco **16:9** com **redimensionamento automático** (escala via container queries).
  - Cada slide = header + corpo + rodapé; transições e design consistentes.
  - Navegação por botões, **dots clicáveis**, contador `n/N`, teclado, swipe e **deep-link `#slide-k`**.
  - **Contadores animados** nos números de resultado; **modo impressão/PDF** (1 slide por página).
  - Visual **SVG-first** (vetorial, nítido em qualquer escala); sem imagens externas.

Conteúdo curado (números "até 28/06/2026"); para atualizar, edite as constantes abaixo e rode de novo.

Uso: `uv run python scripts/build_presentation.py [--out PATH] [--docs]`
  --out   destino do HTML (default: out/apresentacao.html, gitignored/regenerável)
  --docs  também grava docs/apresentacao.html (cópia versionada/compartilhável)
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = PROJECT_ROOT / "out" / "apresentacao.html"
DOCS_OUT = PROJECT_ROOT / "docs" / "apresentacao.html"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

AS_OF = "28 jun 2026"
VERSION = "v0.2.0"


@dataclass
class Slide:
    """Um slide: `kicker` aparece no header; `body` é o HTML do corpo (entre header e rodapé)."""

    kicker: str
    body: str


# --------------------------------------------------------------------------- helpers de conteúdo (SVG/HTML)


def _icon(path: str, *, size: float = 1.0) -> str:
    """Ícone SVG inline (stroke neon), `path` no viewBox 0 0 24 24."""
    return (
        f'<svg class="ic" viewBox="0 0 24 24" style="width:{size}em;height:{size}em" '
        f'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
        f'stroke-linejoin="round">{path}</svg>'
    )


_IC_TROPHY = _icon(
    '<path d="M8 21h8M12 17v4M7 4h10v4a5 5 0 0 1-10 0V4Z"/>'
    '<path d="M5 5H3v2a3 3 0 0 0 3 3"/><path d="M19 5h2v2a3 3 0 0 1-3 3"/>'
)
_IC_BALL = _icon('<circle cx="12" cy="12" r="9"/><path d="m12 7 3 2-1 4h-4l-1-4 3-2Z"/>')
_IC_CHART = _icon(
    '<path d="M3 3v18h18"/><rect x="7" y="11" width="3" height="7"/><rect x="13" y="7" width="3" height="11"/>'
)
_IC_BRAIN = _icon(
    '<path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-1 5 3 3 0 0 0 2 4 3 3 0 0 0 5 1V4.5A2.5 2.5 0 0 0 9 4Z"/>'
    '<path d="M15 4a3 3 0 0 1 3 3 3 3 0 0 1 1 5 3 3 0 0 1-2 4 3 3 0 0 1-5 1"/>'
)
_IC_SCALE = _icon('<path d="M12 3v18M5 7h14M7 7l-3 6a3 3 0 0 0 6 0L7 7Zm10 0-3 6a3 3 0 0 0 6 0l-3-6Z"/>')
_IC_REWIND = _icon('<path d="M11 5 4 12l7 7M20 5l-7 7 7 7"/>')
_IC_REFRESH = _icon(
    '<path d="M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5"/>'
)
_IC_INFINITY = _icon('<path d="M6 9a3 3 0 0 0 0 6c2 0 3-2 6-3s4-3 6-3a3 3 0 0 1 0 6c-2 0-3-2-6-3S8 9 6 9Z"/>')


def cover_svg() -> str:
    """Cena de capa SVG: estádio neon estilizado (gramado, linhas, bola, brilho)."""
    return """
<svg class="hero" viewBox="0 0 1280 520" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <radialGradient id="sky" cx="50%" cy="0%" r="90%">
      <stop offset="0%" stop-color="#13324a"/><stop offset="60%" stop-color="#0a1726"/>
      <stop offset="100%" stop-color="#070b12"/>
    </radialGradient>
    <linearGradient id="grass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0e3b2e"/><stop offset="100%" stop-color="#072018"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#22d3ee" stop-opacity=".55"/>
      <stop offset="100%" stop-color="#22d3ee" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1280" height="520" fill="url(#sky)"/>
  <g opacity=".5">
    <circle cx="180" cy="70" r="1.6" fill="#9fe9ff"/><circle cx="420" cy="40" r="1.2" fill="#9fe9ff"/>
    <circle cx="900" cy="60" r="1.4" fill="#9fe9ff"/><circle cx="1120" cy="90" r="1.2" fill="#9fe9ff"/>
    <circle cx="650" cy="30" r="1" fill="#9fe9ff"/>
  </g>
  <path d="M0 300 L1280 300 L1280 520 L0 520 Z" fill="url(#grass)"/>
  <g stroke="#3ad6a0" stroke-opacity=".5" stroke-width="2" fill="none">
    <path d="M0 360 L1280 360"/>
    <path d="M640 300 L640 520"/>
    <ellipse cx="640" cy="410" rx="120" ry="46"/>
    <path d="M420 520 L420 470 L860 470 L860 520"/>
    <path d="M540 520 L540 500 L740 500 L740 520"/>
  </g>
  <ellipse cx="640" cy="412" rx="320" ry="120" fill="url(#glow)"/>
  <g transform="translate(640 410)">
    <circle r="34" fill="#0b1220" stroke="#e8edf4" stroke-width="2"/>
    <path d="M0 -20 l14 10 -5 17 -18 0 -5 -17 Z" fill="#e8edf4"/>
  </g>
</svg>
"""


def _embed(name: str) -> str | None:
    """Lê uma imagem livre de `scripts/assets/` e devolve um data-URI base64 (offline). None se ausente."""
    p = ASSETS_DIR / name
    if not p.exists():
        return None
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def hero_bg(name: str) -> str:
    """Fundo fotográfico da capa (foto livre embutida) + scrim escuro; cai para o SVG se a foto faltar."""
    uri = _embed(name)
    if uri is None:
        return cover_svg()
    return f'<div class="bgphoto on-hero" style="background-image:url({uri})"></div><div class="scrim"></div>'


def photo_bg(name: str, *, opacity: str = ".34") -> str:
    """Fundo fotográfico discreto (divisória) + scrim suave; vazio se a foto faltar (degradação graciosa)."""
    uri = _embed(name)
    if uri is None:
        return ""
    return (
        f'<div class="bgphoto" style="background-image:url({uri});opacity:{opacity}"></div>'
        '<div class="scrim soft"></div>'
    )


def bar_compare() -> str:
    """Barras 'zebra vale mais': favorito (pouco) vs zebra (muito)."""
    rows = [
        ("Brasil 2×0 (óbvio)", 18, "+2 pts", "home"),
        ("Suíça 2×0 a Argentina (zebra)", 100, "+13 pts", "upset"),
    ]
    out = ['<div class="bars">']
    for label, pct, pts, cls in rows:
        out.append(
            f'<div class="barrow"><span class="blabel">{label}</span>'
            f'<span class="btrack"><i class="{cls}" style="width:{pct}%"></i></span>'
            f'<span class="bpts {cls}">{pts}</span></div>'
        )
    out.append("</div>")
    return "".join(out)


def champ_bars(teams: list[tuple[str, int]] | None = None) -> str:
    """Favoritos ao título (Monte Carlo, até 28/06 — fase de grupos encerrada)."""
    if teams is None:
        teams = [("Argentina", 30), ("Espanha", 20), ("França", 12), ("Brasil", 9), ("Portugal", 7)]
    out = ['<div class="champ">']
    for name, pct in teams:
        out.append(
            f'<div class="crow"><span class="cname">{name}</span>'
            f'<span class="ctrack"><i style="width:{pct}%"></i></span>'
            f'<span class="cval"><b class="num" data-to="{pct}">0</b>%</span></div>'
        )
    out.append("</div>")
    return "".join(out)


def stat(value: str, to: str, label: str, *, suffix: str = "", cls: str = "accent") -> str:
    """Cartão de número grande com contador animado (data-to)."""
    return (
        f'<div class="stat"><div class="snum {cls}">'
        f'<span class="num" data-to="{to}">0</span>{suffix}</div>'
        f'<div class="slab">{label}</div></div>'
    )


def card(icon: str, title: str, text: str) -> str:
    return f'<div class="card"><div class="cardic accent">{icon}</div><b>{title}</b><span>{text}</span></div>'


def timeline(items: list[tuple[str, str, str]]) -> str:
    """Linha do tempo de lições: (data, título-lição, detalhe)."""
    out = ['<div class="tl">']
    for date, lesson, detail in items:
        out.append(
            f'<div class="tli"><span class="tldot"></span>'
            f'<div class="tlc"><span class="tldate">{date}</span>'
            f'<b>{lesson}</b><span class="tldet">{detail}</span></div></div>'
        )
    out.append("</div>")
    return "".join(out)


# --------------------------------------------------------------------------- os slides


def build_slides() -> list[Slide]:
    s: list[Slide] = []

    # 1 — capa
    s.append(
        Slide(
            "worldcup",
            f"""
      {hero_bg("cover-stadium.jpg")}
      <div class="cover">
        <div class="badge">{_IC_TROPHY} bolão da Copa · modelo estatístico</div>
        <h1>O palpite <span class="accent">inteligente</span><br>para cada jogo da Copa</h1>
        <p class="lede">Num bolão com 100 amigos, 99 chutam Brasil 2×0. Um arrisca Paraguai 1×1.
          Se a zebra sai, ele <b>leva uma bolada de pontos</b> — e os outros 99 zeram. Quem está
          certo? Depende do sistema de pontos — e é exatamente isso que esta ferramenta calcula.</p>
        <div class="hint">use ← → ou os botões para navegar</div>
      </div>""",
        )
    )

    # 2 — o que é
    s.append(
        Slide(
            "Visão geral",
            f"""
      <div class="center">
        <h2>O que é o worldcup</h2>
        <p class="big">Uma ferramenta que calcula, para os <b>104 jogos</b> de uma Copa, o placar
          que <b class="accent">rende mais pontos no bolão</b> — não o "mais provável".</p>
        <div class="row3">
          {card(_IC_BRAIN, "Modelo estatístico", "Estima a força de cada seleção a partir do histórico.")}
          {card(_IC_CHART, "Odds de mercado", "Funde a opinião das casas de aposta para mais acurácia.")}
          {card(_IC_SCALE, "Valor esperado", "Escolhe o placar que maximiza os pontos do bolão.")}
        </div>
      </div>""",
        )
    )

    # 3 — Sistema I / valor esperado
    s.append(
        Slide(
            "Conceito 01 · Pontuação",
            """
      <div class="split">
        <div>
          <h2>Não é o mais provável.<br>É o mais <span class="accent">valioso</span>.</h2>
          <p>O bolão (Sistema I) dá <b>mais pontos a resultados raros</b>. Então o palpite certo nem
            sempre é o favorito: às vezes vale arriscar, porque o ganho compensa a improbabilidade.</p>
          <p class="muted">A ferramenta varre todos os placares possíveis e devolve o que maximiza os
            <b>pontos esperados</b> — risco calculado, não chute.</p>
        </div>
        <div class="formula">
          <div class="fbig">E[pontos]</div>
          <div class="fsub">máximo</div>
          <div class="fnote">probabilidade × pontos, somado sobre todos os placares</div>
        </div>
      </div>""",
        )
    )

    # 4 — zebra vale mais
    s.append(
        Slide(
            "Conceito 02 · Zebra",
            f"""
      <div class="center">
        <h2>Zebra vale <span class="upset">muito</span> mais</h2>
        <p class="big">A pontuação-base cresce com <b>1 / probabilidade</b>: acertar um favorito óbvio
          vale pouco; cravar uma surpresa vale uma fortuna.</p>
        {bar_compare()}
        <p class="muted">Por isso o palpite inteligente <b>não é tímido</b> — quando a conta fecha,
          ele toma o risco.</p>
      </div>""",
        )
    )

    # 5 — Dixon-Coles
    s.append(
        Slide(
            "Conceito 03 · O modelo",
            f"""
      <div class="split">
        <div>
          <h2>Dixon–Coles:<br>ataque × defesa</h2>
          <p>Cada seleção tem dois "poderes": <b>ataque</b> (fazer gols) e <b>defesa</b> (sofrer
            menos). O modelo combina os dois e gera uma <b>matriz de placares</b> — a chance de cada
            resultado (0×0, 1×0, 2×1…). Daí escolhe o mais valioso.</p>
          <p class="muted">Treina o histórico de seleções <b>desde 2006</b>; jogos recentes pesam mais
            e Copa pesa mais que amistoso. Reconhece quem "vem em forma".</p>
        </div>
        <div class="matrix">
          <div class="mtitle">{_IC_BALL} matriz de placares</div>
          <div class="grid5">
            <span></span><span>0</span><span>1</span><span>2</span><span>3</span>
            <span>0</span><i style="--p:.10"></i><i style="--p:.16"></i><i style="--p:.09"></i><i style="--p:.03"></i>
            <span>1</span><i style="--p:.14"></i><i style="--p:.20"></i><i style="--p:.11"></i><i style="--p:.04"></i>
            <span>2</span><i style="--p:.07"></i><i style="--p:.10"></i><i style="--p:.06"></i><i style="--p:.02"></i>
            <span>3</span><i style="--p:.02"></i><i style="--p:.03"></i><i style="--p:.02"></i><i style="--p:.01"></i>
          </div>
          <div class="mfoot">mais escuro = mais provável</div>
        </div>
      </div>""",
        )
    )

    # 6 — blend
    s.append(
        Slide(
            "Conceito 04 · Blend",
            f"""
      <div class="center">
        <h2>Modelo <span class="home">+</span> mercado <span class="accent">conversando</span></h2>
        <p class="big">O modelo é bom, mas cego a escalação, lesão e motivação. As <b>odds de mercado</b>
          enxergam isso. O blend funde as duas opiniões.</p>
        <div class="flow">
          <span class="fstep">odds da casa</span><span class="farr">→</span>
          <span class="fstep">tira a margem<small>(des-vig)</small></span><span class="farr">→</span>
          <span class="fstep accent">funde com o modelo<small>(peso 0,6)</small></span><span class="farr">→</span>
          <span class="fstep">palpite mais preciso</span>
        </div>
        <p class="muted">Sem odds? O modelo roda sozinho — <b>degradação graciosa</b>. {_IC_REFRESH}</p>
      </div>""",
        )
    )

    # 7 — realimentação / as-of
    s.append(
        Slide(
            "Conceito 05 · Tempo",
            f"""
      <div class="split">
        <div>
          <h2>{_IC_REFRESH} Aprende a cada rodada</h2>
          <p>Conforme a Copa acontece, os placares reais entram no treino com <b>peso extra</b>. O
            modelo capta a forma das seleções <b>neste torneio</b> — depois de 2–3 rodadas, fica bem
            mais preciso.</p>
        </div>
        <div>
          <h2>{_IC_REWIND} Rebobina o tempo</h2>
          <p>O modo <code>--as-of</code> reconstrói o palpite <b>como estava na manhã de um jogo</b>
            (só com o que se sabia até a véspera). Serve para medir sua eficiência, auditar decisões e
            validar o modelo <b>sem vazar o futuro</b>.</p>
        </div>
      </div>""",
        )
    )

    # 8 — diferenciais
    s.append(
        Slide(
            "Diferenciais",
            f"""
      <div class="center">
        <h2>O que torna especial</h2>
        <div class="row4">
          {card(_IC_INFINITY, "Agnóstico à edição", "Nenhum ano no código. Copa nova = só uma pasta de dados.")}
          {card(_IC_SCALE, "Honestidade científica", "Limitações documentadas; calibração medida em 4 Copas.")}
          {card(_IC_REFRESH, "Realimentação", "Repalpita rodada a rodada com os resultados reais.")}
          {card(_IC_REWIND, "Reprodutibilidade", "Ambiente travado; qualquer run é reproduzível anos depois.")}
        </div>
      </div>""",
        )
    )

    # 9 — resultados campanha
    s.append(
        Slide(
            f"Resultados · campanha 2026 ({AS_OF})",
            f"""
      <div class="center">
        <h2>A campanha 2026 — fase de grupos encerrada</h2>
        <div class="stats">
          {stat("2", "2", "lugar de 60", suffix="º")}
          {stat("235", "235", "pontos (72 de 104 jogos)")}
          {stat("103", "103", "de eficiência*", suffix="%")}
        </div>
        <p class="muted">*eficiência ≈ quanto dos pontos que o tool renderia você capturou (segue o blend).</p>
        <div class="champwrap"><div class="cwtitle">{_IC_TROPHY} favoritos ao título</div>{champ_bars()}</div>
      </div>""",
        )
    )

    # 9b — balanço da fase de grupos + expectativa do mata-mata
    s.append(
        Slide(
            "Balanço · fase de grupos",
            f"""
      <div class="center">
        <h2>72 jogos depois: o <span class="accent">mapa do mata-mata</span></h2>
        <div class="row2">
          <div class="panel">
            <div class="ptitle">{_IC_BALL} a fase de grupos</div>
            <div class="stats mini">
              {stat("72", "72", "jogos disputados")}
              {stat("32", "32", "classificados · 16 caem")}
            </div>
            <p class="muted"><b>28% de empates</b> (20/72) — a marca desta Copa; com o scorer
              corrigido, o modelo voltou a palpitá-los.</p>
            <p class="muted">Zebra da fase: <b>Cabo Verde</b> passou em 2º <b>no grupo da Espanha</b> —
              "zebra vale mais" na prática.</p>
          </div>
          <div class="panel">
            <div class="ptitle">{_IC_TROPHY} o que esperar</div>
            {champ_bars([("Argentina", 30), ("Espanha", 20), ("França", 12)])}
            <p class="muted">final prevista: <b>Espanha × Argentina</b> → <b class="accent">Argentina</b> campeã.</p>
            <p class="muted">jogos para ficar de olho: <b>Brasil × Japão</b>, Holanda × Marrocos (57%),
              Costa do Marfim × Noruega (52%).</p>
          </div>
        </div>
        <p class="muted">Agora cada jogo do mata-mata vale <b>2× / 4×</b> — é onde o bolão se decide.</p>
      </div>""",
        )
    )

    # 10 — o modelo funciona
    s.append(
        Slide(
            "Resultados · validação",
            f"""
      <div class="center">
        <h2>O blend <span class="accent">funciona</span> — e está medido</h2>
        <div class="row2">
          <div class="panel">
            <div class="ptitle">{_IC_CHART} Erro de previsão (Brier · menor = melhor)</div>
            <div class="vs">
              <div class="vrow"><span>modelo puro</span><span class="vtrack"><i style="width:100%"
                class="away"></i></span><b>0,442</b></div>
              <div class="vrow"><span>com blend</span><span class="vtrack"><i style="width:95%"
                class="home"></i></span><b class="accent">0,418</b></div>
            </div>
            <p class="muted">49 jogos rastreados · o blend reduz o erro a cada rodada.</p>
          </div>
          <div class="panel">
            <div class="ptitle">{_IC_SCALE} Backtest em 4 Copas (2010–22)</div>
            <div class="stats mini">
              {stat("578", "578", "Brier (256 jogos)", cls="ok")}
              {stat("256", "256", "jogos avaliados")}
            </div>
            <p class="muted">0,578 &lt; 0,667 (palpite cego): o modelo tem resolução real.</p>
          </div>
        </div>
      </div>""",
        )
    )

    # 11 — bug ENG-23
    s.append(
        Slide(
            "Bastidores · ENG-23",
            """
      <div class="split">
        <div>
          <h2>O bug que achamos<br>— e corrigimos</h2>
          <p>A régua de pontos somava os bônus de placar. O app, na verdade, dá <b>só o maior nível</b>.
            Descobrimos ao <b>cruzar com as telas reais do app</b>.</p>
          <p class="muted">Travado por <b>testes de ouro</b> (12 jogos do app viram regressão). Honestidade
            e rigor &gt; varrer pra baixo do tapete.</p>
        </div>
        <div class="beforeafter">
          <div class="ba wrong"><span>antes (errado)</span><b>13 pts</b>
            <small>Curaçao 0×2 cravado</small></div>
          <div class="baarrow">→</div>
          <div class="ba right"><span>app (correto)</span><b class="accent">7 pts</b>
            <small>base + exato, sem somar</small></div>
        </div>
      </div>""",
        )
    )

    # 12 — evolução / lições da Copa 2026
    s.append(
        Slide(
            "Evolução & lições · Copa 2026",
            f"""
      <div class="center">
        <h2>O que a Copa nos ensinou</h2>
        {
                timeline(
                    [
                        (
                            "13–17/06",
                            "Risco não é alavanca; acurácia é.",
                            "Subir a ousadia piora a chance de top-10. Ficamos no fiel.",
                        ),
                        (
                            "19/06",
                            "A fraqueza é o empate, não o placar exato.",
                            "Os erros eram empates — variância, não viés. Não forçar.",
                        ),
                        (
                            "rodada a rodada",
                            "Deixe o mercado corrigir o modelo.",
                            "O blend com odds melhora o Brier a cada rodada.",
                        ),
                        (
                            "26/06",
                            "Confie nos dados crus.",
                            "O bug de pontuação só apareceu nas telas do app.",
                        ),
                        (
                            "26/06",
                            "Aceitar limites com honestidade.",
                            "Parte da pontuação do app é inobservável — calcular + avisar.",
                        ),
                    ]
                )
            }
        <p class="muted">Hoje: <b>23 melhorias de engenharia entregues</b>, cobertura de testes 86%,
          CI em duas versões de Python. Rigor é consequência das lições, não enfeite.</p>
      </div>""",
        )
    )

    # 13 — honestidade científica
    s.append(
        Slide(
            "Honestidade",
            """
      <div class="center">
        <h2>Não promete acertar.<br>Promete <span class="accent">valor esperado</span>.</h2>
        <p class="big">As limitações são <b>documentadas</b>, não escondidas:</p>
        <div class="row2 lim">
          <div class="limcard"><b>Baseado em resultados</b><span>Favorece quem vem bem; pode subestimar
            potência em má fase recente.</span></div>
          <div class="limcard"><b>Empates</b><span>O otimizador raramente crava empate — monitorado por
            alerta estatístico.</span></div>
          <div class="limcard"><b>Desempates de grupo</b><span>Simplificados (sem confronto direto
            oficial).</span></div>
          <div class="limcard"><b>Melhores 3ºs</b><span>Aproxima o Annex C; a alocação oficial da
            combinação realizada é cravada.</span></div>
        </div>
      </div>""",
        )
    )

    # 14 — futuro
    s.append(
        Slide(
            "Futuro · próximas Copas",
            f"""
      <div class="split">
        <div>
          <h2>Código <span class="accent">eterno</span></h2>
          <p>Em 2030, 2034, 2038… basta criar <code>data/editions/&lt;ano&gt;/</code> com os novos
            dados. <b>O código não muda</b>. É um motor que serve qualquer Copa.</p>
          <p class="muted">Ideias no radar: fusão com mais casas de odds, monitores automáticos, e
            estender o motor para ligas e torneios além da Copa.</p>
        </div>
        <div class="years">
          <span class="year on">{_IC_TROPHY} 2026</span>
          <span class="year">2030</span><span class="year">2034</span><span class="year">2038</span>
          <div class="yearnote">mesmo código · só dados novos</div>
        </div>
      </div>""",
        )
    )

    # 15 — encerramento + créditos
    s.append(
        Slide(
            "Obrigado",
            f"""
      {photo_bg("pitch-wembley.jpg")}
      <div class="center end">
        <div class="badge">{_IC_TROPHY} worldcup · {VERSION}</div>
        <h1>A alavanca é <span class="accent">acurácia</span>,<br>não ousadia.</h1>
        <p class="lede">Um modelo honesto, reprodutível e agnóstico à edição — pronto para a próxima Copa.</p>
        <p class="credits">Dados: martj42/international_results (CC0) · odds: The Odds API ·
          gerado por <code>scripts/build_presentation.py</code>.<br>
          Fotos: estádio à noite por Krzysztof Popławski (CC BY 4.0) · Wembley por Alex Kinney
          (CC BY-SA 2.0), via Wikimedia Commons.</p>
      </div>""",
        )
    )

    return s


# --------------------------------------------------------------------------- CSS / JS / render

_CSS = """
:root{
  --bg:#0a0e14; --panel:#121826; --panel2:#0e1421; --ink:#e8edf4; --muted:#8b97a8;
  --home:#3b82f6; --away:#ef4444; --upset:#f59e0b; --accent:#22d3ee; --line:#1e293b;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  background:#05080d;color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  display:flex;align-items:center;justify-content:center;overflow:hidden;
  min-height:100vh;min-height:100dvh; /* dvh: desconta a barra do navegador mobile (vh fica atrás dela) */
}
.stage{
  position:relative;
  /* dvh garante que o palco (e o rodapé no fundo dele) caiba na área VISÍVEL no mobile/paisagem */
  width:min(100vw,177.78vh);height:min(56.25vw,100vh);
  width:min(100dvw,177.78dvh);height:min(56.25dvw,100dvh);
  container-type:size;display:flex;flex-direction:column;overflow:hidden;
  background:
    radial-gradient(120% 90% at 50% -20%, #14233a 0%, #0a0e14 55%, #070b12 100%);
  box-shadow:0 0 90px #000c, inset 0 0 0 1px #ffffff08;
}
.stage::before{
  content:"";position:absolute;inset:0;pointer-events:none;opacity:.5;
  background:
    repeating-linear-gradient(90deg,#ffffff05 0 1px,transparent 1px 64px),
    radial-gradient(80% 60% at 50% 120%, #22d3ee14, transparent 70%);
}
/* ---- chrome: header / footer ---- */
.topbar,.bottombar{
  position:relative;z-index:3;display:flex;align-items:center;
  padding:0 4cqw;height:9cqh;font-size:1.25cqw;color:var(--muted);
}
.topbar{justify-content:space-between;border-bottom:1px solid var(--line)}
.brand{font-weight:700;color:var(--ink);letter-spacing:.04em}
.brand .dot{color:var(--accent)}
#kicker{text-transform:uppercase;letter-spacing:.12em;font-size:1.05cqw}
.tright{display:flex;align-items:center;gap:1.4cqw}
.dots{display:flex;gap:.7cqw}
.dot-i{width:.9cqw;height:.9cqw;border-radius:50%;background:#28344a;cursor:pointer;
  transition:background .25s,transform .25s;border:0;padding:0}
.dot-i:hover{background:#3b4a66}
.dot-i.on{background:var(--accent);transform:scale(1.25);box-shadow:0 0 8px var(--accent)}
.counter{font-variant-numeric:tabular-nums;color:var(--ink);font-weight:600}
.counter b{color:var(--accent)}
.bottombar{justify-content:space-between;border-top:1px solid var(--line)}
.nav{display:inline-flex;align-items:center;gap:.6cqw;background:#141d2e;color:var(--ink);
  border:1px solid var(--line);border-radius:999px;padding:1cqh 1.6cqw;cursor:pointer;
  font-size:1.2cqw;font-family:inherit;transition:background .2s,border-color .2s}
.nav:hover{background:#1b2740;border-color:var(--accent)}
.nav:disabled{opacity:.35;cursor:default}
.footcenter{flex:1;display:flex;flex-direction:column;align-items:center;gap:.8cqh;margin:0 3cqw}
.pbar{width:100%;height:.5cqh;background:#1a2334;border-radius:999px;overflow:hidden}
.pbar i{display:block;height:100%;width:0;border-radius:999px;
  background:linear-gradient(90deg,var(--home),var(--accent));transition:width .35s ease}
.foot-credit{font-size:1cqw;color:#54627a;letter-spacing:.04em}
/* ---- deck / slides ---- */
.deck{position:relative;flex:1;z-index:2;overflow:hidden}
.slide{position:absolute;inset:0;padding:4cqh 6cqw;display:flex;flex-direction:column;
  justify-content:center;gap:.4cqh;opacity:0;transform:translateY(2.5cqh);pointer-events:none;
  transition:opacity .35s ease,transform .35s ease}
.slide.on{opacity:1;transform:none;pointer-events:auto}
/* ---- tipografia ---- */
h1{font-size:5.4cqw;line-height:1.05;font-weight:800;letter-spacing:-.01em}
h2{font-size:3.6cqw;line-height:1.08;font-weight:800;margin-bottom:1.6cqh;letter-spacing:-.01em}
p{font-size:1.85cqw;line-height:1.5;color:#cbd5e1;max-width:62cqw}
p.big{font-size:2.3cqw;color:var(--ink);margin-bottom:2cqh}
p.lede{font-size:2cqw;color:#cbd5e1;max-width:60cqw;margin-top:1.5cqh}
p.muted{color:var(--muted);font-size:1.6cqw;margin-top:1.8cqh}
.accent{color:var(--accent)} .home{color:var(--home)} .away{color:var(--away)} .upset{color:var(--upset)}
code{background:#0e1626;border:1px solid var(--line);border-radius:5px;padding:.1em .35em;
  font-size:.92em;color:#a5f3ef}
b{color:#f1f5f9}
.center{align-items:flex-start;position:relative;z-index:2}
.split{position:relative;z-index:2}
/* ---- capa / fundos fotográficos ---- */
.hero{position:absolute;inset:0;width:100%;height:100%;z-index:0;opacity:.9}
.bgphoto{position:absolute;inset:0;z-index:0;background-size:cover;background-position:center;opacity:.5}
.bgphoto.on-hero{opacity:.78}
.scrim{position:absolute;inset:0;z-index:1;
  background:linear-gradient(180deg,#05080db3 0%,#05080d66 42%,#0a0e14ee 100%)}
.scrim.soft{background:radial-gradient(135% 115% at 50% 45%,#05080d40 0%,#0a0e14ee 100%)}
.cover{position:relative;z-index:2}
.badge{display:inline-flex;align-items:center;gap:.6cqw;font-size:1.3cqw;color:#bfe9f5;
  background:#0c2330;border:1px solid #14455a;border-radius:999px;padding:.9cqh 1.4cqw;
  margin-bottom:2.4cqh;letter-spacing:.04em}
.hint{margin-top:3cqh;font-size:1.2cqw;color:#6b7a93;letter-spacing:.06em}
.end{align-items:flex-start}
.credits{font-size:1.25cqw;color:#54627a;margin-top:2.6cqh}
/* ---- ícones ---- */
.ic{vertical-align:-.15em}
.cardic{font-size:2.6cqw;margin-bottom:.8cqh;display:block}
/* ---- cards ---- */
.row2,.row3,.row4{display:grid;gap:1.6cqw;margin-top:2.4cqh;width:100%}
.row2{grid-template-columns:1fr 1fr}
.row3{grid-template-columns:repeat(3,1fr)}
.row4{grid-template-columns:repeat(4,1fr)}
.card{background:#0d1726cc;border:1px solid var(--line);border-radius:14px;padding:2.2cqh 1.6cqw;
  display:flex;flex-direction:column;gap:.5cqh}
.card b{font-size:1.7cqw} .card span{font-size:1.35cqw;color:var(--muted);line-height:1.4}
/* ---- split ---- */
.split{display:grid;grid-template-columns:1fr 1fr;gap:4cqw;align-items:center}
.split>div>h2+*{margin-top:1cqh}
.split h2{font-size:3.2cqw}
/* ---- zebra bars ---- */
.bars{display:flex;flex-direction:column;gap:1.6cqh;margin:1cqh 0 0;width:100%}
.barrow{display:grid;grid-template-columns:26cqw 1fr auto;align-items:center;gap:1.4cqw}
.blabel{font-size:1.5cqw;color:#cbd5e1}
.btrack{height:2.2cqh;background:#16202f;border-radius:999px;overflow:hidden}
.btrack i{display:block;height:100%;border-radius:999px}
.btrack i.home{background:linear-gradient(90deg,#1d4ed8,var(--home))}
.btrack i.upset{background:linear-gradient(90deg,#b45309,var(--upset))}
.bpts{font-size:1.8cqw;font-weight:800;font-variant-numeric:tabular-nums}
/* ---- formula ---- */
.formula{background:#0c1422;border:1px solid var(--line);border-radius:18px;padding:4cqh 2cqw;
  text-align:center}
.fbig{font-size:5cqw;font-weight:800;color:var(--accent)}
.fsub{font-size:1.6cqw;color:var(--muted);letter-spacing:.3em;text-transform:uppercase}
.fnote{font-size:1.3cqw;color:#7b8aa3;margin-top:1.4cqh}
/* ---- matrix ---- */
.matrix{background:#0c1422;border:1px solid var(--line);border-radius:16px;padding:2.4cqh 1.8cqw}
.mtitle{font-size:1.4cqw;color:var(--muted);margin-bottom:1.4cqh;display:flex;align-items:center;gap:.5cqw}
.grid5{display:grid;grid-template-columns:repeat(5,1fr);gap:.5cqw;font-size:1.2cqw;color:var(--muted)}
.grid5 span{display:flex;align-items:center;justify-content:center}
.grid5 i{aspect-ratio:1;border-radius:5px;background:rgba(34,211,238,calc(var(--p)*4))}
.mfoot{font-size:1.1cqw;color:#647189;margin-top:1.2cqh;text-align:center}
/* ---- flow ---- */
.flow{display:flex;align-items:center;gap:1cqw;flex-wrap:wrap;margin:1cqh 0}
.fstep{background:#0d1726;border:1px solid var(--line);border-radius:12px;padding:1.4cqh 1.4cqw;
  font-size:1.45cqw;display:flex;flex-direction:column}
.fstep.accent{border-color:#155e6b;background:#082530;color:#bdeef6}
.fstep small{color:var(--muted);font-size:1.05cqw}
.farr{color:var(--accent);font-size:2cqw}
/* ---- stats / counters ---- */
.stats{display:flex;gap:2.4cqw;margin:1.4cqh 0;flex-wrap:wrap}
.stats.mini{gap:1.6cqw;margin:1cqh 0}
.stat{background:#0d1726;border:1px solid var(--line);border-radius:16px;padding:2.2cqh 2cqw;min-width:14cqw}
.snum{font-size:5.4cqw;font-weight:800;font-variant-numeric:tabular-nums;line-height:1}
.snum.accent{color:var(--accent)} .snum.ok{color:#34d399}
.stats.mini .snum{font-size:3.6cqw}
.slab{font-size:1.35cqw;color:var(--muted);margin-top:.6cqh}
/* ---- champ ---- */
.champwrap{margin-top:2.2cqh;width:100%}
.cwtitle{font-size:1.4cqw;color:var(--muted);margin-bottom:1cqh;display:flex;align-items:center;gap:.5cqw}
.champ{display:flex;flex-direction:column;gap:.8cqh}
.crow{display:grid;grid-template-columns:12cqw 1fr 7cqw;align-items:center;gap:1.2cqw;font-size:1.5cqw}
.cname{font-weight:600}
.ctrack{height:1.8cqh;background:#16202f;border-radius:999px;overflow:hidden}
.ctrack i{display:block;height:100%;border-radius:999px;
  background:linear-gradient(90deg,#1d4ed8,var(--accent))}
.cval{text-align:right;font-variant-numeric:tabular-nums;color:#cbd5e1}
/* ---- panels (validação) ---- */
.panel{background:#0d1726;border:1px solid var(--line);border-radius:16px;padding:2.4cqh 1.8cqw}
.ptitle{font-size:1.45cqw;color:var(--muted);margin-bottom:1.6cqh;display:flex;align-items:center;gap:.5cqw}
.vs{display:flex;flex-direction:column;gap:1.2cqh}
.vrow{display:grid;grid-template-columns:9cqw 1fr auto;align-items:center;gap:1cqw;font-size:1.4cqw}
.vtrack{height:1.8cqh;background:#16202f;border-radius:999px;overflow:hidden}
.vtrack i{display:block;height:100%;border-radius:999px}
.vtrack i.home{background:linear-gradient(90deg,#1d4ed8,var(--home))}
.vtrack i.away{background:linear-gradient(90deg,#991b1b,var(--away))}
.vrow b{font-variant-numeric:tabular-nums;font-size:1.5cqw}
/* ---- before/after ---- */
.beforeafter{display:flex;align-items:center;gap:1.6cqw;justify-content:center}
.ba{background:#0d1726;border:1px solid var(--line);border-radius:16px;padding:2.6cqh 2cqw;text-align:center;flex:1}
.ba span{font-size:1.25cqw;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.ba b{display:block;font-size:4.6cqw;font-weight:800;margin:.6cqh 0;font-variant-numeric:tabular-nums}
.ba small{font-size:1.2cqw;color:#7b8aa3}
.ba.wrong{border-color:#5b2330} .ba.wrong b{color:var(--away)}
.ba.right{border-color:#155e6b}
.baarrow{font-size:2.6cqw;color:var(--accent)}
/* ---- timeline ---- */
.tl{display:flex;flex-direction:column;gap:2cqh;margin:1.4cqh 0;width:100%;
  border-left:2px solid #1e2a3e;padding-left:2.6cqw}
.tli{position:relative}
.tldot{position:absolute;left:calc(-2.6cqw - 1px);top:.5cqh;width:1.2cqw;height:1.2cqw;border-radius:50%;
  background:var(--accent);transform:translateX(-50%);box-shadow:0 0 8px var(--accent)}
.tlc{display:flex;flex-direction:column;gap:.3cqh}
.tldate{font-size:1.15cqw;color:var(--accent);letter-spacing:.06em;text-transform:uppercase}
.tlc b{font-size:1.75cqw;line-height:1.15} .tldet{font-size:1.32cqw;color:var(--muted);line-height:1.35}
/* ---- limitações ---- */
.lim{margin-top:2cqh} .limcard{background:#0d1726;border:1px solid var(--line);border-radius:12px;padding:1.8cqh 1.6cqw}
.limcard b{font-size:1.6cqw;display:block;margin-bottom:.5cqh}
.limcard span{font-size:1.3cqw;color:var(--muted);line-height:1.4}
/* ---- anos (futuro) ---- */
.years{display:flex;flex-direction:column;gap:1.2cqh;align-items:flex-start}
.year{font-size:2.4cqw;font-weight:700;color:#46566f;border:1px solid var(--line);border-radius:12px;
  padding:1cqh 2cqw}
.year.on{color:var(--ink);border-color:#155e6b;background:#082530}
.yearnote{font-size:1.3cqw;color:var(--muted);margin-top:.6cqh}
/* ---- reduced motion ---- */
@media (prefers-reduced-motion:reduce){
  .slide{transition:none} .pbar i{transition:none} .dot-i{transition:none}
}
/* ---- impressão / PDF (handout) ---- */
@media print{
  @page{size:A4 landscape;margin:1cm}
  body{background:#fff;display:block;height:auto;overflow:visible}
  .stage{width:100%;height:auto;display:block;box-shadow:none;background:#fff;container-type:normal}
  .stage::before{display:none}
  .topbar,.bottombar{display:none}
  .deck{position:static}
  .slide{position:relative;inset:auto;opacity:1;transform:none;break-after:page;
    min-height:18cm;border:1px solid #ddd;border-radius:10px;margin-bottom:.6cm;padding:1.4cm;
    color:#0a0e14;font-size:11pt}
  .slide h1,.slide h2,.slide b{color:#0a0e14}
  .slide p,.muted,.slab{color:#33415a}
  .hero,.bgphoto,.scrim{display:none}
  .card,.panel,.stat,.matrix,.formula,.ba,.limcard,.fstep,.year{background:#f6f8fb;border-color:#d7deea}
  .accent{color:#0e7490}
  *{font-size:revert}
}
"""

_JS = """
(function(){
  var slides=[].slice.call(document.querySelectorAll('.slide'));
  var dots=[].slice.call(document.querySelectorAll('.dot-i'));
  var N=slides.length, i=0;
  var elPrev=document.getElementById('prev'), elNext=document.getElementById('next');
  var elKick=document.getElementById('kicker'), elNow=document.getElementById('now');
  var elBar=document.getElementById('pbar-i');
  var reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;

  function animateCounts(slide){
    var nums=[].slice.call(slide.querySelectorAll('.num[data-to]'));
    nums.forEach(function(el){
      var to=parseFloat(el.getAttribute('data-to'))||0;
      if(reduce){el.textContent=to;return;}
      var t0=null, dur=650;
      function step(ts){
        if(!t0)t0=ts; var p=Math.min(1,(ts-t0)/dur);
        var e=1-Math.pow(1-p,3);
        el.textContent=Math.round(to*e);
        if(p<1)requestAnimationFrame(step); else el.textContent=to;
      }
      el.textContent='0'; requestAnimationFrame(step);
    });
  }
  function show(n,push){
    i=Math.max(0,Math.min(N-1,n));
    slides.forEach(function(s,k){s.classList.toggle('on',k===i);});
    dots.forEach(function(d,k){d.classList.toggle('on',k===i);});
    elKick.textContent=slides[i].getAttribute('data-kicker')||'';
    elNow.textContent=(i+1);
    elBar.style.width=((i+1)/N*100)+'%';
    elPrev.disabled=(i===0); elNext.disabled=(i===N-1);
    animateCounts(slides[i]);
    var h='#slide-'+(i+1);
    if(push!==false && location.hash!==h) history.replaceState(null,'',h);
  }
  function next(){show(i+1);} function prev(){show(i-1);}
  elNext.onclick=next; elPrev.onclick=prev;
  dots.forEach(function(d,k){d.onclick=function(){show(k);};});
  document.addEventListener('keydown',function(e){
    if(['ArrowRight','PageDown',' '].indexOf(e.key)>=0){e.preventDefault();next();}
    else if(['ArrowLeft','PageUp'].indexOf(e.key)>=0){e.preventDefault();prev();}
    else if(e.key==='Home'){show(0);} else if(e.key==='End'){show(N-1);}
  });
  var x0=null;
  document.addEventListener('touchstart',function(e){x0=e.touches[0].clientX;},{passive:true});
  document.addEventListener('touchend',function(e){
    if(x0===null)return; var dx=e.changedTouches[0].clientX-x0;
    if(Math.abs(dx)>40){dx<0?next():prev();} x0=null;
  },{passive:true});
  window.addEventListener('hashchange',function(){
    var m=/^#slide-(\\d+)$/.exec(location.hash); if(m)show(parseInt(m[1],10)-1,false);
  });
  var m=/^#slide-(\\d+)$/.exec(location.hash);
  show(m?parseInt(m[1],10)-1:0);
})();
"""


def render_presentation(slides: list[Slide]) -> str:
    """Monta o HTML self-contained do deck a partir dos slides."""
    n = len(slides)
    dots = "".join(f'<button class="dot-i" aria-label="slide {k + 1}"></button>' for k in range(n))
    body = "".join(f'<section class="slide" data-kicker="{s.kicker}">{s.body}</section>' for s in slides)
    return (
        "<!doctype html>\n"
        '<html lang="pt-BR"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>worldcup — apresentação do projeto</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head><body>\n"
        '<div class="stage">\n'
        '  <div class="topbar">\n'
        '    <span id="kicker"></span>\n'
        '    <span class="brand">⚽ world<span class="dot">cup</span></span>\n'
        f'    <span class="tright"><span class="dots">{dots}</span>'
        f'<span class="counter"><b id="now">1</b> / {n}</span></span>\n'
        "  </div>\n"
        f'  <div class="deck">{body}</div>\n'
        '  <div class="bottombar">\n'
        '    <button class="nav" id="prev">‹ Anterior</button>\n'
        '    <div class="footcenter"><span class="pbar"><i id="pbar-i"></i></span>'
        '<span class="foot-credit">worldcup · ' + VERSION + " · 2026</span></div>\n"
        '    <button class="nav" id="next">Próximo ›</button>\n'
        "  </div>\n"
        "</div>\n"
        f"<script>{_JS}</script>\n"
        "</body></html>\n"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gera a apresentação HTML do projeto (deck autocontido)")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"destino do HTML (default: {DEFAULT_OUT})")
    p.add_argument("--docs", action="store_true", help="também grava docs/apresentacao.html (versionado)")
    args = p.parse_args(argv)

    html = render_presentation(build_slides())
    targets = [args.out] + ([DOCS_OUT] if args.docs else [])
    for path in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        print(f"💾 Apresentação: {path}  ({len(html) // 1024} KB, {len(build_slides())} slides)")
    print("   Abra no navegador · ← → para navegar · Ctrl+P para PDF/handout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
