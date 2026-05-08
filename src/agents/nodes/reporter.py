import anthropic
import json
import os
from dotenv import load_dotenv
from src.db.reports import save_report
from src.db.sessions import update_session_status

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_report_node(state: dict) -> dict:
    findings_text = "\n".join([
        f"Step {f['step']}: {f['query']}\nFinding: {f['finding']}"
        for f in state["findings"]
    ])
    avg_conf = sum(f["confidence"] for f in state["findings"]) / max(len(state["findings"]), 1)

    prompt = f"""Write a financial research report. JSON only:
{{
    "executive_summary": "2-3 paragraphs with specific numbers...",
    "sections": [
        {{"title": "Financial Performance", "content": "...", "data_points": []}}
    ],
    "key_metrics": {{"revenue": "...", "pe_ratio": "..."}},
    "investment_outlook": "...",
    "risk_factors": ["risk1", "risk2"]
}}

Query: {state['original_query']}
Sector: {state['sector']}
Findings:
{findings_text}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        report_data = json.loads(text)
    except Exception as e:
        print(f"Report error: {e}")
        report_data = {
            "executive_summary": "\n".join([f["finding"] for f in state["findings"]]),
            "sections": [],
            "key_metrics": {},
            "investment_outlook": "See findings above.",
            "risk_factors": []
        }

    md = f"# {state['original_query']}\n\n"
    md += f"## Executive Summary\n{report_data['executive_summary']}\n\n"
    for s in report_data.get("sections", []):
        md += f"## {s['title']}\n{s['content']}\n\n"
    md += "## Sources\n" + "\n".join(f"- {s}" for s in state["sources"])

    report_data["markdown_export"] = md
    report_data["confidence_avg"] = round(avg_conf, 2)
    report_data["citations"] = [{"url": s} for s in state["sources"]]

    if state.get("session_id"):
        saved = save_report(state["session_id"], report_data)
        update_session_status(state["session_id"], "completed")
        return {**state, "report": saved}

    return {**state, "report": report_data}