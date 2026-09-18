# SETUP DO ZERO — FleetOps AI

Este guia mostra como subir o FleetOps AI do zero em uma nova máquina Windows.

## 1. Pré-requisitos

Instale:

- Git
- Docker Desktop
- Python 3.12
- Ollama

Opcional, mas recomendado:

- VS Code
- PowerShell 7+

---

## 2. Clonar o projeto

```powershell
git clone <URL_DO_REPOSITORIO>
cd fleetops-ai
```

---

## 3. Criar ambiente virtual Python

```powershell
python -m venv .venv
```

Ativar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar dependências locais:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Observação: o ambiente local Windows usa `requirements.txt` completo, incluindo dependências específicas de Windows.

---

## 4. Configurar Ollama

Verifique se o Ollama está instalado:

```powershell
ollama --version
```

Baixe os modelos usados pelo projeto:

```powershell
ollama pull qwen2.5:1.5b-instruct
ollama pull embeddinggemma
```

Modelo adicional opcional:

```powershell
ollama pull qwen2.5:3b
```

Confira:

```powershell
ollama list
```

Esperado:

```text
qwen2.5:1.5b-instruct
embeddinggemma
qwen2.5:3b
```

---

## 5. Configurar variáveis de ambiente locais

Crie um `.env` na raiz.

Exemplo:

```env
DATABASE_URL=postgresql+psycopg://fleetops:banco123@localhost:5432/fleetops

POSTGRES_DB=fleetops
POSTGRES_USER=fleetops
POSTGRES_PASSWORD=banco123
POSTGRES_PORT=5432

APP_PORT=8000

OLLAMA_HOST=http://host.docker.internal:11434

FLEETOPS_FORCE_DIAGNOSTIC_ERROR=false
FLEETOPS_FORCE_RAG_ERROR=false
FLEETOPS_FORCE_LLM_ERROR=false
```

Importante:

- dentro do Docker, o host do banco é `postgres`;
- no Windows local, o host do banco é `localhost`.

---

## 6. Validar Docker Compose

Antes de subir:

```powershell
docker compose config
```

Se não houver erro, prossiga.

---

## 7. Subir os containers

```powershell
docker compose up -d --build
```

Verifique:

```powershell
docker compose ps
```

Esperado:

```text
fleetops-postgres   Up (healthy)
fleetops-api        Up (healthy)
```

---

## 8. Ver logs da API

```powershell
docker compose logs api
```

Sinais esperados:

```text
application_starting
agent_graph_ready
Application startup complete
```

---

## 9. Validar healthcheck

No navegador:

```text
http://localhost:8000/health
```

Ou PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Esperado:

```text
200 OK
```

---

## 10. Ingerir a base de conhecimento

Depois de subir um banco novo:

```powershell
docker compose exec api python -m app.ingest_knowledge
```

Esperado:

```text
Ingestao concluida. 12 chunks gravados.
```

Arquivos ingeridos:

```text
docs/contracts.md
docs/processing.md
docs/troubleshooting.md
```

Checkpoints e outros arquivos Markdown não entram no RAG.

---

## 11. Testar uma pergunta analítica

No PowerShell:

```powershell
$body = @{
    message = "Por que a OS 10235 está bloqueada?"
    thread_id = "docker-teste-1"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/agent/chat" `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

Esperado:

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

---

## 12. Testar memória + fast path

Use o mesmo `thread_id`:

```powershell
$body = @{
    message = "qual o contrato dela?"
    thread_id = "docker-teste-1"
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

---

## 13. Testar Scope Guard

```powershell
$body = @{
    message = "como fazer bolo de cenoura?"
    thread_id = "docker-teste-1"
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

---

## 14. Rodar os testes automatizados

Com o ambiente virtual ativo:

```powershell
python -m pytest
```

Estado homologado:

```text
32 passed
```

---

## 15. Rodar a API localmente sem Docker

No Windows, use:

```powershell
python run_api.py
```

Evite usar diretamente:

```powershell
uvicorn app.main:app --reload
```

porque o projeto possui um ajuste específico de event loop para Windows em `run_api.py`.

---

## 16. Parar o ambiente Docker

Parar containers sem apagar dados:

```powershell
docker compose down
```

Isso preserva o volume do PostgreSQL.

---

## 17. Reset total do banco

Use somente se realmente quiser apagar tudo e reconstruir do zero:

```powershell
docker compose down -v
```

Depois:

```powershell
docker compose up -d --build
```

E reingira a base:

```powershell
docker compose exec api python -m app.ingest_knowledge
```

Atenção:

`down -v` remove o volume e os dados persistidos.

---

## 18. Diagnóstico rápido

### API não sobe

```powershell
docker compose logs api
```

### PostgreSQL não sobe

```powershell
docker compose logs postgres
```

### Ver status

```powershell
docker compose ps
```

### Ver containers

```powershell
docker ps -a
```

### Ver modelos Ollama

```powershell
ollama list
```

---

## 19. Problemas conhecidos

### pywin32 no Docker

`pywin32` é exclusivo de Windows.

O Dockerfile remove essa dependência apenas durante o build Linux, mantendo o `requirements.txt` original para desenvolvimento local.

### requirements.txt em UTF-16

O Dockerfile normaliza automaticamente o arquivo para UTF-8 antes da instalação.

### Uvicorn

A imagem instala `uvicorn` explicitamente e inicia com:

```text
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Acentuação no PowerShell

Em alguns terminais, respostas UTF-8 podem aparecer como:

```text
estÃ¡
ServiÃ§o
```

Isso é um problema de exibição do terminal, não da API.

---

## 20. Arquitetura final

```text
Usuário
  ↓
FastAPI
  ↓
LangGraph
  ↓
Scope Guard
  ↓
MCP
  ↓
PostgreSQL + pgvector
  ↓
RAG
  ↓
Ollama
  ↓
Resposta
```

---

## 21. Checklist de homologação em uma nova máquina

```text
[ ] Projeto clonado
[ ] Python 3.12 instalado
[ ] Docker Desktop instalado
[ ] Ollama instalado
[ ] Modelos baixados
[ ] .env criado
[ ] docker compose config sem erro
[ ] containers healthy
[ ] health endpoint 200
[ ] 12 chunks ingeridos
[ ] pergunta analítica funcionando
[ ] memória funcionando
[ ] fast path funcionando
[ ] scope guard funcionando
[ ] 32 testes passando
```

Quando todos os itens estiverem marcados, o FleetOps AI está homologado na nova máquina.
