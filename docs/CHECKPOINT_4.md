# Checkpoint 4 — Homologacao e Testes Automatizados

## Objetivo

Transformar o FleetOps AI de um prototipo funcional em um sistema com
comportamentos verificaveis automaticamente.

## Estado homologado

A arquitetura validada nesta etapa e:

Frontend HTML/CSS/JS
→ FastAPI
→ LangGraph
→ MCP
→ PostgreSQL / dados operacionais
→ RAG / pgvector
→ Ollama
→ resposta ao usuario

O agente possui memoria persistente por `thread_id`, observabilidade por
`trace_id`, fast path para perguntas factuais e fallback deterministico
quando dependencias de IA ficam indisponiveis.

## Resultado dos testes

### Testes unitarios

Resultado:

- 12 testes executados
- 12 testes aprovados
- 0 falhas

Comportamentos protegidos:

- extracao do numero da OS;
- identificacao de intencoes de fast path;
- traducao de codigos tecnicos;
- resposta direta do contrato;
- resposta direta da placa;
- modo degradado sem chamada ao LLM;
- falha controlada do RAG;
- falha controlada do LLM;
- falha critica do diagnostico.

### Testes de integracao

Resultado:

- 6 testes executados
- 6 testes aprovados
- 0 falhas

Fluxos validados:

- `/health`;
- OS 10235 bloqueada;
- consulta de conhecimento via RAG;
- retorno de fontes do RAG;
- memoria persistente na mesma thread;
- fast path apos pergunta analitica;
- fast path sem consulta ao RAG;
- OS 10236 em estado OK;
- erro HTTP 400 para thread nova sem OS em contexto.

## Evidencias visiveis na interface

Para a OS 10235 o FleetOps apresenta:

- diagnostico: BLOQUEADA;
- contrato: 2002;
- status do contrato: INATIVO;
- fila: ERRO;
- processamento: Analise com IA;
- modo: Normal;
- trace ID;
- tempo de resposta;
- documentos consultados pelo RAG;
- similaridade de cada documento.

A resposta analitica observada ficou na faixa aproximada de 2 a 3 segundos
nos testes recentes com o modelo local.

## Decisao arquitetural consolidada

O LLM nao e a fonte da verdade.

Dados operacionais sao obtidos pelas ferramentas.
Regras sao recuperadas pelo RAG.
O LLM e utilizado para explicar os fatos e regras encontrados.

Para perguntas factuais simples, o FleetOps utiliza fast path e evita RAG
e LLM quando essas etapas nao agregam valor.

## Proxima melhoria

Foi identificado um ponto de qualidade no chunking.

O modelo atual pode separar:

`CONTR-001`

da descricao da regra.

A melhoria seguinte garante que identificador e descricao sejam gravados
no mesmo chunk, aumentando a rastreabilidade e a qualidade das evidencias
recuperadas pelo RAG.
