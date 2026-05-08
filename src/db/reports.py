from src.db.client import get_supabase
import uuid


def save_report(session_id: str, report: dict) -> dict:
    db = get_supabase()
    data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "executive_summary": report.get("executive_summary", ""),
        "sections": report.get("sections", []),
        "key_metrics": report.get("key_metrics", {}),
        "investment_outlook": report.get("investment_outlook", ""),
        "risk_factors": report.get("risk_factors", []),
        "citations": report.get("citations", []),
        "confidence_avg": report.get("confidence_avg", 0.0),
        "markdown_export": report.get("markdown_export", ""),
    }
    result = db.table("research_reports").insert(data).execute()
    print(f"✅ Report saved: {data['id'][:8]}")
    return result.data[0]


def save_research_plan(session_id: str, plan: dict) -> dict:
    db = get_supabase()
    data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "dimensions": plan.get("dimensions", []),
        "planned_steps": plan.get("planned_steps", []),
        "sources_to_use": plan.get("sources_to_use", []),
        "estimated_depth": plan.get("estimated_depth", "standard"),
    }
    result = db.table("research_plans").insert(data).execute()
    return result.data[0]


def get_report_by_session(session_id: str) -> dict | None:
    db = get_supabase()
    result = db.table("research_reports").select("*").eq(
        "session_id", session_id
    ).execute()
    return result.data[0] if result.data else None


def get_report_by_id(report_id: str) -> dict | None:
    db = get_supabase()
    result = db.table("research_reports").select("*").eq(
        "id", report_id
    ).execute()
    return result.data[0] if result.data else None


def delete_report(report_id: str):
    db = get_supabase()
    db.table("research_reports").delete().eq(
        "id", report_id
    ).execute()


if __name__ == "__main__":
    from src.db.sessions import create_session, delete_session

    print("Testing reports...")

    # Create a session first (report needs a session)
    session = create_session(
        user_id="test_user",
        query="Test query for report",
        sector="IT",
        depth="standard"
    )

    # Save a test report
    report = save_report(session["id"], {
        "executive_summary": "This is a test report",
        "sections": [{"title": "Test", "content": "Test content"}],
        "key_metrics": {"revenue": "$10B"},
        "investment_outlook": "Positive",
        "risk_factors": ["Market risk"],
        "citations": [{"url": "https://example.com"}],
        "confidence_avg": 0.85,
        "markdown_export": "# Test Report"
    })
    print(f"Report ID: {report['id'][:8]}")

    # Get it back
    fetched = get_report_by_id(report["id"])
    print(f"Fetched summary: {fetched['executive_summary']}")

    # Cleanup
    delete_report(report["id"])
    delete_session(session["id"])
    print("✅ All reports tests passed!")