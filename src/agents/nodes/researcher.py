import anthropic
import json
import os
from dotenv import load_dotenv
from src.tools.web_search import web_search
from src.db.sessions import save_research_step, increment_steps

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def pick_tool(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["stock price", "pe ratio", "market cap", "eps"]):
        return "yfinance"
    return "web_search"


def ask_next_query(topic: str, findings: list, sector: str) -> str:
    summary = "\n".join([
        f"Step {f['step']}: {f['query']} → {f['finding'][:80]}"
        for f in findings[-5:]
    ])
    prompt = f"""What is the single most important next research query?
Output ONLY the search query. Nothing else.

Topic: {topic}
Sector: {sector}
Steps done: {len(findings)}
Recent findings:
{summary}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=80,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


def summarise_finding(query: str, raw: dict) -> tuple:
    prompt = f"""Summarise in 2-3 sentences. Give confidence 0.0-1.0.
JSON only: {{"summary": "...", "confidence": 0.85}}

Query: {query}
Data: {str(raw)[:2000]}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        result = json.loads(text)
        return result["summary"], result["confidence"]
    except Exception:
        return str(raw)[:200], 0.5


def no_new_info(new_finding: str, existing: list) -> bool:
    if len(existing) < 3:
        return False
    recent = [f["finding"].lower() for f in existing[-3:]]
    new_words = set(new_finding.lower().split())
    overlap = sum(1 for r in recent if len(set(r.split()) & new_words) > 8)
    return overlap >= 2


def execute_step_node(state: dict) -> dict:
    step_num = state["steps_completed"] + 1
    next_query = ask_next_query(
        state["original_query"],
        state["findings"],
        state["sector"]
    )

    raw = web_search(next_query)
    sources = raw.get("sources", [])
    tool = "web_search"

    finding, confidence = summarise_finding(next_query, raw)

    if state.get("session_id"):
        save_research_step(
            state["session_id"], step_num, next_query,
            tool, finding, confidence, raw, sources
        )
        increment_steps(state["session_id"], step_num)

    all_done = (
        step_num >= state["max_steps"] or
        (step_num >= 5 and no_new_info(finding, state["findings"]))
    )

    print(f"  Step {step_num}: {next_query[:50]} → confidence: {confidence}")

    return {
        **state,
        "steps_completed": step_num,
        "findings": state["findings"] + [{
            "step": step_num,
            "query": next_query,
            "tool": tool,
            "finding": finding,
            "confidence": confidence,
            "sources": sources
        }],
        "sources": list(set(state["sources"] + sources)),
        "all_complete": all_done
    }