# schemas.py
# These define the SHAPE of data
# What data comes IN to your API
# What data goes OUT of your API
# Pydantic checks everything automatically

from pydantic import BaseModel, field_validator
from typing import Optional, Literal, List


# ══════════════════════════════════════════════════════
# REQUEST SCHEMAS (data user sends TO your API)
# ══════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    """
    What user sends when starting research.

    Example request body:
    {
        "query": "Analyze Infosys financial performance",
        "user_id": "user123",
        "depth": "standard"
    }
    """
    query: str
    user_id: str
    depth: Literal["quick", "standard", "deep"] = "standard"

    @field_validator("query")
    @classmethod
    def check_query(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Query must be at least 10 characters long")
        if len(v) > 500:
            raise ValueError("Query must be under 500 characters")
        return v

    @field_validator("user_id")
    @classmethod
    def check_user_id(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("user_id cannot be empty")
        return v


class ApproveRequest(BaseModel):
    """
    Sent when user approves the research plan.

    Example:
    {
        "approved": true,
        "notes": "Looks good, please proceed"
    }
    """
    approved: bool = True
    notes: Optional[str] = None


# ══════════════════════════════════════════════════════
# RESPONSE SCHEMAS (data your API sends BACK to user)
# ══════════════════════════════════════════════════════

class QueryResponse(BaseModel):
    """Response after creating a new research session"""
    session_id: str
    status: str
    sector: str
    message: str
    approve_url: str
    status_url: str
    stream_url: str


class StepResponse(BaseModel):
    """One research step"""
    step_number: int
    query: str
    tool_used: str
    finding: str
    confidence: float
    sources: List[str] = []


class SessionResponse(BaseModel):
    """Full session details"""
    id: str
    status: str
    sector: str
    original_query: str
    steps_completed: int
    max_steps: int
    plan_approved: bool
    steps: Optional[List[dict]] = []
    steps_count: int = 0


class ReportResponse(BaseModel):
    """Final research report"""
    id: str
    session_id: str
    executive_summary: str
    sections: List[dict] = []
    key_metrics: Optional[dict] = {}
    investment_outlook: Optional[str] = ""
    risk_factors: Optional[List[str]] = []
    confidence_avg: Optional[float] = 0.0
    citations: Optional[List[dict]] = []
    markdown_export: Optional[str] = ""


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    recoverable: bool = True
    suggested_action: Optional[str] = None
    suggested_queries: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Health check"""
    status: str
    service: str
    version: str


# ── Test your schemas ─────────────────────────────────
if __name__ == "__main__":
    print("Testing schemas...")

    # Test valid request
    req = QueryRequest(
        query="Analyze Infosys financial performance 2025",
        user_id="user123",
        depth="standard"
    )
    print(f"✅ Valid request: {req.query[:30]}...")

    # Test short query (should fail)
    try:
        bad_req = QueryRequest(query="Hi", user_id="u1")
    except Exception as e:
        print(f"✅ Short query correctly rejected: {e}")

    print("✅ Schema tests done!")
