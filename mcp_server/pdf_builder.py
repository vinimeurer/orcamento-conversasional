"""
Módulo de montagem do PDF do relatório de gastos.

Usa o chart_builder para os gráficos e monta o layout final: cabeçalho de
marca, cards de KPI, seções com gráficos, tabela de detalhamento e rodapé
com paginação — tudo com a paleta definida em chart_builder.
"""
import functools

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from chart_builder import (
    COR_FUNDO_CARD, COR_NEGATIVO, COR_POSITIVO, COR_PRIMARIA,
    COR_PRIMARIA_CLARA, COR_TEXTO, COR_TEXTO_SECUNDARIO,
    grafico_comparacao_periodos, grafico_distribuicao_categoria,
    grafico_evolucao_diaria, _cor_categoria, nome_categoria,
)

LARGURA_PAGINA, ALTURA_PAGINA = A4
MARGEM = 2 * cm
ALTURA_FAIXA_TOPO = 2.9 * cm


# ---------------------------------------------------------------------------
# Card de KPI (flowable customizado — rounded rect desenhado direto no canvas)
# ---------------------------------------------------------------------------

class CardKPI(Flowable):
    def __init__(self, width, height, titulo, valor, subtitulo=None, cor=COR_PRIMARIA):
        super().__init__()
        self.width = width
        self.height = height
        self.titulo = titulo
        self.valor = valor
        self.subtitulo = subtitulo
        self.cor = cor

    def draw(self):
        c = self.canv
        c.setFillColor(colors.HexColor(COR_FUNDO_CARD))
        c.roundRect(0, 0, self.width, self.height, radius=6, fill=1, stroke=0)

        c.setFillColor(colors.HexColor(self.cor))
        c.roundRect(0, self.height - 5, self.width, 5, radius=2.5, fill=1, stroke=0)
        # cobre os cantos de baixo do topo pra não ficarem arredondados
        c.rect(0, self.height - 5, self.width, 2.5, fill=1, stroke=0)

        pad = 0.4 * cm
        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.setFont("Helvetica", 9.5)
        c.drawString(pad, self.height - 1.0 * cm, self.titulo.upper())

        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica-Bold", 16)
        c.drawString(pad, self.height - 1.75 * cm, self.valor)

        if self.subtitulo:
            c.setFillColor(colors.HexColor(self.cor))
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(pad, pad, self.subtitulo)


def _linha_cards(cards: list[CardKPI], largura_total: float) -> Table:
    gap = 0.35 * cm
    largura_card = (largura_total - gap * (len(cards) - 1)) / len(cards)
    for card in cards:
        card.width = largura_card
    linha = [cards]
    tabela = Table(linha, colWidths=[largura_card] * len(cards))
    tabela.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), gap),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    tabela._argW[len(cards) - 1] = largura_card  # última coluna sem gap à direita
    return tabela


# ---------------------------------------------------------------------------
# Cabeçalho / rodapé (desenhados direto no canvas de cada página)
# ---------------------------------------------------------------------------

def _cabecalho_rodape(canv, doc, data_inicio: str, data_fim: str):
    canv.saveState()

    canv.setFillColor(colors.HexColor(COR_PRIMARIA))
    canv.rect(0, ALTURA_PAGINA - ALTURA_FAIXA_TOPO, LARGURA_PAGINA, ALTURA_FAIXA_TOPO,
               fill=1, stroke=0)

    canv.setFillColor(colors.white)
    canv.setFont("Helvetica-Bold", 20)
    canv.drawString(MARGEM, ALTURA_PAGINA - 1.5 * cm, "Relatório de Gastos")

    canv.setFont("Helvetica", 11)
    canv.setFillColor(colors.HexColor(COR_PRIMARIA_CLARA))
    canv.drawString(MARGEM, ALTURA_PAGINA - 2.15 * cm,
                     f"Período de {data_inicio} a {data_fim}  ·  Orçamento Conversacional")

    canv.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
    canv.setFont("Helvetica", 7.5)
    canv.drawString(MARGEM, 1 * cm,
                     "Relatório gerado automaticamente. Tem caráter informativo — "
                     "não constitui aconselhamento financeiro profissional.")
    canv.drawRightString(LARGURA_PAGINA - MARGEM, 1 * cm, f"Página {doc.page}")

    canv.restoreState()


# ---------------------------------------------------------------------------
# Montagem principal
# ---------------------------------------------------------------------------

def montar_pdf(
    caminho: str,
    data_inicio: str,
    data_fim: str,
    total_atual: float,
    total_anterior: float,
    resumo_categoria: list[dict],
    evolucao: list[dict],
    maior_despesa: dict | None,
    categoria_destaque: str | None,
) -> None:
    largura_util = LARGURA_PAGINA - 2 * MARGEM

    doc = SimpleDocTemplate(
        caminho, pagesize=A4,
        topMargin=ALTURA_FAIXA_TOPO + 0.8 * cm,
        bottomMargin=1.6 * cm,
        leftMargin=MARGEM, rightMargin=MARGEM,
    )

    estilo_secao = ParagraphStyle(
        "secao", fontName="Helvetica-Bold", fontSize=13, textColor=colors.HexColor(COR_TEXTO),
        spaceBefore=6, spaceAfter=8,
    )
    estilo_destaque = ParagraphStyle(
        "destaque", fontName="Helvetica", fontSize=10.5, textColor=colors.HexColor(COR_TEXTO_SECUNDARIO),
        leading=15,
    )

    variacao_pct = None
    if total_anterior > 0:
        variacao_pct = round((total_atual - total_anterior) / total_anterior * 100, 1)

    categoria_top = resumo_categoria[0] if resumo_categoria else None
    n_despesas_txt = f"{len(evolucao)} dia(s) com gasto" if evolucao else "—"

    cor_variacao = COR_POSITIVO
    variacao_txt = "—"
    if variacao_pct is not None:
        cor_variacao = COR_NEGATIVO if variacao_pct > 0 else COR_POSITIVO
        variacao_txt = f"{variacao_pct:+.1f}%"

    cards = [
        CardKPI(0, 2.6 * cm, "Total gasto", f"R$ {total_atual:,.2f}".replace(",", "."),
                cor=COR_PRIMARIA),
        CardKPI(0, 2.6 * cm, "Vs. período anterior", variacao_txt,
                subtitulo="mais alto" if (variacao_pct or 0) > 0 else "mais baixo",
                cor=cor_variacao),
        CardKPI(0, 2.6 * cm, "Categoria principal",
                nome_categoria(categoria_top["categoria"]) if categoria_top else "—",
                subtitulo=(f'R$ {categoria_top["total"]:,.2f}'.replace(",", ".")
                           if categoria_top else None),
                cor=_cor_categoria(categoria_top["categoria"]) if categoria_top else COR_PRIMARIA),
    ]

    elementos = [
        _linha_cards(cards, largura_util),
        Spacer(1, 0.7 * cm),
    ]

    destaques = []
    if maior_despesa:
        destaques.append(
            f"<b>Maior despesa:</b> R$ {float(maior_despesa['valor']):,.2f} — "
            f"{maior_despesa['descricao']} ({maior_despesa['data_despesa']})".replace(",", ".")
        )
    if categoria_destaque:
        destaques.append(f"<b>Destaque:</b> {categoria_destaque}")
    if destaques:
        elementos.append(Paragraph("  &nbsp;&nbsp;|&nbsp;&nbsp;  ".join(destaques), estilo_destaque))
        elementos.append(Spacer(1, 0.6 * cm))

    if resumo_categoria:
        elementos.append(Paragraph("Distribuição por categoria", estilo_secao))
        elementos.append(Image(
            grafico_distribuicao_categoria(resumo_categoria, total_atual),
            width=largura_util, height=largura_util * 0.42,
        ))
        elementos.append(Spacer(1, 0.5 * cm))

    if evolucao:
        elementos.append(Paragraph("Evolução diária", estilo_secao))
        elementos.append(Image(
            grafico_evolucao_diaria(evolucao),
            width=largura_util, height=largura_util * 0.32,
        ))
        elementos.append(Spacer(1, 0.5 * cm))

    if total_anterior > 0:
        elementos.append(Paragraph("Comparação com o período anterior", estilo_secao))
        elementos.append(Image(
            grafico_comparacao_periodos(total_atual, total_anterior, "Este período", "Período anterior"),
            width=largura_util, height=largura_util * 0.16,
        ))
        elementos.append(Spacer(1, 0.5 * cm))

    if resumo_categoria:
        elementos.append(Paragraph("Detalhamento por categoria", estilo_secao))
        dados = [["", "Categoria", "Total (R$)"]]
        for r in resumo_categoria:
            dados.append(["●", nome_categoria(r["categoria"]), f'{float(r["total"]):,.2f}'.replace(",", ".")])
        tabela = Table(dados, colWidths=[0.7 * cm, largura_util - 0.7 * cm - 3.5 * cm, 3.5 * cm])
        estilo_tabela = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COR_PRIMARIA)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ]
        for i, r in enumerate(resumo_categoria, start=1):
            estilo_tabela.append(("TEXTCOLOR", (0, i), (0, i), colors.HexColor(_cor_categoria(r["categoria"]))))
        tabela.setStyle(TableStyle(estilo_tabela))
        elementos.append(tabela)

    doc.build(
        elementos,
        onFirstPage=functools.partial(_cabecalho_rodape, data_inicio=data_inicio, data_fim=data_fim),
        onLaterPages=functools.partial(_cabecalho_rodape, data_inicio=data_inicio, data_fim=data_fim),
    )
