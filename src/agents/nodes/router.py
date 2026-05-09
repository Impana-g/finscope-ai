import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def route_query_node(state: dict) -> dict:

    prompt = f"""Classify this financial query.
Options: IT, PHARMA, COMPARATIVE, UNKNOWN

IT: TCS, Infosys, Wipro, HCL, software, cloud
PHARMA: Sun Pharma, Cipla, Biocon, drugs, FDA
COMPARATIVE: compare, vs, versus
UNKNOWN: food, sports, anything non-financial

JSON only: {{"sector": "IT", "confidence": 0.95}}

Query: {state['original_query']}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        result = json.loads(text)
        sector = result.get("sector", "UNKNOWN")
        print(f"✅ Sector classified: {sector}")
        return {**state, "sector": sector}

    except Exception as e:
        print(f"❌ Router error: {e}")
        return {**state, "sector": "UNKNOWN"}


if __name__ == "__main__":
    print("Testing router...")

    test_state = {
        "session_id": "test-123",
        "original_query": "Analyze Infosys financial performance 2025",
        "sector": "UNKNOWN",
        "depth": "standard",
        "research_plan": None,
        "plan_approved": False,
        "steps_completed": 0,
        "max_steps": 10,
        "findings": [],
        "sources": [],
        "all_complete": False,
        "report": None,
        "error": None
    }

    result = route_query_node(test_state)
    print(f"Result sector: {result['sector']}")
    print("✅ Router test passed!")