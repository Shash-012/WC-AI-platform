"""
Load and chunk World Cup text files for embedding.
Week 1: reads from backend/data/*.txt
Week 2: optionally pull live from API-Football and write to the same dir.
"""
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")

def load_documents() -> list[Document]:
    docs = []
    for fname in os.listdir(DATA_DIR):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            continue
        for para in content.replace("\r\n", "\n").replace("\r", "\n").split("\n\n"):
            para = para.strip()
            if para:
                docs.append(Document(page_content=para, metadata={"source": fname}))
    return docs

def split_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_documents(docs)
