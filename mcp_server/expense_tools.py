import datetime
import sys
from pathlib import Path

from mcp.server import MCPServer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import get_cursor, get_or_create_usuario

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
