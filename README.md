# FleetOps AI

MVP de um **AI Operations Copilot** para diagnóstico de Ordens de Serviço, combinando dados operacionais estruturados, RAG, LangGraph, MCP, memória persistente, observabilidade e execução containerizada com Docker.

## Visão geral

O FleetOps AI foi criado como um projeto de portfólio para demonstrar uma arquitetura de IA aplicada a operações.

A aplicação responde perguntas como:

```text
Por que a OS 10235 está bloqueada?
```

O sistema não usa o LLM como fonte da verdade.

A arquitetura segue este princípio:

```text
Fatos operacionais → banco / ferramentas
Regras             → RAG
LLM                → interpretação e explicação
```

Isso reduz alucinações e mantém a resposta baseada em dados e regras conhecidas.

---

## Arquitetura

```text
Usuário / Frontend
        ↓
FastAPI
        ↓
LangGraph
        ↓
Scope Guard
        ↓
MCP Tools
        ↓
PostgreSQL + pgvector
        ↓
RAG
        ↓
Ollama
        ↓
Resposta
```

### Responsabilidades

- **FastAPI**: expõe a API HTTP.
- **LangGraph**: orquestra o fluxo do agente.
- **Scope Guard**: impede respostas fora do domínio operacional.
- **MCP**: expõe ferramentas de diagnóstico e busca de conhecimento.
- **PostgreSQL**: armazena dados operacionais fictícios.
- **pgvector**: armazena embeddings da base de conhecimento.
- **RAG**: recupera regras e procedimentos relevantes.
- **Ollama**: executa os modelos locais.
- **Docker**: empacota API e banco em containers reproduzíveis.

---

## Tecnologias

- Python 3.12
- FastAPI
- LangGraph
- MCP
- PostgreSQL
- pgvector
- SQLAlchemy
- psycopg
- Pydantic
- Ollama
- Qwen 2.5
- EmbeddingGemma
- Docker
- Docker Compose
- Pytest
- HTML
- CSS
- JavaScript

---

## Funcionalidades

### Diagnóstico operacional

Consulta uma Ordem de Serviço e combina:

- dados da OS;
- contrato relacionado;
- fila de processamento;
- status operacional;
- problemas identificados.

### RAG

As regras operacionais são consultadas semanticamente antes da geração da resposta.

Arquivos atuais da base de conhecimento:

```text
docs/contracts.md
docs/processing.md
docs/troubleshooting.md
```

### Memória

O agente utiliza `thread_id` para manter contexto entre perguntas.

Exemplo:

```text
Por que a OS 10235 está bloqueada?
qual o contrato dela?
```

A segunda pergunta reutiliza o contexto da primeira.

### Fast path

Perguntas factuais simples podem ser respondidas diretamente, sem chamar o LLM.

Exemplos:

```text
qual o contrato dela?
qual a placa dela?
qual o status da fila?
```

### Scope Guard

Perguntas fora do domínio são bloqueadas antes de acessar RAG ou LLM.

Exemplo:

```text
como fazer bolo de cenoura?
```

Resultado:

```text
response_mode: OUT_OF_SCOPE
```

### Resiliência

O projeto possui cenários simulados de falha para:

- diagnóstico;
- RAG;
- LLM.

Em caso de falha do LLM ou RAG, respostas determinísticas podem ser usadas como fallback.

### Observabilidade

Cada execução utiliza:

- `trace_id`;
- `thread_id`;
- logs estruturados em JSON;
- tempos de execução;
- eventos por etapa do fluxo.

---

## Modos de resposta

O agente pode responder em diferentes modos:

```text
AI
DIRECT
OUT_OF_SCOPE
```

### AI

Fluxo completo com diagnóstico, RAG e LLM.

### DIRECT

Resposta factual usando fast path.

### OUT_OF_SCOPE

Resposta determinística para perguntas fora do domínio.

---

## Exemplo

Pergunta:

```text
Por que a OS 10235 está bloqueada?
```

Resposta esperada:

```text
A OS 10235 está bloqueada porque o contrato 2002 está inativo.
O contrato precisa ser regularizado para que a OS seja processada.
```

Evidências recuperadas pelo RAG incluem a regra:

```text
CONTR-001
```

---

## Docker

A aplicação está containerizada.

Serviços:

```text
fleetops-api
fleetops-postgres
```

### Subir o ambiente

```powershell
docker compose up -d
```

### Ver status

```powershell
docker compose ps
```

Esperado:

```text
fleetops-api        healthy
fleetops-postgres   healthy
```

### Ver logs

```powershell
docker compose logs api
```

### Parar

```powershell
docker compose down
```

> Evite `docker compose down -v` caso queira preservar o volume do PostgreSQL.

---

## Ollama

O Ollama roda no host Windows e é acessado pela API Docker através de:

```text
http://host.docker.internal:11434
```

Modelos utilizados:

```text
qwen2.5:1.5b-instruct
embeddinggemma
```

Modelo adicional disponível:

```text
qwen2.5:3b
```

---

## Ingestão da base de conhecimento

Após criar um banco novo:

```powershell
docker compose exec api python -m app.ingest_knowledge
```

Resultado esperado:

```text
Ingestao concluida. 12 chunks gravados.
```

O ingest utiliza uma whitelist para evitar que documentação interna e checkpoints entrem no RAG.

---

## Testes

Executar:

```powershell
python -m pytest
```

Estado homologado:

```text
32 passed
```

Os testes cobrem:

- health endpoint;
- diagnóstico de OS;
- RAG;
- memória;
- fast path;
- scope guard;
- chunking;
- respostas diretas;
- falha forçada de RAG;
- falha forçada de LLM;
- falha forçada de diagnóstico;
- integrações do fluxo principal.

---

## Estrutura principal

```text
fleetops-ai/
│
├── app/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── main.py
│   ├── mcp_server.py
│   └── ingest_knowledge.py
│
├── docs/
│   ├── contracts.md
│   ├── processing.md
│   ├── troubleshooting.md
│   └── CHECKPOINT_*.md
│
├── docker/
│   └── postgres/
│       └── 001_init.sql
│
├── tests/
│
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── README_CHUNKING.md
├── README_DOCKER.md
├── README_SCOPE_GUARD.md
├── README_TESTES.md
└── README.md
```

---

## Documentação complementar

Documentos específicos existentes no projeto:

```text
README_CHUNKING.md
README_DOCKER.md
README_SCOPE_GUARD.md
README_TESTES.md
```

Checkpoints do projeto ficam em:

```text
docs/
```

---

## Estado atual

O FleetOps AI está em estado de:

```text
MVP funcional, testado e containerizado.
```

Itens homologados:

```text
[OK] Banco PostgreSQL
[OK] pgvector
[OK] FastAPI
[OK] LangGraph
[OK] MCP
[OK] RAG
[OK] Embeddings
[OK] Memória persistente
[OK] Fast path
[OK] Scope Guard
[OK] Observabilidade
[OK] Resiliência
[OK] Frontend
[OK] Docker
[OK] Healthcheck
[OK] Testes automatizados
```

---

## Próximas evoluções

- diagrama visual de arquitetura;
- script de setup do zero;
- roteiro de demonstração;
- separação entre `.env` local e `.env.docker`;
- transporte MCP externo;
- integração futura com SQL Server;
- adaptação futura para Sankhya;
- deploy em ambiente remoto.

---

## Objetivo futuro

A arquitetura fictícia do FleetOps foi construída para validar conceitos antes de uma futura adaptação para um ambiente corporativo real com:

```text
Sankhya
SQL Server
Ordens de Serviço
regras operacionais
diagnóstico
integrações
```

O objetivo é manter a mesma separação arquitetural:

```text
dados operacionais confiáveis
+
regras recuperadas
+
LLM como camada de interpretação
```
