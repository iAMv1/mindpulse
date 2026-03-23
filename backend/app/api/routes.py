"""MindPulse Backend — API Routes."""

from __future__ import annotations
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.schemas.stress import (
    InferenceRequest,
    InferenceResponse,
    HistoryPoint,
    FeedbackRequest,
    CalibrationStatus,
    HealthResponse,
    BatchPredictRequest,
    BatchPredictResponse,
)
from app.services.inference import engine
from app.services.websocket_manager import manager
from app.services import history

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model_loaded=engine.is_ready,
        version="1.0.0",
        active_connections=manager.count,
    )


@router.post("/inference", response_model=InferenceResponse)
@limiter.limit("100/minute")
async def run_inference(request: Request, req: InferenceRequest):
    try:
        result = engine.predict(req.features.model_dump(), req.user_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    history.append(req.user_id, result)
    await manager.broadcast({"type": "stress_update", **result, "user_id": req.user_id})
    return InferenceResponse(**result)


@router.get("/history", response_model=list[HistoryPoint])
@limiter.limit("100/minute")
async def get_history(request: Request, user_id: str = "default", hours: int = 24):
    return history.get_history(user_id, hours)


@router.get("/stats")
@limiter.limit("100/minute")
async def get_stats(request: Request, user_id: str = "default"):
    return history.get_stats(user_id)


@router.post("/feedback")
@limiter.limit("100/minute")
async def submit_feedback(request: Request, req: FeedbackRequest):
    try:
        from app.ml.model import PersonalBaseline, BASELINE_DB
        import os

        db_path = BASELINE_DB.replace(".db", f"_{req.user_id}.db")
        if os.path.exists(db_path):
            baseline = PersonalBaseline(db_path=db_path)
            score = 0.0
            if req.actual_level == "STRESSED":
                score = 1.0
            elif req.actual_level == "MILD":
                score = 0.5
            baseline.save_feedback(
                timestamp_ms=req.timestamp
                if hasattr(req, "timestamp")
                else (time.time() * 1000),
                model_label=req.predicted_level,
                user_feedback=req.actual_level,
                score=score,
            )
            saved = True
        else:
            saved = False
    except Exception:
        saved = False
    return {
        "status": "ok",
        "message": f"Feedback recorded: predicted {req.predicted_level}, actual {req.actual_level}",
        "saved": saved,
    }


@router.get("/calibration/{user_id}", response_model=CalibrationStatus)
@limiter.limit("100/minute")
async def get_calibration(request: Request, user_id: str):
    try:
        from app.ml.model import PersonalBaseline, BASELINE_DB
        import os

        db_path = BASELINE_DB.replace(".db", f"_{user_id}.db")
        if os.path.exists(db_path):
            baseline = PersonalBaseline(db_path=db_path)
            is_calibrated = baseline.is_calibrated()
            history = baseline.get_session_history(limit_hours=168)
            conn = baseline._connect()
            try:
                rows = conn.execute(
                    "SELECT hour, sample_count FROM baselines"
                ).fetchall()
                total_samples = sum(r[1] for r in rows)
            finally:
                conn.close()
            completion_pct = min(100.0, (total_samples / 500.0) * 100)
            days_collected = len(set(int(h[0] / 24) for h in history)) if history else 0
            return CalibrationStatus(
                user_id=user_id,
                is_calibrated=is_calibrated,
                days_collected=days_collected,
                samples_per_hour={},
                completion_pct=completion_pct,
            )
    except Exception:
        pass
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


@router.post("/batch-predict", response_model=BatchPredictResponse)
@limiter.limit("100/minute")
async def batch_predict(request: Request, req: BatchPredictRequest):
    predictions = []
    for feature_set in req.features:
        try:
            result = engine.predict(feature_set.model_dump(), req.user_id)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        history.append(req.user_id, result)
        predictions.append(InferenceResponse(**result))
    return BatchPredictResponse(predictions=predictions)


@router.get("/export/{user_id}")
async def export_user_data(user_id: str, format: str = "json"):
    from app.ml.model import PersonalBaseline, BASELINE_DB
    import os

    db_path = BASELINE_DB.replace(".db", f"_{user_id}.db")

    calibration_data = {}
    if os.path.exists(db_path):
        try:
            baseline = PersonalBaseline(db_path=db_path)
            conn = baseline._connect()
            try:
                rows = conn.execute("SELECT * FROM baselines").fetchall()
                calibration_data = {
                    "samples": [
                        {"hour": r[0], "sample_count": r[1], "mean": r[2], "std": r[3]}
                        for r in rows
                    ]
                }
            finally:
                conn.close()
        except Exception:
            calibration_data = {"samples": []}

    pred_history = history.get_history(user_id, hours=168)

    if format.lower() == "csv":
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "score", "level", "insights"])
        for point in pred_history:
            writer.writerow(
                [point.timestamp, point.score, point.level, "|".join(point.insights)]
            )
        return {"Content-Type": "text/csv", "body": output.getvalue()}

    return {
        "user_id": user_id,
        "calibration": calibration_data,
        "predictions": [p.model_dump() for p in pred_history],
    }


@router.post("/auth/login")
async def login(user_id: str):
    from app.ml.model import BASELINE_DB
    import os

    db_path = BASELINE_DB.replace(".db", f"_{user_id}.db")
    exists = os.path.exists(db_path)

    return {
        "authenticated": exists,
        "token": user_id if exists else None,
        "user_id": user_id,
    }
