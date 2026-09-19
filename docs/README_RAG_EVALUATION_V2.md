# Avaliação Formal do RAG — FleetOps AI v2

A v2 amplia o benchmark para 18 perguntas com formulações mais naturais e ambíguas.

## O que é medido

- Hit@K
- Recall@K
- MRR
- Top1 Accuracy
- Term Coverage

## Executar

```powershell
python -m app.evals.evaluate_rag
```

Saída detalhada em:

```text
evals/rag_eval_results.json
```

## Metas internas do MVP

```text
Hit@3 >= 0.80
MRR >= 0.60
Top1 Accuracy >= 0.50
Term Coverage >= 0.75
```

Esses limites são metas internas deste projeto e não padrões universais.

## Interpretação

- Hit@3 alto: o documento correto está chegando ao agente.
- MRR alto: a fonte correta aparece cedo no ranking.
- Top1 Accuracy alto: a primeira fonte costuma ser relevante.
- Term Coverage alto: termos críticos das regras aparecem no contexto recuperado.

## Próxima evolução

Depois desta v2, separar avaliação de retrieval da avaliação da resposta final do agente.
