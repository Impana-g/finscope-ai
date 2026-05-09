from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from src.db.sessions import (
    get_session, approve_session_plan,
    get_session_steps, get_all_sessions,
    delete_session
)
from src.db.reports import get_report_by_session
from src.agents.graph import research_graph
import asyncio
import json

router = APIRouter()

@router.get("/")
def list_sessions(user_id: str):
    sessions = get_all_sessions(user_id)
    return {"sessions": sessions, "total": len(sessions)}

@router.get("/{session_id}")
def get_session_status(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
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
async def approve_plan(session_id: str, background_tasks: BackgroundTasks):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("plan_approved"):
        raise HTTPException(status_code=400, detail="Already approved!")

    approve_session_plan(session_id)
    background_tasks.add_task(run_research, session_id, session)

    return {
        "session_id": session_id,
        "status": "researching",
        "message": "Plan approved! Research starting...",
        "urls": {
            "status": f"/sessions/{session_id}",
            "stream": f"/sessions/{session_id}/stream",
            "report": f"/sessions/{session_id}/report"
        }
    }

@router.post("/{session_id}/run")
async def run_research_endpoint(session_id: str, background_tasks: BackgroundTasks):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.get("plan_approved"):
        raise HTTPException(status_code=400, detail="Approve the plan first!")

    background_tasks.add_task(run_research, session_id, session)
    return {
        "message": "Research started!",
        "session_id": session_id,
        "check_progress": f"/sessions/{session_id}",
        "stream": f"/sessions/{session_id}/stream"
    }

@router.get("/{session_id}/report")
def get_session_report(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") != "completed":
        raise HTTPException(
            status_code=202,
            detail={
                "message": "Research still in progress",
                "status": session.get("status"),
                "steps_done": session.get("steps_completed", 0),
                "total_steps": session.get("max_steps", 10)
            }
        )
    report = get_report_by_session(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/{session_id}/stream")
async def stream_progress(session_id: str):
    async def event_generator():
        last_step = 0
        total_waited = 0
        yield f"data: {json.dumps({'event': 'connected', 'session_id': session_id})}\n\n"

        while total_waited < 300:
            steps = get_session_steps(session_id)
            session = get_session(session_id)
            if not session:
                break

            new_steps = [s for s in steps if s.get("step_number", 0) > last_step]
            for step in new_steps:
                yield f"data: {json.dumps({'event': 'step', 'step': step.get('step_number'), 'finding': step.get('finding'), 'confidence': step.get('confidence')})}\n\n"
                last_step = step.get("step_number", last_step)

            if session.get("status") == "completed":
                report = get_report_by_session(session_id)
                yield f"data: {json.dumps({'event': 'complete', 'report_id': report['id'] if report else None})}\n\n"
                break

            if session.get("status") == "failed":
                yield f"data: {json.dumps({'event': 'failed'})}\n\n"
                break

            await asyncio.sleep(3)
            total_waited += 3

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@router.delete("/{session_id}")
def cancel_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") == "researching":
        raise HTTPException(status_code=400, detail="Cannot delete while researching")
    delete_session(session_id)
    return {"message": f"Session {session_id} deleted successfully"}

# ── Background research runner ─────────────────────────
async def run_research(session_id: str, session: dict):
    try:
        state = {
            "session_id": session_id,
            "original_query": session["original_query"],
            "sector": session["sector"],
            "depth": session["depth"],
            "research_plan": None,
            "plan_approved": True,
            "steps_completed": 0,
            "max_steps": {"quick":5,"standard":10,"deep":20}.get(session["depth"], 10),
            "findings": [],
            "sources": [],
            "all_complete": False,
            "report": None,
            "error": None
        }
        research_graph.invoke(state)
        print(f"✅ Research completed for session {session_id}")
    except Exception as e:
        print(f"❌ Research failed: {e}")