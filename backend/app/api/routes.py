"""MindPulse Backend — API Routes."""

from __future__ import annotations
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.schemas.stress import (
    InferenceRequest,
    InferenceResponse,
    HistoryPoint,
    FeedbackRequest,
    CalibrationStatus,
    HealthResponse,
)
from app.services.inference import engine
from app.services.websocket_manager import manager
from app.services import history

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model_loaded=engine.is_ready,
        version="1.0.0",
        active_connections=manager.count,
    )


@router.post("/inference", response_model=InferenceResponse)
async def run_inference(req: InferenceRequest):
    result = engine.predict(req.features.model_dump(), req.user_id)
    history.append(req.user_id, result)
    await manager.broadcast({"type": "stress_update", **result, "user_id": req.user_id})
    return InferenceResponse(**result)


@router.get("/history", response_model=list[HistoryPoint])
async def get_history(user_id: str = "default", hours: int = 24):
    return history.get_history(user_id, hours)


@router.get("/stats")
async def get_stats(user_id: str = "default"):
    return history.get_stats(user_id)


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    return {
        "status": "ok",
        "message": f"Feedback recorded: predicted {req.predicted_level}, actual {req.actual_level}",
    }


@router.get("/calibration/{user_id}", response_model=CalibrationStatus)
async def get_calibration(user_id: str):
    return CalibrationStatus(
        user_id=user_id,
        is_calibrated=False,
        days_collected=0,
        samples_per_hour={},
        completion_pct=0.0,
    )


@router.websocket("/ws/stress")
async def websocket_stress(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            # Client can send feature vectors for real-time prediction
            import json

            try:
                payload = json.loads(data)
                if payload.get("type") == "features":
                    from app.schemas.stress import FeatureVector

                    fv = FeatureVector(**payload["features"])
                    result = engine.predict(
                        fv.model_dump(), payload.get("user_id", "default")
                    )
                    uid = payload.get("user_id", "default")
                    history.append(uid, result)
                    await ws.send_json({"type": "stress_update", **result})
            except (json.JSONDecodeError, KeyError):
                pass
    except WebSocketDisconnect:
        manager.disconnect(ws)
