from typing import Optional, Dict, Any
from src.db.client import get_supabase
import uuid


def save_report(session_id: str, report: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a completed report. Called by reporter.py after research completes."""
    db = get_supabase()
    if "id" not in report:
        report["id"] = str(uuid.uuid4())
    report["session_id"] = session_id
    result = db.table("research_reports").insert(report).execute()
    db.table("research_sessions").update(
        {"report_id": report["id"]}
    ).eq("id", session_id).execute()
    return result.data[0]


def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    """Used by GET /reports/{report_id}"""
    db = get_supabase()
    result = (
        db.table("research_reports")
        .select("*")
        .eq("id", report_id)
        .execute()
    )
    return result.data[0] if result.data else None


def get_report_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Used by GET /sessions/{id}/report and SSE stream."""
    db = get_supabase()
    result = (
        db.table("research_reports")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def delete_report_by_session(session_id: str) -> bool:
    """Called when a session is deleted."""
    db = get_supabase()
    result = (
        db.table("research_reports")
        .delete()
        .eq("session_id", session_id)
        .execute()
    )
    return bool(result.data)