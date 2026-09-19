# Avaliação Formal do RAG — FleetOps AI

Arquivos:
- `evals/rag_cases.json`
- `app/evals/evaluate_rag.py`
- `app/evals/__init__.py` vazio

Métricas:
- Hit@K: ao menos uma fonte relevante no top K.
- Recall@K: proporção das fontes relevantes recuperadas.
- MRR: posição da primeira fonte relevante.
- Term Coverage: presença de termos esperados no conteúdo recuperado.

Executar:

```powershell
python -m app.evals.evaluate_rag
```

Por padrão usa `K=3`.

Meta inicial do MVP:
- Hit@3 >= 0.80
- MRR >= 0.60

Essas metas são internas ao projeto, não um padrão universal.
