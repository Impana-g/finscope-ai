# src/db/reports.py
# Supabase data-access layer for research reports.

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Supabase client (lazy, shared via sessions module) ────────────────────────
_supabase = None


def _get_client():
    global _supabase
    if _supabase is None:
        try:
            from supabase import create_client  # type: ignore
            url = os.getenv("SUPABASE_URL", "")
            key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
            if not url or not key or url.startswith("get_from"):
                raise EnvironmentError("Supabase credentials not configured")
            _supabase = create_client(url, key)
        except Exception as exc:
            raise RuntimeError(f"[DB] Cannot connect to Supabase: {exc}") from exc
    return _supabase


# ── Report CRUD ───────────────────────────────────────────────────────────────

def get_report_by_id(report_id: str) -> Optional[dict]:
    """Return a single report dict by its primary-key ID."""
    try:
        client = _get_client()
        resp = (
            client.table("reports")
            .select("*")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception as exc:
        print(f"[DB] get_report_by_id error: {exc}")
        return None


def get_report_by_session(session_id: str) -> Optional[dict]:
    """Return the report linked to a given session_id."""
    try:
        client = _get_client()
        resp = (
            client.table("reports")
            .select("*")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception as exc:
        print(f"[DB] get_report_by_session error: {exc}")
        return None
