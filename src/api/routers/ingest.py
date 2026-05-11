import os
import shutil
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.rag.ingestion import RAGIngestion

router   = APIRouter()
ingestor = RAGIngestion()

VALID_SECTORS = {"IT", "PHARMA"}


class TextIngestRequest(BaseModel):
    text:       str
    sector:     str
    company:    str
    source_url: Optional[str] = "unknown"
    doc_type:   Optional[str] = "text"
    year:       Optional[int] = None


class IngestResponse(BaseModel):
    chunks_added: int
    sector:       str
    company:      str
    message:      str


class StatsResponse(BaseModel):
    sector:         str
    total_chunks:   int
    sample_sources: list


def _validate_sector(sector: str) -> str:
    s = sector.upper()
    if s not in VALID_SECTORS:
        raise HTTPException(422, f"sector must be one of {VALID_SECTORS}")
    return s


@router.post("/pdf", response_model=IngestResponse)
async def ingest_pdf(
    file:     UploadFile    = File(...),
    sector:   str           = Form(...),
    company:  str           = Form(...),
    doc_type: str           = Form("annual_report"),
    year:     Optional[int] = Form(None),
):
    sector = _validate_sector(sector)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    tmp_dir  = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)

    try:
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        chunks = ingestor.ingest_pdf(
            pdf_path=tmp_path, sector=sector,
            company=company, doc_type=doc_type, year=year,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return IngestResponse(
        chunks_added=chunks, sector=sector, company=company,
        message=f"Ingested {chunks} chunks from '{file.filename}'.",
    )


@router.post("/text", response_model=IngestResponse)
async def ingest_text(req: TextIngestRequest):
    sector = _validate_sector(req.sector)
    if not req.text.strip():
        raise HTTPException(400, "text field cannot be empty.")

    chunks = ingestor.ingest_text(
        text=req.text, sector=sector, company=req.company,
        source_url=req.source_url or "unknown",
        doc_type=req.doc_type or "text", year=req.year,
    )

    return IngestResponse(
        chunks_added=chunks, sector=sector, company=req.company,
        message=f"Ingested {chunks} new chunks.",
    )


@router.get("/stats/{sector}", response_model=StatsResponse)
async def collection_stats(sector: str):
    sector = _validate_sector(sector)
    stats  = ingestor.collection_stats(sector)
    return StatsResponse(**stats)