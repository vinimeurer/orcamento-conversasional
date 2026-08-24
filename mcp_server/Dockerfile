FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db/ ./db/
COPY mcp_server/ ./mcp_server/

ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8100

EXPOSE 8100

CMD ["python3", "mcp_server/expense_tools.py"]
