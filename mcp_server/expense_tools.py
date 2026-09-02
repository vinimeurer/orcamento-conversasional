import datetime
import sys
import io
import os
import tempfile
import matplotlib
import matplotlib.pyplot as plt
import requests

from datetime import timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from mcp.server import MCPServer

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

matplotlib.use("Agg")  # backend sem display, necessário em container

from db.connection import get_cursor, get_or_create_usuario

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

server = MCPServer(
    name="orcamento-despesas",
    instructions=(
        "Ferramentas para registrar e consultar despesas pessoais. "
        "Use registrar_despesa sempre que o usuário relatar um gasto, e "
        "listar_despesas ou resumo_por_categoria quando ele pedir para "
        "consultar ou entender seus gastos em um período."
    ),
)

CATEGORIAS_VALIDAS = (
    "alimentacao",
    "transporte",
    "moradia",
    "saude",
    "lazer",
    "educacao",
    "compras",
    "assinaturas",
    "outros",
)


@server.tool()
def registrar_despesa(
    telegram_id: int,
    valor: float,
    descricao: str,
    categoria: str,
    forma_pagamento: str | None = None,
    data_despesa: str | None = None,
    mensagem_original: str | None = None,
) -> dict:
    """
    Registra uma despesa a partir de uma mensagem em linguagem natural já
    interpretada pelo agente.

    Args:
        telegram_id: id numérico do usuário no Telegram.
        valor: valor da despesa em reais, sempre positivo.
        descricao: descrição curta do gasto (ex: "almoço", "uber").
        categoria: uma das categorias válidas; use "outros" se não tiver
            certeza.
        forma_pagamento: opcional, ex. "cartão", "pix", "dinheiro".
        data_despesa: data no formato YYYY-MM-DD; se omitida, usa hoje.
        mensagem_original: texto original enviado pelo usuário, para
            auditoria e futura correção manual.
    """
    if valor <= 0:
        return {"sucesso": False, "erro": "O valor da despesa deve ser positivo."}

    categoria_normalizada = categoria.strip().lower()
    if categoria_normalizada not in CATEGORIAS_VALIDAS:
        categoria_normalizada = "outros"

    data_final = data_despesa or datetime.date.today().isoformat()

    usuario_id = get_or_create_usuario(telegram_id)

    with get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT id FROM categorias WHERE nome = %s",
            (categoria_normalizada,),
        )
        categoria_id = cur.fetchone()["id"]

        cur.execute(
            """
            INSERT INTO despesas
                (usuario_id, valor, descricao, categoria_id,
                 forma_pagamento, data_despesa, mensagem_original)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                usuario_id,
                valor,
                descricao,
                categoria_id,
                forma_pagamento,
                data_final,
                mensagem_original,
            ),
        )
        despesa_id = cur.fetchone()["id"]

    return {
        "sucesso": True,
        "despesa_id": despesa_id,
        "valor": valor,
        "descricao": descricao,
        "categoria": categoria_normalizada,
        "data_despesa": data_final,
    }


@server.tool()
def listar_despesas(
    telegram_id: int,
    data_inicio: str,
    data_fim: str,
    categoria: str | None = None,
) -> dict:
    """
    Lista despesas de um usuário dentro de um período, opcionalmente
    filtradas por categoria.

    Args:
        telegram_id: id numérico do usuário no Telegram.
        data_inicio: data inicial no formato YYYY-MM-DD, inclusiva.
        data_fim: data final no formato YYYY-MM-DD, inclusiva.
        categoria: opcional, filtra por uma categoria específica.
    """
    usuario_id = get_or_create_usuario(telegram_id)

    query = """
        SELECT d.id, d.valor, d.descricao, c.nome AS categoria,
               d.forma_pagamento, d.data_despesa
        FROM despesas d
        JOIN categorias c ON c.id = d.categoria_id
        WHERE d.usuario_id = %s
          AND d.data_despesa BETWEEN %s AND %s
    """
    params: list = [usuario_id, data_inicio, data_fim]

    if categoria:
        query += " AND c.nome = %s"
        params.append(categoria.strip().lower())

    query += " ORDER BY d.data_despesa DESC, d.id DESC"

    with get_cursor() as cur:
        cur.execute(query, params)
        despesas = cur.fetchall()

    total = sum(float(d["valor"]) for d in despesas)

    return {
        "periodo": {"inicio": data_inicio, "fim": data_fim},
        "total_gasto": round(total, 2),
        "quantidade": len(despesas),
        "despesas": [dict(d) for d in despesas],
    }


@server.tool()
def resumo_por_categoria(
    telegram_id: int,
    data_inicio: str,
    data_fim: str,
) -> dict:
    """
    Retorna o total gasto por categoria em um período, ordenado do maior
    para o menor. Útil para responder perguntas como "onde gastei mais
    este mês".

    Args:
        telegram_id: id numérico do usuário no Telegram.
        data_inicio: data inicial no formato YYYY-MM-DD, inclusiva.
        data_fim: data final no formato YYYY-MM-DD, inclusiva.
    """
    usuario_id = get_or_create_usuario(telegram_id)

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT c.nome AS categoria,
                   COUNT(d.id) AS quantidade,
                   SUM(d.valor) AS total
            FROM despesas d
            JOIN categorias c ON c.id = d.categoria_id
            WHERE d.usuario_id = %s
              AND d.data_despesa BETWEEN %s AND %s
            GROUP BY c.nome
            ORDER BY total DESC
            """,
            (usuario_id, data_inicio, data_fim),
        )
        linhas = cur.fetchall()

    total_geral = sum(float(linha["total"]) for linha in linhas)

    return {
        "periodo": {"inicio": data_inicio, "fim": data_fim},
        "total_geral": round(total_geral, 2),
        "por_categoria": [
            {
                "categoria": linha["categoria"],
                "quantidade": linha["quantidade"],
                "total": round(float(linha["total"]), 2),
                "percentual": (
                    round(float(linha["total"]) / total_geral * 100, 1)
                    if total_geral > 0
                    else 0.0
                ),
            }
            for linha in linhas
        ],
    }


















###################################################################

def _periodo_anterior(data_inicio: str, data_fim: str) -> tuple[str, str]:
    """
    Calcula o período imediatamente anterior, com a mesma duração do
    período informado, para permitir comparação (RF28-RF30).
    """
    inicio = datetime.date.fromisoformat(data_inicio)
    fim = datetime.date.fromisoformat(data_fim)
    duracao = (fim - inicio).days + 1
    novo_fim = inicio - timedelta(days=1)
    novo_inicio = novo_fim - timedelta(days=duracao - 1)
    return novo_inicio.isoformat(), novo_fim.isoformat()


def _resumo_categoria_periodo(usuario_id: int, data_inicio: str, data_fim: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT c.nome AS categoria, SUM(d.valor) AS total
            FROM despesas d
            JOIN categorias c ON c.id = d.categoria_id
            WHERE d.usuario_id = %s AND d.data_despesa BETWEEN %s AND %s
            GROUP BY c.nome
            ORDER BY total DESC
            """,
            (usuario_id, data_inicio, data_fim),
        )
        return [dict(r) for r in cur.fetchall()]


def _evolucao_diaria(usuario_id: int, data_inicio: str, data_fim: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT data_despesa, SUM(valor) AS total
            FROM despesas
            WHERE usuario_id = %s AND data_despesa BETWEEN %s AND %s
            GROUP BY data_despesa
            ORDER BY data_despesa
            """,
            (usuario_id, data_inicio, data_fim),
        )
        return [dict(r) for r in cur.fetchall()]


def _grafico_pizza_categoria(resumo: list[dict]) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.pie(
        [float(r["total"]) for r in resumo],
        labels=[r["categoria"] for r in resumo],
        autopct="%1.1f%%",
        startangle=90,
    )
    ax.set_title("Distribuição de gastos por categoria")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _grafico_evolucao_diaria(evolucao: list[dict]) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(10, 4))
    dias = [e["data_despesa"].strftime("%d/%m") for e in evolucao]
    valores = [float(e["total"]) for e in evolucao]
    ax.bar(dias, valores, color="#4C72B0")
    ax.set_title("Evolução diária de gastos")
    ax.set_ylabel("R$")
    plt.xticks(rotation=90, fontsize=6)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _montar_pdf(
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
    doc = SimpleDocTemplate(caminho, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle("titulo", parent=styles["Title"], fontSize=18)
    subtitulo = styles["Heading2"]
    corpo = styles["BodyText"]

    variacao_pct = None
    if total_anterior > 0:
        variacao_pct = round((total_atual - total_anterior) / total_anterior * 100, 1)

    elementos = [
        Paragraph("Relatório de Gastos", titulo),
        Paragraph(f"Período: {data_inicio} a {data_fim}", corpo),
        Spacer(1, 0.4 * cm),
    ]

    resumo_txt = f"<b>Total gasto:</b> R$ {total_atual:.2f}"
    if variacao_pct is not None:
        resumo_txt += f" &nbsp;&nbsp; <b>Variação vs. período anterior:</b> {variacao_pct:+.1f}%"
    elementos.append(Paragraph(resumo_txt, corpo))

    if maior_despesa:
        elementos.append(Paragraph(
            f"<b>Maior despesa do período:</b> R$ {maior_despesa['valor']:.2f} "
            f"— {maior_despesa['descricao']} ({maior_despesa['data_despesa']})",
            corpo,
        ))
    if categoria_destaque:
        elementos.append(Paragraph(f"<b>Destaque:</b> {categoria_destaque}", corpo))

    elementos.append(Spacer(1, 0.5 * cm))

    if resumo_categoria:
        elementos.append(Paragraph("Distribuição por categoria", subtitulo))
        elementos.append(Image(_grafico_pizza_categoria(resumo_categoria), width=14 * cm, height=8.4 * cm))
        elementos.append(Spacer(1, 0.3 * cm))

    if evolucao:
        elementos.append(Paragraph("Evolução diária", subtitulo))
        elementos.append(Image(_grafico_evolucao_diaria(evolucao), width=16 * cm, height=6.4 * cm))
        elementos.append(Spacer(1, 0.5 * cm))

    if resumo_categoria:
        elementos.append(Paragraph("Detalhamento por categoria", subtitulo))
        dados = [["Categoria", "Total (R$)"]]
        for r in resumo_categoria:
            dados.append([r["categoria"], f'{r["total"]:.2f}'])
        tabela = Table(dados, colWidths=[9 * cm, 5 * cm])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C72B0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elementos.append(tabela)

    doc.build(elementos)


def _enviar_pdf_telegram(telegram_id: int, caminho: str, legenda: str) -> bool:
    """
    Envia o PDF diretamente pela API do Telegram (sendDocument), sem
    depender do Nanobot interpretar um artefato retornado pelo MCP.

    Nota de arquitetura: isso acopla esta tool ao canal Telegram
    especificamente (RNF45 previa desacoplamento entre agente e
    ferramentas). Foi uma escolha deliberada — a alternativa (devolver o
    PDF como recurso MCP e confiar que o Nanobot repassa como anexo) não
    tem suporte documentado/testado no framework para o tipo "resource"
    do MCP. Se isso mudar em uma versão futura do Nanobot, esta função
    pode ser removida e a tool pode voltar a apenas retornar o arquivo.
    """
    if not TELEGRAM_TOKEN:
        return False, "TELEGRAM_TOKEN não está definido no ambiente do servidor MCP."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    try:
        with open(caminho, "rb") as f:
            resp = requests.post(
                url,
                data={"chat_id": telegram_id, "caption": legenda},
                files={"document": (os.path.basename(caminho), f, "application/pdf")},
                timeout=30,
            )
        if resp.ok:
            return True, None
        return False, f"Telegram respondeu {resp.status_code}: {resp.text[:300]}"
    except requests.RequestException as exc:
        # Falha de rede/timeout não pode derrubar a tool inteira — o
        # chamador trata isso como "não foi possível enviar" e informa
        # o usuário de forma controlada.
        return False, f"Erro de rede ao chamar a API do Telegram: {exc}"


@server.tool()
def gerar_relatorio_pdf(
    telegram_id: int,
    data_inicio: str,
    data_fim: str,
) -> dict:
    """
    Gera um relatório de gastos em PDF, com gráficos de distribuição por
    categoria e evolução diária, comparação com o período anterior e
    detalhamento por categoria. Envia o PDF diretamente para o usuário
    no Telegram.

    IMPORTANTE: data_inicio e data_fim são obrigatórios. Se o usuário
    pedir um relatório sem informar um período, pergunte o período antes
    de chamar esta ferramenta — nunca assuma um período por conta própria.

    Args:
        telegram_id: id numérico do usuário no Telegram.
        data_inicio: data inicial no formato YYYY-MM-DD, inclusiva.
        data_fim: data final no formato YYYY-MM-DD, inclusiva.
    """
    usuario_id = get_or_create_usuario(telegram_id)

    resumo_categoria = _resumo_categoria_periodo(usuario_id, data_inicio, data_fim)
    evolucao = _evolucao_diaria(usuario_id, data_inicio, data_fim)
    total_atual = sum(float(r["total"]) for r in resumo_categoria)

    if not resumo_categoria:
        return {
            "sucesso": False,
            "erro": "Não há despesas registradas nesse período para gerar o relatório.",
        }

    data_inicio_ant, data_fim_ant = _periodo_anterior(data_inicio, data_fim)
    resumo_anterior = _resumo_categoria_periodo(usuario_id, data_inicio_ant, data_fim_ant)
    total_anterior = sum(float(r["total"]) for r in resumo_anterior)

    # despesa individual de maior valor, e categoria com maior alta em
    # relação ao período anterior — usados nos "destaques" do relatório
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT valor, descricao, data_despesa
            FROM despesas
            WHERE usuario_id = %s AND data_despesa BETWEEN %s AND %s
            ORDER BY valor DESC LIMIT 1
            """,
            (usuario_id, data_inicio, data_fim),
        )
        maior_despesa = cur.fetchone()
        maior_despesa = dict(maior_despesa) if maior_despesa else None

    anterior_por_categoria = {r["categoria"]: float(r["total"]) for r in resumo_anterior}
    categoria_destaque = None
    maior_alta_pct = 0.0
    for r in resumo_categoria:
        cat = r["categoria"]
        atual = float(r["total"])
        antes = anterior_por_categoria.get(cat, 0.0)
        if antes > 0:
            variacao = (atual - antes) / antes * 100
            if variacao > maior_alta_pct:
                maior_alta_pct = variacao
                categoria_destaque = (
                    f"Gastos com {cat} subiram {variacao:.0f}% em relação ao período anterior."
                )

    with tempfile.TemporaryDirectory() as tmp:
        caminho_pdf = os.path.join(tmp, f"relatorio_{data_inicio}_a_{data_fim}.pdf")
        _montar_pdf(
            caminho_pdf,
            data_inicio,
            data_fim,
            total_atual,
            total_anterior,
            resumo_categoria,
            evolucao,
            maior_despesa,
            categoria_destaque,
        )

        legenda = f"Relatório de gastos: {data_inicio} a {data_fim}"
        enviado, motivo_falha = _enviar_pdf_telegram(telegram_id, caminho_pdf, legenda)

    if not enviado:
        # O motivo detalhado fica em "detalhe_tecnico" (não em "erro") de
        # propósito: assim o SOUL.md pode instruir o agente a nunca repetir
        # esse texto técnico pro usuário (RNF11), mas ele ainda aparece no
        # log de "Tool call" do Nanobot pra você diagnosticar.
        return {
            "sucesso": False,
            "erro": "O relatório foi gerado, mas não foi possível enviá-lo pelo Telegram.",
            "detalhe_tecnico": motivo_falha,
        }

    return {
        "sucesso": True,
        "total_gasto": round(total_atual, 2),
        "periodo": {"inicio": data_inicio, "fim": data_fim},
    }




###################################################################












if __name__ == "__main__":
    import os

    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "stdio":
        server.run(transport="stdio")
    else:
        # Modo HTTP: usado quando o servidor roda em seu próprio container e
        # o Nanobot se conecta por rede em vez de subprocesso. stateless_http
        # evita depender de sessão entre chamadas, o que não é necessário
        # para tools simples de leitura/escrita.
        server.run(
            transport="streamable-http",
            host=os.environ.get("MCP_HOST", "0.0.0.0"),
            port=int(os.environ.get("MCP_PORT", "8100")),
            stateless_http=True,
        )
