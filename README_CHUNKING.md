# FleetOps AI — melhoria de chunking

Este pacote prepara a proxima melhoria do RAG.

## Arquivos

```text
app/services/knowledge_chunking.py
tests/test_knowledge_chunking.py
docs/CHECKPOINT_4.md
```

## O que muda

O chunking deixa de separar identificadores de regra como:

```text
CONTR-001

Uma Ordem de Servico...
```

Em vez de dois chunks, o resultado passa a ser um unico chunk:

```text
CONTR-001

Uma Ordem de Servico...
```

Isso melhora a rastreabilidade porque, quando a busca vetorial retornar a
descricao da regra, o identificador da regra vem junto.

## Testar agora

Copie os arquivos para o projeto e rode:

```powershell
python -m pytest tests/test_knowledge_chunking.py
```

Esses testes nao alteram o banco.

## Importante

Ainda nao rode a reingestao.

Para integrar o novo chunking com seguranca, precisamos alterar o
`ingest_knowledge.py` atual do projeto. Envie esse arquivo e a integracao
sera devolvida completa, preservando sua conexao com PostgreSQL, Ollama e
o modelo `knowledge_documents`.
