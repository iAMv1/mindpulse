"""MindPulse Backend — API Key Authentication."""

from __future__ import annotations
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key in requests."""

    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key
        self.excluded_paths = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if (
            path in self.excluded_paths
            or path.startswith("/docs")
            or path.startswith("/redoc")
        ):
            return await call_next(request)

        api_key_header = request.headers.get("X-API-Key")

        if not api_key_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing X-API-Key header"},
            )

        if api_key_header != self.api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"},
            )

        return await call_next(request)


def get_api_key() -> str:
    """Get API key from environment variables."""
    return os.environ.get("API_KEY", "")
