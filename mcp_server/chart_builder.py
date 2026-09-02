"""
Módulo de construção de gráficos para o relatório de gastos.

Centraliza paleta de cores e estilo visual, para manter consistência entre
todos os gráficos do relatório (e facilitar trocar o "tema" no futuro sem
mexer na lógica de geração do PDF).
"""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch

# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------

COR_PRIMARIA = "#4F46E5"       # indigo — cor de marca, usada em títulos/destaques
COR_PRIMARIA_CLARA = "#EEF2FF"
COR_TEXTO = "#111827"
COR_TEXTO_SECUNDARIO = "#6B7280"
COR_POSITIVO = "#12B76A"       # queda de gasto / variação boa
COR_NEGATIVO = "#F04438"       # alta de gasto / variação ruim
COR_GRADE = "#E5E7EB"
COR_FUNDO_CARD = "#F9FAFB"

# Uma cor fixa por categoria — assim a mesma categoria sempre aparece com a
# mesma cor em qualquer gráfico do relatório, o que ajuda a leitura.
CORES_CATEGORIA = {
    "alimentacao": "#F97066",
    "transporte": "#2E90FA",
    "moradia": "#7A5AF8",
    "saude": "#12B76A",
    "lazer": "#F79009",
    "educacao": "#06AED4",
    "compras": "#EE46BC",
    "assinaturas": "#667085",
    "outros": "#98A2B3",
}

# O banco guarda a categoria como slug sem acento (ex: "alimentacao"); este
# mapeamento é só para exibição no relatório.
NOMES_CATEGORIA = {
    "alimentacao": "Alimentação",
    "transporte": "Transporte",
    "moradia": "Moradia",
    "saude": "Saúde",
    "lazer": "Lazer",
    "educacao": "Educação",
    "compras": "Compras",
    "assinaturas": "Assinaturas",
    "outros": "Outros",
}


def nome_categoria(nome: str) -> str:
    return NOMES_CATEGORIA.get(nome, nome.capitalize())


def _cor_categoria(nome: str) -> str:
    return CORES_CATEGORIA.get(nome, "#98A2B3")


def _aplicar_estilo():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "text.color": COR_TEXTO,
        "axes.edgecolor": COR_GRADE,
        "axes.labelcolor": COR_TEXTO_SECUNDARIO,
        "xtick.color": COR_TEXTO_SECUNDARIO,
        "ytick.color": COR_TEXTO_SECUNDARIO,
        "axes.grid": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })


def _salvar(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

def grafico_distribuicao_categoria(resumo: list[dict], total: float) -> io.BytesIO:
    """
    Donut chart com o total no centro e legenda lateral (em vez de labels
    coladas nas fatias, que costumam poluir e sobrepor em relatórios com
    muitas categorias).
    """
    _aplicar_estilo()
    fig, ax = plt.subplots(figsize=(9, 5.2))

    categorias = [r["categoria"] for r in resumo]
    valores = [float(r["total"]) for r in resumo]
    cores = [_cor_categoria(c) for c in categorias]

    wedges, _ = ax.pie(
        valores,
        colors=cores,
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 3},
    )

    ax.text(0, 0.12, "Total", ha="center", va="center",
            fontsize=12, color=COR_TEXTO_SECUNDARIO)
    ax.text(0, -0.12, f"R$ {total:,.2f}".replace(",", "."), ha="center", va="center",
            fontsize=17, color=COR_TEXTO, fontweight="bold")

    ax.set_aspect("equal")

    legendas = [
        f"{nome_categoria(c)}  —  R$ {v:,.2f}  ({v/total*100:.1f}%)".replace(",", ".")
        for c, v in zip(categorias, valores)
    ]
    ax.legend(
        wedges, legendas,
        loc="center left", bbox_to_anchor=(1.05, 0.5),
        frameon=False, fontsize=10.5, labelcolor=COR_TEXTO,
        handlelength=1.2, handleheight=1.2,
    )

    fig.subplots_adjust(right=0.55)
    return _salvar(fig)


def grafico_evolucao_diaria(evolucao: list[dict]) -> io.BytesIO:
    """
    Barras diárias com linha de média tracejada e eixo Y em reais (grade
    horizontal leve para leitura, sem moldura ao redor do gráfico).
    """
    _aplicar_estilo()
    dias = [e["data_despesa"] for e in evolucao]
    valores = [float(e["total"]) for e in evolucao]
    media = sum(valores) / len(valores) if valores else 0

    fig, ax = plt.subplots(figsize=(11, 4.2))
    x = range(len(dias))
    ax.bar(x, valores, color=COR_PRIMARIA, width=0.65, zorder=3)
    ax.grid(axis="y", color=COR_GRADE, linewidth=0.7, zorder=0)

    ax.axhline(media, color=COR_TEXTO_SECUNDARIO, linestyle="--", linewidth=1, zorder=2)
    ax.text(len(x) - 0.5, media, f"  média: R$ {media:,.2f}".replace(",", "."),
            va="center", fontsize=9.5, color=COR_TEXTO_SECUNDARIO)

    passo = max(1, len(dias) // 12)
    ax.set_xticks(list(x)[::passo])
    ax.set_xticklabels([d.strftime("%d/%m") for d in dias[::passo]], fontsize=9)

    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: f"R$ {v:,.0f}".replace(",", "."))
    )
    ax.tick_params(axis="y", labelsize=9)

    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(COR_GRADE)
    ax.tick_params(left=False)
    ax.set_ylim(0, max(valores) * 1.25 if valores else 1)

    return _salvar(fig)