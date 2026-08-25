FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir nanobot-ai

# Dependências do servidor MCP (executado via stdio dentro deste container)
# em venv isolado: o expense_tools.py usa o SDK mcp 2.x, mas o nanobot
# exige mcp>=1.26,<2 — instalar no ambiente global quebraria o cliente
# MCP do próprio nanobot.
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/mcpvenv && \
    /opt/mcpvenv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

EXPOSE 18790

CMD ["nanobot", "gateway", "--verbose"]
