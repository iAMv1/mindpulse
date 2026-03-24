"""MindPulse Backend — Inference Service."""

from __future__ import annotations
import numpy as np
import time
from typing import List

from app.core.config import (
    FEATURE_NAMES,
    LABELS,
)


class InferenceEngine:
    """Wraps XGBoost model + DualNormalizer for stress prediction."""

    def __init__(self):
        self._model = None
        self._stats = None
        self._normalizer = None
        self._baselines = {}
        self._ready = False

    def load(self):
        """Lazy-load model from ml package."""
        if self._ready:
            return
        try:
            from app.ml.model import load_model, DualNormalizer

            self._model, self._stats = load_model(
                allow_download=True, allow_train_fallback=True
            )
            self._normalizer = DualNormalizer(self._stats)
            self._ready = True
            print("[MindPulse] Model loaded")
        except Exception as e:
            print(f"[MindPulse] Model load failed: {e}")
            self._ready = False

    def _get_baseline(self, user_id: str):
        """Get or create a PersonalBaseline for a user."""
        if user_id not in self._baselines:
            try:
                from app.ml.model import PersonalBaseline, BASELINE_DB

                db_path = BASELINE_DB.replace(".db", f"_{user_id}.db")
                self._baselines[user_id] = PersonalBaseline(db_path=db_path)
            except Exception:
                self._baselines[user_id] = None
        return self._baselines[user_id]

    @property
    def is_ready(self) -> bool:
        return self._ready and self._model is not None

    def set_ready_for_tests(self, ready: bool = True):
        """Force readiness flag for tests without loading the full model."""
        self._ready = ready
        if ready:
            if self._model is None:
                self._model = object()
        else:
            self._model = None

    def predict(self, features_dict: dict, user_id: str = "default") -> dict:
        """Run inference and return structured result."""
        if not self.is_ready:
            return self._fallback_result()

        raw = np.array([features_dict[f] for f in FEATURE_NAMES], dtype=np.float32)

        non_finite_mask = ~np.isfinite(raw)
        if np.any(non_finite_mask):
            non_finite_features = [
                FEATURE_NAMES[i]
                for i in range(len(FEATURE_NAMES))
                if non_finite_mask[i]
            ]
            raise ValueError(
                f"Invalid input: features contain non-finite values (NaN or Inf): {non_finite_features}"
            )

        hour = int(features_dict.get("hour_of_day", 12))
        baseline = self._get_baseline(user_id)
        z = self._normalizer.transform(raw, hour, baseline)

        probs = self._model.predict_proba(z.reshape(1, -1))[0]
        level_idx = int(np.argmax(probs))
        level = LABELS[level_idx]
        confidence = float(np.max(probs))
        score = float(probs[1] * 50.0 + probs[2] * 100.0)

        if baseline:
            baseline.update(raw, hour)

        insights = self._generate_insights(features_dict, level)

        return {
            "score": round(score, 1),
            "level": level,
            "confidence": round(confidence, 3),
            "probabilities": {
                label: round(float(p), 3) for label, p in zip(LABELS, probs)
            },
            "insights": insights,
            "timestamp": time.time(),
        }

    def _generate_insights(self, features: dict, level: str) -> List[str]:
        """Generate human-readable stress insights from feature values."""
        insights = []

        if features.get("rage_click_count", 0) > 2:
            insights.append(
                "Frustrated clicking detected — consider taking a short break"
            )
        if features.get("error_rate", 0) > 0.1:
            insights.append("Higher than usual error rate — possible cognitive fatigue")
        if features.get("rhythm_entropy", 0) > 3.5:
            insights.append("Typing rhythm is erratic — stress may be affecting focus")
        if features.get("session_fragmentation", 0) > 0.7:
            insights.append(
                "Highly fragmented session — frequent context switching detected"
            )
        if features.get("tab_switch_freq", 0) > 10:
            insights.append("Rapid app switching — may indicate difficulty focusing")
        if features.get("typing_speed_wpm", 50) < 30:
            insights.append("Typing speed is lower than typical — possible fatigue")
        if features.get("mouse_speed_std", 0) > 150:
            insights.append("Inconsistent mouse movements — possible restlessness")

        if not insights and level == "STRESSED":
            insights.append("Multiple behavioral signals indicate elevated stress")

        return insights[:3]  # Max 3 insights

    def _fallback_result(self) -> dict:
        """Return when model is not loaded."""
        return {
            "score": 0.0,
            "level": "UNKNOWN",
            "confidence": 0.0,
            "probabilities": {"NEUTRAL": 0.33, "MILD": 0.33, "STRESSED": 0.34},
            "insights": ["Model not loaded — check server logs"],
            "timestamp": time.time(),
        }


# Singleton
engine = InferenceEngine()
