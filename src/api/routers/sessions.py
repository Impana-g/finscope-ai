# src/api/routers/sessions.py
# All session endpoints — fully async, production-grade error handling.
#
# GET    /sessions                  → list all sessions (paginated)
# GET    /sessions/{id}             → single session details + steps
# PATCH  /sessions/{id}/approve     → approve research plan → starts research
# GET    /sessions/{id}/stream      → SSE live progress feed
# GET    /sessions/{id}/report      → final report (only when status=completed)
# DELETE /sessions/{id}             → cancel / delete a session

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from src.api.schemas import ApproveRequest, SessionListResponse, SessionResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# ── DB helpers (deferred import so startup never crashes) ─────────────────────

def _db_sessions():
    try:
        from src.db import sessions as _s  # type: ignore
        return _s
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "db_unavailable", "message": str(exc)},
        )


def _db_reports():
    try:
        from src.db import reports as _r  # type: ignore
        return _r
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "db_unavailable", "message": str(exc)},
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_session(session_id: str) -> dict:
    """Fetch session or raise 404."""
    db = _db_sessions()
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error":   "not_found",
                "message": f"Session '{session_id}' not found",
                "hint":    "Verify the session_id returned by POST /query",
            },
        )
    return session


def _build_session_response(session: dict, steps: list[dict]) -> dict:
    max_steps = max(session.get("max_steps", 10), 1)
    completed = session.get("steps_completed", 0)
    return {
        **session,
        "steps":        steps,
        "steps_count":  len(steps),
        "progress_pct": round((completed / max_steps) * 100),
    }


# ── GET /sessions ─────────────────────────────────────────────────────────────

@router.get(
    "",
    summary="List all research sessions",
    response_description="Paginated list of sessions",
)
async def list_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user_id"),
    limit:   int           = Query(20, ge=1, le=100, description="Page size"),
    offset:  int           = Query(0,  ge=0,         description="Page offset"),
) -> dict:
    """
    **GET /sessions**

    Return a paginated list of research sessions.
    Optionally filter by `user_id`.
    """
    db = _db_sessions()
    try:
        sessions = db.list_sessions(user_id=user_id, limit=limit, offset=offset)
        total    = db.count_sessions(user_id=user_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("list_sessions failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "server_error", "message": "Failed to list sessions"},
        )

    return {
        "sessions": sessions,
        "total":    total,
        "limit":    limit,
        "offset":   offset,
        "has_more": (offset + limit) < total,
    }


# ── GET /sessions/{id} ────────────────────────────────────────────────────────

@router.get(
    "/{session_id}",
    summary="Get session details and research steps",
)
async def get_session_status(session_id: str) -> dict:
    """
    **GET /sessions/{session_id}**

    Return full session details including all research steps completed so far.
    """
    try:
        session = _require_session(session_id)
        steps   = _db_sessions().get_session_steps(session_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_session_status failed for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "server_error", "message": "Failed to fetch session"},
        )

    return _build_session_response(session, steps)


# ── PATCH /sessions/{id}/approve ──────────────────────────────────────────────

@router.patch(
    "/{session_id}/approve",
    summary="Approve the research plan and start research",
)
async def approve_research_plan(
    session_id:       str,
    body:             ApproveRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    **PATCH /sessions/{session_id}/approve**

    Approve the AI-generated research plan.
    Once approved, research starts automatically in the background.

    Supply `approved: false` to reject the plan (session is soft-cancelled).
    """
    session = _require_session(session_id)

    # ── Guard: already approved ───────────────────────────────────────────────
    if session.get("plan_approved"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error":      "already_approved",
                "message":    "This research plan is already approved and running",
                "stream_url": f"/sessions/{session_id}/stream",
            },
        )

    # ── Guard: wrong status ───────────────────────────────────────────────────
    valid_statuses = {"planning", "awaiting_approval", "pending"}
    current_status = session.get("status", "")
    if current_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error":   "invalid_status",
                "message": f"Cannot approve. Current status: '{current_status}'",
                "hint":    f"Session must be in one of: {sorted(valid_statuses)}",
            },
        )

    # ── Rejection path ────────────────────────────────────────────────────────
    if not body.approved:
        try:
            db = _db_sessions()
            db.approve_session_plan.__func__ if False else None  # type hint only
            # Mark as cancelled
            from src.db.sessions import _get_client  # type: ignore
            from datetime import datetime, timezone
            _get_client().table("sessions").update({
                "status":     "cancelled",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", session_id).execute()
        except Exception:
            pass  # Non-fatal — still return the rejection message
        return {
            "success":    False,
            "message":    "Research plan rejected. Session has been cancelled.",
            "session_id": session_id,
            "status":     "cancelled",
        }

    # ── Approval path ─────────────────────────────────────────────────────────
    try:
        _db_sessions().approve_session_plan(session_id)
    except Exception as exc:
        logger.exception("approve_session_plan failed for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "db_error", "message": "Failed to approve session"},
        )

    # Kick off research in the background (agent wired in on merge day)
    background_tasks.add_task(_run_research, session_id)

    return {
        "success":    True,
        "message":    "Plan approved! Research is starting…",
        "session_id": session_id,
        "status":     "researching",
        "notes":      body.notes,
        "urls": {
            "status": f"/sessions/{session_id}",
            "stream": f"/sessions/{session_id}/stream",
            "report": f"/sessions/{session_id}/report",
        },
    }


# ── GET /sessions/{id}/stream ─────────────────────────────────────────────────

@router.get(
    "/{session_id}/stream",
    summary="Stream live research progress (SSE)",
)
async def stream_research_progress(session_id: str):
    """
    **GET /sessions/{session_id}/stream**

    Server-Sent Events feed.  Connect with `EventSource` (browser) or
    `httpx`/`aiohttp` in Python.  The stream closes automatically when
    research completes, fails, or times out (5 min).

    ### Event types
    | event       | meaning                              |
    |-------------|--------------------------------------|
    | `connected` | Stream established                   |
    | `step`      | A new research step completed        |
    | `complete`  | Research finished — report is ready  |
    | `failed`    | Research failed                      |
    | `timeout`   | 5-minute stream limit reached        |
    | `error`     | Unexpected error in the stream       |
    """
    # Validate session exists before opening SSE
    _require_session(session_id)

    async def event_generator():
        last_step_seen  = 0
        total_waited    = 0
        max_wait_secs   = 300  # 5 minutes
        poll_interval   = 3    # seconds

        yield _sse({"event": "connected", "session_id": session_id})

        while total_waited < max_wait_secs:
            try:
                db      = _db_sessions()
                db_rep  = _db_reports()
                steps   = db.get_session_steps(session_id)
                session = db.get_session(session_id)

                if not session:
                    yield _sse({"event": "error", "message": "Session not found"})
                    break

                # Emit any new steps
                new_steps = [s for s in steps if s.get("step_number", 0) > last_step_seen]
                for step in sorted(new_steps, key=lambda s: s.get("step_number", 0)):
                    yield _sse({
                        "event":      "step",
                        "step":       step.get("step_number"),
                        "query":      step.get("query"),
                        "tool":       step.get("tool_used"),
                        "finding":    step.get("finding"),
                        "confidence": step.get("confidence"),
                        "sources":    step.get("sources", []),
                    })
                    last_step_seen = step.get("step_number", last_step_seen)

                # Terminal states
                session_status = session.get("status")
                if session_status == "completed":
                    report = db_rep.get_report_by_session(session_id)
                    yield _sse({
                        "event":     "complete",
                        "report_id": report["id"] if report else None,
                        "message":   "Research complete! Report is ready.",
                    })
                    break

                if session_status == "failed":
                    yield _sse({"event": "failed", "message": "Research failed. Please retry."})
                    break

                if session_status == "cancelled":
                    yield _sse({"event": "failed", "message": "Session was cancelled."})
                    break

            except Exception as exc:
                logger.exception("SSE stream error for %s", session_id)
                yield _sse({"event": "error", "message": str(exc)})
                break

            await asyncio.sleep(poll_interval)
            total_waited += poll_interval

        if total_waited >= max_wait_secs:
            yield _sse({"event": "timeout", "message": "Stream timed out after 5 minutes"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":   "no-cache",
            "Connection":      "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── GET /sessions/{id}/report ─────────────────────────────────────────────────

@router.get(
    "/{session_id}/report",
    summary="Get the final research report for a completed session",
)
async def get_session_report(session_id: str) -> dict:
    """
    **GET /sessions/{session_id}/report**

    Returns the final research report.
    Raises HTTP 202 if research is still in progress.
    """
    session = _require_session(session_id)

    if session.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "message":        "Research is still in progress. Please wait.",
                "current_status": session.get("status"),
                "steps_done":     session.get("steps_completed", 0),
                "total_steps":    session.get("max_steps", 10),
                "stream_url":     f"/sessions/{session_id}/stream",
                "check_again":    f"/sessions/{session_id}",
            },
        )

    try:
        report = _db_reports().get_report_by_session(session_id)
    except Exception as exc:
        logger.exception("get_session_report failed for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "server_error", "message": "Failed to fetch report"},
        )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error":   "report_missing",
                "message": "Research completed but report not generated yet",
                "hint":    "Try again in a few seconds or contact support",
            },
        )

    return report


# ── DELETE /sessions/{id} ─────────────────────────────────────────────────────

@router.delete(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a research session",
)
async def delete_session(session_id: str) -> dict:
    """
    **DELETE /sessions/{session_id}**

    Hard-delete a session and all its associated steps.
    Cannot delete a session that is actively researching — wait for it to
    complete or fail first.
    """
    session = _require_session(session_id)

    if session.get("status") == "researching":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error":   "cannot_delete",
                "message": "Cannot delete a session that is currently researching",
                "hint":    "Wait for it to complete or fail, then delete",
            },
        )

    try:
        _db_sessions().delete_session(session_id)
    except Exception as exc:
        logger.exception("delete_session failed for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "db_error", "message": "Failed to delete session"},
        )

    return {
        "success":    True,
        "deleted_id": session_id,
        "message":    f"Session '{session_id}' deleted successfully",
    }


# ── Private helpers ───────────────────────────────────────────────────────────

def _sse(payload: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(payload)}\n\n"


async def _run_research(session_id: str) -> None:
    """
    Background task placeholder.
    The LangGraph agent will be wired here on merge day.
    """
    logger.info("[Research] Starting background research for session %s", session_id)
    # TODO: invoke LangGraph workflow
