"""Paleta e constantes de estilo do dashboard (tema navy/azul, inspirado no
template de referência fornecido)."""

COR_TITULO = "#16213E"
COR_PRIMARIA = "#1B3A6B"
COR_SECUNDARIA = "#2F6FD4"
COR_TEXTO = "#1F2937"
COR_TEXTO_SECUNDARIO = "#6B7280"
COR_ICONE_BG = "#E7EEFC"
COR_CARD_BORDA = "#E5E9F0"
COR_INSIGHT_BG = "#EEF3FC"
COR_FOOTER_BG = "#EEF3FC"
COR_TRILHO_BARRA = "#EEF1F6"

CORES_CATEGORIA = {
    "alimentacao": "#16325C",
    "moradia": "#2E5FA3",
    "transporte": "#5B9BD5",
    "lazer": "#4CAF7D",
    "saude": "#F2A541",
    "compras": "#C2699A",
    "educacao": "#7C6FD4",
    "assinaturas": "#4FB6AE",
    "outros": "#B9BEC7",
}

NOMES_CATEGORIA = {
    "alimentacao": "Alimentação",
    "moradia": "Moradia",
    "transporte": "Transporte",
    "lazer": "Lazer",
    "saude": "Saúde",
    "compras": "Compras",
    "educacao": "Educação",
    "assinaturas": "Assinaturas",
    "outros": "Outros",
}

ICONE_CATEGORIA = {
    "alimentacao": "fork",
    "moradia": "house",
    "transporte": "car",
    "lazer": "music",
    "saude": "heart",
    "compras": "bag",
    "educacao": "book",
    "assinaturas": "refresh",
    "outros": "dots",
}


def nome_categoria(nome: str) -> str:
    return NOMES_CATEGORIA.get(nome, nome.capitalize())


def cor_categoria(nome: str) -> str:
    return CORES_CATEGORIA.get(nome, "#B9BEC7")


def icone_categoria(nome: str) -> str:
    return ICONE_CATEGORIA.get(nome, "dots")


# ---------------------------------------------------------------------------
# Métodos de pagamento (página 2 do relatório)
# ---------------------------------------------------------------------------

CORES_METODO_PAGAMENTO = {
    "pix": "#2E6FF2",
    "credito": "#22A559",
    "debito": "#8B5CF6",
    "dinheiro": "#F2A541",
    "boleto": "#EC4899",
    "debito_automatico": "#06B6D4",
    "faturamento": "#F43F5E",
    "ted": "#84A414",
    "vale_refeicao": "#FB923C",
    "vale_alimentacao": "#14B8A6",
    "outros": "#B9BEC7",
}

NOMES_METODO_PAGAMENTO = {
    "pix": "Pix",
    "credito": "Cartão de Crédito",
    "debito": "Cartão de Débito",
    "dinheiro": "Dinheiro",
    "boleto": "Boleto",
    "debito_automatico": "Débito Automático",
    "faturamento": "Faturamento",
    "ted": "TED",
    "vale_refeicao": "Vale-Refeição",
    "vale_alimentacao": "Vale-Alimentação",
    "outros": "Outros",
}

ICONE_METODO_PAGAMENTO = {
    "pix": "bolt",
    "credito": "card",
    "debito": "card",
    "dinheiro": "banknote",
    "boleto": "barcode",
    "debito_automatico": "refresh",
    "faturamento": "invoice",
    "ted": "transfer",
    "vale_refeicao": "ticket",
    "vale_alimentacao": "ticket",
    "outros": "dots",
}


def nome_metodo_pagamento(nome: str) -> str:
    return NOMES_METODO_PAGAMENTO.get(nome, nome.replace("_", " ").capitalize())


def cor_metodo_pagamento(nome: str) -> str:
    return CORES_METODO_PAGAMENTO.get(nome, "#B9BEC7")


def icone_metodo_pagamento(nome: str) -> str:
    return ICONE_METODO_PAGAMENTO.get(nome, "dots")


def moeda(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")