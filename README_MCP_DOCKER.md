# MCP Externo no Docker — FleetOps AI

O FleetOps possui um servidor MCP independente acessível por Streamable HTTP.

## Serviços

```text
fleetops-postgres   PostgreSQL + pgvector
fleetops-api        FastAPI + LangGraph
fleetops-mcp        MCP Server
```

## Endpoint MCP

```text
http://localhost:8001/mcp
```

## Subir o ambiente

```powershell
docker compose up -d --build
```

## Conferir containers

```powershell
docker compose ps
```

Esperado:

```text
fleetops-postgres   healthy
fleetops-api        healthy
fleetops-mcp        healthy
```

## Logs do MCP

```powershell
docker compose logs mcp --tail 100
```

## Teste manual

Com a virtualenv ativa:

```powershell
python .\experiments\test_mcp_docker_client.py
```

O teste valida:

- conexão MCP via Streamable HTTP;
- descoberta das tools;
- diagnóstico da OS 10235;
- busca RAG.

## Arquitetura

```text
Cliente MCP
    |
    | Streamable HTTP :8001
    v
fleetops-mcp
    |
    +--> diagnóstico operacional --> PostgreSQL
    |
    +--> search_knowledge --> pgvector
                           |
                           +--> Ollama no host
```

O Ollama permanece fora do Docker e é acessado pelos containers via:

```text
http://host.docker.internal:11434
```
