"""
Pagina 3 do relatorio: tabela completa de gastos por dia.

Modulo separado das paginas 1 e 2 - reaproveita os helpers genericos de
dashboard_builder.py (cabecalho, titulo de secao, badge de icone, textos
truncados/ajustados, rodape), mas implementa sua propria logica de tabela
porque essa pagina tem uma particularidade que as outras duas nao tem:
pode nao caber numa unica pagina fisica (o periodo pode ter dezenas de
despesas), entao precisa paginar sozinha, repetindo o cabecalho a cada
nova pagina fisica e so mostrando o total geral e o rodape no final.

Ponto de entrada unico: desenhar_pagina_gastos_por_dia(...).
"""
from reportlab.lib import colors
from reportlab.lib.units import cm

from dash_style import moeda
from dashboard_builder import (
    ALTURA, CARD_PAD, COR_CARD_BORDA, COR_INSIGHT_BG, COR_PRIMARIA,
    COR_TEXTO, COR_TEXTO_SECUNDARIO, GAP, LARGURA, LARGURA_UTIL, MARGEM,
    _desenhar_cabecalho, _desenhar_rodape, _desenhar_titulo_secao,
    _icone_badge, _truncar_com_reticencias,
)

ALTURA_LINHA = 0.52 * cm
ALTURA_CABECALHO_TABELA = 0.55 * cm
LIMITE_INFERIOR = MARGEM + 1.0 * cm
ALTURA_BLOCO_TOTAL = 1.3 * cm
ALTURA_BLOCO_RODAPE = 1.7 * cm

# Larguras de coluna fixas (a Descrição absorve o que sobrar)
COL_DATA = 2.2 * cm
COL_METODO = 3.5 * cm
COL_CATEGORIA = 3.3 * cm
COL_VALOR = 2.3 * cm


def _posicoes_colunas():
    x_data = MARGEM
    x_valor_direita = MARGEM + LARGURA_UTIL
    x_categoria = x_valor_direita - COL_VALOR - COL_CATEGORIA
    x_metodo = x_categoria - COL_METODO
    x_descricao = x_data + COL_DATA
    largura_descricao = x_metodo - x_descricao - 0.3 * cm
    return x_data, x_descricao, largura_descricao, x_metodo, x_categoria, x_valor_direita


def _desenhar_cabecalho_tabela(c, y) -> float:
    x_data, x_descricao, _, x_metodo, x_categoria, x_valor_direita = _posicoes_colunas()
    c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x_data, y, "DATA")
    c.drawString(x_descricao, y, "DESCRIÇÃO")
    c.drawString(x_metodo, y, "MÉTODO DE PAGAMENTO")
    c.drawString(x_categoria, y, "CATEGORIA")
    c.drawRightString(x_valor_direita, y, "VALOR (R$)")
    y -= 0.18 * cm
    c.setStrokeColor(colors.HexColor(COR_CARD_BORDA))
    c.setLineWidth(0.7)
    c.line(MARGEM, y, MARGEM + LARGURA_UTIL, y)
    return y - (ALTURA_CABECALHO_TABELA - 0.18 * cm)


def _desenhar_linha_despesa(c, d, y, nome_categoria_fn, icone_categoria_fn, cor_categoria_fn,
                             nome_metodo_fn, icone_metodo_fn, cor_metodo_fn):
    x_data, x_descricao, largura_descricao, x_metodo, x_categoria, x_valor_direita = _posicoes_colunas()

    c.setFillColor(colors.HexColor(COR_TEXTO))
    c.setFont("Helvetica", 8.3)
    c.drawString(x_data, y, d["data_despesa"].strftime("%d/%m/%Y"))

    desc_final = _truncar_com_reticencias(c, d["descricao"], "Helvetica", 8.3, largura_descricao)
    c.drawString(x_descricao, y, desc_final)

    metodo = d.get("metodo_pagamento")
    if metodo:
        _icone_badge(c, x_metodo + 0.1 * cm, y + 0.08 * cm, 0.2 * cm, icone_metodo_fn(metodo), cor_icone=COR_PRIMARIA)
        nome_met = _truncar_com_reticencias(c, nome_metodo_fn(metodo), "Helvetica", 8.3, COL_METODO - 0.5 * cm)
        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica", 8.3)
        c.drawString(x_metodo + 0.35 * cm, y, nome_met)
    else:
        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.drawString(x_metodo, y, "—")

    cat = d["categoria"]
    _icone_badge(c, x_categoria + 0.1 * cm, y + 0.08 * cm, 0.2 * cm, icone_categoria_fn(cat), cor_icone=COR_PRIMARIA)
    nome_cat = _truncar_com_reticencias(c, nome_categoria_fn(cat), "Helvetica", 8.3, COL_CATEGORIA - 0.5 * cm)
    c.setFillColor(colors.HexColor(COR_TEXTO))
    c.setFont("Helvetica", 8.3)
    c.drawString(x_categoria + 0.35 * cm, y, nome_cat)

    c.setFont("Helvetica-Bold", 8.3)
    c.drawRightString(x_valor_direita, y, moeda(float(d["valor"])))

    c.setStrokeColor(colors.HexColor("#F0F2F5"))
    c.setLineWidth(0.5)
    c.line(MARGEM, y - 0.16 * cm, MARGEM + LARGURA_UTIL, y - 0.16 * cm)


def _desenhar_total_geral(c, y, total: float) -> float:
    altura = 1.0 * cm
    y_caixa = y - altura
    c.setFillColor(colors.HexColor(COR_INSIGHT_BG))
    c.roundRect(MARGEM, y_caixa, LARGURA_UTIL, altura, 0.12 * cm, stroke=0, fill=1)
    _icone_badge(c, MARGEM + 0.55 * cm, y_caixa + altura / 2, 0.3 * cm, "wallet")
    c.setFillColor(colors.HexColor(COR_TEXTO))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGEM + 1.0 * cm, y_caixa + altura / 2 - 0.15 * cm, "TOTAL GERAL DO PERÍODO")
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(MARGEM + LARGURA_UTIL - 0.5 * cm, y_caixa + altura / 2 - 0.17 * cm, moeda(total))
    return y_caixa - GAP


def desenhar_pagina_gastos_por_dia(
    c,
    mes_ano_titulo: str,
    data_inicio: str,
    data_fim: str,
    despesas: list[dict],
    total: float,
    data_geracao: str,
    dica: str,
    nome_categoria_fn,
    icone_categoria_fn,
    cor_categoria_fn,
    nome_metodo_fn,
    icone_metodo_fn,
    cor_metodo_fn,
) -> None:
    """
    Desenha a página 3 (tabela completa de gastos por dia) na página
    CORRENTE do canvas — quem chama já deve ter feito c.showPage() antes.

    Pode ocupar mais de uma página física de PDF se o período tiver muitas
    despesas: o cabeçalho é redesenhado a cada nova página física, e o
    total geral + rodapé só aparecem depois da última linha.
    """
    despesas_ordenadas = sorted(despesas, key=lambda d: d["data_despesa"])

    def novo_cabecalho() -> float:
        y = ALTURA - MARGEM
        y = _desenhar_cabecalho(
            c, mes_ano_titulo, data_inicio, data_fim, y,
            icone_card="invoice", linha1_card="Detalhamento completo",
            linha2_card="dos gastos por dia.",
        )
        _desenhar_titulo_secao(c, MARGEM, y, "GASTOS POR DIA")
        y -= 0.5 * cm
        y = _desenhar_cabecalho_tabela(c, y)
        return y

    y = novo_cabecalho()

    for d in despesas_ordenadas:
        if y - ALTURA_LINHA < LIMITE_INFERIOR:
            c.showPage()
            y = novo_cabecalho()
        _desenhar_linha_despesa(
            c, d, y, nome_categoria_fn, icone_categoria_fn, cor_categoria_fn,
            nome_metodo_fn, icone_metodo_fn, cor_metodo_fn,
        )
        y -= ALTURA_LINHA

    if y - ALTURA_BLOCO_TOTAL - ALTURA_BLOCO_RODAPE < MARGEM:
        c.showPage()
        y = novo_cabecalho()

    y = _desenhar_total_geral(c, y, total)
    _desenhar_rodape(c, dica, data_geracao, y)
