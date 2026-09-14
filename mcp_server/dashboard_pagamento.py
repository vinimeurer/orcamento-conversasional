"""
Pagina 2 do relatorio: panorama por metodo de pagamento.

Modulo separado da pagina 1 (dashboard_builder.py) - reaproveita os
helpers genericos de la (cards, molduras, titulo de secao, textos
ajustados/truncados, cabecalho, "em resumo", rodape), mas implementa suas
proprias versoes dos graficos de composicao/evolucao porque esses sao
dimensionados por metodo de pagamento, nao por categoria.

Ponto de entrada unico: desenhar_pagina_metodo_pagamento(...). O
dashboard_builder.py so chama essa funcao depois de fechar a pagina 1 com
c.showPage() - nenhum outro arquivo precisa saber como a pagina 2 e
montada por dentro.
"""
import io
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

import icons
from dash_style import (
    COR_CARD_BORDA, COR_PRIMARIA, COR_TEXTO, COR_TEXTO_SECUNDARIO,
    COR_TRILHO_BARRA, cor_metodo_pagamento, icone_metodo_pagamento,
    moeda, nome_metodo_pagamento,
)
from dashboard_builder import (
    ALTURA, CARD_PAD, GAP, GAP_ANTES_RESUMO, LARGURA, LARGURA_UTIL, MARGEM,
    _desenhar_cabecalho, _desenhar_em_resumo, _desenhar_kpi_card,
    _desenhar_linha_kpis, _desenhar_moldura_card, _desenhar_rodape,
    _desenhar_titulo_secao, _icone_badge, _texto_ajustado,
    _texto_centralizado, _truncar_com_reticencias,
)


# ---------------------------------------------------------------------------
# Agrupamento (mesmo espirito do _agrupar_top5_outros da pagina 1, so que
# por metodo de pagamento em vez de categoria)
# ---------------------------------------------------------------------------

def _agrupar_top5_outros_metodo(resumo: list[dict]) -> list[dict]:
    principais = [r for r in resumo if r["metodo_pagamento"] != "outros"]
    outros_real = next((r for r in resumo if r["metodo_pagamento"] == "outros"), None)

    if len(principais) <= 5:
        resultado = list(principais)
        if outros_real:
            resultado.append(outros_real)
        return resultado

    top = principais[:5]
    resto_total = sum(float(r["total"]) for r in principais[5:])
    resto_transacoes = sum(int(r["transacoes"]) for r in principais[5:])
    if outros_real:
        resto_total += float(outros_real["total"])
        resto_transacoes += int(outros_real["transacoes"])
    if resto_total > 0:
        top.append({
            "metodo_pagamento": "outros", "total": resto_total,
            "transacoes": resto_transacoes, "_rotulo_forcado": "Outros",
        })
    return top


# ---------------------------------------------------------------------------
# 1) Distribuicao dos gastos por tipo de pagamento (donut) + legenda
# ---------------------------------------------------------------------------

def _grafico_donut_metodo(resumo_donut: list[dict], total: float):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(5.2, 5.2))

    valores = [float(r["total"]) for r in resumo_donut]
    cores = [cor_metodo_pagamento(r["metodo_pagamento"]) for r in resumo_donut]

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


def _desenhar_distribuicao_metodo(c, resumo: list[dict], total: float, x, y_topo, largura,
                                   extra_gap_topo=0) -> float:
    _desenhar_titulo_secao(c, x, y_topo, "DISTRIBUIÇÃO POR PAGAMENTO", largura)
    resumo_donut = _agrupar_top5_outros_metodo(resumo)

    tam_img = largura * 0.50
    x_img = x + (largura - tam_img) / 2
    y_img = y_topo - 0.5 * cm - extra_gap_topo - tam_img
    c.drawImage(ImageReader(_grafico_donut_metodo(resumo_donut, total)),
                x_img, y_img, width=tam_img, height=tam_img, mask="auto")

    y = y_img - 0.35 * cm
    total_donut = sum(float(r["total"]) for r in resumo_donut)
    for r in resumo_donut:
        metodo = r["metodo_pagamento"]
        rotulo = r.get("_rotulo_forcado") or nome_metodo_pagamento(metodo)
        pct = (float(r["total"]) / total_donut * 100) if total_donut else 0
        cor = cor_metodo_pagamento(metodo)

        c.setFillColor(colors.HexColor(cor))
        c.circle(x + 0.12 * cm, y - 0.03 * cm, 0.11 * cm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica", 8.5)
        rotulo_final = _truncar_com_reticencias(c, rotulo, "Helvetica", 8.5, largura * 0.6)
        c.drawString(x + 0.4 * cm, y - 0.12 * cm, rotulo_final)
        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.drawRightString(x + largura, y - 0.12 * cm, f"{pct:.0f}%")
        y -= 0.42 * cm

    return y


# ---------------------------------------------------------------------------
# 2) Resumo por tipo de pagamento (tabela: transacoes, total, ticket medio)
# ---------------------------------------------------------------------------

def _desenhar_resumo_metodo(c, resumo: list[dict], x, y_topo, largura, altura_disponivel=None) -> float:
    """
    altura_disponivel: mesma ideia da lista de categorias da pagina 1 -
    se informado, as linhas se espacam dinamicamente para preencher esse
    espaco (usado para bater com a altura da coluna do donut ao lado).
    """
    _desenhar_titulo_secao(c, x, y_topo, "RESUMO POR TIPO DE PAGAMENTO", largura)
    y = y_topo - 0.55 * cm

    n = len(resumo)
    linha_altura_natural = 0.72 * cm
    if altura_disponivel is not None and n > 0:
        linha_altura = max(linha_altura_natural, (altura_disponivel - 0.55 * cm) / n)
    else:
        linha_altura = linha_altura_natural

    maior_ticket = max((float(r["total"]) / r["transacoes"] for r in resumo if r["transacoes"]), default=1)

    # Colunas numéricas ancoradas pela direita com largura fixa (números
    # têm largura praticamente constante, ao contrário do nome do método)
    # — assim a tabela continua legível não importa a largura da coluna.
    largura_ticket_col = 2.2 * cm
    largura_total_col = 1.9 * cm
    largura_transacoes_col = 1.3 * cm

    x_icone = x + 0.25 * cm
    x_nome = x + 0.65 * cm
    x_ticket = x + largura
    x_total = x_ticket - largura_ticket_col
    x_transacoes = x_total - largura_total_col
    largura_nome = x_transacoes - largura_transacoes_col - x_nome - 0.15 * cm

    c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
    c.setFont("Helvetica", 7.3)
    c.drawRightString(x_transacoes, y, "Transações")
    c.drawRightString(x_total, y, "Total (R$)")
    c.drawRightString(x_ticket, y, "Ticket médio")
    y -= 0.5 * cm

    for r in resumo:
        metodo = r["metodo_pagamento"]
        transacoes = int(r["transacoes"])
        total_metodo = float(r["total"])
        ticket = total_metodo / transacoes if transacoes else 0
        cor = cor_metodo_pagamento(metodo)

        _icone_badge(c, x_icone, y - 0.12 * cm, 0.28 * cm, icone_metodo_pagamento(metodo), cor_icone=COR_PRIMARIA)

        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica", 8.7)
        nome_final = _truncar_com_reticencias(c, nome_metodo_pagamento(metodo), "Helvetica", 8.7, largura_nome)
        c.drawString(x_nome, y - 0.18 * cm, nome_final)

        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica", 8.7)
        c.drawRightString(x_transacoes, y - 0.18 * cm, str(transacoes))

        c.setFont("Helvetica-Bold", 8.7)
        c.drawRightString(x_total, y - 0.18 * cm, moeda(total_metodo))

        c.drawRightString(x_ticket, y - 0.18 * cm, moeda(ticket))

        largura_barra = 2.3 * cm
        c.setFillColor(colors.HexColor(COR_TRILHO_BARRA))
        c.roundRect(x_ticket - largura_barra, y - 0.42 * cm, largura_barra, 0.1 * cm, 0.05 * cm, stroke=0, fill=1)
        larg_preenchida = largura_barra * (ticket / maior_ticket) if maior_ticket else 0
        if larg_preenchida > 0.01:
            c.setFillColor(colors.HexColor(cor))
            c.roundRect(x_ticket - largura_barra, y - 0.42 * cm, larg_preenchida, 0.1 * cm, 0.05 * cm, stroke=0, fill=1)

        y -= linha_altura

    return y


# ---------------------------------------------------------------------------
# 3) Evolucao diaria dos gastos por tipo de pagamento (multi-linha, largura
#    cheia)
# ---------------------------------------------------------------------------

def _pivotar_evolucao_metodo(evolucao_raw: list[dict], data_inicio: str, data_fim: str):
    import datetime

    di = datetime.date.fromisoformat(data_inicio)
    df = datetime.date.fromisoformat(data_fim)
    dias = []
    d = di
    while d <= df:
        dias.append(d)
        d += datetime.timedelta(days=1)

    totais = defaultdict(float)
    for r in evolucao_raw:
        totais[r["metodo_pagamento"]] += float(r["total"])
    metodos_ordenados = sorted(totais.keys(), key=lambda m: -totais[m])

    valores = {m: {d: 0.0 for d in dias} for m in metodos_ordenados}
    for r in evolucao_raw:
        valores[r["metodo_pagamento"]][r["data_despesa"]] = float(r["total"])

    return dias, metodos_ordenados, valores


def _grafico_evolucao_metodo(dias, metodos, valores):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9,
        "text.color": COR_TEXTO_SECUNDARIO, "axes.edgecolor": "#E5E9F0",
        "xtick.color": COR_TEXTO_SECUNDARIO, "ytick.color": COR_TEXTO_SECUNDARIO,
    })
    fig, ax = plt.subplots(figsize=(11.5, 3.6))

    x = range(len(dias))
    for m in metodos:
        y = [valores[m][d] for d in dias]
        ax.plot(x, y, color=cor_metodo_pagamento(m), linewidth=1.4,
                 marker="o", markersize=2.4, markerfacecolor="white",
                 markeredgecolor=cor_metodo_pagamento(m), markeredgewidth=0.9, zorder=3)

    passo = max(1, len(dias) // 15)
    ax.set_xticks(list(x)[::passo])
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


def _desenhar_legenda_metodos(c, metodos, x, y_topo, largura) -> float:
    """Legenda horizontal (bolinha colorida + nome), quebrando pra nova
    linha se nao couber tudo na largura disponivel — usada abaixo dos
    graficos de evolucao e de categoria x metodo."""
    x_atual = x
    y_atual = y_topo
    altura_linha = 0.4 * cm
    for m in metodos:
        rotulo = nome_metodo_pagamento(m)
        c.setFont("Helvetica", 8)
        largura_item = 0.35 * cm + c.stringWidth(rotulo, "Helvetica", 8) + 0.35 * cm
        if x_atual + largura_item > x + largura and x_atual > x:
            x_atual = x
            y_atual -= altura_linha
        c.setFillColor(colors.HexColor(cor_metodo_pagamento(m)))
        c.circle(x_atual + 0.09 * cm, y_atual - 0.03 * cm, 0.09 * cm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
        c.drawString(x_atual + 0.28 * cm, y_atual - 0.12 * cm, rotulo)
        x_atual += largura_item
    return y_atual - altura_linha


def _desenhar_evolucao_metodo(c, evolucao_raw: list[dict], data_inicio: str, data_fim: str,
                               x, y_topo, largura, altura_img=None) -> float:
    _desenhar_titulo_secao(c, x, y_topo, "EVOLUÇÃO DIÁRIA POR TIPO DE PAGAMENTO", largura,
                            "Valor gasto por dia (R$)")
    dias, metodos, valores = _pivotar_evolucao_metodo(evolucao_raw, data_inicio, data_fim)

    if altura_img is None:
        altura_img = largura * 0.09
    y_img = y_topo - 0.5 * cm - altura_img
    c.drawImage(ImageReader(_grafico_evolucao_metodo(dias, metodos, valores)),
                x, y_img, width=largura, height=altura_img, mask="auto")

    y_legenda = _desenhar_legenda_metodos(c, metodos, x, y_img - 0.35 * cm, largura)
    return y_legenda


# ---------------------------------------------------------------------------
# 4) Gastos por categoria e tipo de pagamento (barras empilhadas, largura
#    cheia)
# ---------------------------------------------------------------------------

def _pivotar_categoria_metodo(categoria_metodo_raw: list[dict]) -> dict:
    """Retorna {categoria: {metodo: total}}."""
    matriz = defaultdict(dict)
    for r in categoria_metodo_raw:
        matriz[r["categoria"]][r["metodo_pagamento"]] = float(r["total"])
    return matriz


def _desenhar_categoria_metodo(c, resumo_categoria: list[dict], categoria_metodo_raw: list[dict],
                                ordem_metodos: list[str], x, y_topo, largura,
                                nome_categoria_fn, icone_categoria_fn, cor_categoria_fn,
                                altura_disponivel=None) -> float:
    """
    resumo_categoria: [{"categoria": ..., "total": ...}, ...] já ordenado
    (mesma ordem/dados usados na página 1, para os dois panoramas baterem).
    nome_categoria_fn/icone_categoria_fn/cor_categoria_fn: passadas de fora
    (vêm de dash_style, mas para CATEGORIA, não método — evita import
    circular e deixa este módulo agnóstico sobre qual dicionário usar).
    """
    _desenhar_titulo_secao(c, x, y_topo, "GASTOS POR CATEGORIA E TIPO DE PAGAMENTO", largura)
    y = y_topo - 0.6 * cm

    n = len(resumo_categoria)
    linha_altura_natural = 0.40 * cm
    if altura_disponivel is not None and n > 0:
        linha_altura = max(linha_altura_natural, (altura_disponivel - 0.6 * cm) / n)
    else:
        linha_altura = linha_altura_natural

    matriz = _pivotar_categoria_metodo(categoria_metodo_raw)

    x_icone = x + 0.22 * cm
    x_label = x + 0.6 * cm
    largura_label = largura * 0.18
    x_total = x + largura * 0.30
    x_barra = x + largura * 0.34
    largura_barra = x + largura - x_barra

    c.setFillColor(colors.HexColor(COR_TEXTO_SECUNDARIO))
    c.setFont("Helvetica", 7.3)
    c.drawString(x_label, y, "Categoria")
    c.drawRightString(x_total, y, "Total (R$)")
    c.drawString(x_barra, y, "Composição por tipo de pagamento")
    y -= 0.5 * cm

    for r in resumo_categoria:
        cat = r["categoria"]
        total_cat = float(r["total"])
        cor_cat = cor_categoria_fn(cat)

        _icone_badge(c, x_icone, y - 0.12 * cm, 0.26 * cm, icone_categoria_fn(cat), cor_icone=COR_PRIMARIA)
        c.setFillColor(colors.HexColor(COR_TEXTO))
        c.setFont("Helvetica", 8.7)
        nome_final = _truncar_com_reticencias(c, nome_categoria_fn(cat), "Helvetica", 8.7, largura_label)
        c.drawString(x_label, y - 0.18 * cm, nome_final)

        c.setFont("Helvetica-Bold", 8.5)
        c.drawRightString(x_total, y - 0.18 * cm, moeda(total_cat))

        x_seg = x_barra
        altura_barra = 0.34 * cm
        y_barra = y - 0.32 * cm
        c.setFillColor(colors.HexColor(COR_TRILHO_BARRA))
        c.roundRect(x_barra, y_barra, largura_barra, altura_barra, 0.06 * cm, stroke=0, fill=1)

        segmentos = matriz.get(cat, {})
        for metodo in ordem_metodos:
            valor_seg = segmentos.get(metodo, 0)
            if valor_seg <= 0:
                continue
            largura_seg = largura_barra * (valor_seg / total_cat) if total_cat else 0
            c.setFillColor(colors.HexColor(cor_metodo_pagamento(metodo)))
            c.rect(x_seg, y_barra, largura_seg, altura_barra, stroke=0, fill=1)
            pct_seg = valor_seg / total_cat * 100 if total_cat else 0
            if largura_seg > 0.85 * cm:
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 6.8)
                c.drawCentredString(x_seg + largura_seg / 2, y_barra + altura_barra / 2 - 0.09 * cm,
                                     f"{pct_seg:.0f}%")
            x_seg += largura_seg

        y -= linha_altura

    y_legenda = _desenhar_legenda_metodos(c, ordem_metodos, x, y - 0.15 * cm, largura)
    return y_legenda


# ---------------------------------------------------------------------------
# Ponto de entrada da página 2
# ---------------------------------------------------------------------------

def desenhar_pagina_metodo_pagamento(
    c,
    mes_ano_titulo: str,
    data_inicio: str,
    data_fim: str,
    total_atual: float,
    n_transacoes: int,
    ticket_medio_geral: float,
    resumo_metodo: list[dict],
    resumo_categoria: list[dict],
    evolucao_metodo_raw: list[dict],
    categoria_metodo_raw: list[dict],
    insights_pagamento: list[dict],
    dica: str,
    data_geracao: str,
    nome_categoria_fn,
    icone_categoria_fn,
    cor_categoria_fn,
) -> None:
    """
    Desenha a página 2 inteira (panorama por método de pagamento) na
    página CORRENTE do canvas — quem chama já deve ter feito c.showPage()
    antes, então nada daqui pode "vazar" pra página 1.

    resumo_metodo: [{"metodo_pagamento", "transacoes", "total"}, ...]
    ordenado por total decrescente.
    resumo_categoria: mesma lista/ordem já usada na página 1 (garante que
    os dois panoramas batem entre si).
    """
    metodo_top_transacoes = max(resumo_metodo, key=lambda r: r["transacoes"]) if resumo_metodo else None
    pct_top_transacoes = (
        metodo_top_transacoes["transacoes"] / n_transacoes * 100
        if metodo_top_transacoes and n_transacoes else 0
    )
    ticket_top = (
        float(metodo_top_transacoes["total"]) / metodo_top_transacoes["transacoes"]
        if metodo_top_transacoes and metodo_top_transacoes["transacoes"] else 0
    )
    nome_top = nome_metodo_pagamento(metodo_top_transacoes["metodo_pagamento"]) if metodo_top_transacoes else "—"

    y = ALTURA - MARGEM
    y = _desenhar_cabecalho(
        c, mes_ano_titulo, data_inicio, data_fim, y,
        icone_card="card", linha1_card="Visão geral dos gastos",
        linha2_card="por tipo de pagamento.",
    )

    cards = [
        dict(icone="wallet", label="Gasto total", valor=moeda(total_atual),
             subtitulo="Total gasto no período"),
        dict(icone="list", label="Nº de transações", valor=str(n_transacoes),
             subtitulo="Total de lançamentos"),
        dict(icone="barchart", label="Ticket médio geral", valor=moeda(ticket_medio_geral),
             subtitulo="Média por transação"),
        dict(icone=icone_metodo_pagamento(metodo_top_transacoes["metodo_pagamento"]) if metodo_top_transacoes else "card",
             label="Meio mais utilizado", valor=nome_top,
             subtitulo=(f"{metodo_top_transacoes['transacoes']} transações ({pct_top_transacoes:.0f}%)"
                        if metodo_top_transacoes else None)),
        dict(icone=icone_metodo_pagamento(metodo_top_transacoes["metodo_pagamento"]) if metodo_top_transacoes else "card",
             label="Ticket médio do mais usado", valor=moeda(ticket_top),
             subtitulo=nome_top),
    ]
    y = _desenhar_linha_kpis(c, cards, y)

    # =====================================================================
    # Linha 1: Distribuição por pagamento (donut) | Resumo por tipo de
    # pagamento (tabela). Mesma lógica de equalização de altura da página 1.
    # =====================================================================
    largura_col1 = LARGURA_UTIL * 0.44
    largura_col2 = LARGURA_UTIL * 0.52
    x_col2 = MARGEM + LARGURA_UTIL - largura_col2
    y_secoes = y

    largura_donut_interna = largura_col1 - 2 * CARD_PAD
    n_metodo_donut = len(_agrupar_top5_outros_metodo(resumo_metodo))
    tam_img_donut = largura_donut_interna * 0.50
    altura_donut_natural = 0.5 * cm + tam_img_donut + 0.35 * cm + n_metodo_donut * 0.42 * cm + 2 * CARD_PAD

    largura_tab_interna = largura_col2 - 2 * CARD_PAD
    n_metodo = len(resumo_metodo)
    altura_tab_natural = 0.55 * cm + n_metodo * 0.72 * cm + 2 * CARD_PAD

    if altura_donut_natural >= altura_tab_natural:
        altura_tab_card = altura_donut_natural
        altura_donut_card = altura_donut_natural
        extra_gap_donut = 0
        disp_tab = altura_tab_card - 2 * CARD_PAD
    else:
        altura_tab_card = altura_tab_natural
        altura_donut_card = altura_tab_natural
        extra_gap_donut = altura_donut_card - altura_donut_natural
        disp_tab = None

    _desenhar_moldura_card(c, MARGEM, y_secoes, largura_col1, altura_donut_card)
    _desenhar_distribuicao_metodo(
        c, resumo_metodo, total_atual, MARGEM + CARD_PAD, y_secoes - CARD_PAD,
        largura_donut_interna, extra_gap_topo=extra_gap_donut,
    )

    _desenhar_moldura_card(c, x_col2, y_secoes, largura_col2, altura_tab_card)
    _desenhar_resumo_metodo(
        c, resumo_metodo, x_col2 + CARD_PAD, y_secoes - CARD_PAD,
        largura_tab_interna, altura_disponivel=disp_tab,
    )

    y_apos_linha1 = y_secoes - altura_donut_card - GAP  # == altura_tab_card por construção

    # =====================================================================
    # Linha 2: Evolução diária por tipo de pagamento (largura cheia)
    # =====================================================================
    largura_evo_interna = LARGURA_UTIL - 2 * CARD_PAD
    altura_img_evo = largura_evo_interna * 0.09
    altura_evo_card = 0.5 * cm + altura_img_evo + 0.35 * cm + 0.4 * cm + 2 * CARD_PAD

    _desenhar_moldura_card(c, MARGEM, y_apos_linha1, LARGURA_UTIL, altura_evo_card)
    _desenhar_evolucao_metodo(
        c, evolucao_metodo_raw, data_inicio, data_fim,
        MARGEM + CARD_PAD, y_apos_linha1 - CARD_PAD, largura_evo_interna, altura_img=altura_img_evo,
    )
    y_apos_linha2 = y_apos_linha1 - altura_evo_card - GAP

    # =====================================================================
    # Linha 3: Gastos por categoria e tipo de pagamento (largura cheia)
    # =====================================================================
    largura_cm_interna = LARGURA_UTIL - 2 * CARD_PAD
    n_cat = len(resumo_categoria)
    altura_cm_card = 0.6 * cm + n_cat * 0.40 * cm + 0.55 * cm + 2 * CARD_PAD

    ordem_metodos_geral = [r["metodo_pagamento"] for r in resumo_metodo]

    _desenhar_moldura_card(c, MARGEM, y_apos_linha2, LARGURA_UTIL, altura_cm_card)
    _desenhar_categoria_metodo(
        c, resumo_categoria, categoria_metodo_raw, ordem_metodos_geral,
        MARGEM + CARD_PAD, y_apos_linha2 - CARD_PAD, largura_cm_interna,
        nome_categoria_fn, icone_categoria_fn, cor_categoria_fn,
    )
    y_apos_linha3 = y_apos_linha2 - altura_cm_card - GAP_ANTES_RESUMO

    # =====================================================================
    # Em resumo + rodapé (reaproveita as funções genéricas da página 1)
    # =====================================================================
    y_apos_resumo = _desenhar_em_resumo(c, insights_pagamento, y_apos_linha3)
    _desenhar_rodape(c, dica, data_geracao, y_apos_resumo)