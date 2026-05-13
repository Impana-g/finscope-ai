# src/api/routers/query.py
# POST /query  →  Start a new research session
#
# Flow:
#   1. Validate QueryRequest (Pydantic)
#   2. Detect financial sector from query keywords
#   3. Insert session row into Supabase via db.sessions
#   4. Return session_id + URLs for approve / stream / status

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, status

from src.api.schemas import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Sector detection ──────────────────────────────────────────────────────────

_IT_KEYWORDS = {
    "infosys", "tcs", "wipro", "hcl", "tech mahindra", "ltimindtree",
    "mphasis", "hexaware", "persistent", "coforge", "software", "it sector",
    "information technology", "saas", "cloud", "digital transformation",
}

_PHARMA_KEYWORDS = {
    "sun pharma", "dr reddy", "cipla", "lupin", "aurobindo", "biocon",
    "alkem", "ipca", "glenmark", "torrent pharma", "pharma", "pharmaceutical",
    "drug", "api", "formulation", "ncb", "clinical", "healthcare",
}


def _detect_sector(query: str) -> Literal["IT", "PHARMA", "GENERAL"]:
    """Best-effort sector detection from query text (case-insensitive)."""
    q = query.lower()
    it_score    = sum(1 for kw in _IT_KEYWORDS    if kw in q)
    pharma_score = sum(1 for kw in _PHARMA_KEYWORDS if kw in q)

    if it_score == 0 and pharma_score == 0:
        return "GENERAL"
    return "IT" if it_score >= pharma_score else "PHARMA"


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new financial research session",
    response_description="Session created — use approve_url to kick off research",
)
async def create_research_session(body: QueryRequest) -> QueryResponse:
    """
    **POST /query**

    Create a new AI research session for the given financial query.

    - Detects sector automatically (IT / PHARMA / GENERAL)
    - Returns `session_id` and URLs for approving, streaming, and fetching status
    - Research does **not** start until the plan is approved via `PATCH /sessions/{id}/approve`

    ### Request body
    ```json
    {
      "query":   "Analyse Infosys revenue trends 2023–2025",
      "user_id": "user_abc",
      "depth":   "standard"
    }
    ```
    """
    try:
        from src.db.sessions import create_session  # deferred to avoid startup crash
    except RuntimeError as exc:
        logger.error("DB unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error":   "db_unavailable",
                "message": "Database is not reachable. Check SUPABASE_* environment variables.",
            },
        )

    sector = _detect_sector(body.query)

    try:
        session = create_session(
            query=body.query,
            user_id=body.user_id,
            sector=sector,
            depth=body.depth,
        )
    except RuntimeError as exc:
        logger.exception("create_session failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "db_error", "message": str(exc)},
        )
    except Exception as exc:
        logger.exception("Unexpected error in create_research_session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "server_error", "message": "Failed to create research session"},
        )

    sid = session["id"]

    return QueryResponse(
        session_id=sid,
        status="awaiting_approval",
        sector=sector,
        message=(
            f"Research session created for sector '{sector}'. "
            "Review the plan and approve to begin."
        ),
        approve_url=f"/sessions/{sid}/approve",
        status_url=f"/sessions/{sid}",
        stream_url=f"/sessions/{sid}/stream",
    )
