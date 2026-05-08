from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.routers.query import router as query_router
from src.api.routers.sessions import router as sessions_router
from src.api.routers.reports import router as reports_router

app = FastAPI(
    title="FinScope AI",
    version="2.0.0",
    description="AI-powered financial research for IT and Pharma"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(query_router,    prefix="/query",    tags=["Research"])
app.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
app.include_router(reports_router,  prefix="/reports",  tags=["Reports"])

@app.get("/")
def home():
    return {
        "service": "FinScope AI",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "FinScope AI"}

@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "hint": "Check /docs for all endpoints"}
    )