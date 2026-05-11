import os
from typing import Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_PATH       = "./data/chromadb"
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"
DEFAULT_TOP_K     = 5
MAX_CONTEXT_CHARS = 4000

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


class RAGRetriever:
    def __init__(self):
        self._client = _get_client()

    def search(self, query: str, sector: str,
               top_k: int = DEFAULT_TOP_K,
               company_filter: Optional[str] = None) -> list[dict]:
        collection = _get_collection(sector, self._client)
        if collection.count() == 0:
            return []

        where = None
        if company_filter:
            where = {"company": {"$eq": company_filter}}

        try:
            results = collection.query(
                query_texts=[query],
                n_results=min(top_k, collection.count()),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            print(f"RAG search error: {e}")
            return []

        docs      = results.get("documents",  [[]])[0]
        metas     = results.get("metadatas",  [[]])[0]
        distances = results.get("distances",  [[]])[0]

        hits = []
        for doc, meta, dist in zip(docs, metas, distances):
            hits.append({
                "text":        doc,
                "source_url":  meta.get("source_url",  "unknown"),
                "company":     meta.get("company",     "unknown"),
                "doc_type":    meta.get("doc_type",    "unknown"),
                "year":        meta.get("year",        "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "distance":    round(dist, 4),
            })

        return hits

    def get_context(self, query: str, sector: str,
                    top_k: int = DEFAULT_TOP_K,
                    company_filter: Optional[str] = None) -> str:
        hits = self.search(query, sector, top_k, company_filter)
        if not hits:
            return ""

        parts       = []
        total_chars = 0

        for i, hit in enumerate(hits, start=1):
            chunk = (
                f"[{i}] Source: {hit['source_url']} | "
                f"Company: {hit['company']} | "
                f"Type: {hit['doc_type']} | "
                f"Year: {hit['year']}\n"
                f"{hit['text']}"
            )
            total_chars += len(chunk)
            if total_chars > MAX_CONTEXT_CHARS:
                break
            parts.append(chunk)

        return "\n\n---\n\n".join(parts)

    def has_documents(self, sector: str) -> bool:
        try:
            return _get_collection(sector, self._client).count() > 0
        except Exception:
            return False
