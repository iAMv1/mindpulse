"""Smoke tests for key API routes to ensure basic request handling works."""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import history
from app.services.inference import engine


def _dummy_features() -> dict:
    return {
        "hold_time_mean": 120.0,
        "hold_time_std": 10.0,
        "hold_time_median": 115.0,
        "flight_time_mean": 80.0,
        "flight_time_std": 8.0,
        "typing_speed_wpm": 60.0,
        "error_rate": 0.05,
        "pause_frequency": 2.0,
        "pause_duration_mean": 150.0,
        "burst_length_mean": 5.0,
        "rhythm_entropy": 2.5,
        "mouse_speed_mean": 200.0,
        "mouse_speed_std": 50.0,
        "direction_change_rate": 0.2,
        "click_count": 30.0,
        "rage_click_count": 0.0,
        "scroll_velocity_std": 10.0,
        "tab_switch_freq": 5.0,
        "switch_entropy": 1.2,
        "session_fragmentation": 0.3,
        "hour_of_day": 10.0,
        "day_of_week": 2.0,
        "session_duration_min": 45.0,
    }


@pytest.fixture()
def client(monkeypatch):
    """Provide a TestClient with inference engine stubbed for speed."""

    def _fake_load():
        engine._ready = True

    def _fake_predict(features: dict, user_id: str = "default"):
        return {
            "score": 42.0,
            "level": "MILD",
            "confidence": 0.9,
            "probabilities": {"NEUTRAL": 0.1, "MILD": 0.9, "STRESSED": 0.0},
            "insights": ["ok"],
            "timestamp": time.time(),
        }

    history._store.clear()
    monkeypatch.setattr(engine, "load", _fake_load)
    monkeypatch.setattr(engine, "predict", _fake_predict)
    engine._ready = True

    with TestClient(app) as client:
        yield client

    history._store.clear()


def test_health(client: TestClient):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data


def test_inference_history_and_stats(client: TestClient):
    payload = {"features": _dummy_features(), "user_id": "alice"}
    res = client.post("/api/v1/inference", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["level"] == "MILD"

    hist = client.get("/api/v1/history", params={"user_id": "alice", "hours": 24})
    assert hist.status_code == 200
    hist_body = hist.json()
    assert len(hist_body) == 1
    assert hist_body[0]["level"] == "MILD"

    stats = client.get("/api/v1/stats", params={"user_id": "alice"})
    assert stats.status_code == 200
    stats_body = stats.json()
    assert stats_body["total_samples"] == 1
    assert stats_body["current_level"] == "MILD"


def test_feedback_and_calibration_defaults(client: TestClient):
    feedback = {
        "user_id": "bob",
        "timestamp": time.time(),
        "predicted_level": "MILD",
        "actual_level": "NEUTRAL",
    }
    res = client.post("/api/v1/feedback", json=feedback)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    calib = client.get("/api/v1/calibration/bob")
    assert calib.status_code == 200
    body = calib.json()
    assert body["user_id"] == "bob"
    assert body["completion_pct"] == 0.0


def test_batch_predict_returns_predictions(client: TestClient):
    payload = {"features": [_dummy_features(), _dummy_features()], "user_id": "carol"}
    res = client.post("/api/v1/batch-predict", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert len(body["predictions"]) == 2
    assert all(pred["level"] == "MILD" for pred in body["predictions"])
