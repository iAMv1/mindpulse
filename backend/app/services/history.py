"""MindPulse Backend — SQLite-backed history store."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from typing import List

from app.schemas.stress import HistoryPoint

MAX_POINTS = 500
_LOCK = threading.RLock()
_DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml", "artifacts", "history.db")
)


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    return sqlite3.connect(_DB_PATH, check_same_thread=False)


def _init_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                score REAL NOT NULL,
                level TEXT NOT NULL,
                confidence REAL NOT NULL,
                insights_json TEXT NOT NULL,
                model_score REAL DEFAULT 0,
                equation_score REAL DEFAULT 0,
                final_score REAL DEFAULT 0,
                typing_speed_wpm REAL DEFAULT 0,
                rage_click_count INTEGER DEFAULT 0,
                error_rate REAL DEFAULT 0,
                click_count INTEGER DEFAULT 0,
                mouse_speed_mean REAL DEFAULT 0,
                mouse_reentry_count REAL DEFAULT 0,
                mouse_reentry_latency_ms REAL DEFAULT 0
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_user_time ON history(user_id, timestamp)"
        )
        conn.commit()


_init_db()


def reset(user_id: str):
    with _LOCK:
        with _connect() as conn:
            conn.execute("DELETE FROM history WHERE user_id=?", (user_id,))
            conn.commit()


def append(user_id: str, point: dict):
    insights = point.get("insights", [])
    if not isinstance(insights, list):
        insights = []
    with _LOCK:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO history (
                    user_id, timestamp, score, level, confidence, insights_json,
                    model_score, equation_score, final_score,
                    typing_speed_wpm, rage_click_count, error_rate, click_count, mouse_speed_mean,
                    mouse_reentry_count, mouse_reentry_latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    float(point.get("timestamp", time.time())),
                    float(point.get("score", 0.0)),
                    str(point.get("level", "UNKNOWN")),
                    float(point.get("confidence", 0.0)),
                    json.dumps(insights),
                    float(point.get("model_score", point.get("score", 0.0))),
                    float(point.get("equation_score", point.get("score", 0.0))),
                    float(point.get("final_score", point.get("score", 0.0))),
                    float(point.get("typing_speed_wpm", 0.0)),
                    int(point.get("rage_click_count", 0)),
                    float(point.get("error_rate", 0.0)),
                    int(point.get("click_count", 0)),
                    float(point.get("mouse_speed_mean", 0.0)),
                    float(point.get("mouse_reentry_count", 0.0)),
                    float(point.get("mouse_reentry_latency_ms", 0.0)),
                ),
            )

            overflow = conn.execute(
                "SELECT COUNT(*) FROM history WHERE user_id=?", (user_id,)
            ).fetchone()[0] - MAX_POINTS
            if overflow > 0:
                conn.execute(
                    """
                    DELETE FROM history
                    WHERE id IN (
                        SELECT id FROM history
                        WHERE user_id=?
                        ORDER BY timestamp ASC
                        LIMIT ?
                    )
                    """,
                    (user_id, overflow),
                )
            conn.commit()


def get_history(user_id: str, hours: int = 24) -> List[HistoryPoint]:
    cutoff = time.time() - (hours * 3600)
    with _LOCK:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, score, level, insights_json
                FROM history
                WHERE user_id=? AND timestamp > ?
                ORDER BY timestamp ASC
                """,
                (user_id, cutoff),
            ).fetchall()
    points = []
    for ts, score, level, insights_json in rows:
        try:
            insights = json.loads(insights_json) if insights_json else []
        except json.JSONDecodeError:
            insights = []
        points.append(
            HistoryPoint(
                timestamp=float(ts),
                score=float(score),
                level=str(level),
                insights=insights if isinstance(insights, list) else [],
            )
        )
    return points


def get_stats(user_id: str) -> dict:
    with _LOCK:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT score, level, typing_speed_wpm, rage_click_count, error_rate, click_count
                FROM history
                WHERE user_id=?
                ORDER BY timestamp ASC
                """,
                (user_id,),
            ).fetchall()

    if not rows:
        return {
            "total_samples": 0,
            "avg_score": 0,
            "stressed_pct": 0,
            "current_level": "UNKNOWN",
            "typing_speed_wpm": 0,
            "rage_click_count": 0,
            "error_rate": 0,
            "click_count": 0,
        }

    total = len(rows)
    stressed = sum(1 for r in rows if r[1] == "STRESSED")
    avg_score = sum(float(r[0]) for r in rows) / total
    avg_wpm = sum(float(r[2]) for r in rows) / total
    total_rage = sum(int(r[3]) for r in rows)
    avg_error = sum(float(r[4]) for r in rows) / total
    total_clicks = sum(int(r[5]) for r in rows)

    return {
        "total_samples": total,
        "avg_score": round(avg_score, 1),
        "stressed_pct": round(stressed / total * 100, 1),
        "current_level": rows[-1][1] if rows else "UNKNOWN",
        "typing_speed_wpm": round(avg_wpm, 1),
        "rage_click_count": int(total_rage),
        "error_rate": round(avg_error, 3),
        "click_count": int(total_clicks),
    }
