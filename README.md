# FleetOps AI

[![CI](https://github.com/quevedocarla/fleetops-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/quevedocarla/fleetops-ai/actions/workflows/ci.yml)

**AI Operations Copilot para diagnóstico de Ordens de Serviço com RAG, LangGraph, MCP, memória, observabilidade e Docker.**

O FleetOps AI é um MVP de portfólio criado para demonstrar uma arquitetura de IA aplicada a operações.  
A solução combina **dados estruturados**, **regras recuperadas por RAG** e **IA generativa** para explicar diagnósticos de forma rastreável e controlada.

> **Princípio central:** fatos vêm do banco e das ferramentas; regras vêm do RAG; o LLM interpreta e explica.

![Arquitetura do FleetOps AI](./diagrama%20de%20arquitetura.png)

---

## Destaques técnicos

- FastAPI como camada HTTP
- LangGraph para orquestração do agente
- MCP para exposição de ferramentas
- PostgreSQL + pgvector para dados e embeddings
- RAG com chunking customizado
- Ollama com modelos locais
- memória persistente por `thread_id`
- fast path para perguntas factuais
- scope guard para bloquear perguntas fora do domínio
- fallback seguro para falhas de RAG/LLM
- observabilidade com `trace_id` e logs estruturados
- Docker Compose com healthchecks
- testes unitários e de integração
- **32 testes homologados**

---

## Problema que o projeto resolve

Em operações, muitas perguntas exigem combinar dados de diferentes fontes e regras de negócio.

Exemplo:

```text
Por que a OS 10235 está bloqueada?
```

O FleetOps consulta:

```text
Ordem de Serviço
+ contrato relacionado
+ fila de processamento
+ regras operacionais
```

e retorna uma explicação objetiva.

Exemplo de resposta:

```text
A OS 10235 está bloqueada porque o contrato 2002 está inativo.
O contrato precisa ser regularizado para que a OS seja processada.
```

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

### Separação de responsabilidades

```text
Fatos operacionais  → PostgreSQL / ferramentas
Regras              → RAG
Orquestração        → LangGraph
Integrações         → MCP
Explicação          → LLM
Proteção de domínio → Scope Guard
```

Essa separação reduz o risco de o modelo inventar fatos operacionais.

---

## Fluxos de resposta

O agente possui três modos principais.

### `AI`

Usado quando a pergunta exige análise.

Fluxo:

```text
diagnóstico
→ busca de conhecimento
→ RAG
→ LLM
→ resposta
```

### `DIRECT`

Usado para perguntas factuais simples.

Exemplos:

```text
qual o contrato dela?
qual a placa dela?
qual o status da fila?
```

Essas respostas não precisam chamar o LLM.

### `OUT_OF_SCOPE`

Perguntas fora do domínio são bloqueadas antes do RAG e do LLM.

Exemplo:

```text
como fazer bolo de cenoura?
```

Resposta:

```text
Posso ajudar com assuntos do FleetOps, como Ordens de Serviço,
contratos, placas, filas de processamento e diagnósticos operacionais.
Essa pergunta está fora desse escopo.
```

---

## Memória de conversa

O agente mantém contexto através de `thread_id`.

Exemplo:

```text
Usuário: Por que a OS 10235 está bloqueada?

FleetOps:
A OS 10235 está bloqueada porque o contrato 2002 está inativo.

Usuário: qual o contrato dela?

FleetOps:
O contrato da OS 10235 é o 2002.
```

A segunda pergunta reutiliza o contexto anterior.

---

## RAG

A base de conhecimento atual é composta por:

```text
docs/contracts.md
docs/processing.md
docs/troubleshooting.md
```

O processo de ingestão:

```text
Markdown
→ chunking
→ embedding
→ pgvector
→ busca semântica
```

### Chunking customizado

O projeto possui uma regra específica para manter identificadores junto de suas descrições.

Exemplo:

```text
CONTR-001

Uma Ordem de Serviço de instalação somente pode ser processada
quando o contrato relacionado estiver com status ACTIVE.
```

Isso evita que o ID da regra e seu conteúdo sejam armazenados em chunks separados.

A ingestão também usa uma whitelist para impedir que documentação interna e checkpoints entrem no RAG.

---

## MCP

O projeto expõe ferramentas operacionais através do MCP.

Exemplos:

```text
get_service_order_diagnostic
search_knowledge
```

A função do MCP é separar o agente das fontes operacionais e permitir que as ferramentas tenham contratos claros.

---

## Observabilidade

Cada execução pode ser acompanhada através de:

- `trace_id`
- `thread_id`
- logs estruturados em JSON
- tempos de execução
- eventos do agente

Eventos incluem:

```text
application_starting
agent_graph_ready
agent_chat_started
intent_detected
agent_scope_decision
rag_search_completed
llm_completed
http_request_completed
```

---

## Resiliência

O FleetOps possui mecanismos para testar falhas de dependências:

```text
FLEETOPS_FORCE_DIAGNOSTIC_ERROR
FLEETOPS_FORCE_RAG_ERROR
FLEETOPS_FORCE_LLM_ERROR
```

Comportamentos implementados:

- falha de LLM → fallback determinístico
- falha de RAG → resposta segura sem inventar conhecimento
- falha de diagnóstico → erro controlado

---

## Docker

A aplicação está containerizada.

Serviços:

```text
fleetops-api
fleetops-postgres
```

O Ollama roda no host e é acessado pelo container através de:

```text
http://host.docker.internal:11434
```

### Subir o ambiente

```powershell
docker compose up -d
```

### Verificar

```powershell
docker compose ps
```

Esperado:

```text
fleetops-api        healthy
fleetops-postgres   healthy
```

### Healthcheck

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Resposta esperada:

```text
status  service
------  -------
ok      fleetops-ai
```

---

## Setup rápido

### 1. Clonar

```powershell
git clone https://github.com/quevedocarla/fleetops-ai.git
cd fleetops-ai
```

### 2. Criar os arquivos de ambiente

Para desenvolvimento local:

```powershell
Copy-Item .env.example .env
```

Para Docker:

```powershell
Copy-Item .env.docker.example .env.docker
```

Ajuste as senhas antes de subir o ambiente.

### 3. Preparar Ollama

```powershell
ollama pull qwen2.5:1.5b-instruct
ollama pull embeddinggemma
```

### 4. Subir Docker

```powershell
docker compose up -d --build
```

### 5. Ingerir conhecimento

```powershell
docker compose exec api python -m app.ingest_knowledge
```

Resultado esperado:

```text
Ingestao concluida. 12 chunks gravados.
```

---

## Testes

Execute:

```powershell
python -m pytest
```

Estado homologado:

```text
32 passed
```

Os testes cobrem:

- API
- diagnóstico
- memória
- fast path
- RAG
- chunking
- scope guard
- fallback
- falha de diagnóstico
- falha de RAG
- falha de LLM
- integração ponta a ponta

---

## Estrutura do projeto

```text
fleetops-ai/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── rag/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── static/
│   ├── tools/
│   ├── agent_graph.py
│   ├── ingest_knowledge.py
│   ├── main.py
│   └── mcp_server.py
│
├── docker/
│   └── postgres/
│       └── 001_init.sql
│
├── docs/
├── experiments/
├── tests/
│
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Tecnologias

| Área | Tecnologia |
|---|---|
| API | FastAPI |
| Orquestração | LangGraph |
| Ferramentas | MCP |
| Banco | PostgreSQL |
| Vetores | pgvector |
| ORM | SQLAlchemy |
| Validação | Pydantic |
| LLM local | Ollama / Qwen 2.5 |
| Embeddings | EmbeddingGemma |
| Containerização | Docker / Docker Compose |
| Testes | Pytest |
| Frontend | HTML / CSS / JavaScript |

---

## Decisões de arquitetura

### LLM não é fonte da verdade

O modelo não decide sozinho se uma OS está bloqueada.

O diagnóstico é produzido a partir dos dados operacionais e regras disponíveis.

### Fast path reduz custo e latência

Perguntas simples não precisam passar pelo LLM.

### Scope Guard limita o domínio

Perguntas fora do FleetOps são interrompidas antes de consumir RAG ou geração.

### RAG usa conhecimento operacional explícito

As regras podem ser atualizadas independentemente do código do modelo.

### Docker torna o ambiente reproduzível

API e banco podem ser reconstruídos com configuração conhecida.

---

## Estado atual

```text
[OK] FastAPI
[OK] PostgreSQL
[OK] pgvector
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
[OK] Healthchecks
[OK] 32 testes automatizados
```

---

## Próximas evoluções

- transporte MCP externo
- refinamento do pipeline de avaliação
- métricas de qualidade do RAG
- CI/CD
- deploy remoto
- integração com SQL Server
- adaptação para Sankhya
- ferramentas operacionais específicas por domínio

---

## Documentação complementar

- `README_DOCKER.md`
- `README_TESTES.md`
- `README_CHUNKING.md`
- `README_SCOPE_GUARD.md`
- `docs/SETUP_DO_ZERO.md`
- `docs/ROTEIRO_DEMONSTRACAO.md`
- `docs/CHECKPOINT_5_DOCKER.md`

---

## Objetivo do projeto

O FleetOps AI foi construído para validar, em um ambiente fictício e controlado, conceitos que podem ser aplicados depois em sistemas corporativos reais.

A evolução prevista é reaproveitar a mesma arquitetura com:

```text
Sankhya
SQL Server
Ordens de Serviço
regras operacionais reais
integrações corporativas
```

mantendo a separação:

```text
dados confiáveis
+
regras recuperadas
+
IA como camada de interpretação
```

---

## Repositório

GitHub:

```text
https://github.com/quevedocarla/fleetops-ai
```
