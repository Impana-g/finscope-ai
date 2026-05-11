"""
RAG Ingestor — loads documents into ChromaDB for retrieval.

Supports:
  • Plain-text files (.txt)
  • PDF files (.pdf) — requires PyPDF2
  • Raw text strings via ingest_text()

Each document is chunked into ~500 character segments with 50-char overlap,
then embedded and stored in a sector-specific ChromaDB collection.
"""

import os
import uuid
import hashlib
from typing import Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_PATH     = "./data/chromadb"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50

_embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)


def _get_client() -> chromadb.PersistentClient:
    os.makedirs(CHROMA_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PATH)


def _get_collection(sector: str, client: chromadb.PersistentClient):
    # ChromaDB requires names to be 3-512 chars
    name = f"sector_{sector.lower()}"
    return client.get_or_create_collection(
        name=name,
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
                overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def _content_hash(text: str) -> str:
    """Generate a short hash for deduplication."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


class RAGIngestor:
    """Ingests documents into ChromaDB for RAG retrieval."""

    def __init__(self):
        self._client = _get_client()

    def ingest_text(self, text: str, sector: str,
                    company: str = "unknown",
                    doc_type: str = "report",
                    year: str = "unknown",
                    source_url: str = "manual") -> int:
        """
        Chunk and store a raw text string.
        Returns the number of chunks stored.
        """
        collection = _get_collection(sector, self._client)
        chunks = _chunk_text(text)

        if not chunks:
            return 0

        ids, documents, metadatas = [], [], []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{_content_hash(chunk)}_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "company":     company,
                "doc_type":    doc_type,
                "year":        year,
                "source_url":  source_url,
                "chunk_index": i,
            })

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"  [INGESTED] {len(chunks)} chunks -> {sector}/{company}")
        return len(chunks)

    def ingest_file(self, filepath: str, sector: str,
                    company: str = "unknown",
                    doc_type: str = "report",
                    year: str = "unknown") -> int:
        """
        Read a file (.txt or .pdf) and ingest its contents.
        Returns the number of chunks stored.
        """
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".txt":
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        elif ext == ".pdf":
            text = self._read_pdf(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Use .txt or .pdf")

        return self.ingest_text(
            text=text,
            sector=sector,
            company=company,
            doc_type=doc_type,
            year=year,
            source_url=filepath,
        )

    def ingest_directory(self, dirpath: str, sector: str,
                         company: str = "unknown",
                         doc_type: str = "report",
                         year: str = "unknown") -> int:
        """Ingest all .txt and .pdf files in a directory."""
        total = 0
        for fname in os.listdir(dirpath):
            if fname.endswith((".txt", ".pdf")):
                fpath = os.path.join(dirpath, fname)
                total += self.ingest_file(
                    fpath, sector, company, doc_type, year
                )
        return total

    def collection_stats(self, sector: str) -> dict:
        """Return basic stats about a sector collection."""
        try:
            col = _get_collection(sector, self._client)
            return {"sector": sector, "count": col.count()}
        except Exception:
            return {"sector": sector, "count": 0}

    @staticmethod
    def _read_pdf(filepath: str) -> str:
        """Extract text from a PDF file."""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF ingestion. "
                "Install it with: pip install PyPDF2"
            )
