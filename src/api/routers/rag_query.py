from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

import anthropic
import os
from dotenv import load_dotenv

from src.rag.retriever import RAGRetriever

load_dotenv()

router    = APIRouter()
retriever = RAGRetriever()
client    = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

VALID_SECTORS = {"IT", "PHARMA"}


class RAGSearchRequest(BaseModel):
    query:          str
    sector:         str
    top_k:          Optional[int] = 5
    company_filter: Optional[str] = None


class RAGChunk(BaseModel):
    text:       str
    source_url: str
    company:    str
    doc_type:   str
    year:       str
    distance:   float


class RAGSearchResponse(BaseModel):
    query:   str
    sector:  str
    results: list[RAGChunk]
    total:   int


class RAGAnswerRequest(BaseModel):
    question:       str
    sector:         str
    company_filter: Optional[str] = None
    top_k:          Optional[int] = 6


class RAGAnswerResponse(BaseModel):
    question: str
    answer:   str
    sources:  list[str]
    rag_used: bool


def _validate_sector(sector: str) -> str:
    s = sector.upper()
    if s not in VALID_SECTORS:
        raise HTTPException(422, f"sector must be one of {VALID_SECTORS}")
    return s


@router.post("/search", response_model=RAGSearchResponse)
async def rag_search(req: RAGSearchRequest):
    sector = _validate_sector(req.sector)
    hits   = retriever.search(
        query=req.query, sector=sector,
        top_k=req.top_k or 5,
        company_filter=req.company_filter,
    )
    return RAGSearchResponse(
        query=req.query, sector=sector,
        results=[RAGChunk(**h) for h in hits],
        total=len(hits),
    )


@router.post("/answer", response_model=RAGAnswerResponse)
async def rag_answer(req: RAGAnswerRequest):
    sector  = _validate_sector(req.sector)
    context = retriever.get_context(
        query=req.question, sector=sector,
        top_k=req.top_k or 6,
        company_filter=req.company_filter,
    )
    rag_used = bool(context)

    if rag_used:
        prompt = f"""You are a senior financial analyst.
Answer the question using ONLY the document context below.
Be specific — cite figures, dates, and company names from the documents.
If the documents don't contain enough information, say so clearly.

DOCUMENT CONTEXT:
{context}

QUESTION: {req.question}"""
    else:
        prompt = f"""You are a senior financial analyst.
Answer the following question about {sector} sector companies.
No stored documents available — answer from general knowledge and note this clearly.

QUESTION: {req.question}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.content[0].text.strip()
    except Exception as e:
        raise HTTPException(500, f"LLM error: {e}")

    hits    = retriever.search(req.question, sector, req.top_k or 6, req.company_filter)
    sources = list({h["source_url"] for h in hits if h["source_url"] != "unknown"})

    return RAGAnswerResponse(
        question=req.question, answer=answer,
        sources=sources, rag_used=rag_used,
    )