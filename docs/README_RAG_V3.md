# RAG v3 — Hybrid Retrieval + Source Diversity

Mudança proposta para `app/rag/knowledge_search.py`.

## Estratégia

1. pgvector busca um pool maior de candidatos (`12` por padrão);
2. cada candidato recebe `lexical_score`;
3. o ranking final usa:
   - 70% similaridade vetorial;
   - 30% cobertura lexical;
4. no top final, no máximo 2 chunks do mesmo documento quando houver alternativas;
5. `similarity` continua sendo o score vetorial original;
6. `retrieval_score` registra o score híbrido usado para ordenar.

## Variáveis opcionais

- `RAG_CANDIDATE_LIMIT=12`
- `RAG_VECTOR_WEIGHT=0.70`
- `RAG_LEXICAL_WEIGHT=0.30`
- `RAG_MAX_CHUNKS_PER_SOURCE=2`

## Validação

```powershell
python -m pytest tests/test_rag_reranking.py -v
python -m pytest
python -m app.evals.evaluate_rag
```

Compare o novo relatório com o baseline anterior:

- Hit@3: 0.944
- Recall@3: 0.917
- MRR: 0.861
- Top1 Accuracy: 0.778
- Term Coverage: 0.833

Não aceite a mudança apenas porque os três casos-alvo melhoraram.
A avaliação completa de 18 casos deve permanecer saudável.
