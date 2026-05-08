# src/api/routers/query.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from src.db.client import get_supabase
from src.db.sessions import create_session, update_session_status, save_research_plan
import uuid

router = APIRouter()

# ── Request / Response schemas ─────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    user_id: str
    depth: Optional[str] = "standard"  # quick | standard | deep

class QueryResponse(BaseModel):
    session_id: str
    status: str
    sector: str
    plan: dict
    approve_url: str

# ── Out-of-scope helper ────────────────────────────────────────────────────

OUT_OF_SCOPE_SUGGESTIONS = [
    "Analyze Infosys AI strategy",
    "Research Sun Pharma pipeline",
    "Compare Indian IT sector trends",
]

def _is_financial_query(query: str) -> bool:
    """Quick keyword check before calling Claude."""
    it_keywords = {"tcs", "infosys", "wipro", "hcl", "tech mahindra", "software",
                   "cloud", "saas", "it ", "technology"}
    pharma_keywords = {"pharma", "drug", "clinical", "fda", "sun pharma",
                       "cipla", "dr reddy", "biocon", "pipeline", "biosimilar"}
    q = query.lower()
    return any(k in q for k in it_keywords | pharma_keywords)

# ── Route classification via Claude ───────────────────────────────────────

async def _classify_query(query: str) -> dict:
    """Call Claude to classify sector and return {sector, confidence, reason}."""
    import anthropic, json, os
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""You are a financial research query classifier.
Classify the query into: IT, PHARMA, or UNKNOWN.

IT: TCS, Infosys, Wipro, HCL, software, cloud, SaaS, tech services.
PHARMA: drugs, clinical trials, FDA, Sun Pharma, Cipla, Dr Reddy's, biosimilar.
UNKNOWN: anything not related to IT or Pharma financial analysis.

Respond in JSON only:
{{"sector": "IT", "confidence": 0.95, "reason": "Query mentions Infosys"}}

Query: {query}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if Claude wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ── Research plan generation via Claude ───────────────────────────────────

async def _generate_plan(query: str, sector: str, depth: str) -> dict:
    """Ask Claude to produce a structured research plan."""
    import anthropic, json, os
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    depth_steps = {"quick": 5, "standard": 10, "deep": 20}
    max_steps = depth_steps.get(depth, 10)

    prompt = f"""You are a senior financial analyst. Create a research plan.
Output JSON only:
{{
  "dimensions": ["..."],
  "planned_steps": ["..."],
  "sources_to_use": ["web", "yfinance"],
  "estimated_depth": "{depth}"
}}

Rules:
- {max_steps} planned_steps maximum
- For IT: cover financials, AI strategy, competitive position, deal pipeline, risks
- For Pharma: cover drug pipeline, R&D spend, regulatory status, patent cliff, risks

Query: {query}
Sector: {sector}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ── Main endpoint ──────────────────────────────────────────────────────────

@router.post("/", response_model=QueryResponse, status_code=202)
async def start_research(request: QueryRequest):
    """
    POST /query

    1. Validate query
    2. Classify sector via Claude
    3. Reject out-of-scope queries
    4. Create session in Supabase
    5. Generate research plan via Claude
    6. Save plan to Supabase
    7. Return session_id + plan
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if len(query) > 1000:
        raise HTTPException(status_code=400, detail="Query too long (max 1000 chars).")

    # ── Step 1: Classify ──────────────────────────────────────────────────
    try:
        classification = await _classify_query(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")

    sector = classification.get("sector", "UNKNOWN")
    confidence = classification.get("confidence", 0.5)

    # ── Step 2: Reject out-of-scope ───────────────────────────────────────
    if sector == "UNKNOWN":
        raise HTTPException(
            status_code=422,
            detail={
                "error": "out_of_scope",
                "message": (
                    "FinScope AI specialises in IT and Pharma sector financial analysis. "
                    "Your query appears to be outside this scope."
                ),
                "suggested_queries": OUT_OF_SCOPE_SUGGESTIONS,
            }
        )

    # ── Step 3: Create session ────────────────────────────────────────────
    try:
        session = create_session(
            user_id=request.user_id,
            query=query,
            sector=sector,
            depth=request.depth,
        )
        session_id = session["id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {e}")

    # ── Step 4: Generate + save plan ──────────────────────────────────────
    try:
        plan = await _generate_plan(query, sector, request.depth)
        save_research_plan(session_id, plan)
        update_session_status(session_id, "awaiting_approval")
    except Exception as e:
        update_session_status(session_id, "failed")
        raise HTTPException(status_code=500, detail=f"Planning failed: {e}")

    return QueryResponse(
        session_id=session_id,
        status="awaiting_approval",
        sector=sector,
        plan={**plan, "confidence": confidence},
        approve_url=f"/sessions/{session_id}/approve",
    )