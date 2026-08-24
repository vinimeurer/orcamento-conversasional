import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool

_pool: SimpleConnectionPool | None = None


def _dsn() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://orcamento:orcamento@localhost:5432/orcamento",
    )


def get_pool() -> SimpleConnectionPool:
    """
    Cria o pool de conexões na primeira chamada e reutiliza nas seguintes.

    Por que: abrir uma conexão nova por chamada de tool é desnecessariamente
    caro para um agente que roda em loop contínuo (Nanobot). Um pool pequeno
    evita esse custo sem introduzir complexidade de um ORM.
    """
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(minconn=1, maxconn=5, dsn=_dsn())
    return _pool


@contextmanager
def get_cursor(commit: bool = False):
    """
    Fornece um cursor com dicionários como resultado (RealDictCursor).

    Por que: os tools do MCP retornam JSON para a LLM, então já receber
    linhas como dict evita conversões manuais em cada tool.
    """
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def get_or_create_usuario(telegram_id: int, nome: str | None = None) -> int:
    """
    Garante que o usuário do Telegram exista na tabela `usuarios` e retorna
    seu id interno.

    Por que: os tools recebem apenas o telegram_id vindo do canal; a
    resolução para o id interno fica centralizada aqui para não duplicar
    essa lógica em cada tool.
    """
    with get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT id FROM usuarios WHERE telegram_id = %s",
            (telegram_id,),
        )
        row = cur.fetchone()
        if row:
            return row["id"]

        cur.execute(
            "INSERT INTO usuarios (telegram_id, nome) VALUES (%s, %s) RETURNING id",
            (telegram_id, nome),
        )
        return cur.fetchone()["id"]
