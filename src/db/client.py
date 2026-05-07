from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

_client: Client | None = None

def get_supabase() -> Client:
    global _client

    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"
            )

        _client = create_client(url, key)
        print("✅ Supabase connected!")

    return _client


if __name__ == "__main__":
    try:
        db = get_supabase()

        result = (
            db.table("research_sessions")
            .select("*")
            .limit(1)
            .execute()
        )

        print("✅ Database connection working!")
        print(f"Sessions in DB: {len(result.data)}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")