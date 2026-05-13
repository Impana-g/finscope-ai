from typing import Optional, Dict, Any, List
from src.db.client import get_supabase
import uuid


# ── Create ────────────────────────────────────────────────────────────

def create_session(user_id: str, query: str, sector: str, depth: str) -> Dict[str, Any]:
    """Called by POST /query/"""
    db = get_supabase()
    session = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "original_query": query,
        "sector": sector,
        "depth": depth,
        "status": "pending",
        "plan_approved": False,
        "steps_completed": 0,
        "max_steps": {"quick": 5, "standard": 10, "deep": 20}.get(depth, 10),
        "error": None,
    }
    result = db.table("research_sessions").insert(session).execute()
    return result.data[0]


# ── Read ──────────────────────────────────────────────────────────────

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    result = db.table("research_sessions").select("*").eq("id", session_id).execute()
    return result.data[0] if result.data else None


def get_all_sessions(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_supabase()
    query = db.table("research_sessions").select("*").order("created_at", desc=True)
    if user_id:
        query = query.eq("user_id", user_id)
    result = query.execute()
    return result.data or []


def get_session_steps(session_id: str) -> List[Dict[str, Any]]:
    db = get_supabase()
    result = (
        db.table("research_steps")
        .select("*")
        .eq("session_id", session_id)
        .order("step_number")
        .execute()
    )
    return result.data or []


# ── Update ────────────────────────────────────────────────────────────

def update_session(session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    result = (
        db.table("research_sessions")
        .update(updates)
        .eq("id", session_id)
        .execute()
    )
    return result.data[0] if result.data else None


def update_session_status(session_id: str, status: str) -> None:
    """Called by query.py after plan generation."""
    update_session(session_id, {"status": status})


def approve_session_plan(session_id: str) -> None:
    """Called by PATCH /sessions/{id}/approve"""
    update_session(session_id, {"plan_approved": True, "status": "awaiting_approval"})


def save_research_plan(session_id: str, plan: dict) -> None:
    """Called by query.py after Claude generates the research plan."""
    update_session(session_id, {"research_plan": plan})


# ── Steps ─────────────────────────────────────────────────────────────

def save_research_step(
    session_id: str,
    step_number: int,
    query: str,
    tool: str,
    finding: str,
    confidence: float,
    raw_data: dict,
    sources: list,
) -> None:
    """Called by researcher.py after each research step completes."""
    db = get_supabase()
    db.table("research_steps").insert({
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "step_number": step_number,
        "query": query,
        "tool": tool,
        "finding": finding,
        "confidence": confidence,
        "raw_data": raw_data,
        "sources": sources,
    }).execute()


def increment_steps(session_id: str, step_number: int) -> None:
    """Called by researcher.py to keep steps_completed in sync."""
    update_session(session_id, {"steps_completed": step_number})


def add_step(session_id: str, step: Dict[str, Any]) -> None:
    """Generic step insert (used by sessions router)."""
    db = get_supabase()
    db.table("research_steps").insert({
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        **step,
    }).execute()


# ── Delete ────────────────────────────────────────────────────────────

def delete_session(session_id: str) -> bool:
    db = get_supabase()
    db.table("research_steps").delete().eq("session_id", session_id).execute()
    result = db.table("research_sessions").delete().eq("id", session_id).execute()
    return bool(result.data)