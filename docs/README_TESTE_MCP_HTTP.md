# Teste automatizado do transporte MCP HTTP

Arquivo:

```text
tests/test_mcp_http_transport.py
```

O teste valida três pontos:

1. o cliente consegue conectar ao servidor MCP via Streamable HTTP;
2. as tools esperadas estão registradas;
3. diagnóstico operacional e busca RAG respondem corretamente.

## Local

Com Docker ativo:

```powershell
docker compose up -d
python -m pytest tests/test_mcp_http_transport.py -v
```

Por padrão o teste usa:

```text
http://127.0.0.1:8001/mcp
```

## Dentro do Docker / CI

De dentro do container `api`, `localhost` não aponta para o container MCP.

Por isso use:

```text
MCP_SERVER_URL=http://mcp:8001/mcp
```

Exemplo:

```powershell
docker compose exec `
  -e MCP_SERVER_URL=http://mcp:8001/mcp `
  api `
  python -m pytest tests/test_mcp_http_transport.py -v
```

## Resultado esperado

```text
3 passed
```

Esse teste cobre o transporte real do MCP e evita regressões em:

- disponibilidade do endpoint;
- registro das tools;
- acesso ao PostgreSQL;
- acesso ao pgvector/RAG;
- integração do container MCP com os demais serviços.
