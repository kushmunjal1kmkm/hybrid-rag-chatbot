"""
core/vector_store.py — ChromaDB persistent vector store for ChatMind.

Responsibilities:
  • Init / return the Chroma collection backed by local disk
  • Process uploaded files (PDF / TXT) → chunk → embed → store
  • Expose a retriever filtered by conversation ID
  • List uploaded documents for a given conversation
"""
import os
import tempfile
from pathlib import Path
from typing import Optional

from functools import lru_cache
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

import config


# ─────────────────────────────────────────────────────────────────────────────
# Embeddings
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_embeddings():

    """
    Return embedding function.
    Default: HuggingFace sentence-transformers (local, no API key needed).
    Optional: More embedding models will be added later LOL.
    """

    # Default: local HuggingFace embeddings (~90 MB download on first run)
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Vector Store singleton
# ─────────────────────────────────────────────────────────────────────────────

def get_vector_store() -> Chroma:
    """Return (or create) the persistent ChromaDB collection."""
    return Chroma(
        collection_name="chatmind_docs",
        embedding_function=_get_embeddings(),
        persist_directory=config.CHROMA_PERSIST_PATH,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Document processing
# ─────────────────────────────────────────────────────────────────────────────

def process_uploaded_file(
    file_path: str,
    file_name: str,
    conv_id: str,
) -> int:
    """
    Load a file, split into chunks, embed, and store in ChromaDB.
    Returns the number of chunks indexed.
    """
    ext = Path(file_name).suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
        docs = loader.load()
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
    else:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: .pdf, .txt")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Document] = splitter.split_documents(docs)

    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = file_name
        chunk.metadata["chunk_index"] = i
        chunk.metadata["conversation_id"] = conv_id
        chunk.metadata["total_chunks"] = len(chunks)

    if not chunks:
        return 0

    store = get_vector_store()
    store.add_documents(chunks)
    return len(chunks)


# ─────────────────────────────────────────────────────────────────────────────
# Retriever
# ─────────────────────────────────────────────────────────────────────────────

def get_retriever(conv_id: Optional[str] = None):
    """
    Return a retriever. If conv_id is given, filter results to that
    conversation's documents only.
    """
    store = get_vector_store()
    search_kwargs: dict = {"k": config.RAG_TOP_K}
    if conv_id:
        search_kwargs["filter"] = {"conversation_id": conv_id}
    return store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Metadata queries
# ─────────────────────────────────────────────────────────────────────────────

def get_uploaded_docs_for_conversation(conv_id: str) -> list[str]:
    """Return sorted list of unique source filenames for a conversation."""
    try:
        store = get_vector_store()
        results = store.get(where={"conversation_id": conv_id})
        sources: set[str] = set()
        for meta in results.get("metadatas", []):
            if meta and "source" in meta:
                sources.add(meta["source"])
        return sorted(sources)
    except Exception:
        return []


def delete_docs_for_conversation(conv_id: str) -> None:
    """Remove all ChromaDB documents belonging to a conversation."""
    try:
        store = get_vector_store()
        results = store.get(where={"conversation_id": conv_id})
        ids = results.get("ids", [])
        if ids:
            store.delete(ids=ids)
    except Exception:
        pass
