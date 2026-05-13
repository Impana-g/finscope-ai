# main.py
# This is the ENTRY POINT of the entire application
# It connects all routers and starts the server

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import all routers
from src.api.routers import sessions, reports

# Try to import Skandan's query router
try:
    from src.api.routers import query  # type: ignore
    QUERY_ROUTER_READY = True
except ImportError:
    print("[WARNING] Query router not ready yet")
    QUERY_ROUTER_READY = False


# ── Create FastAPI app ────────────────────────────────
app = FastAPI(
    title="FinScope AI",
    description=(
        "AI-powered financial research tool for IT and Pharma sectors. "
        "Ask any financial question and get a detailed research report."
    ),
    version="2.0.0",
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc"      # Alternative docs at /redoc
)


# ── CORS Middleware ───────────────────────────────────
# Allows frontend to call your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Connect Routers ───────────────────────────────────
if QUERY_ROUTER_READY:
    app.include_router(
        query.router,
        prefix="/query",
        tags=["🔍 Research"]
    )

app.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["📋 Sessions"]
)

app.include_router(
    reports.router,
    prefix="/reports",
    tags=["📄 Reports"]
)


# ── Basic Endpoints ───────────────────────────────────

@app.get("/", tags=["General"])
def home():
    """Home endpoint — check if server is running"""
    return {
        "service": "FinScope AI",
        "version": "2.0.0",
        "status": "running",
        "message": "Welcome to FinScope AI!",
        "links": {
            "docs": "/docs",
            "health": "/health",
            "start_research": "POST /query"
        }
    }


@app.get("/health", tags=["General"])
def health_check():
    """Health check — used by deployment systems"""
    return {
        "status": "ok",
        "service": "FinScope AI",
        "version": "2.0.0",
        "components": {
            "api": "running",
            "query_router": "ready" if QUERY_ROUTER_READY else "pending",
            "sessions_router": "ready",
            "reports_router": "ready"
        }
    }


# ── Global Error Handler ──────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if hasattr(exc, "detail") and isinstance(exc.detail, dict):
        return JSONResponse(status_code=404, content={"detail": exc.detail})
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": f"Path '{request.url.path}' not found",
            "hint": "Check /docs for all available endpoints"
        }
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "server_error",
            "message": "Something went wrong on our side",
            "hint": "Please try again or contact support"
        }
    )


# ── Run directly ──────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
