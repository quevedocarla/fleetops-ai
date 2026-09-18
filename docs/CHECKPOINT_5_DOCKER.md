# CHECKPOINT 5 — Dockerização Homologada

Data: 18/09/2026

## 1. Objetivo

Containerizar o FleetOps AI para tornar o ambiente mais reproduzível, reduzindo dependências manuais da máquina local e aproximando o projeto de um cenário real de desenvolvimento e implantação.

Neste checkpoint, a aplicação foi validada com:

- API FastAPI em container Docker
- PostgreSQL + pgvector em container Docker
- volume persistente para o banco
- healthchecks
- LangGraph com memória persistente
- RAG com embeddings locais
- Ollama executando no Windows e acessado pelo container
- fast path
- scope guard
- fallback e resiliência
- testes automatizados

---

## 2. Arquitetura validada

```text
Usuário / Frontend
        ↓
FastAPI
(container Docker)
        ↓
LangGraph
        ↓
Scope Guard
        ↓
MCP Tools
        ↓
PostgreSQL + pgvector
(container Docker)
        ↓
RAG
        ↓
Ollama
(host Windows)
        ↓
Resposta
```

Princípio arquitetural mantido:

> Fatos operacionais vêm do banco e das ferramentas.  
> Regras vêm da base de conhecimento/RAG.  
> O LLM interpreta e explica, mas não é a fonte da verdade.

---

## 3. Containers

### fleetops-api

Responsável por:

- FastAPI
- LangGraph
- MCP
- RAG
- integração com PostgreSQL
- integração com Ollama
- observabilidade
- endpoints da aplicação

Imagem construída localmente:

```text
fleetops-ai-api
```

Porta:

```text
8000
```

### fleetops-postgres

Imagem:

```text
pgvector/pgvector:pg16
```

Responsável por:

- PostgreSQL
- extensão pgvector
- dados operacionais fictícios
- embeddings da base de conhecimento
- checkpoints persistentes do LangGraph

Porta:

```text
5432
```

---

## 4. Persistência

Volume Docker criado:

```text
fleetops-ai_fleetops_postgres_data
```

Esse volume mantém os dados do PostgreSQL mesmo quando os containers são reiniciados.

Importante:

```powershell
docker compose down
```

mantém o volume.

Já:

```powershell
docker compose down -v
```

remove também o volume e os dados persistidos.

---

## 5. Inicialização do banco

O arquivo:

```text
docker/postgres/001_init.sql
```

é executado na primeira criação do volume.

Ele cria e prepara:

- extensão vector
- contracts
- service_orders
- processing_queue
- knowledge_documents
- dados fictícios iniciais

Casos principais mantidos:

- OS 10234
- OS 10235
- OS 10236
- OS 10237

---

## 6. RAG

A base de conhecimento foi ingerida novamente após a reconstrução do banco.

Comando utilizado:

```powershell
docker compose exec api python -m app.ingest_knowledge
```

Resultado validado:

```text
Ingestao concluida. 12 chunks gravados.
```

Arquivos operacionais permitidos no RAG:

- contracts.md
- processing.md
- troubleshooting.md

Documentos de checkpoint e documentação interna não entram no RAG.

---

## 7. Chunking validado

O chunker customizado mantém identificadores de regra junto da respectiva descrição.

Exemplo:

```text
REGRA CONTR-001

Uma Ordem de Servico de instalacao somente pode ser processada
quando o contrato relacionado estiver com status ACTIVE.
```

Isso evita separar o código da regra do conteúdo semântico usado na recuperação vetorial.

---

## 8. Ollama

O Ollama permanece executado no Windows host.

O container acessa o serviço através de:

```text
http://host.docker.internal:11434
```

Modelos utilizados:

- qwen2.5:1.5b-instruct
- qwen2.5:3b
- embeddinggemma

Uso atual:

- qwen2.5:1.5b-instruct → geração final de resposta
- embeddinggemma → embeddings
- qwen2.5:3b → mantido para usos futuros

---

## 9. Healthcheck

O endpoint:

```text
GET /health
```

foi validado dentro do Docker.

Exemplo registrado:

```text
HTTP/1.1 200 OK
```

Estado final dos containers:

```text
fleetops-api        healthy
fleetops-postgres   healthy
```

---

## 10. Validação funcional

### Pergunta analítica

Pergunta:

```text
Por que a OS 10235 está bloqueada?
```

Resultado:

```text
status: BLOCKED
response_mode: AI
degraded: False
```

Resposta funcional:

```text
A OS 10235 está bloqueada porque o contrato 2002 está inativo.
O contrato precisa ser regularizado para que a OS seja processada.
```

Fontes recuperadas pelo RAG incluíram:

- contracts.md#chunk-3
- troubleshooting.md#chunk-3
- contracts.md#chunk-2

A regra CONTR-001 foi recuperada corretamente.

---

## 11. Fast path validado

Pergunta seguinte usando o mesmo thread:

```text
qual o contrato dela?
```

Resultado:

```text
service_order_id: 10235
answer: O contrato da OS 10235 é o 2002.
response_mode: DIRECT
sources: {}
degraded: False
```

Isso confirmou:

- memória persistente por thread_id
- recuperação do contexto anterior
- resposta direta
- ausência de chamada desnecessária ao RAG

---

## 12. Scope Guard validado

Pergunta:

```text
como fazer bolo de cenoura?
```

Resultado:

```text
response_mode: OUT_OF_SCOPE
sources: {}
degraded: False
```

Resposta:

```text
Posso ajudar com assuntos do FleetOps, como Ordens de Serviço,
contratos, placas, filas de processamento e diagnósticos operacionais.
Essa pergunta está fora desse escopo.
```

Isso confirma que perguntas fora do domínio:

- não consultam RAG
- não usam o LLM para responder conteúdo fora do escopo
- não quebram o contexto da conversa

---

## 13. Observabilidade validada

Eventos observados nos logs:

```text
application_starting
agent_graph_ready
http_request_started
http_request_completed
```

Exemplo:

```text
status_code: 200
```

A API continua usando:

- trace_id
- thread_id
- logs estruturados em JSON
- tempos de execução por request

---

## 14. Ajustes necessários durante a Dockerização

### Dockerfile CMD

O comando inicial precisou ser corrigido para:

```dockerfile
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### pywin32

O requirements.txt local contém:

```text
pywin32
```

Essa biblioteca é exclusiva do Windows e não pode ser instalada no container Linux.

O Dockerfile passou a criar uma lista de dependências compatível com Linux sem alterar o requirements.txt original.

### requirements.txt em UTF-16

O arquivo requirements.txt havia sido salvo em formato interpretado como binário no Linux.

O Dockerfile passou a:

- detectar UTF-16
- converter para UTF-8
- remover somente pywin32
- instalar as demais dependências

### uvicorn

O uvicorn foi instalado explicitamente dentro da imagem Docker.

---

## 15. Configuração de banco

Dentro do Docker:

```text
postgresql+psycopg://fleetops:<senha>@postgres:5432/fleetops
```

No Windows local:

```text
postgresql+psycopg://fleetops:<senha>@localhost:5432/fleetops
```

Diferença principal:

```text
Docker → host postgres
Windows → host localhost
```

---

## 16. Testes automatizados

Comando:

```powershell
python -m pytest
```

Resultado:

```text
32 passed in 37.35s
```

Cobertura funcional validada:

- health endpoint
- diagnóstico de OS bloqueada
- RAG
- memória por thread
- fast path
- consulta de placa
- OS concluída
- tratamento de thread sem OS
- extração de OS
- detecção de intenção
- normalização de resposta
- respostas diretas
- falha forçada de RAG
- falha forçada de LLM
- falha forçada de diagnóstico
- chunking
- regras CONTR-001 / R121
- scope guard
- out-of-scope
- integração de memória + scope guard

---

## 17. Estado final do MVP

O projeto pode ser descrito neste ponto como:

> MVP funcional, testado e containerizado de um AI Operations Copilot com RAG, MCP, LangGraph, memória persistente, observabilidade, fast path, scope guard e fallback seguro.

Status atual:

```text
[OK] Banco
[OK] pgvector
[OK] API
[OK] MCP
[OK] RAG
[OK] Embeddings
[OK] LangGraph
[OK] Memória
[OK] Fast path
[OK] Scope Guard
[OK] Observabilidade
[OK] Resiliência
[OK] Frontend
[OK] Docker
[OK] Healthcheck
[OK] Testes automatizados — 32/32
```

---

## 18. Próximas etapas

Próximo ciclo recomendado:

1. README principal do projeto
2. diagrama de arquitetura
3. documentação de setup do zero
4. script/demo de apresentação
5. revisão da estrutura de pastas
6. `.env.docker` separado do `.env` local
7. melhoria final de encoding/acentuação no PowerShell
8. transporte MCP externo real
9. adaptação futura para Sankhya + SQL Server

---

## 19. Comandos principais

Subir:

```powershell
docker compose up -d
```

Ver status:

```powershell
docker compose ps
```

Ver logs:

```powershell
docker compose logs api
```

Ingerir conhecimento:

```powershell
docker compose exec api python -m app.ingest_knowledge
```

Rodar testes:

```powershell
python -m pytest
```

Parar:

```powershell
docker compose down
```

Não usar em ambiente com dados que deseja preservar:

```powershell
docker compose down -v
```

---

## 20. Conclusão

A Dockerização foi homologada com sucesso.

O FleetOps AI agora possui um ambiente reproduzível contendo a API e o PostgreSQL/pgvector em containers, mantendo o Ollama local no host.

A reconstrução completa do ambiente foi validada com ingestão de conhecimento, respostas analíticas, fast path, memória, proteção de escopo e 32 testes automatizados aprovados.
