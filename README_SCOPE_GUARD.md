# FleetOps v7 — Scope Guard

## Problema encontrado

Com uma OS ja salva na memoria da thread, perguntas sem relacao com
FleetOps ainda percorriam o fluxo operacional.

Exemplos:

- `qual a soma de 1 + 2`
- `como fazer bolo de cenoura?`

Isso fazia o sistema consultar diagnostico, RAG e LLM mesmo quando a
pergunta estava fora do objetivo do produto.

## Novo fluxo

```text
START
  |
scope_guard
  |------------------------|
  |                        |
dentro do dominio      fora do dominio
  |                        |
diagnostic            out_of_scope
  |                        |
...                      END
```

Uma pergunta fora do escopo nao chama:

- diagnostico operacional;
- MCP de diagnostico;
- RAG;
- embedding;
- Ollama.

## Follow-ups que continuam validos

A memoria continua funcionando para perguntas como:

- `qual o status da fila?`
- `qual o contrato dela?`
- `qual a placa dela?`
- `por que ela esta bloqueada?`

## Testes

Com a API desligada:

```powershell
python -m pytest tests/test_scope_guard.py
```

Com a API rodando:

```powershell
python -m pytest tests/test_scope_guard_integration.py
```

Depois execute toda a regressao:

```powershell
python -m pytest
```
