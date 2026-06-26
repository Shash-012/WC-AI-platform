"""
benchmarks/metrics.py

Pure metric functions for retrieval quality evaluation.
All use binary relevance: a document is relevant if any of the
relevant_keywords appears (case-insensitive) in its page_content.

Metrics implemented:
  hit_rate_at_k      - 1 if any top-k doc is relevant, else 0
  precision_at_k     - fraction of top-k docs that are relevant
  reciprocal_rank    - 1/rank of the first relevant doc (0 if none)
  ndcg_at_k          - normalised discounted cumulative gain at k
  mean_metric        - convenience aggregator
"""

import math
from langchain_core.documents import Document


def _is_relevant(doc: Document, relevant_keywords: list[str]) -> bool:
    content = doc.page_content.lower()
    return any(kw.lower() in content for kw in relevant_keywords)


def hit_rate_at_k(docs: list[Document], relevant_keywords: list[str], k: int) -> float:
    """1.0 if at least one of the top-k retrieved documents is relevant."""
    return float(any(_is_relevant(d, relevant_keywords) for d in docs[:k]))


def precision_at_k(docs: list[Document], relevant_keywords: list[str], k: int) -> float:
    """Fraction of the top-k retrieved documents that are relevant."""
    if k == 0:
        return 0.0
    relevant = sum(1 for d in docs[:k] if _is_relevant(d, relevant_keywords))
    return relevant / k


def reciprocal_rank(docs: list[Document], relevant_keywords: list[str]) -> float:
    """1/rank of the first relevant document (0.0 if no relevant doc found)."""
    for rank, doc in enumerate(docs, start=1):
        if _is_relevant(doc, relevant_keywords):
            return 1.0 / rank
    return 0.0


def ndcg_at_k(docs: list[Document], relevant_keywords: list[str], k: int) -> float:
    """
    Normalised Discounted Cumulative Gain at k with binary relevance.

    DCG  = Σ rel_i / log2(i+2)   for i in 0..k-1
    IDCG = DCG of a perfect ranking (all relevant docs first)
    nDCG = DCG / IDCG
    """
    gains = [
        1.0 / math.log2(i + 2)
        for i, doc in enumerate(docs[:k])
        if _is_relevant(doc, relevant_keywords)
    ]
    dcg = sum(gains)

    # Best possible DCG: fill positions 0..k-1 with relevant docs
    n_relevant_in_top_k = sum(1 for d in docs[:k] if _is_relevant(d, relevant_keywords))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(n_relevant_in_top_k))

    return dcg / idcg if idcg > 0 else 0.0


def mean_metric(values: list[float]) -> float:
    """Average of a list of metric values."""
    return sum(values) / len(values) if values else 0.0
