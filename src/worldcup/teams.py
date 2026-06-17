"""Normalização de nomes de seleções e nomes de exibição em português.

O nome **canônico** interno é o usado pelo dataset histórico (em inglês). Os arquivos de
dados das edições (`groups.csv`, `fixtures.csv`) usam esses nomes canônicos, e a exibição
em português é resolvida por `display()` na hora de imprimir/gravar os palpites.
"""

from __future__ import annotations

# Aliases de variações encontradas em fontes -> nome canônico (do dataset martj42).
# Mantido enxuto: o dataset já é bastante consistente para o período recente.
_ALIASES: dict[str, str] = {
    "Türkiye": "Turkey",
    "Turkiye": "Turkey",
    "Czechia": "Czech Republic",
    "Korea Republic": "South Korea",
    "Republic of Korea": "South Korea",
    "USA": "United States",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",  # forma com & (The Odds API)
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Cabo Verde": "Cape Verde",
    "DR Congo": "DR Congo",
    "Congo DR": "DR Congo",
}

# Nomes de exibição em português (canônico em inglês -> pt-BR).
_PT_DISPLAY: dict[str, str] = {
    "Algeria": "Argélia",
    "Argentina": "Argentina",
    "Australia": "Austrália",
    "Austria": "Áustria",
    "Belgium": "Bélgica",
    "Bosnia and Herzegovina": "Bósnia e Herzegovina",
    "Brazil": "Brasil",
    "Canada": "Canadá",
    "Cape Verde": "Cabo Verde",
    "Colombia": "Colômbia",
    "Croatia": "Croácia",
    "Curaçao": "Curaçao",
    "Czech Republic": "República Tcheca",
    "DR Congo": "RD Congo",
    "Ecuador": "Equador",
    "Egypt": "Egito",
    "England": "Inglaterra",
    "France": "França",
    "Germany": "Alemanha",
    "Ghana": "Gana",
    "Haiti": "Haiti",
    "Iran": "Irã",
    "Iraq": "Iraque",
    "Ivory Coast": "Costa do Marfim",
    "Japan": "Japão",
    "Jordan": "Jordânia",
    "Mexico": "México",
    "Morocco": "Marrocos",
    "Netherlands": "Holanda",
    "New Zealand": "Nova Zelândia",
    "Norway": "Noruega",
    "Panama": "Panamá",
    "Paraguay": "Paraguai",
    "Portugal": "Portugal",
    "Qatar": "Catar",
    "Saudi Arabia": "Arábia Saudita",
    "Scotland": "Escócia",
    "Senegal": "Senegal",
    "South Africa": "África do Sul",
    "South Korea": "Coreia do Sul",
    "Spain": "Espanha",
    "Sweden": "Suécia",
    "Switzerland": "Suíça",
    "Tunisia": "Tunísia",
    "Turkey": "Turquia",
    "United States": "Estados Unidos",
    "Uruguay": "Uruguai",
    "Uzbekistan": "Uzbequistão",
    # extras úteis em histórico/edições antigas
    "Italy": "Itália",
    "Poland": "Polônia",
    "Denmark": "Dinamarca",
    "Russia": "Rússia",
    "Serbia": "Sérvia",
    "Nigeria": "Nigéria",
    "Cameroon": "Camarões",
    "Costa Rica": "Costa Rica",
    "Wales": "País de Gales",
}


def canonical(name: str) -> str:
    """Retorna o nome canônico de uma seleção, resolvendo aliases conhecidos."""
    n = name.strip()
    return _ALIASES.get(n, n)


def display(name: str) -> str:
    """Nome de exibição em português; cai no canônico se não houver tradução."""
    return _PT_DISPLAY.get(canonical(name), name)
