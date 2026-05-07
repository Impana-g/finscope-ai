from fastapi import FastAPI

from src.api.routers.query import router as query_router

app = FastAPI(
    title="FinScope AI",
    version="1.0.0"
)

app.include_router(
    query_router,
    prefix="/query",
    tags=["Query"]
)


@app.get("/")
def home():

    return {
        "message": "FinScope AI backend running"
    }