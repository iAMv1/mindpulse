"""MindPulse Backend — FastAPI Application."""

from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import APP_NAME, VERSION, DESCRIPTION
from app.api.routes import router
from app.api.metrics import router as metrics_router
from app.services.inference import engine
from app.middleware.auth import APIKeyMiddleware, get_api_key
import os


limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.load()
    yield


app = FastAPI(
    title=APP_NAME, version=VERSION, description=DESCRIPTION, lifespan=lifespan
)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = get_api_key()
if api_key:
    app.add_middleware(APIKeyMiddleware, api_key=api_key)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "0",
            "Retry-After": str(exc.detail),
        },
    )


app.state.limiter = limiter

app.include_router(router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"app": APP_NAME, "version": VERSION, "status": "running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
