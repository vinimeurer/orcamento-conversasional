"""
Montagem do dashboard de gastos em PDF (página única, A4), desenhado direto
no canvas do ReportLab para replicar com precisão o grid do template de
referência (cabeçalho, 5 KPIs, categoria+donut, evolução+top gastos,
resumo, rodapé).
"""
import calendar
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as canvas_module

import icons
from dash_style import (
    COR_CARD_BORDA, COR_FOOTER_BG, COR_ICONE_BG, COR_INSIGHT_BG,
    COR_PRIMARIA, COR_SECUNDARIA, COR_TEXTO, COR_TEXTO_SECUNDARIO,
    COR_TITULO, COR_TRILHO_BARRA, cor_categoria, icone_categoria,
    moeda, nome_categoria,
)

LARGURA, ALTURA = A4
MARGEM = 1.3 * cm
LARGURA_UTIL = LARGURA - 2 * MARGEM
CARD_PAD = 0.45 * cm
GAP = 0.3 * cm
GAP_ANTES_RESUMO = 0.5 * cm  # um pouco mais de respiro antes do "EM RESUMO"

MESES_PT = [
    "", "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
]

ICONS_POR_NOME = {
    "fork": icons.icon_fork, "house": icons.icon_house, "car": icons.icon_car,
    "music": icons.icon_music, "heart": icons.icon_heart, "bag": icons.icon_bag,
    "book": icons.icon_book, "gear": icons.icon_gear, "refresh": icons.icon_refresh,
    "dots": icons.icon_dots, "calendar": icons.icon_calendar, "list": icons.icon_list,
    "barchart": icons.icon_barchart, "star": icons.icon_star, "wallet": icons.icon_wallet,
    "lightbulb": icons.icon_lightbulb,
    # métodos de pagamento (página 2)
    "bolt": icons.icon_bolt, "card": icons.icon_card, "banknote": icons.icon_banknote,
    "barcode": icons.icon_barcode, "transfer": icons.icon_transfer,
    "ticket": icons.icon_ticket, "invoice": icons.icon_invoice,
}


def _icone_badge(c, cx, cy, raio_circulo, nome_icone, cor_icone=COR_PRIMARIA, cor_bg=COR_ICONE_BG, fracao_pie=0.24):
    c.setFillColor(colors.HexColor(cor_bg))
    c.circle(cx, cy, raio_circulo, stroke=0, fill=1)
    if nome_icone == "pie":
        icons.icon_pie(c, cx, cy, raio_circulo * 0.62, cor_bg, cor_icone, fracao_pie)
    else:
        fn = ICONS_POR_NOME[nome_icone]
        fn(c, cx, cy, raio_circulo * 0.62, cor_icone)


def _texto_centralizado(c, x, y, texto, fonte, tamanho, cor):
    c.setFillColor(colors.HexColor(cor))
    c.setFont(fonte, tamanho)
    c.drawCentredString(x, y, texto)


def _truncar_com_reticencias(c, texto, fonte, tamanho, largura_max):
    """Trunca 'texto' e adiciona '...' se ele não couber em largura_max, na
    fonte/tamanho dados. Usado em todo lugar onde um texto de tamanho
    variável (descrição de despesa, nome de categoria etc.) poderia
    sobrescrever outro elemento ao lado."""
    if c.stringWidth(texto, fonte, tamanho) <= largura_max:
        return texto
    reticencias = "..."
    txt = texto
    while txt and c.stringWidth(txt + reticencias, fonte, tamanho) > largura_max:
        txt = txt[:-1]
    return (txt + reticencias) if txt else reticencias


def _texto_ajustado(c, texto, fonte, tamanho_max, largura_disponivel, tamanho_min=7):
    """Reduz a fonte até tamanho_min tentando caber o texto; se mesmo no
    tamanho mínimo ainda não couber, trunca com reticências nesse tamanho.
    Retorna (texto_final, tamanho_final)."""
    tamanho = tamanho_max
    while tamanho > tamanho_min and c.stringWidth(texto, fonte, tamanho) > largura_disponivel:
        tamanho -= 0.5
    if c.stringWidth(texto, fonte, tamanho) > largura_disponivel:
        texto = _truncar_com_reticencias(c, texto, fonte, tamanho, largura_disponivel)
    return texto, tamanho


def _desenhar_moldura_card(c, x, y_topo, largura, altura):
    """
    Desenha a mesma moldura sutil dos cards de KPI (fundo branco + borda
    clara arredondada) por trás de uma seção de gráfico, pra dar a mesma
    organização visual do template de referência.
    """
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor(COR_CARD_BORDA))
    c.roundRect(x, y_topo - altura, largura, altura, 0.14 * cm, stroke=1, fill=1)


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------

def _desenhar_cabecalho(c, titulo_periodo: str, data_inicio: str, data_fim: str, y_topo: float,
                         icone_card: str = "list", linha1_card: str = "Resumo simples e claro",
                         linha2_card: str = "dos seus gastos no período.") -> float:
    x = MARGEM
    c.setFillColor(colors.HexColor(COR_TITULO))
    c.setFont("Helvetica-Bold", 24)
    c.drawString(x, y_topo - 0.75 * cm, "RELATÓRIO DE GASTOS")

    c.setFillColor(colors.HexColor(COR_SECUNDARIA))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x, y_topo - 1.35 * cm, titulo_periodo)

    icons.icon_calendar(c, x + 0.15 * cm, y_topo - 1.85 * cm, 0.16 * cm, COR_TEXTO_SECUNDARIO)
    c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
    c.setFont("Helvetica", 9)
    c.drawString(x + 0.4 * cm, y_topo - 1.9 * cm,
                 f"Período analisado: {data_inicio} a {data_fim}")

    # card decorativo à direita
    largura_card = 6.4 * cm
    altura_card = 1.55 * cm
    x_card = LARGURA - MARGEM - largura_card
    y_card = y_topo - 0.35 * cm - altura_card
    c.setFillColor(colors.HexColor(COR_INSIGHT_BG))
    c.roundRect(x_card, y_card, largura_card, altura_card, 0.15 * cm, stroke=0, fill=1)
    _icone_badge(c, x_card + 0.9 * cm, y_card + altura_card / 2, 0.42 * cm, icone_card)
    c.setFillColor(colors.HexColor(COR_TEXTO))
    c.setFont("Helvetica", 9)
    c.drawString(x_card + 1.55 * cm, y_card + altura_card / 2 + 0.12 * cm, linha1_card)
    c.drawString(x_card + 1.55 * cm, y_card + altura_card / 2 - 0.18 * cm, linha2_card)

    return y_topo - 2.35 * cm


# ---------------------------------------------------------------------------
# Linha de cards de KPI
# ---------------------------------------------------------------------------

def _desenhar_kpi_card(c, x, y, largura, altura, icone, label, valor, subtitulo, cor_valor=COR_TEXTO):
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor(COR_CARD_BORDA))
    c.roundRect(x, y, largura, altura, 0.12 * cm, stroke=1, fill=1)

    cx = x + largura / 2
    _icone_badge(c, cx, y + altura - 0.55 * cm, 0.42 * cm, icone)

    _texto_centralizado(c, cx, y + altura - 1.35 * cm, label.upper(), "Helvetica", 7.3, COR_TEXTO_SECUNDARIO)

    valor_final, tam_valor = _texto_ajustado(c, valor, "Helvetica-Bold", 14, largura - 0.3 * cm, tamanho_min=8)
    _texto_centralizado(c, cx, y + altura - 1.95 * cm, valor_final, "Helvetica-Bold", tam_valor, cor_valor)

    if subtitulo:
        sub_final, tam_sub = _texto_ajustado(c, subtitulo, "Helvetica", 7.3, largura - 0.3 * cm, tamanho_min=6)
        _texto_centralizado(c, cx, y + 0.35 * cm, sub_final, "Helvetica", tam_sub, COR_TEXTO_SECUNDARIO)


def _desenhar_linha_kpis(c, cards: list[dict], y_topo: float) -> float:
    altura = 2.75 * cm
    gap = 0.3 * cm
    n = len(cards)
    largura = (LARGURA_UTIL - gap * (n - 1)) / n
    x = MARGEM
    y = y_topo - altura
    for card in cards:
        _desenhar_kpi_card(c, x, y, largura, altura, **card)
        x += largura + gap
    return y - GAP


# ---------------------------------------------------------------------------
# Seção: Gastos por categoria (barras) + Composição (donut)
# ---------------------------------------------------------------------------

def _desenhar_titulo_secao(c, x, y, texto, largura=None, extra_direita=None):
    """
    largura, quando informado, também limita a largura do próprio título
    (reduzindo a fonte se necessário) — evita que um título comprido
    estoure a borda da coluna quando ela é mais estreita (ex: colunas de
    38% de largura na página 2). Se extra_direita também for informado,
    reserva uma fatia da largura pra ele não ficar espremido pelo título.
    """
    largura_titulo_max = largura * (0.55 if extra_direita else 1.0) if largura else None
    titulo_final, tamanho = (
        _texto_ajustado(c, texto, "Helvetica-Bold", 11, largura_titulo_max, tamanho_min=8.5)
        if largura_titulo_max else (texto, 11)
    )
    c.setFillColor(colors.HexColor(COR_TEXTO))
    c.setFont("Helvetica-Bold", tamanho)
    c.drawString(x, y, titulo_final)
    if extra_direita and largura:
        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.setFont("Helvetica", 8)
        c.drawRightString(x + largura, y, extra_direita)


def _desenhar_lista_categorias(c, resumo: list[dict], x, y_topo, largura, altura_max, altura_disponivel=None) -> float:
    """
    altura_disponivel: se informado, a altura total que a lista deve
    ocupar (título + linhas) é esse valor — as linhas se espaçam
    dinamicamente para preencher exatamente esse espaço, em vez de usar
    uma altura de linha fixa. Usado para a lista "esticar" e preencher o
    mesmo espaço que a coluna vizinha (composição), sem sobrar vão em
    branco nem precisar de um elemento extra embaixo.
    """
    _desenhar_titulo_secao(c, x, y_topo, "GASTOS POR CATEGORIA", largura, "Valor (R$)  |  % total")
    y = y_topo - 0.55 * cm

    n = len(resumo)
    linha_altura_natural = 0.62 * cm
    if altura_disponivel is not None and n > 0:
        linha_altura = max(linha_altura_natural, (altura_disponivel - 0.55 * cm) / n)
    else:
        linha_altura = linha_altura_natural

    total = sum(float(r["total"]) for r in resumo)
    maior = max((float(r["total"]) for r in resumo), default=1)

    largura_valor = 2.1 * cm
    largura_pct = 1.0 * cm
    x_icone = x + 0.25 * cm
    x_label = x + 0.65 * cm
    x_barra = x + 3.0 * cm
    largura_barra = largura - 3.0 * cm - largura_valor - largura_pct - 0.3 * cm
    largura_label_max = x_barra - x_label - 0.15 * cm

    for r in resumo:
        cat = r["categoria"]
        valor = float(r["total"])
        pct = (valor / total * 100) if total else 0
        cor = cor_categoria(cat)

        _icone_badge(c, x_icone, y - 0.06 * cm, 0.32 * cm, icone_categoria(cat), cor_icone=COR_PRIMARIA)

        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica", 9)
        label_final = _truncar_com_reticencias(c, nome_categoria(cat), "Helvetica", 9, largura_label_max)
        c.drawString(x_label, y - 0.12 * cm, label_final)

        c.setFillColor(colors.HexColor(COR_TRILHO_BARRA))
        c.roundRect(x_barra, y - 0.17 * cm, largura_barra, 0.22 * cm, 0.1 * cm, stroke=0, fill=1)
        larg_preenchida = largura_barra * (valor / maior) if maior else 0
        if larg_preenchida > 0.01:
            c.setFillColor(colors.HexColor(cor))
            c.roundRect(x_barra, y - 0.17 * cm, larg_preenchida, 0.22 * cm, 0.1 * cm, stroke=0, fill=1)

        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x_barra + largura_barra + 0.15 * cm, y - 0.12 * cm, moeda(valor))

        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.setFont("Helvetica", 8.5)
        c.drawRightString(x + largura, y - 0.12 * cm, f"{pct:.0f}%")

        y -= linha_altura

    return y


def _desenhar_caixa_insight(c, x, y_topo, largura, icone, texto, altura=1.05 * cm) -> float:
    y = y_topo - altura
    c.setFillColor(colors.HexColor(COR_INSIGHT_BG))
    c.roundRect(x, y, largura, altura, 0.12 * cm, stroke=0, fill=1)
    _icone_badge(c, x + 0.6 * cm, y + altura / 2, 0.32 * cm, icone)
    c.setFillColor(colors.HexColor(COR_TEXTO))
    c.setFont("Helvetica", 8.5)
    _texto_paragrafo_simples(c, texto, x + 1.15 * cm, y + altura / 2 + 0.12 * cm,
                              largura - 1.5 * cm, "Helvetica", 8.5, COR_TEXTO)
    return y


def _texto_paragrafo_simples(c, texto, x, y, largura_max, fonte, tamanho, cor, entrelinha=0.32 * cm, max_linhas=2):
    """Quebra de linha simples por largura, sem depender de Platypus — usado
    dentro de boxes desenhados manualmente no canvas."""
    c.setFillColor(colors.HexColor(cor))
    c.setFont(fonte, tamanho)
    palavras = texto.split()
    linha = ""
    linhas = []
    for palavra in palavras:
        tentativa = (linha + " " + palavra).strip()
        if c.stringWidth(tentativa, fonte, tamanho) > largura_max and linha:
            linhas.append(linha)
            linha = palavra
        else:
            linha = tentativa
    if linha:
        linhas.append(linha)
    yy = y
    for linha in linhas[:max_linhas]:
        c.drawString(x, yy, linha)
        yy -= entrelinha


# ---------------------------------------------------------------------------
# Donut de composição (matplotlib) + legenda
# ---------------------------------------------------------------------------

def _agrupar_top5_outros(resumo: list[dict]) -> list[dict]:
    """
    Mantém até 5 categorias "de verdade" (excluindo "outros") como fatias
    individuais, e agrupa o restante — incluindo a categoria "outros" real,
    se houver — em um único balde "Outros". Isso evita o caso de aparecer
    "Outros" duplicado na legenda (a categoria real + o balde genérico).
    """
    principais = [r for r in resumo if r["categoria"] != "outros"]
    outros_real = next((r for r in resumo if r["categoria"] == "outros"), None)

    if len(principais) <= 5:
        resultado = list(principais)
        if outros_real:
            resultado.append(outros_real)
        return resultado

    top = principais[:5]
    resto = sum(float(r["total"]) for r in principais[5:])
    if outros_real:
        resto += float(outros_real["total"])
    if resto > 0:
        top.append({"categoria": "outros", "total": resto, "_rotulo_forcado": "Outros"})
    return top


def _grafico_donut(resumo_donut: list[dict], total: float):
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(5.2, 5.2))

    valores = [float(r["total"]) for r in resumo_donut]
    cores = [cor_categoria(r["categoria"]) for r in resumo_donut]

    wedges, _, autotexts = ax.pie(
        valores, colors=cores, startangle=90, counterclock=False,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 3},
        autopct=lambda p: f"{p:.0f}%" if p >= 5 else "",
        pctdistance=0.79,
    )
    for t in autotexts:
        t.set_color("white")
        t.set_fontsize(13)
        t.set_fontweight("bold")

    ax.text(0, 0.10, moeda(total), ha="center", va="center", fontsize=15, fontweight="bold", color=COR_TEXTO)
    ax.text(0, -0.14, "Total", ha="center", va="center", fontsize=10.5, color=COR_TEXTO_SECUNDARIO)
    ax.set_aspect("equal")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, transparent=True, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    buf.seek(0)
    return buf


def _desenhar_composicao(c, resumo: list[dict], total: float, x, y_topo, largura, extra_gap_topo=0) -> float:
    from reportlab.lib.utils import ImageReader

    _desenhar_titulo_secao(c, x, y_topo, "COMPOSIÇÃO DOS GASTOS")
    resumo_donut = _agrupar_top5_outros(resumo)

    tam_img = largura * 0.8
    x_img = x + (largura - tam_img) / 2
    y_img = y_topo - 0.5 * cm - extra_gap_topo - tam_img
    c.drawImage(ImageReader(_grafico_donut(resumo_donut, total)),
                x_img, y_img, width=tam_img, height=tam_img, mask="auto")

    y = y_img - 0.35 * cm
    total_donut = sum(float(r["total"]) for r in resumo_donut)
    for r in resumo_donut:
        cat = r["categoria"]
        rotulo = r.get("_rotulo_forcado") or nome_categoria(cat)
        pct = (float(r["total"]) / total_donut * 100) if total_donut else 0
        cor = cor_categoria(cat)

        c.setFillColor(colors.HexColor(cor))
        c.circle(x + 0.12 * cm, y - 0.03 * cm, 0.11 * cm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica", 8.5)
        c.drawString(x + 0.4 * cm, y - 0.12 * cm, rotulo)
        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.drawRightString(x + largura, y - 0.12 * cm, f"{pct:.0f}%")
        y -= 0.42 * cm

    return y


# ---------------------------------------------------------------------------
# Evolução diária (área) + Principais gastos (tabela)
# ---------------------------------------------------------------------------

def _grafico_evolucao_area(evolucao: list[dict]):
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9,
        "text.color": COR_TEXTO_SECUNDARIO, "axes.edgecolor": "#E5E9F0",
        "xtick.color": COR_TEXTO_SECUNDARIO, "ytick.color": COR_TEXTO_SECUNDARIO,
    })
    fig, ax = plt.subplots(figsize=(10, 3.6))

    dias = [e["data_despesa"] for e in evolucao]
    valores = [float(e["total"]) for e in evolucao]

    ax.plot(range(len(dias)), valores, color=COR_PRIMARIA, linewidth=1.6, marker="o",
            markersize=3.2, markerfacecolor="white", markeredgecolor=COR_PRIMARIA,
            markeredgewidth=1.2, zorder=3)
    ax.fill_between(range(len(dias)), valores, color=COR_PRIMARIA, alpha=0.08, zorder=2)

    passo = max(1, len(dias) // 10)
    ax.set_xticks(list(range(len(dias)))[::passo])
    ax.set_xticklabels([d.strftime("%d/%m") for d in dias[::passo]], fontsize=8)
    ax.set_xlim(-0.5, len(dias) - 0.5)

    ax.grid(axis="y", color="#EEF1F6", linewidth=0.8, zorder=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#E5E9F0")
    ax.tick_params(left=False)
    ax.set_ylim(bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, transparent=True, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    buf.seek(0)
    return buf


def _desenhar_evolucao(c, evolucao: list[dict], x, y_topo, largura, altura_img=None) -> float:
    from reportlab.lib.utils import ImageReader

    _desenhar_titulo_secao(c, x, y_topo, "GASTOS AO LONGO DO MÊS", largura, "Valor gasto por dia (R$)")
    if altura_img is None:
        altura_img = largura * 0.33
    y_img = y_topo - 0.5 * cm - altura_img
    c.drawImage(ImageReader(_grafico_evolucao_area(evolucao)),
                x, y_img, width=largura, height=altura_img, mask="auto")
    return y_img - 0.3 * cm


def _desenhar_top_gastos(c, despesas_top: list[dict], x, y_topo, largura) -> float:
    _desenhar_titulo_secao(c, x, y_topo, "PRINCIPAIS GASTOS")
    y = y_topo - 0.55 * cm

    x_num = x + 0.15 * cm
    x_icone = x + 0.55 * cm
    x_desc = x + 0.95 * cm
    x_valor = x + largura
    largura_valor_col = 2.5 * cm
    largura_desc_max = (x_valor - largura_valor_col) - x_desc - 0.15 * cm

    c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
    c.setFont("Helvetica", 7.5)
    c.drawString(x_desc, y, "DESCRIÇÃO")
    c.drawRightString(x_valor, y, "VALOR (R$)")
    y -= 0.5 * cm

    for i, d in enumerate(despesas_top, start=1):
        cat = d["categoria"]
        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.setFont("Helvetica", 8.5)
        c.drawString(x_num, y - 0.12 * cm, str(i))

        _icone_badge(c, x_icone, y - 0.05 * cm, 0.24 * cm, icone_categoria(cat), cor_icone=COR_PRIMARIA)

        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica", 8.7)
        desc_final = _truncar_com_reticencias(c, d["descricao"], "Helvetica", 8.7, largura_desc_max)
        c.drawString(x_desc, y - 0.12 * cm, desc_final)

        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.setFont("Helvetica", 7.3)
        cat_final = _truncar_com_reticencias(c, nome_categoria(cat), "Helvetica", 7.3, largura_desc_max)
        c.drawString(x_desc, y - 0.4 * cm, cat_final)

        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica-Bold", 8.7)
        c.drawRightString(x_valor, y - 0.12 * cm, moeda(float(d["valor"])))

        y -= 0.85 * cm

    return y


# ---------------------------------------------------------------------------
# "Em resumo" (3 cards) + rodapé
# ---------------------------------------------------------------------------

def _desenhar_em_resumo(c, insights: list[dict], y_topo: float) -> float:
    _desenhar_titulo_secao(c, MARGEM, y_topo, "EM RESUMO")
    y_topo -= GAP + 0.2 * cm

    altura = 2.3 * cm
    gap = GAP
    n = len(insights)
    largura = (LARGURA_UTIL - gap * (n - 1)) / n
    x = MARGEM
    y = y_topo - altura

    for item in insights:
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor(COR_CARD_BORDA))
        c.roundRect(x, y, largura, altura, 0.12 * cm, stroke=1, fill=1)
        _icone_badge(c, x + 0.65 * cm, y + altura - 0.55 * cm, 0.34 * cm, item["icone"])
        _texto_paragrafo_simples(c, item["texto"], x + 0.35 * cm, y + altura - 1.3 * cm,
                                  largura - 0.7 * cm, "Helvetica", 8, COR_TEXTO,
                                  entrelinha=0.32 * cm, max_linhas=3)
        x += largura + gap

    return y


def _desenhar_rodape(c, dica: str, data_geracao: str, y_topo: float):
    """
    y_topo: posição imediatamente após o último conteúdo acima (os cards
    de "Em resumo"). O rodapé é posicionado a partir daí, com um vão bem
    menor do que o espaço usado entre as seções de cima — em vez de ficar
    fixo lá embaixo na margem da página, independente de quanto conteúdo
    tem acima.
    """
    altura = 1.0 * cm
    gap_acima_disclaimer = 0.2 * cm
    gap_disclaimer_banda = 0.15 * cm

    y_disclaimer = y_topo - gap_acima_disclaimer
    c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(LARGURA / 2, y_disclaimer,
                         "Relatório com caráter informativo — não constitui aconselhamento financeiro profissional.")

    y_banda_topo = y_disclaimer - gap_disclaimer_banda
    c.setFillColor(colors.HexColor(COR_FOOTER_BG))
    c.roundRect(MARGEM, y_banda_topo - altura, LARGURA_UTIL, altura, 0.1 * cm, stroke=0, fill=1)

    y_texto = y_banda_topo - altura / 2 - 0.1 * cm
    icons.icon_lightbulb(c, MARGEM + 0.5 * cm, y_texto + 0.05 * cm, 0.22 * cm, COR_SECUNDARIA)
    c.setFillColor(colors.HexColor(COR_TEXTO))
    c.setFont("Helvetica", 8)
    c.drawString(MARGEM + 0.85 * cm, y_texto, f"Dica: {dica}")

    c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
    c.setFont("Helvetica", 8)
    c.drawRightString(MARGEM + LARGURA_UTIL - 0.4 * cm, y_texto, f"Relatório gerado em {data_geracao}")


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------

def montar_dashboard_pdf(
    caminho: str,
    mes_ano_titulo: str,
    data_inicio: str,
    data_fim: str,
    total_atual: float,
    n_lancamentos: int,
    gasto_medio: float,
    resumo_categoria: list[dict],
    evolucao: list[dict],
    despesas_top: list[dict],
    maior_despesa: dict,
    insights: list[dict],
    dica: str,
    data_geracao: str,
    dados_pagamento: dict | None = None,
) -> None:
    """
    Monta o dashboard de gastos. Página 1 (categorias) é desenhada por
    este módulo; se dados_pagamento for informado, uma página 2 (métodos
    de pagamento) é desenhada em seguida — em uma página nova de verdade
    (c.showPage()), então nada da página 2 pode aparecer na página 1.

    dados_pagamento, quando informado, precisa ter as chaves:
    resumo_metodo, n_transacoes, ticket_medio_geral, evolucao_metodo_raw,
    categoria_metodo_raw, insights.

    Todo o layout é desenhado com coordenadas absolutas (em vez de
    flowables do Platypus) porque o grid do template de referência é bem
    específico — é mais simples garantir fidelidade desenhando direto do
    que tentando encaixar num fluxo automático de parágrafos/tabelas.
    """
    c = canvas_module.Canvas(caminho, pagesize=A4)
    c.setFillColor(colors.white)
    c.rect(0, 0, LARGURA, ALTURA, stroke=0, fill=1)

    categoria_top = resumo_categoria[0] if resumo_categoria else None

    y = ALTURA - MARGEM
    y = _desenhar_cabecalho(c, mes_ano_titulo, data_inicio, data_fim, y)

    cards = [
        dict(icone="wallet", label="Gasto total", valor=moeda(total_atual),
             subtitulo="Total gasto no período"),
        dict(icone="list", label="Nº de lançamentos", valor=str(n_lancamentos),
             subtitulo="Total de gastos registrados"),
        dict(icone="barchart", label="Gasto médio", valor=moeda(gasto_medio),
             subtitulo="Média por lançamento"),
        dict(icone="pie", label="Maior categoria",
             valor=nome_categoria(categoria_top["categoria"]) if categoria_top else "—",
             subtitulo=(f'{moeda(float(categoria_top["total"]))} '
                        f'({float(categoria_top["total"]) / total_atual * 100:.0f}%)'
                        if categoria_top and total_atual else None)),
        dict(icone="star", label="Maior gasto",
             valor=maior_despesa["descricao"] if maior_despesa else "—",
             subtitulo=moeda(float(maior_despesa["valor"])) if maior_despesa else None),
    ]
    y = _desenhar_linha_kpis(c, cards, y)

    largura_col1 = LARGURA_UTIL * 0.58
    largura_col2 = LARGURA_UTIL * 0.38
    x_col2 = MARGEM + LARGURA_UTIL - largura_col2
    y_secoes = y

    # =====================================================================
    # Linha 1: Gastos por categoria | Composição dos gastos
    #
    # As duas colunas raramente têm a mesma altura "natural" (depende de
    # quantas categorias existem e de quantos itens tem a legenda do
    # donut). Em vez de alinhar pelo menor e deixar sobra de espaço em
    # branco na coluna mais curta, calculamos as duas alturas primeiro e
    # esticamos o elemento flexível da coluna mais curta — as próprias
    # linhas da lista de categorias (espaçamento dinâmico), ou o espaço
    # acima do donut à direita — até as duas baterem exatamente.
    # =====================================================================
    largura_cat_interna = largura_col1 - 2 * CARD_PAD
    n_cat = len(resumo_categoria)
    altura_cat_natural = 0.55 * cm + n_cat * 0.62 * cm + 2 * CARD_PAD

    largura_comp_interna = largura_col2 - 2 * CARD_PAD
    n_legenda = len(_agrupar_top5_outros(resumo_categoria))
    tam_img_comp = largura_comp_interna * 0.8
    altura_comp_natural = 0.5 * cm + tam_img_comp + 0.35 * cm + n_legenda * 0.42 * cm + 2 * CARD_PAD

    if altura_comp_natural >= altura_cat_natural:
        altura_cat_card = altura_comp_natural
        altura_comp_card = altura_comp_natural
        extra_gap_comp = 0
        conteudo_disponivel_cat = altura_cat_card - 2 * CARD_PAD
    else:
        altura_cat_card = altura_cat_natural
        altura_comp_card = altura_cat_natural
        extra_gap_comp = altura_comp_card - altura_comp_natural
        conteudo_disponivel_cat = None

    _desenhar_moldura_card(c, MARGEM, y_secoes, largura_col1, altura_cat_card)
    _desenhar_lista_categorias(
        c, resumo_categoria, MARGEM + CARD_PAD, y_secoes - CARD_PAD, largura_cat_interna, 6 * cm,
        altura_disponivel=conteudo_disponivel_cat,
    )
    y1_final = y_secoes - altura_cat_card

    _desenhar_moldura_card(c, x_col2, y_secoes, largura_col2, altura_comp_card)
    _desenhar_composicao(
        c, resumo_categoria, total_atual, x_col2 + CARD_PAD, y_secoes - CARD_PAD, largura_comp_interna,
        extra_gap_topo=extra_gap_comp,
    )
    y2_final = y_secoes - altura_comp_card

    y_meio = y1_final - GAP  # y1_final == y2_final por construção

    # =====================================================================
    # Linha 2: Gastos ao longo do mês | Principais gastos
    # Mesma lógica: a tabela de principais gastos tem altura previsível
    # (até 5 linhas fixas); esticamos o gráfico de evolução para bater
    # exatamente com ela.
    # =====================================================================
    largura_evo_interna = largura_col1 - 2 * CARD_PAD
    altura_img_evo_natural = largura_evo_interna * 0.33
    altura_evo_natural = 0.5 * cm + altura_img_evo_natural + 0.3 * cm + 2 * CARD_PAD

    largura_top_interna = largura_col2 - 2 * CARD_PAD
    n_top = len(despesas_top)
    altura_top_card = 1.05 * cm + n_top * 0.85 * cm + 2 * CARD_PAD

    if altura_top_card >= altura_evo_natural:
        altura_img_evo = altura_img_evo_natural + (altura_top_card - altura_evo_natural)
        altura_evo_card = altura_top_card
    else:
        altura_img_evo = altura_img_evo_natural
        altura_evo_card = altura_evo_natural
        altura_top_card = altura_evo_natural

    _desenhar_moldura_card(c, MARGEM, y_meio, largura_col1, altura_evo_card)
    _desenhar_evolucao(c, evolucao, MARGEM + CARD_PAD, y_meio - CARD_PAD, largura_evo_interna,
                        altura_img=altura_img_evo)
    y3_final = y_meio - altura_evo_card

    _desenhar_moldura_card(c, x_col2, y_meio, largura_col2, altura_top_card)
    _desenhar_top_gastos(c, despesas_top, x_col2 + CARD_PAD, y_meio - CARD_PAD, largura_top_interna)
    y4_final = y_meio - altura_top_card

    y_resumo = y3_final - GAP_ANTES_RESUMO  # y3_final == y4_final por construção
    y_apos_resumo = _desenhar_em_resumo(c, insights, y_resumo)

    _desenhar_rodape(c, dica, data_geracao, y_apos_resumo)

    if dados_pagamento is not None:
        # Import local (não no topo do arquivo) para evitar import
        # circular: dashboard_pagamento.py importa helpers DESTE módulo,
        # então este módulo não pode importar dashboard_pagamento.py no
        # nível de topo. c.showPage() fecha a página 1 de vez — nada
        # desenhado depois disso pode "vazar" para ela.
        from dashboard_pagamento import desenhar_pagina_metodo_pagamento

        c.showPage()
        desenhar_pagina_metodo_pagamento(
            c,
            mes_ano_titulo,
            data_inicio,
            data_fim,
            total_atual,
            dados_pagamento["n_transacoes"],
            dados_pagamento["ticket_medio_geral"],
            dados_pagamento["resumo_metodo"],
            resumo_categoria,
            dados_pagamento["evolucao_metodo_raw"],
            dados_pagamento["categoria_metodo_raw"],
            dados_pagamento["insights"],
            dica,
            data_geracao,
            nome_categoria_fn=nome_categoria,
            icone_categoria_fn=icone_categoria,
            cor_categoria_fn=cor_categoria,
        )

    c.save()