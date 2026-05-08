# sessions.py router
# Handles everything about sessions
# GET    /sessions/{id}          → get session status
# PATCH  /sessions/{id}/approve  → approve research plan
# GET    /sessions/{id}/report   → get final report
# GET    /sessions/{id}/stream   → live updates

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter()


# ── Import Skandan's DB functions ─────────────────────
# Stubs used until Skandan's code is ready
try:
    from src.db.sessions import (  # type: ignore
        get_session,
        approve_session_plan,
        get_session_steps,
        delete_session
    )
    from src.db.reports import get_report_by_session  # type: ignore
except ImportError:
    print("⚠️  Skandan's db code not ready — using stubs")

    def get_session(sid):
        return None

    def approve_session_plan(sid):
        pass

    def get_session_steps(sid):
        return []

    def delete_session(sid):
        pass

    def get_report_by_session(sid):
        return None


# ── Endpoints ─────────────────────────────────────────

@router.get("/{session_id}")
def get_session_status(session_id: str):
    """
    Get full details of a research session.
    Shows status, steps completed, and all research steps.

    Example: GET /sessions/abc-123
    """
    session = get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": f"Session '{session_id}' not found",
                "hint": "Double check your session_id"
            }
        )

    # Get all research steps for this session
    steps = get_session_steps(session_id)

    return {
        **session,
        "steps": steps,
        "steps_count": len(steps),
        "progress_pct": round(
            (session.get("steps_completed", 0) /
             max(session.get("max_steps", 10), 1)) * 100
        )
    }


@router.patch("/{session_id}/approve")
async def approve_research_plan(
    session_id: str,
    background_tasks: BackgroundTasks
):
    """
    User approves the AI research plan.
    Research starts automatically after approval.

    Example: PATCH /sessions/abc-123/approve
    """
    # Check session exists
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Session not found"}
        )

    # Check not already approved
    if session.get("plan_approved"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "already_approved",
                "message": "This research plan is already approved and running",
                "stream_url": f"/sessions/{session_id}/stream"
            }
        )

    # Check status is correct
    valid_statuses = ["planning", "awaiting_approval", "pending"]
    if session.get("status") not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_status",
                "message": f"Cannot approve. Current status: {session.get('status')}",
                "hint": "Session must be in awaiting_approval status"
            }
        )

    # Approve in database
    approve_session_plan(session_id)

    # Start research in background
    # (Skandan's AI agent will be added here on merge day)
    background_tasks.add_task(
        run_research_placeholder,
        session_id
    )

    return {
        "success": True,
        "message": "Plan approved! Research is now starting...",
        "session_id": session_id,
        "status": "researching",
        "urls": {
            "status": f"/sessions/{session_id}",
            "stream": f"/sessions/{session_id}/stream",
            "report": f"/sessions/{session_id}/report"
        }
    }


@router.get("/{session_id}/report")
def get_session_report(session_id: str):
    """
    Get the completed research report.
    Only works after research is complete.

    Example: GET /sessions/abc-123/report
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Session not found"}
        )

    # Check if research is done
    if session.get("status") != "completed":
        raise HTTPException(
            status_code=202,
            detail={
                "message": "Research is still in progress. Please wait.",
                "current_status": session.get("status"),
                "steps_done": session.get("steps_completed", 0),
                "total_steps": session.get("max_steps", 10),
                "check_again": f"/sessions/{session_id}"
            }
        )

    # Get the report
    report = get_report_by_session(session_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "report_missing",
                "message": "Research completed but report not found",
                "hint": "Please contact support"
            }
        )

    return report


@router.get("/{session_id}/stream")
async def stream_research_progress(session_id: str):
    """
    Live stream of research steps as they complete.
    Uses SSE (Server-Sent Events).
    Connect using EventSource in browser or httpx in Python.

    Example: GET /sessions/abc-123/stream
    """
    async def event_generator():
        last_step_seen = 0
        total_waited = 0
        max_wait_seconds = 300  # 5 minutes max

        # Send connected message
        yield f"data: {json.dumps({'event': 'connected', 'session_id': session_id})}\n\n"

        while total_waited < max_wait_seconds:
            try:
                # Get latest steps
                steps = get_session_steps(session_id)
                session = get_session(session_id)

                if not session:
                    yield f"data: {json.dumps({'event': 'error', 'message': 'Session not found'})}\n\n"
                    break

                # Send any new steps
                new_steps = [
                    s for s in steps
                    if s.get("step_number", 0) > last_step_seen
                ]

                for step in new_steps:
                    step_data = {
                        "event": "step",
                        "step": step.get("step_number"),
                        "query": step.get("query"),
                        "tool": step.get("tool_used"),
                        "finding": step.get("finding"),
                        "confidence": step.get("confidence"),
                        "sources": step.get("sources", [])
                    }
                    yield f"data: {json.dumps(step_data)}\n\n"
                    last_step_seen = step.get("step_number", last_step_seen)

                # Check if completed
                if session.get("status") == "completed":
                    report = get_report_by_session(session_id)
                    yield f"data: {json.dumps({'event': 'complete', 'report_id': report['id'] if report else None, 'message': 'Research complete!'})}\n\n"
                    break

                # Check if failed
                if session.get("status") == "failed":
                    yield f"data: {json.dumps({'event': 'failed', 'message': 'Research failed. Please try again.'})}\n\n"
                    break

                # Wait before checking again
                await asyncio.sleep(3)
                total_waited += 3

            except Exception as e:
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
                break

        # Timeout message
        if total_waited >= max_wait_seconds:
            yield f"data: {json.dumps({'event': 'timeout', 'message': 'Stream timed out after 5 minutes'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.delete("/{session_id}")
def cancel_session(session_id: str):
    """
    Cancel and delete a research session.

    Example: DELETE /sessions/abc-123
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Session not found"}
        )

    if session.get("status") == "researching":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "cannot_delete",
                "message": "Cannot delete a session that is currently researching",
                "hint": "Wait for it to complete or fail first"
            }
        )

    delete_session(session_id)
    return {
        "success": True,
        "message": f"Session {session_id} deleted successfully"
    }


# ── Placeholder for AI research ───────────────────────
async def run_research_placeholder(session_id: str):
    """
    PLACEHOLDER — Skandan's AI agent goes here on merge day.
    For now just prints a message.
    """
    print(f"🔬 Research started for session: {session_id}")
    print("   (AI agent will be connected on merge day)")
# src/api/routers/sessions.py

from fastapi import APIRouter, HTTPException
from src.db.sessions import (
    get_session, update_session_status,
    approve_session_plan, get_session_steps,
    get_all_sessions, delete_session
)

router = APIRouter()

@router.get("/{session_id}")
def get_session_status(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    steps = get_session_steps(session_id)
    return {
        "session": session,
        "steps": steps,
        "steps_completed": len(steps)
    }

@router.patch("/{session_id}/approve")
def approve_plan(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    approve_session_plan(session_id)
    return {
        "session_id": session_id,
        "status": "researching",
        "message": "Plan approved — research will begin"
    }

@router.get("/")
def list_sessions(user_id: str):
    sessions = get_all_sessions(user_id)
    return {"sessions": sessions, "total": len(sessions)}

@router.delete("/{session_id}")
def cancel_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    delete_session(session_id)
    return {"message": "Session deleted"}