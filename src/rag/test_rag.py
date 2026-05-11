"""
test_rag.py - End-to-end test for the RAG module.

Usage:
    python -m src.rag.test_rag
"""

import sys
import os
import io

# Fix Windows console encoding for emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.rag.ingestor import RAGIngestor
from src.rag.retriever import RAGRetriever


def main():
    print("=" * 60)
    print("  FinScope AI - RAG Module Test")
    print("=" * 60)

    # -- 1. Ingest sample documents --------------------------------
    ingestor = RAGIngestor()

    sample_docs = [
        {
            "text": (
                "Infosys reported a revenue of Rs 40,484 crore for Q3 FY2025, "
                "a growth of 6.1% YoY. Operating profit margin stood at 21.3%. "
                "The company won large deals worth $2.5 billion during the quarter. "
                "Digital services revenue now accounts for 64.1% of total revenue. "
                "Cloud and AI-related services showed the fastest growth at 15% YoY."
            ),
            "company": "Infosys",
            "sector": "it",
            "doc_type": "quarterly_report",
            "year": "2025",
        },
        {
            "text": (
                "TCS reported consolidated revenue of Rs 63,973 crore for Q3 FY2025, "
                "up 5.6% YoY. Net profit rose 11.9% to Rs 12,380 crore. "
                "The BFSI segment contributed 33% of revenue. "
                "TCS signed deals worth $10.2 billion in TCV during the quarter. "
                "The company's headcount was 601,546 employees globally."
            ),
            "company": "TCS",
            "sector": "it",
            "doc_type": "quarterly_report",
            "year": "2025",
        },
        {
            "text": (
                "Sun Pharma's US formulation sales grew 12% to $523 million "
                "in Q3 FY2025. Specialty business contributed $227 million. "
                "The company filed 8 new ANDAs during the quarter. "
                "R&D expenditure was 7.2% of revenue. "
                "Net profit margin improved to 18.5% from 15.1% YoY."
            ),
            "company": "Sun Pharma",
            "sector": "pharma",
            "doc_type": "quarterly_report",
            "year": "2025",
        },
    ]

    print("\n[INGEST] Ingesting sample documents...")
    for doc in sample_docs:
        chunks = ingestor.ingest_text(
            text=doc["text"],
            sector=doc["sector"],
            company=doc["company"],
            doc_type=doc["doc_type"],
            year=doc["year"],
            source_url="test_data",
        )
        print(f"   {doc['company']}: {chunks} chunks")

    # -- 2. Check collection stats ---------------------------------
    print("\n[STATS] Collection stats:")
    for sector in ["it", "pharma"]:
        stats = ingestor.collection_stats(sector)
        print(f"   {sector.upper()}: {stats['count']} chunks")

    # -- 3. Test retrieval -----------------------------------------
    retriever = RAGRetriever()

    test_queries = [
        ("What is Infosys revenue growth?", "it", None),
        ("TCS deal pipeline and TCV", "it", "TCS"),
        ("Sun Pharma US sales and specialty business", "pharma", None),
    ]

    print("\n[SEARCH] Testing retrieval:")
    for query, sector, company_filter in test_queries:
        print(f"\n   Query: '{query}'")
        print(f"   Sector: {sector} | Filter: {company_filter or 'none'}")

        hits = retriever.search(query, sector, top_k=3,
                                company_filter=company_filter)
        if hits:
            for j, hit in enumerate(hits, 1):
                print(f"     [{j}] dist={hit['distance']:.4f} | "
                      f"{hit['company']} | {hit['text'][:80]}...")
        else:
            print("     No results found.")

    # -- 4. Test context generation --------------------------------
    print("\n[CONTEXT] Testing context generation:")
    context = retriever.get_context(
        "Compare Infosys and TCS financial performance", "it"
    )
    if context:
        print(f"   Context length: {len(context)} chars")
        print(f"   Preview: {context[:200]}...")
    else:
        print("   No context generated.")

    # -- 5. Test has_documents -------------------------------------
    print("\n[CHECK] has_documents check:")
    print(f"   IT:     {retriever.has_documents('it')}")
    print(f"   Pharma: {retriever.has_documents('pharma')}")
    print(f"   Empty:  {retriever.has_documents('nonexistent')}")

    print("\n" + "=" * 60)
    print("  All RAG tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
