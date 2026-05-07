from src.db.client import supabase


def save_research_plan(session_id, plan):

    data = {
        "session_id": session_id,
        "dimensions": plan["dimensions"],
        "planned_steps": plan["planned_steps"],
        "sources_to_use": plan["sources_to_use"],
        "estimated_depth": plan["estimated_depth"]
    }

    response = supabase.table(
        "research_plans"
    ).insert(data).execute()

    return response.data[0]