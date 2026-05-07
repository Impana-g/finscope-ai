from src.db.client import supabase


def create_session(user_id, query, sector, depth):

    data = {
        "user_id": user_id,
        "original_query": query,
        "sector": sector,
        "depth": depth
    }

    print("Sending data:", data)

    response = supabase.table(
        "research_sessions"
    ).insert(data).execute()

    print("Supabase response:", response)

    return response.data[0]