from .client import get_supabase
import uuid


def create_session(user_id: str, query: str,
                   sector: str, depth: str) -> dict:

    db = get_supabase()

    depth_to_steps = {
        "quick": 5,
        "standard": 10,
        "deep": 20
    }

    max_steps = depth_to_steps.get(depth, 10)

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "original_query": query,
        "sector": sector,
        "depth": depth,
        "status": "awaiting_approval",
        "plan_approved": False,
        "steps_completed": 0,
        "max_steps": max_steps,
    }

    result = db.table("research_sessions").insert(data).execute()

    print(f"✅ Session created: {data['id']}")

    return result.data[0]


def get_session(session_id: str):

    db = get_supabase()

    result = (
        db.table("research_sessions")
        .select("*")
        .eq("id", session_id)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def update_session_status(session_id: str, status: str):

    db = get_supabase()

    db.table("research_sessions") \
      .update({"status": status}) \
      .eq("id", session_id) \
      .execute()

    print(f"✅ Session updated to {status}")


def delete_session(session_id: str):

    db = get_supabase()

    db.table("research_sessions") \
      .delete() \
      .eq("id", session_id) \
      .execute()

    print("✅ Session deleted")