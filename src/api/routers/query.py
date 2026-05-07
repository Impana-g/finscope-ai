from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

from pydantic import BaseModel

from src.db.sessions import create_session
from src.agents.planner import generate_plan
from src.db.reports import save_research_plan

OUT_OF_SCOPE = [
    "recipe",
    "food",
    "sport",
    "movie",
    "music"
]

IT_KEYWORDS = [
    "infosys",
    "tcs",
    "wipro",
    "hcl"
]

PHARMA_KEYWORDS = [
    "sun pharma",
    "cipla",
    "biocon"
]


class QueryRequest(BaseModel):
    query: str
    user_id: str
    depth: str = "standard"


def simple_classify(query: str):

    q = query.lower()

    if any(kw in q for kw in IT_KEYWORDS):
        return "IT"

    if any(kw in q for kw in PHARMA_KEYWORDS):
        return "PHARMA"

    return "UNKNOWN"


@router.post("/")
async def start_research(req: QueryRequest):

    query_lower = req.query.lower()

    if any(word in query_lower for word in OUT_OF_SCOPE):

        raise HTTPException(
            status_code=422,
            detail="Out of scope query"
        )

    sector = simple_classify(req.query)

    if sector == "UNKNOWN":

        raise HTTPException(
            status_code=422,
            detail="Could not identify company sector"
        )

    session = create_session(
        user_id=req.user_id,
        query=req.query,
        sector=sector,
        depth=req.depth
    )

    plan = generate_plan(
        req.query,
        sector
    )

    save_research_plan(
        session["id"],
        plan
    )

    return {
        "session_id": session["id"],
        "status": "awaiting_approval",
        "sector": sector,
        "plan": plan,
        "message": "Research session and plan created"
    }


@router.get("/health")
def query_health():

    return {
        "status": "query router working"
    }