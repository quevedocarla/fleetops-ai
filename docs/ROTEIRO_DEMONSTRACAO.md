# ROTEIRO DE DEMONSTRAÇÃO — FleetOps AI

## Objetivo

Apresentar o FleetOps AI em poucos minutos, mostrando:

- problema;
- arquitetura;
- resposta analítica;
- RAG;
- memória;
- fast path;
- scope guard;
- observabilidade;
- Docker;
- testes.

Tempo sugerido:

```text
5 a 8 minutos
```

---

## 1. Abertura — 30 segundos

### Fala sugerida

> O FleetOps AI é um copiloto operacional criado para diagnosticar Ordens de Serviço usando dados estruturados, regras de negócio e IA generativa.
>
> A ideia principal é não deixar o modelo de IA inventar fatos. Os dados vêm do banco, as regras vêm do RAG, e o LLM é usado para interpretar e explicar o diagnóstico.

---

## 2. Mostrar a arquitetura — 40 segundos

Abra o diagrama de arquitetura.

### Fala sugerida

> O fluxo começa no usuário e passa pela API FastAPI.
>
> O LangGraph orquestra o agente e decide qual caminho seguir.
>
> Se a pergunta for fora do domínio, o Scope Guard responde sem chamar o modelo.
>
> Se for uma pergunta simples, entra no Fast Path.
>
> Se for uma pergunta analítica, o agente usa ferramentas MCP, consulta o PostgreSQL, recupera regras no RAG e usa o Ollama para gerar a resposta final.

Destaque:

```text
Dados → PostgreSQL
Regras → RAG
Explicação → LLM
```

---

## 3. Mostrar que está rodando em Docker — 30 segundos

No terminal:

```powershell
docker compose ps
```

Mostre:

```text
fleetops-api        healthy
fleetops-postgres   healthy
```

### Fala sugerida

> A aplicação está containerizada. A API e o PostgreSQL com pgvector rodam em Docker, e o Ollama roda localmente no host.
>
> Isso permite reconstruir o ambiente de forma mais previsível em outra máquina.

---

## 4. Demonstração principal — pergunta analítica — 1 minuto

Use:

```powershell
$body = @{
    message = "Por que a OS 10235 está bloqueada?"
    thread_id = "demo-1"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/agent/chat" `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

Resultado esperado:

```text
service_order_id : 10235
status           : BLOCKED
response_mode    : AI
degraded         : False
```

Resposta esperada:

```text
A OS 10235 está bloqueada porque o contrato 2002 está inativo.
O contrato precisa ser regularizado para que a OS seja processada.
```

### Fala sugerida

> Aqui o agente consultou os dados da OS, identificou o contrato inativo, recuperou as regras relevantes e gerou uma resposta objetiva.
>
> O status BLOCKED vem do diagnóstico determinístico, e não de uma decisão inventada pelo LLM.

---

## 5. Mostrar as fontes do RAG — 40 segundos

Destaque as fontes retornadas:

```text
contracts.md#chunk-3
troubleshooting.md#chunk-3
contracts.md#chunk-2
```

Mostre a regra:

```text
CONTR-001
```

### Fala sugerida

> A resposta também traz rastreabilidade.
>
> O RAG recuperou a regra CONTR-001, que diz que uma OS de instalação só pode ser processada quando o contrato está ativo.
>
> Assim, a resposta fica baseada em conhecimento explícito e verificável.

---

## 6. Demonstrar memória + fast path — 40 segundos

Use o mesmo `thread_id`:

```powershell
$body = @{
    message = "qual o contrato dela?"
    thread_id = "demo-1"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/agent/chat" `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

Esperado:

```text
answer        : O contrato da OS 10235 é o 2002.
response_mode : DIRECT
sources       : {}
```

### Fala sugerida

> A segunda pergunta não informa novamente o número da OS.
>
> O agente recupera o contexto pelo thread_id.
>
> Como a pergunta é factual, ele usa o Fast Path e não chama RAG nem LLM desnecessariamente.

---

## 7. Demonstrar Scope Guard — 40 segundos

Use:

```powershell
$body = @{
    message = "como fazer bolo de cenoura?"
    thread_id = "demo-1"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/agent/chat" `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

Esperado:

```text
response_mode : OUT_OF_SCOPE
sources       : {}
degraded      : False
```

### Fala sugerida

> Mesmo mantendo o contexto da OS, o agente não responde qualquer coisa.
>
> O Scope Guard identifica que a pergunta está fora do domínio e bloqueia o fluxo antes de chamar RAG ou LLM.

---

## 8. Mostrar observabilidade — 40 segundos

No terminal:

```powershell
docker compose logs api --tail 50
```

Destaque eventos como:

```text
http_request_started
agent_chat_started
intent_detected
agent_scope_decision
rag_search_completed
llm_completed
http_request_completed
```

### Fala sugerida

> Cada execução gera trace_id e logs estruturados.
>
> Isso permite acompanhar o caminho da requisição, identificar gargalos e diagnosticar falhas.

---

## 9. Mostrar testes — 30 segundos

Rode:

```powershell
python -m pytest
```

Ou mostre o resultado homologado:

```text
32 passed
```

### Fala sugerida

> O projeto possui testes unitários e de integração.
>
> Eles cobrem RAG, memória, fast path, scope guard, chunking, tratamento de erros e fluxo completo da API.

---

## 10. Fechamento — 30 segundos

### Fala sugerida

> O objetivo do projeto foi validar uma arquitetura de AI Engineer aplicada a operações.
>
> O FleetOps combina dados estruturados, RAG, ferramentas, memória, observabilidade, Docker e testes.
>
> A próxima evolução é adaptar esse mesmo padrão para dados corporativos reais, como SQL Server e Sankhya, mantendo a separação entre fatos, regras e interpretação por IA.

---

# Versão curta — 3 minutos

Se o tempo for muito curto, apresente apenas:

1. arquitetura;
2. pergunta "Por que a OS 10235 está bloqueada?";
3. memória com "qual o contrato dela?";
4. Scope Guard;
5. `32 passed`;
6. fechamento.

---

# Checklist antes da apresentação

```text
[ ] Docker Desktop aberto
[ ] Ollama rodando
[ ] qwen2.5:1.5b-instruct disponível
[ ] embeddinggemma disponível
[ ] docker compose ps → ambos healthy
[ ] RAG ingerido
[ ] endpoint /health respondendo
[ ] terminal limpo
[ ] thread_id novo para a demo
[ ] diagrama aberto
[ ] README disponível
[ ] resultado dos testes conhecido
```

---

# Comandos rápidos da apresentação

## Status

```powershell
docker compose ps
```

## Health

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Logs

```powershell
docker compose logs api --tail 50
```

## Testes

```powershell
python -m pytest
```

## Pergunta principal

```powershell
$body = @{
    message = "Por que a OS 10235 está bloqueada?"
    thread_id = "demo-1"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/agent/chat" `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

---

# Mensagem principal da apresentação

Se precisar resumir o projeto em uma frase:

> FleetOps AI é um copiloto operacional que combina dados confiáveis, regras recuperadas por RAG e IA generativa para explicar diagnósticos de forma rastreável, segura e reproduzível.
