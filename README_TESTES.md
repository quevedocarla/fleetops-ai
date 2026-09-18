# FleetOps AI - Testes automatizados

Este pacote adiciona uma camada de homologação automatizada ao projeto.

## 1. Instalar dependências de teste

Na raiz do projeto:

```powershell
pip install -r requirements-test.txt
```

## 2. Copiar arquivos

Copie:

- `tests/test_agent_unit.py`
- `tests/test_agent_integration.py`
- `pytest.ini`
- `requirements-test.txt`

para a raiz do projeto FleetOps.

Estrutura esperada:

```text
fleetops-ai/
├── app/
├── tests/
│   ├── test_agent_unit.py
│   └── test_agent_integration.py
├── pytest.ini
└── requirements-test.txt
```

## 3. Rodar somente testes unitários

A API pode estar desligada.

```powershell
pytest tests/test_agent_unit.py
```

## 4. Rodar testes de integração

Primeiro deixe a API rodando em outro PowerShell:

```powershell
python run_api.py
```

Em um segundo PowerShell:

```powershell
pytest tests/test_agent_integration.py
```

## 5. Rodar tudo

Com a API rodando:

```powershell
pytest
```

## O que os testes protegem

- extração do número da OS;
- detecção de fast path;
- tradução dos termos técnicos;
- resposta direta de contrato;
- resposta direta de placa;
- fallback sem LLM;
- falha simulada do RAG;
- falha simulada do LLM;
- falha crítica do diagnóstico;
- health check;
- OS 10235 bloqueada;
- RAG e fontes;
- memória por thread;
- fast path sem RAG;
- OS 10236 com diagnóstico OK;
- thread nova sem OS retorna HTTP 400.
