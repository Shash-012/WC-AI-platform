"""
modules/scout/reranker.py

Cross-encoder reranker for the RAG pipeline.

Wraps an existing retriever (e.g. EnsembleRetriever) and reranks its results
using a sentence-transformers CrossEncoder before returning the top-N docs.

Pipeline:
    query → base_retriever.invoke() → cross_encoder.predict() → top_n docs → LLM
"""

from typing import Any

from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict
from sentence_transformers import CrossEncoder


CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-12-v2"
RERANK_TOP_N = 5


class RerankingRetriever(BaseRetriever):
    """
    Retriever that wraps a base retriever and reranks its results with a
    cross-encoder model.

    The cross-encoder scores each (query, document) pair jointly, which is
    more accurate than the bi-encoder similarity used inside FAISS — at the
    cost of an extra forward pass over the top-k candidates.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    base_retriever: BaseRetriever
    cross_encoder: Any  # sentence_transformers.CrossEncoder — typed as Any so mocks pass pydantic v2 validation
    top_n: int = RERANK_TOP_N

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        docs = self.base_retriever.invoke(query)
        if not docs:
            return docs

        pairs = [(query, doc.page_content) for doc in docs]
        scores = self.cross_encoder.predict(pairs)

        ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in ranked[: self.top_n]]


def build_reranking_retriever(
    base_retriever: BaseRetriever,
    model_name: str = CROSS_ENCODER_MODEL,
    top_n: int = RERANK_TOP_N,
) -> RerankingRetriever:
    """
    Factory: loads the cross-encoder model and returns a RerankingRetriever
    that wraps the given base retriever.

    Args:
        base_retriever: The retriever whose results will be reranked
                        (typically an EnsembleRetriever).
        model_name:     HuggingFace cross-encoder model identifier.
        top_n:          Number of documents to keep after reranking.
    """
    cross_encoder = CrossEncoder(model_name)
    return RerankingRetriever(
        base_retriever=base_retriever,
        cross_encoder=cross_encoder,
        top_n=top_n,
    )
