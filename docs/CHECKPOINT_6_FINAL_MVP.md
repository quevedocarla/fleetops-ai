# CHECKPOINT 6 — FleetOps AI Final MVP

Data: 18/09/2026

## 1. Objetivo do checkpoint

Registrar o estado final do MVP fictício FleetOps AI após:

- Dockerização
- documentação de portfólio
- publicação no GitHub
- CI com GitHub Actions
- melhoria de follow-ups contextuais
- ampliação da suíte de testes

---

## 2. Estado atual do projeto

O FleetOps AI pode ser descrito como:

> MVP funcional, testado, containerizado e versionado de um AI Operations Copilot com RAG, MCP, LangGraph, memória persistente, observabilidade, fast path, scope guard, fallback seguro e CI automatizado.

---

## 3. Arquitetura final

```text
Usuário / Frontend
        ↓
FastAPI
        ↓
LangGraph
        ↓
Scope Guard
        ↓
Detecção de intenção
        ↓
┌──────────────────────┬──────────────────────┐
│ Fast Path / DIRECT   │ Fluxo analítico / AI │
└──────────────────────┴──────────────────────┘
        ↓                         ↓
Dados operacionais          MCP + RAG
        ↓                         ↓
PostgreSQL + pgvector      Base de conhecimento
        ↓                         ↓
        └──────────────┬──────────┘
                       ↓
                    Ollama
                       ↓
                    Resposta
```

Princípio arquitetural:

```text
Fatos → banco / ferramentas
Regras → RAG
LLM → interpretação e explicação
```

---

## 4. Componentes homologados

```text
[OK] FastAPI
[OK] PostgreSQL
[OK] pgvector
[OK] SQLAlchemy
[OK] LangGraph
[OK] MCP
[OK] RAG
[OK] Embeddings
[OK] Ollama
[OK] Memória persistente
[OK] Fast path
[OK] Scope Guard
[OK] Observabilidade
[OK] Resiliência
[OK] Frontend
[OK] Docker
[OK] Healthchecks
[OK] Git
[OK] GitHub
[OK] GitHub Actions
[OK] CI
[OK] README de portfólio
[OK] Diagrama de arquitetura
[OK] Setup do zero
[OK] Roteiro de demonstração
```

---

## 5. Docker

Containers:

```text
fleetops-api
fleetops-postgres
```

Estado homologado:

```text
fleetops-api        healthy
fleetops-postgres   healthy
```

O Ollama permanece no host Windows.

Comunicação:

```text
http://host.docker.internal:11434
```

---

## 6. Separação de ambientes

Configuração local:

```text
.env
```

Banco acessado por:

```text
localhost
```

Configuração Docker:

```text
.env.docker
```

Banco acessado por:

```text
postgres
```

Arquivos versionáveis:

```text
.env.example
.env.docker.example
```

Arquivos ignorados pelo Git:

```text
.env
.env.docker
```

---

## 7. RAG

Base operacional:

```text
docs/contracts.md
docs/processing.md
docs/troubleshooting.md
```

Quantidade atual:

```text
12 chunks
```

Características:

- whitelist de arquivos operacionais
- chunking customizado
- regras mantidas junto de suas descrições
- embeddings com EmbeddingGemma
- busca vetorial com pgvector

Exemplo de regra:

```text
CONTR-001
```

---

## 8. Memória

O agente mantém contexto por:

```text
thread_id
```

Exemplo:

```text
Usuário:
Como está a OS 10235?

Usuário:
qual o contrato dela?

FleetOps:
O contrato da OS 10235 é o 2002.
```

---

## 9. Fast path

Perguntas factuais simples são respondidas sem LLM.

Exemplos:

```text
qual o contrato dela
a placa
e a placa
qual contrato está vinculado a essa OS
qual o status da fila
```

Resultado:

```text
response_mode: DIRECT
```

Benefícios:

- menor latência
- menor custo
- menor risco de alucinação
- resposta determinística

---

## 10. Follow-ups contextuais

Durante a validação manual foram encontrados casos em que a linguagem natural não era corretamente classificada.

Exemplos corrigidos:

```text
a placa
e a placa
qual contrato está vinculado a essa os
está em manutenção?
a OS 10236
```

A correção passou a tratar:

- variações curtas
- confirmações de tipo
- perguntas com conectores naturais
- resumo direto de OS
- contexto reaproveitado da conversa

---

## 11. Exemplo de confirmação de tipo

Pergunta:

```text
está em manutenção?
```

Para a OS 10235:

```text
Não. A OS 10235 é do tipo instalação, não manutenção.
```

Esse comportamento é determinístico e não depende do LLM.

---

## 12. Resumo direto de OS

Pergunta:

```text
a OS 10236
```

Resultado esperado:

- status operacional
- tipo
- placa
- contrato
- status do contrato
- fila
- diagnóstico

Sem necessidade de geração livre pelo LLM.

---

## 13. Scope Guard

Perguntas fora do domínio continuam bloqueadas.

Exemplo:

```text
como fazer bolo de cenoura?
```

Resultado:

```text
response_mode: OUT_OF_SCOPE
```

Sem consulta ao RAG e sem chamada ao LLM.

---

## 14. Observabilidade

Eventos disponíveis:

```text
application_starting
agent_graph_ready
http_request_started
agent_chat_started
intent_detected
agent_scope_decision
rag_search_completed
llm_completed
direct_answer_completed
http_request_completed
```

Identificadores:

```text
trace_id
thread_id
```

---

## 15. Resiliência

Flags de teste:

```text
FLEETOPS_FORCE_DIAGNOSTIC_ERROR
FLEETOPS_FORCE_RAG_ERROR
FLEETOPS_FORCE_LLM_ERROR
```

Comportamentos:

```text
LLM falha
→ fallback determinístico

RAG falha
→ resposta segura

diagnóstico falha
→ erro controlado
```

---

## 16. Testes

Suíte inicial:

```text
32 testes
```

Após testes de regressão de follow-up:

```text
43 testes
```

Áreas cobertas:

- API
- diagnóstico
- memória
- fast path
- intents
- follow-ups naturais
- RAG
- chunking
- scope guard
- fallback
- falhas simuladas
- integração ponta a ponta

---

## 17. GitHub Actions

Workflows:

```text
.github/workflows/ci.yml
.github/workflows/full-integration.yml
```

### CI automático

Executado em:

```text
push
pull_request
```

Valida:

- build Docker
- health da API
- testes principais

### Full Integration

Execução manual.

Inclui:

- Ollama
- modelos locais
- Docker
- ingestão RAG
- suíte completa

---

## 18. Badge de CI

README possui badge de status do workflow:

```text
CI
```

Objetivo:

- mostrar rapidamente se a branch principal está saudável
- reforçar a qualidade do projeto no portfólio

---

## 19. Git e GitHub

Repositório:

```text
https://github.com/quevedocarla/fleetops-ai
```

Branch principal:

```text
main
```

Commits principais já realizados:

```text
feat: initial FleetOps AI MVP
docs: improve README for portfolio
ci: add GitHub Actions workflows
fix: improve natural contextual follow-ups
docs: add CI status badge
```

---

## 20. Documentação existente

```text
README.md
README_DOCKER.md
README_TESTES.md
README_CHUNKING.md
README_SCOPE_GUARD.md

docs/CHECKPOINT_4.md
docs/CHECKPOINT_5_DOCKER.md
docs/CHECKPOINT_6_FINAL_MVP.md
docs/SETUP_DO_ZERO.md
docs/ROTEIRO_DEMONSTRACAO.md
```

---

## 21. Lições técnicas importantes

### LLM não deve responder tudo

Perguntas factuais devem usar fast path.

### Linguagem natural exige regressão

Uma funcionalidade pode estar correta tecnicamente e ainda falhar com variações reais de linguagem.

### Regras precisam ser separadas por responsabilidade

No projeto real:

```text
regra de negócio
→ SQL / diagnóstico

regra explicativa
→ RAG

regra de linguagem
→ camada de intents

regra de segurança
→ LangGraph / policy
```

### Docker facilita reconstrução

O ambiente foi destruído e reconstruído durante o desenvolvimento sem perda do código.

### CI fecha o ciclo de engenharia

Cada push pode validar automaticamente o estado do projeto.

---

## 22. Próximas etapas

Após este checkpoint, o MVP fictício pode ser considerado encerrado.

Próximos caminhos:

1. transporte MCP externo real
2. avaliação de RAG
3. métricas de qualidade
4. CI/CD mais completo
5. deploy
6. adaptação para Sankhya + SQL Server

---

## 23. Próxima fase recomendada

A próxima grande fase deve ser:

```text
FleetOps fictício
        ↓
mapear arquitetura equivalente
        ↓
Sankhya + SQL Server
        ↓
MCP com ferramentas reais
        ↓
diagnóstico operacional real
        ↓
RAG com documentação corporativa
```

Sem misturar os dois projetos.

O FleetOps permanece como:

```text
referência arquitetural
+
portfólio
+
ambiente seguro de experimentação
```

---

## 24. Conclusão

O MVP FleetOps AI atingiu o objetivo principal.

Foi construída uma solução completa de AI Engineering contendo:

- backend
- banco
- vetores
- RAG
- agente
- memória
- ferramentas
- guardrails
- observabilidade
- testes
- Docker
- Git
- GitHub
- CI
- documentação

O projeto está pronto para ser utilizado como referência técnica e como base conceitual para uma futura implementação corporativa com Sankhya e SQL Server.
