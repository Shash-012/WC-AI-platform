"""
Build and persist the FAISS vector store.
Week 1: uses OpenAI embeddings (fast to set up, needs API key).
Week 2: swap OpenAIEmbeddings for HuggingFaceEmbeddings (all-MiniLM-L6-v2).
"""
import os
from langchain_community.vectorstores import FAISS

# Week 1 default — swap in Week 2:
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "../../vector_store")

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def build_vector_store(chunks):
    """Embed chunks and save FAISS index locally."""
    embeddings = get_embeddings()
    store = FAISS.from_documents(chunks, embeddings)
    store.save_local(VECTOR_STORE_PATH)
    return store

def load_vector_store(chunks=None):
    """Load persisted FAISS index. Build it first if it doesn't exist."""
    embeddings = get_embeddings()
    if not os.path.exists(VECTOR_STORE_PATH) or not os.listdir(VECTOR_STORE_PATH):
        if chunks is None:
            raise ValueError("No Vector store found and no chunks provided to build vector store.")
        return build_vector_store(chunks)
    return FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
