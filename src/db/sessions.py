# src/db/sessions.py
# Supabase data-access layer for research sessions.
# All functions are async-first; sync wrappers are kept for legacy callers.

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Supabase client (lazy) ────────────────────────────────────────────────────
_supabase = None


def _get_client():
    global _supabase
    if _supabase is None:
        try:
            from supabase import create_client, Client  # type: ignore
            url  = os.getenv("SUPABASE_URL", "")
            key  = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
            if not url or not key or url.startswith("get_from"):
                raise EnvironmentError("Supabase credentials not configured")
            _supabase = create_client(url, key)
        except Exception as exc:
            raise RuntimeError(f"[DB] Cannot connect to Supabase: {exc}") from exc
    return _supabase


# ── Session CRUD ──────────────────────────────────────────────────────────────

def create_session(
    query: str,
    user_id: str,
    sector: str,
    depth: str = "standard",
) -> dict:
    """
    Insert a new session row and return the created record.
    Called by POST /query.
    """
    client = _get_client()
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    depth_map = {"quick": 5, "standard": 10, "deep": 20}
    max_steps = depth_map.get(depth, 10)

    row = {
        "id":              session_id,
        "user_id":         user_id,
        "original_query":  query,
        "sector":          sector,
        "depth":           depth,
        "status":          "awaiting_approval",
        "plan_approved":   False,
        "steps_completed": 0,
        "max_steps":       max_steps,
        "created_at":      now,
        "updated_at":      now,
    }

    resp = client.table("sessions").insert(row).execute()
    data = resp.data
    if not data:
        raise RuntimeError("[DB] Failed to create session — empty response")
    return data[0]


def get_session(session_id: str) -> Optional[dict]:
    """Return a single session dict or None."""
    try:
        client = _get_client()
        resp = (
            client.table("sessions")
            .select("*")
            .eq("id", session_id)
            .limit(1)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception as exc:
        print(f"[DB] get_session error: {exc}")
        return None


def list_sessions(user_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
    """Return a paginated list of sessions, optionally filtered by user_id."""
    try:
        client = _get_client()
        query = client.table("sessions").select("*").order("created_at", desc=True)
        if user_id:
            query = query.eq("user_id", user_id)
        resp = query.range(offset, offset + limit - 1).execute()
        return resp.data or []
    except Exception as exc:
        print(f"[DB] list_sessions error: {exc}")
        return []


def approve_session_plan(session_id: str) -> None:
    """Mark a session as approved and set status to 'researching'."""
    try:
        client = _get_client()
        client.table("sessions").update({
            "plan_approved": True,
            "status":        "researching",
            "updated_at":    datetime.now(timezone.utc).isoformat(),
        }).eq("id", session_id).execute()
    except Exception as exc:
        print(f"[DB] approve_session_plan error: {exc}")
        raise


def get_session_steps(session_id: str) -> list[dict]:
    """Return all research steps for a session, ordered by step_number."""
    try:
        client = _get_client()
        resp = (
            client.table("research_steps")
            .select("*")
            .eq("session_id", session_id)
            .order("step_number")
            .execute()
        )
        return resp.data or []
    except Exception as exc:
        print(f"[DB] get_session_steps error: {exc}")
        return []


def delete_session(session_id: str) -> None:
    """Hard-delete a session (cascades to steps via FK in Supabase)."""
    try:
        client = _get_client()
        client.table("sessions").delete().eq("id", session_id).execute()
    except Exception as exc:
        print(f"[DB] delete_session error: {exc}")
        raise


def count_sessions(user_id: Optional[str] = None) -> int:
    """Return total count of sessions (used for pagination metadata)."""
    try:
        client = _get_client()
        query = client.table("sessions").select("id", count="exact")
        if user_id:
            query = query.eq("user_id", user_id)
        resp = query.execute()
        return resp.count or 0
    except Exception as exc:
        print(f"[DB] count_sessions error: {exc}")
        return 0
