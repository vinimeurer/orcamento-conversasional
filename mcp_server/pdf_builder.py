"""
Módulo de montagem do PDF do relatório de gastos.

Usa o chart_builder para os gráficos e monta o layout final: cabeçalho de
marca, cards de KPI, distribuição por categoria, evolução diária,
detalhamento por categoria, detalhamento por dia e rodapé com paginação —
tudo com a paleta definida em chart_builder.

Este relatório cobre um único período por vez (sem comparação com períodos
anteriores) — é uma foto do mês/período consultado, não uma análise de
tendência.
"""
import functools
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

from chart_builder import (
    COR_FUNDO_CARD, COR_PRIMARIA, COR_PRIMARIA_CLARA, COR_TEXTO,
    COR_TEXTO_SECUNDARIO, grafico_distribuicao_categoria,
    grafico_evolucao_diaria, _cor_categoria, nome_categoria,
)

MARGEM = 2 * cm
ALTURA_FAIXA_TOPO = 2.9 * cm

DIAS_SEMANA = [
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo",
]


def _dia_semana_pt(data) -> str:
    return DIAS_SEMANA[data.weekday()]


def _moeda(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", ".")


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

    @staticmethod
    def _fonte_ajustada(c, texto, fonte, tamanho_max, largura_disponivel, tamanho_min=7):
        """
        Reduz o tamanho da fonte até o texto caber em largura_disponivel,
        pra não depender de adivinhar quantos caracteres cabem em cada
        card (que muda conforme o número de cards na linha).
        """
        tamanho = tamanho_max
        while tamanho > tamanho_min and c.stringWidth(texto, fonte, tamanho) > largura_disponivel:
            tamanho -= 0.5
        return tamanho

    def draw(self):
        c = self.canv
        c.setFillColor(colors.HexColor(COR_FUNDO_CARD))
        c.roundRect(0, 0, self.width, self.height, radius=6, fill=1, stroke=0)

        c.setFillColor(colors.HexColor(self.cor))
        c.roundRect(0, self.height - 5, self.width, 5, radius=2.5, fill=1, stroke=0)
        c.rect(0, self.height - 5, self.width, 2.5, fill=1, stroke=0)

        pad = 0.4 * cm
        largura_disponivel = self.width - 2 * pad

        titulo = self.titulo.upper()
        tam_titulo = self._fonte_ajustada(c, titulo, "Helvetica", 9.5, largura_disponivel)
        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.setFont("Helvetica", tam_titulo)
        c.drawString(pad, self.height - 1.0 * cm, titulo)

        tam_valor = self._fonte_ajustada(c, self.valor, "Helvetica-Bold", 16, largura_disponivel)
        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica-Bold", tam_valor)
        c.drawString(pad, self.height - 1.75 * cm, self.valor)

        if self.subtitulo:
            tam_sub = self._fonte_ajustada(c, self.subtitulo, "Helvetica-Bold", 9.5, largura_disponivel)
            c.setFillColor(colors.HexColor(self.cor))
            c.setFont("Helvetica-Bold", tam_sub)
            c.drawString(pad, pad, self.subtitulo)


def _linha_cards(cards: list[CardKPI], largura_total: float) -> Table:
    gap = 0.35 * cm
    largura_card = (largura_total - gap * (len(cards) - 1)) / len(cards)
    for card in cards:
        card.width = largura_card
    tabela = Table([cards], colWidths=[largura_card] * len(cards))
    tabela.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), gap),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabela


# ---------------------------------------------------------------------------
# Cabeçalho / rodapé (desenhados direto no canvas de cada página)
# ---------------------------------------------------------------------------

def _cabecalho_rodape(canv, doc, data_inicio: str, data_fim: str):
    canv.saveState()
    largura, altura = doc.pagesize

    canv.setFillColor(colors.HexColor(COR_PRIMARIA))
    canv.rect(0, altura - ALTURA_FAIXA_TOPO, largura, ALTURA_FAIXA_TOPO, fill=1, stroke=0)

    canv.setFillColor(colors.white)
    canv.setFont("Helvetica-Bold", 20)
    canv.drawString(MARGEM, altura - 1.5 * cm, "Relatório de Gastos")

    canv.setFont("Helvetica", 11)
    canv.setFillColor(colors.HexColor(COR_PRIMARIA_CLARA))
    canv.drawString(MARGEM, altura - 2.15 * cm,
                     f"Período de {data_inicio} a {data_fim}  ·  Orçamento Conversacional")

    canv.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
    canv.setFont("Helvetica", 7.5)
    canv.drawString(MARGEM, 1 * cm,
                     "Relatório gerado automaticamente. Tem caráter informativo — "
                     "não constitui aconselhamento financeiro profissional.")
    canv.drawRightString(largura - MARGEM, 1 * cm, f"Página {doc.page}")

    canv.restoreState()


# ---------------------------------------------------------------------------
# Agrupamentos
# ---------------------------------------------------------------------------

def _agrupar_por_categoria(despesas: list[dict], ordem: list[str]) -> list[tuple[str, list[dict]]]:
    grupos = defaultdict(list)
    for d in despesas:
        grupos[d["categoria"]].append(d)
    for itens in grupos.values():
        itens.sort(key=lambda d: d["data_despesa"])  # crescente
    return [(cat, grupos[cat]) for cat in ordem if cat in grupos]


def _agrupar_por_dia(despesas: list[dict]) -> list[tuple[object, list[dict]]]:
    grupos = defaultdict(list)
    for d in despesas:
        grupos[d["data_despesa"]].append(d)
    for itens in grupos.values():
        itens.sort(key=lambda d: -float(d["valor"]))  # maior primeiro
    return [(dia, grupos[dia]) for dia in sorted(grupos.keys())]


# ---------------------------------------------------------------------------
# Montagem principal
# ---------------------------------------------------------------------------

def montar_pdf(
    caminho: str,
    data_inicio: str,
    data_fim: str,
    total_atual: float,
    resumo_categoria: list[dict],
    evolucao: list[dict],
    despesas: list[dict],
    maior_despesa: dict | None,
    orientacao: str = "vertical",
) -> None:
    """
    Relatório de gastos de um único período (sem comparação com períodos
    anteriores — este relatório existe só para ver os gastos do próprio
    mês/período consultado).

    orientacao: "vertical" (retrato, padrão — recomendado) ou "horizontal"
    (paisagem). Ver justificativa da escolha no README/comentário do addon.
    """
    pagesize = A4 if orientacao == "vertical" else landscape(A4)
    largura_pagina = pagesize[0]
    largura_util = largura_pagina - 2 * MARGEM

    doc = SimpleDocTemplate(
        caminho, pagesize=pagesize,
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
    estilo_grupo_header = ParagraphStyle(
        "grupo_header", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor(COR_TEXTO),
        spaceBefore=10, spaceAfter=3,
    )
    estilo_item = ParagraphStyle(
        "item", fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor(COR_TEXTO_SECUNDARIO),
        leftIndent=0.5 * cm, spaceAfter=2, leading=13,
    )

    categoria_top = resumo_categoria[0] if resumo_categoria else None
    media_diaria = total_atual / len(evolucao) if evolucao else 0.0

    cards = [
        CardKPI(0, 2.6 * cm, "Total gasto", _moeda(total_atual), cor=COR_PRIMARIA),
        CardKPI(0, 2.6 * cm, "Categoria principal",
                nome_categoria(categoria_top["categoria"]) if categoria_top else "—",
                subtitulo=(_moeda(float(categoria_top["total"])) if categoria_top else None),
                cor=_cor_categoria(categoria_top["categoria"]) if categoria_top else COR_PRIMARIA),
        CardKPI(0, 2.6 * cm, "Média diária", _moeda(media_diaria), cor=COR_PRIMARIA),
        CardKPI(0, 2.6 * cm, "Registros", str(len(despesas)), cor=COR_PRIMARIA),
    ]

    elementos = [_linha_cards(cards, largura_util), Spacer(1, 0.7 * cm)]

    if maior_despesa:
        elementos.append(Paragraph(
            f"<b>Maior despesa do período:</b> {_moeda(float(maior_despesa['valor']))} — "
            f"{maior_despesa['descricao']} ({maior_despesa['data_despesa']})",
            estilo_destaque,
        ))
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

    # -----------------------------------------------------------------
    # Detalhamento por categoria (categorias em ordem decrescente de valor;
    # dentro de cada categoria, registros em ordem crescente de data)
    # -----------------------------------------------------------------
    if despesas and resumo_categoria:
        elementos.append(Paragraph("Detalhamento por categoria", estilo_secao))
        ordem_categorias = [r["categoria"] for r in resumo_categoria]
        for categoria, itens in _agrupar_por_categoria(despesas, ordem_categorias):
            total_cat = sum(float(d["valor"]) for d in itens)
            cor = _cor_categoria(categoria)
            bloco = [Paragraph(
                f'<font color="{cor}">●</font> <b>{nome_categoria(categoria)}</b>'
                f'&nbsp;&nbsp;<font color="{COR_TEXTO_SECUNDARIO}">{_moeda(total_cat)}'
                f' · {len(itens)} registro(s)</font>',
                estilo_grupo_header,
            )]
            for d in itens:
                bloco.append(Paragraph(
                    f'{d["data_despesa"].strftime("%d/%m")} — {d["descricao"]} — '
                    f'{_moeda(float(d["valor"]))}',
                    estilo_item,
                ))
            elementos.append(KeepTogether(bloco))

    # -----------------------------------------------------------------
    # Detalhamento por dia (dias em ordem crescente; dentro de cada dia,
    # registros do maior para o menor valor)
    # -----------------------------------------------------------------
    if despesas:
        elementos.append(Spacer(1, 0.4 * cm))
        elementos.append(Paragraph("Detalhamento por dia", estilo_secao))
        for dia, itens in _agrupar_por_dia(despesas):
            total_dia = sum(float(d["valor"]) for d in itens)
            bloco = [Paragraph(
                f'<b>{dia.strftime("%d/%m/%Y")}</b> — {_dia_semana_pt(dia)}'
                f'&nbsp;&nbsp;<font color="{COR_TEXTO_SECUNDARIO}">{_moeda(total_dia)}'
                f' · {len(itens)} registro(s)</font>',
                estilo_grupo_header,
            )]
            for d in itens:
                cor = _cor_categoria(d["categoria"])
                bloco.append(Paragraph(
                    f'<font color="{cor}">●</font> {d["descricao"]} '
                    f'({nome_categoria(d["categoria"])}) — {_moeda(float(d["valor"]))}',
                    estilo_item,
                ))
            elementos.append(KeepTogether(bloco))

    doc.build(
        elementos,
        onFirstPage=functools.partial(_cabecalho_rodape, data_inicio=data_inicio, data_fim=data_fim),
        onLaterPages=functools.partial(_cabecalho_rodape, data_inicio=data_inicio, data_fim=data_fim),
    )
