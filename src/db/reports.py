from .client import get_supabase
import uuid


def save_report(session_id: str, report: dict) -> dict:

    db = get_supabase()

    data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "executive_summary": report.get(
            "executive_summary", ""
        ),
        "sections": report.get("sections", []),
        "key_metrics": report.get("key_metrics", {}),
        "investment_outlook": report.get(
            "investment_outlook", ""
        ),
        "risk_factors": report.get(
            "risk_factors", []
        ),
        "citations": report.get("citations", []),
        "confidence_avg": report.get(
            "confidence_avg", 0.0
        ),
        "markdown_export": report.get(
            "markdown_export", ""
        ),
    }

    result = (
        db.table("research_reports")
        .insert(data)
        .execute()
    )

    print(f"✅ Report saved: {data['id']}")

    return result.data[0]


def get_report_by_session(session_id: str):

    db = get_supabase()

    result = (
        db.table("research_reports")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def delete_report(report_id: str):

    db = get_supabase()

    db.table("research_reports") \
      .delete() \
      .eq("id", report_id) \
      .execute()

    print("✅ Report deleted")