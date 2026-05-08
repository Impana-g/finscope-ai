from typing import TypedDict, List, Optional


class ResearchState(TypedDict):
    session_id: str
    original_query: str
    sector: str
    depth: str
    research_plan: Optional[dict]
    plan_approved: bool
    steps_completed: int
    max_steps: int
    findings: List[dict]
    sources: List[str]
    all_complete: bool
    report: Optional[dict]
    error: Optional[str]