"""
benchmarks/bench_latency.py

Measures per-component retrieval latency across N rounds of all ground-truth
queries and reports p50 / p95 / p99 in milliseconds.

Components timed independently:
  BM25 only             - keyword retrieval
  FAISS only            - semantic retrieval
  Ensemble (BM25+FAISS) - hybrid RRF fusion
  Ensemble + Reranker   - full pipeline (cross-encoder on top)

Run from the backend/ directory:
    python -m benchmarks.bench_latency
    python -m benchmarks.bench_latency --rounds 5
"""

import sys
import os
import time
import statistics
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from modules.scout.embeddings import load_vector_store, load_chunks
from modules.scout.reranker import build_reranking_retriever
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from benchmarks.ground_truth import GROUND_TRUTH

QUERIES = [item["query"] for item in GROUND_TRUTH]


def _pct(sorted_times_ms: list[float], p: int) -> float:
    idx = max(0, int(p / 100 * len(sorted_times_ms)) - 1)
    return sorted_times_ms[idx]


def _bench_component(label: str, retriever, queries: list[str], rounds: int) -> dict:
    times = []
    for _ in range(rounds):
        for q in queries:
            t0 = time.perf_counter()
            retriever.invoke(q)
            times.append((time.perf_counter() - t0) * 1000)  # ms

    s = sorted(times)
    result = {
        "label": label,
        "n": len(times),
        "mean": statistics.mean(times),
        "p50": _pct(s, 50),
        "p95": _pct(s, 95),
        "p99": _pct(s, 99),
    }

    print(
        f"  {label:<38}"
        f"  mean={result['mean']:>7.1f}ms"
        f"  p50={result['p50']:>7.1f}ms"
        f"  p95={result['p95']:>7.1f}ms"
        f"  p99={result['p99']:>7.1f}ms"
        f"  (n={result['n']})"
    )
    return result


def run(rounds: int = 3):
    print("Loading pipeline components...")
    store  = load_vector_store()
    chunks = load_chunks()

    bm25     = BM25Retriever.from_documents(chunks, k=8)
    faiss    = store.as_retriever(search_kwargs={"k": 8})
    ensemble = EnsembleRetriever(
        retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
    )
    reranker = build_reranking_retriever(ensemble, top_n=5)

    print(f"\nLatency benchmark — {rounds} round(s) × {len(QUERIES)} queries\n")

    results = []
    results.append(_bench_component("BM25 only",             bm25,     QUERIES, rounds))
    results.append(_bench_component("FAISS only",            faiss,    QUERIES, rounds))
    results.append(_bench_component("Ensemble (BM25 + FAISS)", ensemble, QUERIES, rounds))
    results.append(_bench_component("Ensemble + Reranker",   reranker, QUERIES, rounds))

    # Derived: reranker overhead = full pipeline minus ensemble
    reranker_overhead_mean = results[3]["mean"] - results[2]["mean"]
    reranker_overhead_p95  = results[3]["p95"]  - results[2]["p95"]
    print(
        f"\n  {'Reranker overhead (derived)':<38}"
        f"  mean={reranker_overhead_mean:>7.1f}ms"
        f"  p95={reranker_overhead_p95:>7.1f}ms"
    )

    print("\n┌──────────────────────────────────────────────────────────┐")
    for r in results:
        print(f"│  {r['label']:<38}  p50 {r['p50']:>6.0f}ms  p95 {r['p95']:>6.0f}ms  │")
    print("└──────────────────────────────────────────────────────────┘")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rounds", type=int, default=3,
        help="Number of full passes over the query set (default: 3)"
    )
    args = parser.parse_args()
    run(rounds=args.rounds)
