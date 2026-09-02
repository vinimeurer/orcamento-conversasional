import datetime
import sys
import os
import tempfile
import requests

from mcp.server import MCPServer

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import get_cursor, get_or_create_usuario
from pdf_builder import montar_pdf

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


def _despesas_periodo(usuario_id: int, data_inicio: str, data_fim: str) -> list[dict]:
    """
    Busca as despesas individuais do período (não agregadas), usadas nos
    detalhamentos por categoria e por dia do relatório em PDF.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT d.valor, d.descricao, c.nome AS categoria, d.data_despesa
            FROM despesas d
            JOIN categorias c ON c.id = d.categoria_id
            WHERE d.usuario_id = %s AND d.data_despesa BETWEEN %s AND %s
            ORDER BY d.data_despesa ASC
            """,
            (usuario_id, data_inicio, data_fim),
        )
        return [dict(r) for r in cur.fetchall()]


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
    Gera um relatório de gastos de um único período em PDF, com gráficos de
    distribuição por categoria, evolução diária, e detalhamento por
    categoria e por dia. Não faz comparação com períodos anteriores — é uma
    visão fechada do período consultado (ex: os gastos do mês). Envia o
    PDF diretamente para o usuário no Telegram.

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
    despesas = _despesas_periodo(usuario_id, data_inicio, data_fim)
    total_atual = sum(float(r["total"]) for r in resumo_categoria)

    if not resumo_categoria:
        return {
            "sucesso": False,
            "erro": "Não há despesas registradas nesse período para gerar o relatório.",
        }

    # despesa individual de maior valor no período — usada no "destaque" do relatório
    
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

    with tempfile.TemporaryDirectory() as tmp:
        caminho_pdf = os.path.join(tmp, f"relatorio_{data_inicio}_a_{data_fim}.pdf")
        montar_pdf(
            caminho_pdf,
            data_inicio,
            data_fim,
            total_atual,
            resumo_categoria,
            evolucao,
            despesas,
            maior_despesa,
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