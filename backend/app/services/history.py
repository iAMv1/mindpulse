"""MindPulse Backend — In-memory history store."""

from __future__ import annotations
from typing import Dict, List
from app.schemas.stress import HistoryPoint

_store: Dict[str, List[dict]] = {}
MAX_POINTS = 500


def append(user_id: str, point: dict):
    if user_id not in _store:
        _store[user_id] = []
    _store[user_id].append(point)
    if len(_store[user_id]) > MAX_POINTS:
        _store[user_id] = _store[user_id][-MAX_POINTS:]


def get_history(user_id: str, hours: int = 24) -> List[HistoryPoint]:
    import time

    cutoff = time.time() - (hours * 3600)
    points = _store.get(user_id, [])
    return [HistoryPoint(**p) for p in points if p["timestamp"] > cutoff]


def get_stats(user_id: str) -> dict:
    points = _store.get(user_id, [])
    if not points:
        return {"total_samples": 0, "avg_score": 0, "stressed_pct": 0}
    scores = [p["score"] for p in points]
    stressed = sum(1 for p in points if p["level"] == "STRESSED")
    return {
        "total_samples": len(points),
        "avg_score": round(sum(scores) / len(scores), 1),
        "stressed_pct": round(stressed / len(points) * 100, 1),
        "current_level": points[-1]["level"] if points else "UNKNOWN",
    }
