from __future__ import annotations
import argparse, json
from pathlib import Path
from statistics import mean
from app.rag.knowledge_search import search_knowledge

def evaluate_case(case, k):
    raw = search_knowledge(
        query=case["question"],
        limit=k,
        trace_id=f"rag-eval-{case['id']}",
    )
    results = json.loads(raw)

    prefixes = case["relevant_source_prefixes"]
    expected_terms = case.get("expected_terms", [])

    matched = set()
    first_rank = None
    relevant_hits = []

    for rank, item in enumerate(results, start=1):
        source = item.get("source", "")
        for prefix in prefixes:
            if source.startswith(prefix):
                matched.add(prefix)
                relevant_hits.append({"rank": rank, "source": source})
                if first_rank is None:
                    first_rank = rank

    hit = 1.0 if first_rank is not None else 0.0
    recall = len(matched) / len(prefixes) if prefixes else 1.0
    rr = 1.0 / first_rank if first_rank is not None else 0.0

    combined = "\n".join(item.get("content", "") for item in results).upper()
    found_terms = [t for t in expected_terms if t.upper() in combined]
    term_coverage = len(found_terms) / len(expected_terms) if expected_terms else 1.0

    top1_relevant = 1.0 if first_rank == 1 else 0.0

    return {
        "id": case["id"],
        "question": case["question"],
        "hit_at_k": hit,
        "recall_at_k": recall,
        "reciprocal_rank": rr,
        "top1_relevant": top1_relevant,
        "term_coverage": term_coverage,
        "first_relevant_rank": first_rank,
        "retrieved_sources": [item.get("source", "") for item in results],
        "relevant_hits": relevant_hits,
        "expected_terms": expected_terms,
        "found_terms": found_terms,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="evals/rag_cases.json")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--json-out", default="evals/rag_eval_results.json")
    args = parser.parse_args()

    cases = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    rows = [evaluate_case(c, args.k) for c in cases]

    print("\n=== FleetOps RAG Evaluation ===")
    print(f"Cases: {len(rows)} | K: {args.k}\n")

    for r in rows:
        status = "PASS" if r["hit_at_k"] else "FAIL"
        print(
            f"{status} {r['id']} | "
            f"rank={r['first_relevant_rank']} | "
            f"recall={r['recall_at_k']:.2f} | "
            f"top1={r['top1_relevant']:.0f} | "
            f"terms={r['term_coverage']:.2f}"
        )
        print(f"  Q: {r['question']}")
        print("  sources: " + ", ".join(r["retrieved_sources"]))

    summary = {
        f"hit_at_{args.k}": mean(r["hit_at_k"] for r in rows),
        f"recall_at_{args.k}": mean(r["recall_at_k"] for r in rows),
        "mrr": mean(r["reciprocal_rank"] for r in rows),
        "top1_accuracy": mean(r["top1_relevant"] for r in rows),
        "term_coverage": mean(r["term_coverage"] for r in rows),
        "cases": len(rows),
        "k": args.k,
    }

    print("\n=== Summary ===")
    print(f"Hit@{args.k}: {summary[f'hit_at_{args.k}']:.3f}")
    print(f"Recall@{args.k}: {summary[f'recall_at_{args.k}']:.3f}")
    print(f"MRR: {summary['mrr']:.3f}")
    print(f"Top1 Accuracy: {summary['top1_accuracy']:.3f}")
    print(f"Term Coverage: {summary['term_coverage']:.3f}")

    Path(args.json_out).write_text(
        json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nJSON report: {args.json_out}")

    if any(not r["hit_at_k"] for r in rows):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
