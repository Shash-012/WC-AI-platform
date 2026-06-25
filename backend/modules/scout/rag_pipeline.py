"""
The core RAG chain: retriever + LLM + prompt.
Run this file directly to test in terminal (Week 1 goal).

Stateless by design: the chain holds NO server-side memory. Conversation
history is passed in per request via the `chat_history` input, so a single
cached chain instance can serve concurrent requests without any cross-talk.
"""

from dotenv import load_dotenv
from langchain_classic.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_classic.prompts import PromptTemplate
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_groq import ChatGroq

from .data_loader import load_documents, split_documents
from .embeddings import build_vector_store, load_vector_store, load_chunks
import time

load_dotenv()

SYSTEM_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are an AI assistant for the 2026 FIFA World Cup.
Answer using ONLY the context below. Be specific and direct.
If the context contains partial information relevant to the question, use it.
Only say "I don't have that information" if the context contains absolutely nothing related.

Context:
{context}

Question: {question}
Answer:"""
)

def get_chain():
    try:
        store = load_vector_store()
        chunks = load_chunks()
    except Exception:
        print("Vector store not found — building from data files...")
        docs = load_documents()
        chunks = split_documents(docs)
        store = build_vector_store(chunks)  # also persists chunks via save_chunks

    # Hybrid retrieval: BM25 (keyword) + FAISS (semantic), fused via RRF.
    # weights=[0.6, 0.4] → keyword search weighted higher; c=60 is the RRF constant.
    bm25_retriever = BM25Retriever.from_documents(chunks, k=8)
    faiss_retriever = store.as_retriever(search_kwargs={"k": 8})
    retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.6, 0.4],
        c=60,
    )

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

    # No memory= here. Without a memory object the chain expects `chat_history`
    # as an input on every call, which keeps it stateless and thread-safe.
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=False,
        combine_docs_chain_kwargs={"prompt": SYSTEM_PROMPT},
        verbose=True
    )

if __name__ == "__main__":
    chain = get_chain()
    # The REPL keeps its own history and feeds it back in — the chain itself
    # remembers nothing between turns.
    chat_history: list[tuple[str, str]] = []
    print("World Cup AI Scout ready. Type 'quit' to exit.\n")
    while True:
        q = input("You: ").strip()
        if q.lower() in ("quit", "exit"):
            break
        for attempt in range(3):
            try:
                result = chain.invoke({"question": q, "chat_history": chat_history})
                answer = result["answer"]
                print(f"Scout: {answer}\n")
                chat_history.append((q, answer))
                break
            except Exception as e:
                if attempt < 2:
                    print(f"Retrying... ({attempt + 1})")
                    time.sleep(10)
                else:
                    print(f"Failed after 3 attempts: {e}\n")
