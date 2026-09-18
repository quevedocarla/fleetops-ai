# FleetOps AI — Docker local

Este pacote coloca a API e o PostgreSQL/pgvector em containers.

O Ollama continua rodando no Windows host. Isso evita colocar modelos de
linguagem dentro do container e deixa o ambiente local mais simples.

## Arquitetura local

```text
Navegador
   |
   | http://localhost:8000
   v
fleetops-api
   |
   +----> fleetops-postgres
   |      PostgreSQL + pgvector
   |
   +----> host.docker.internal:11434
          Ollama no Windows
```

## 1. Pré-requisitos

- Docker Desktop rodando
- Ollama rodando no Windows
- projeto FleetOps AI completo
- `requirements.txt` na raiz do projeto

Confirme os modelos:

```powershell
ollama list
```

O FleetOps atual usa:

```text
qwen2.5:1.5b-instruct
embeddinggemma
```

Se necessário:

```powershell
ollama pull qwen2.5:1.5b-instruct
ollama pull embeddinggemma
```

## 2. Copiar os arquivos

Na raiz do projeto devem existir:

```text
fleetops-ai/
├── app/
├── docs/
├── tests/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env
└── docker/
    └── postgres/
        └── 001_init.sql
```

## 3. Criar o .env

No PowerShell, na raiz do projeto:

```powershell
Copy-Item .env.example .env
```

Para ambiente local, altere pelo menos:

```text
POSTGRES_PASSWORD=uma_senha_local
```

Não envie o `.env` para o Git.

## 4. Subir o ambiente

```powershell
docker compose up -d --build
```

Acompanhe:

```powershell
docker compose ps
```

E os logs da API:

```powershell
docker compose logs -f api
```

## 5. Ingerir a base de conhecimento

A primeira inicialização cria PostgreSQL, pgvector, tabelas e dados
fictícios.

Depois que os containers estiverem saudáveis:

```powershell
docker compose exec api python -m app.ingest_knowledge
```

Isso gera novamente os embeddings dos arquivos operacionais:

- `contracts.md`
- `processing.md`
- `troubleshooting.md`

## 6. Abrir

Frontend:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Health:

```text
http://localhost:8000/health
```

## 7. Teste rápido

Pergunte:

```text
Por que a OS 10235 está bloqueada?
```

Depois:

```text
Qual é o contrato dela?
```

E teste o Scope Guard:

```text
Como fazer bolo de cenoura?
```

## 8. Rodar testes contra o Docker

Com o ambiente Docker no ar e a `.venv` local ativa:

```powershell
python -m pytest
```

## 9. Parar

```powershell
docker compose down
```

Os dados permanecem no volume Docker.

Para destruir também o banco e começar totalmente do zero:

```powershell
docker compose down -v
```

Depois:

```powershell
docker compose up -d --build
docker compose exec api python -m app.ingest_knowledge
```

## Observação importante sobre PostgreSQL

O arquivo `docker/postgres/001_init.sql` só é executado automaticamente
quando o volume do PostgreSQL é criado pela primeira vez.

Se o volume já existir, alterações nesse arquivo não são reaplicadas
automaticamente. Para recriar o ambiente fictício do zero, use:

```powershell
docker compose down -v
```

## Observação sobre o Ollama

O container usa:

```text
http://host.docker.internal:11434
```

para alcançar o Ollama do Windows.

Se a API não conseguir falar com o Ollama, primeiro confirme no Windows:

```powershell
ollama list
```

e que o serviço do Ollama está ativo.
