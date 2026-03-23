"""MindPulse Backend — System Metrics."""

from __future__ import annotations
import time
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.inference import engine

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

_start_time = time.time()


class MetricsResponse(BaseModel):
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    total_predictions: int = Field(..., description="Total predictions made")
    total_users: int = Field(..., description="Total unique users")
    avg_stress_level: float = Field(..., description="Average stress score")
    model_loaded: bool = Field(..., description="Whether model is loaded")


@router.get("/metrics", response_model=MetricsResponse)
@limiter.limit("100/minute")
async def get_metrics(request: Request):
    from app.services.history import _store

    total_predictions = sum(len(v) for v in _store.values())
    total_users = len(_store)

    all_scores = []
    for user_points in _store.values():
        all_scores.extend(p.get("score", 0) for p in user_points)

    avg_stress = sum(all_scores) / len(all_scores) if all_scores else 0.0

    return MetricsResponse(
        uptime_seconds=round(time.time() - _start_time, 1),
        total_predictions=total_predictions,
        total_users=total_users,
        avg_stress_level=round(avg_stress, 2),
        model_loaded=engine.is_ready,
    )
