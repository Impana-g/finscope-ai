import os
import uuid
import hashlib
import re
from typing import Optional
from datetime import datetime

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_PATH      = "./data/chromadb"
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"
CHUNK_SIZE       = 500
CHUNK_OVERLAP    = 80

_embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)


def _get_chroma_client() -> chromadb.PersistentClient:
    os.makedirs(CHROMA_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PATH)


def _get_collection(sector: str, chroma_client: chromadb.PersistentClient):
    return chroma_client.get_or_create_collection(
        name=sector.lower(),
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = text.strip()
    if not text:
        return []

    chunks = []
    start  = 0

    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary != -1 and boundary > start + overlap:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap

    return chunks


def _make_chunk_id(text: str, source: str, idx: int) -> str:
    digest = hashlib.md5(f"{source}::{idx}::{text[:80]}".encode()).hexdigest()[:12]
    return f"chunk_{digest}"


def _extract_pdf_text(pdf_path: str) -> str:
    try:
        import fitz
        doc   = fitz.open(pdf_path)
        pages = [page.get_text("text") for page in doc]
        doc.close()
        return "\n\n".join(pages)
    except ImportError:
        pass

    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        raise ImportError("Install PyMuPDF:  pip install PyMuPDF")


class RAGIngestion:
    def __init__(self):
        self._client = _get_chroma_client()

    def ingest_pdf(self, pdf_path: str, sector: str, company: str,
                   doc_type: str = "annual_report", year: Optional[int] = None) -> int:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        print(f"📄 Extracting text from {pdf_path}...")
        raw_text = _extract_pdf_text(pdf_path)
        if not raw_text.strip():
            print("⚠️  No text extracted. Skipping.")
            return 0
        return self.ingest_text(
            text=raw_text, sector=sector, company=company,
            source_url=pdf_path, doc_type=doc_type, year=year,
        )

    def ingest_web_results(self, results: dict, sector: str, company: str) -> int:
        if not results.get("success"):
            print("⚠️  Skipping failed search result.")
            return 0

        total       = 0
        raw_results = results.get("raw_results", [])

        if not raw_results:
            raw_results = [{
                "url":     results.get("query", "web_search"),
                "content": results.get("content", ""),
                "title":   results.get("query", ""),
            }]

        for item in raw_results:
            url     = item.get("url", "web_search")
            content = item.get("content", "")
            title   = item.get("title", "")
            if not content.strip():
                continue
            added = self.ingest_text(
                text=f"{title}\n\n{content}" if title else content,
                sector=sector, company=company,
                source_url=url, doc_type="web_article",
            )
            total += added

        return total

    def ingest_text(self, text: str, sector: str, company: str,
                    source_url: str = "unknown", doc_type: str = "text",
                    year: Optional[int] = None) -> int:
        chunks = _chunk_text(text)
        if not chunks:
            return 0

        collection  = _get_collection(sector, self._client)
        ingested_at = datetime.utcnow().isoformat()
        ids         = []
        documents   = []
        metadatas   = []

        for idx, chunk in enumerate(chunks):
            chunk_id = _make_chunk_id(chunk, source_url, idx)
            existing = collection.get(ids=[chunk_id])
            if existing["ids"]:
                continue
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "company":     company,
                "sector":      sector,
                "source_url":  source_url,
                "doc_type":    doc_type,
                "year":        str(year) if year else "unknown",
                "chunk_index": idx,
                "ingested_at": ingested_at,
            })

        if not ids:
            print(f"ℹ️  All {len(chunks)} chunks already stored — skipping.")
            return 0

        collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"✅ [{sector}/{company}] Added {len(ids)} chunks from {source_url[:60]}")
        return len(ids)

    def collection_stats(self, sector: str) -> dict:
        collection = _get_collection(sector, self._client)
        count      = collection.count()
        sample     = collection.peek(limit=3)
        return {
            "sector":         sector,
            "total_chunks":   count,
            "sample_sources": [m.get("source_url", "?") for m in sample.get("metadatas", [])],
        }