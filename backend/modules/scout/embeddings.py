"""
Build and persist the FAISS vector store.
Week 1: uses OpenAI embeddings (fast to set up, needs API key).
Week 2: swap OpenAIEmbeddings for HuggingFaceEmbeddings (all-MiniLM-L6-v2).
"""
import os
import pickle
from langchain_community.vectorstores import FAISS

# Week 1 default — swap in Week 2:
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "../../vector_store")
CHUNKS_PATH = os.path.join(VECTOR_STORE_PATH, "chunks.pkl")

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def save_chunks(chunks):
    """Pickle document chunks alongside the FAISS index for BM25 reuse."""
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

def load_chunks():
    """Load pickled chunks. Raises FileNotFoundError if not yet built."""
    if not os.path.exists(CHUNKS_PATH):
        raise FileNotFoundError(f"No saved chunks at {CHUNKS_PATH}. Run build_vector_store first.")
    with open(CHUNKS_PATH, "rb") as f:
        return pickle.load(f)

def build_vector_store(chunks):
    """Embed chunks, save FAISS index, and persist chunks for BM25."""
    embeddings = get_embeddings()
    store = FAISS.from_documents(chunks, embeddings)
    store.save_local(VECTOR_STORE_PATH)
    save_chunks(chunks)
    return store

def load_vector_store(chunks=None):
    """Load persisted FAISS index. Build it first if it doesn't exist."""
    embeddings = get_embeddings()
    if not os.path.exists(VECTOR_STORE_PATH) or not os.listdir(VECTOR_STORE_PATH):
        if chunks is None:
            raise ValueError("No Vector store found and no chunks provided to build vector store.")
        return build_vector_store(chunks)
    return FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
