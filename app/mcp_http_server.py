"""
Servidor MCP externo do FleetOps via Streamable HTTP.

Execução local:
    python -m app.mcp_http_server

Endpoint:
    http://127.0.0.1:8001/mcp

Em Docker, o servidor escuta em 0.0.0.0 para permitir acesso
a partir do host e de outros containers.
"""

import os

from app.mcp_server import mcp


HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8001"))
PATH = os.getenv("MCP_PATH", "/mcp")


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=HOST,
        port=PORT,
        streamable_http_path=PATH,
        stateless_http=True,
        json_response=True,
    )
