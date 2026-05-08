from src.db.client import get_supabase
import uuid


def create_session(user_id: str, query: str, sector: str, depth: str) -> dict:
    db = get_supabase()
    depth_steps = {"quick": 5, "standard": 10, "deep": 20}
    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "original_query": query,
        "sector": sector,
        "depth": depth,
        "status": "awaiting_approval",
        "plan_approved": False,
        "steps_completed": 0,
        "max_steps": depth_steps.get(depth, 10),
    }
    result = db.table("research_sessions").insert(data).execute()
    print(f"✅ Session created: {data['id'][:8]}")
    return result.data[0]


def get_session(session_id: str) -> dict | None:
    db = get_supabase()
    result = db.table("research_sessions").select("*").eq(
        "id", session_id
    ).execute()
    return result.data[0] if result.data else None


def get_all_sessions(user_id: str) -> list:
    db = get_supabase()
    result = db.table("research_sessions").select("*").eq(
        "user_id", user_id
    ).order("created_at", desc=True).execute()
    return result.data


def update_session_status(session_id: str, status: str):
    db = get_supabase()
    db.table("research_sessions").update(
        {"status": status}
    ).eq("id", session_id).execute()
    print(f"✅ Status updated → {status}")


def approve_session_plan(session_id: str):
    db = get_supabase()
    db.table("research_sessions").update({
        "plan_approved": True,
        "status": "researching"
    }).eq("id", session_id).execute()


def increment_steps(session_id: str, steps_completed: int):
    db = get_supabase()
    db.table("research_sessions").update({
        "steps_completed": steps_completed
    }).eq("id", session_id).execute()


def delete_session(session_id: str):
    db = get_supabase()
    db.table("research_sessions").delete().eq(
        "id", session_id
    ).execute()


def save_research_plan(session_id: str, plan: dict) -> dict:
    db = get_supabase()
    data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "dimensions": plan.get("dimensions", []),
        "planned_steps": plan.get("planned_steps", []),
        "sources_to_use": plan.get("sources_to_use", ["web", "yfinance"]),
        "estimated_depth": plan.get("estimated_depth", "standard"),
    }
    result = db.table("research_plans").insert(data).execute()
    return result.data[0]


def save_research_step(session_id: str, step_num: int, query: str,
                       tool: str, finding: str, confidence: float,
                       raw_data: dict, sources: list) -> dict:
    db = get_supabase()
    data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "step_number": step_num,
        "query": query,
        "tool_used": tool,
        "finding": finding,
        "raw_data": raw_data,
        "sources": sources,
        "confidence": confidence,
    }
    result = db.table("research_steps").insert(data).execute()
    return result.data[0]


def get_session_steps(session_id: str) -> list:
    db = get_supabase()
    result = db.table("research_steps").select("*").eq(
        "session_id", session_id
    ).order("step_number").execute()
    return result.data


if __name__ == "__main__":
    print("Testing sessions...")

    # Create test session
    session = create_session(
        user_id="test_user",
        query="Analyze Infosys financial performance",
        sector="IT",
        depth="standard"
    )
    print(f"Session ID: {session['id']}")

    # Get it back
    fetched = get_session(session["id"])
    print(f"Fetched query: {fetched['original_query']}")

    # Update status
    update_session_status(session["id"], "completed")

    # Delete test data
    delete_session(session["id"])
    print("✅ Deleted test session")
    print("✅ All sessions tests passed!")