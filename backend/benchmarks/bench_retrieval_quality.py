"""
benchmarks/bench_retrieval_quality.py

Measures retrieval quality against a labeled ground truth set.
Supports three retriever modes so you can compare them directly.

Metrics reported per query and as aggregate means:
  Hit Rate @ 1/3/5   - did the right doc appear in top k?
  Precision @ 3/5    - what fraction of top-k docs were relevant?
  MRR                - Mean Reciprocal Rank
  nDCG @ 5           - Normalised DCG at 5

Run from the backend/ directory:
    python -m benchmarks.bench_retrieval_quality                 # full pipeline (default)
    python -m benchmarks.bench_retrieval_quality --mode faiss    # FAISS only
    python -m benchmarks.bench_retrieval_quality --mode hybrid   # BM25 + FAISS, no reranker
    python -m benchmarks.bench_retrieval_quality --mode full     # hybrid + cross-encoder reranker

Compare all three at once:
    for mode in faiss hybrid full; do
        echo "=== $mode ===" && python -m benchmarks.bench_retrieval_quality --mode $mode
    done
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from benchmarks.ground_truth import GROUND_TRUTH
from benchmarks.metrics import (
    hit_rate_at_k,
    precision_at_k,
    reciprocal_rank,
    ndcg_at_k,
    mean_metric,
)
from modules.scout.embeddings import load_vector_store, load_chunks
from modules.scout.reranker import build_reranking_retriever
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever


MODES = ("faiss", "hybrid", "full")


def build_retriever(mode: str):
    store  = load_vector_store()
    chunks = load_chunks()

    if mode == "faiss":
        return store.as_retriever(search_kwargs={"k": 5})

    bm25     = BM25Retriever.from_documents(chunks, k=8)
    faiss    = store.as_retriever(search_kwargs={"k": 8})
    ensemble = EnsembleRetriever(
        retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
    )

    if mode == "hybrid":
        return ensemble

    # mode == "full"
    return build_reranking_retriever(ensemble, top_n=5)


def run(mode: str = "full", k_values=(1, 3, 5)):
    print(f"Loading retrieval pipeline (mode: {mode})...")
    retriever = build_retriever(mode)
    n = len(GROUND_TRUTH)
    print(f"Evaluating {n} queries...\n")

    rows = []
    for item in GROUND_TRUTH:
        docs = retriever.invoke(item["query"])
        row = {
            "description": item["description"],
            "query_short": item["query"][:48],
            "rr": reciprocal_rank(docs, item["relevant_keywords"]),
        }
        for k in k_values:
            row[f"hit@{k}"] = hit_rate_at_k(docs, item["relevant_keywords"], k)
            row[f"p@{k}"]   = precision_at_k(docs, item["relevant_keywords"], k)
            row[f"ndcg@{k}"] = ndcg_at_k(docs, item["relevant_keywords"], k)
        rows.append(row)

    # ── Per-query table ───────────────────────────────────────────────────
    col_w = 50
    k_cols = "".join(f"  Hit@{k}" for k in k_values)
    header = f"  {'Query':<{col_w}} {'MRR':>5}{k_cols}  {'P@3':>5}  {'nDCG@5':>7}"
    sep = "  " + "-" * (len(header) - 2)
    print(header)
    print(sep)

    for r in rows:
        hits = "".join(f"  {r[f'hit@{k}']:>5.0f}" for k in k_values)
        print(
            f"  {r['query_short']:<{col_w}} {r['rr']:>5.2f}"
            f"{hits}  {r['p@3']:>5.2f}  {r['ndcg@5']:>7.3f}"
        )

    # ── Aggregate means ───────────────────────────────────────────────────
    print(sep)
    hits_mean = "".join(f"  {mean_metric([r[f'hit@{k}'] for r in rows]):>5.3f}" for k in k_values)
    print(
        f"  {'MEAN':<{col_w}} {mean_metric([r['rr'] for r in rows]):>5.3f}"
        f"{hits_mean}  {mean_metric([r['p@3'] for r in rows]):>5.3f}"
        f"  {mean_metric([r['ndcg@5'] for r in rows]):>7.3f}"
    )

    # ── Summary box ──────────────────────────────────────────────────────
    print("\n┌─────────────────────────────┐")
    print(f"│  MRR          {mean_metric([r['rr']       for r in rows]):.3f}           │")
    print(f"│  Hit Rate@1   {mean_metric([r['hit@1']    for r in rows]):.3f}           │")
    print(f"│  Hit Rate@3   {mean_metric([r['hit@3']    for r in rows]):.3f}           │")
    print(f"│  Hit Rate@5   {mean_metric([r['hit@5']    for r in rows]):.3f}           │")
    print(f"│  Precision@3  {mean_metric([r['p@3']      for r in rows]):.3f}           │")
    print(f"│  nDCG@5       {mean_metric([r['ndcg@5']   for r in rows]):.3f}           │")
    print("└─────────────────────────────┘")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=MODES, default="full",
        help="Retriever to evaluate: faiss | hybrid | full (default: full)"
    )
    parser.add_argument(
        "--k", nargs="+", type=int, default=[1, 3, 5],
        help="k values for Hit Rate / Precision metrics (default: 1 3 5)"
    )
    args = parser.parse_args()
    run(mode=args.mode, k_values=args.k)
