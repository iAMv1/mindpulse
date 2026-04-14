"""MindPulse Backend — Inference Service."""

from __future__ import annotations
import numpy as np
import time
from typing import Dict, List

from app.core.config import (
    FEATURE_NAMES,
    LABELS,
    STRESS_SCORE_THRESHOLD_MILD,
    STRESS_SCORE_THRESHOLD_HIGH,
    MODEL_SCORE_WEIGHT,
)


class InferenceEngine:
    """Wraps XGBoost model + DualNormalizer for stress prediction."""

    def __init__(self):
        self._model = None
        self._stats = None
        self._normalizer = None
        self._baselines = {}
        self._ready = False

    @staticmethod
    def _sigmoid(x: float) -> float:
        x = max(min(x, 8.0), -8.0)
        return 1.0 / (1.0 + np.exp(-x))

    @staticmethod
    def _clamp_score(x: float) -> float:
        return float(max(0.0, min(100.0, x)))

    def _feature_risk(
        self, z_values: dict, name: str, invert: bool = False, default: float = 0.0
    ) -> float:
        z = float(z_values.get(name, default))
        z = -z if invert else z
        return float(self._sigmoid(z))

    def _compute_equation_score(
        self, features: dict, raw: np.ndarray, baseline, hour: int
    ) -> tuple[float, dict]:
        z_values = {}

        try:
            if baseline is not None and baseline.is_calibrated():
                z_user = baseline.compute_deviations(raw, hour)
                z_values = {name: float(z_user[i]) for i, name in enumerate(FEATURE_NAMES)}
            elif self._stats is not None:
                mean = np.asarray(self._stats["mean"], dtype=np.float32)
                std = np.asarray(self._stats["std"], dtype=np.float32) + 1e-8
                z_global = (raw - mean) / std
                z_values = {
                    name: float(z_global[i]) for i, name in enumerate(FEATURE_NAMES)
                }
        except Exception:
            z_values = {}

        keyboard = np.mean(
            [
                self._feature_risk(z_values, "hold_time_std"),
                self._feature_risk(z_values, "flight_time_std"),
                self._feature_risk(z_values, "pause_frequency"),
                self._feature_risk(z_values, "rhythm_entropy"),
                self._feature_risk(z_values, "error_rate"),
            ]
        )
        speed = self._feature_risk(z_values, "typing_speed_wpm", invert=True)
        switching = np.mean(
            [
                self._feature_risk(z_values, "tab_switch_freq"),
                self._feature_risk(z_values, "switch_entropy"),
                self._feature_risk(z_values, "session_fragmentation"),
            ]
        )
        mouse = np.mean(
            [
                self._feature_risk(z_values, "mouse_speed_std"),
                self._feature_risk(z_values, "direction_change_rate"),
                self._feature_risk(z_values, "rage_click_count"),
            ]
        )

        reentry_count = float(features.get("mouse_reentry_count", 0.0))
        reentry_latency = float(features.get("mouse_reentry_latency_ms", 0.0))
        reentry = np.mean(
            [
                self._sigmoid((reentry_count - 1.0) / 2.0),
                self._sigmoid((reentry_latency - 3000.0) / 1500.0),
            ]
        )

        contributions = {
            "S_keyboard": round(float(keyboard) * 100.0, 1),
            "S_speed": round(float(speed) * 100.0, 1),
            "S_switching": round(float(switching) * 100.0, 1),
            "S_mouse": round(float(mouse) * 100.0, 1),
            "S_reentry": round(float(reentry) * 100.0, 1),
        }

        equation_score = (
            0.30 * contributions["S_keyboard"]
            + 0.15 * contributions["S_speed"]
            + 0.25 * contributions["S_switching"]
            + 0.20 * contributions["S_mouse"]
            + 0.10 * contributions["S_reentry"]
        )
        return self._clamp_score(float(equation_score)), contributions

    @staticmethod
    def _level_from_score(score: float) -> str:
        if score >= STRESS_SCORE_THRESHOLD_HIGH:
            return "STRESSED"
        if score >= STRESS_SCORE_THRESHOLD_MILD:
            return "MILD"
        return "NEUTRAL"

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
                import os

                db_path = BASELINE_DB.replace(".db", f"_{user_id}.db")
                self._baselines[user_id] = PersonalBaseline(db_path=db_path)
            except Exception:
                self._baselines[user_id] = None
        return self._baselines[user_id]

    @property
    def is_ready(self) -> bool:
        return self._ready and self._model is not None

    def predict(self, features_dict: dict, user_id: str = "default") -> dict:
        """Run inference and return structured result."""
        missing = [f for f in FEATURE_NAMES if f not in features_dict]
        if missing:
            return self._fallback_result(
                message=f"Missing required features: {', '.join(missing[:3])}"
            )

        # Convert dict to numpy array in correct order
        raw = np.array([features_dict[f] for f in FEATURE_NAMES], dtype=np.float32)

        hour = int(features_dict.get("hour_of_day", 12))
        baseline = self._get_baseline(user_id)
        equation_score, contributions = self._compute_equation_score(
            features_dict, raw, baseline, hour
        )

        if not self.is_ready:
            model_score = equation_score
            final_score = equation_score
            level = self._level_from_score(final_score)
            confidence = 0.45
            probs = np.array([0.33, 0.33, 0.34], dtype=np.float32)
        else:
            # Dual normalization: global z-score + per-user circadian deviation
            z = self._normalizer.transform(raw, hour, baseline)

            # Predict
            probs = self._model.predict_proba(z.reshape(1, -1))[0]
            confidence = float(np.max(probs))
            model_score = float(probs[0] * 5.0 + probs[1] * 55.0 + probs[2] * 100.0)
            final_score = (
                MODEL_SCORE_WEIGHT * model_score + (1.0 - MODEL_SCORE_WEIGHT) * equation_score
            )
            final_score = self._clamp_score(final_score)
            level = self._level_from_score(final_score)

        timestamp = time.time()

        # Update personal baseline
        if baseline:
            baseline.update(raw, hour)
            baseline.save_session_score(timestamp * 1000.0, final_score, level)

        # Generate insights
        insights = self._generate_insights(features_dict, level)

        return {
            "score": round(final_score, 1),
            "model_score": round(model_score, 1),
            "equation_score": round(equation_score, 1),
            "final_score": round(final_score, 1),
            "level": level,
            "confidence": round(confidence, 3),
            "probabilities": {l: round(float(p), 3) for l, p in zip(LABELS, probs)},
            "feature_contributions": contributions,
            "insights": insights,
            "timestamp": timestamp,
            # Raw features for live dashboard tiles
            "typing_speed_wpm": round(float(features_dict.get("typing_speed_wpm", 0)), 1),
            "rage_click_count": int(features_dict.get("rage_click_count", 0)),
            "error_rate": round(float(features_dict.get("error_rate", 0)), 3),
            "click_count": int(features_dict.get("click_count", 0)),
            "mouse_speed_mean": round(float(features_dict.get("mouse_speed_mean", 0)), 1),
            "mouse_reentry_count": round(
                float(features_dict.get("mouse_reentry_count", 0)), 1
            ),
            "mouse_reentry_latency_ms": round(
                float(features_dict.get("mouse_reentry_latency_ms", 0)), 1
            ),
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
        if features.get("mouse_reentry_count", 0) > 2:
            insights.append("Frequent mouse re-entry after switches — possible task thrashing")

        if not insights and level == "STRESSED":
            insights.append("Multiple behavioral signals indicate elevated stress")

        return insights[:3]  # Max 3 insights

    def _fallback_result(self, message: str = "Model not loaded — check server logs") -> dict:
        """Return when model is not loaded."""
        return {
            "score": 0.0,
            "model_score": 0.0,
            "equation_score": 0.0,
            "final_score": 0.0,
            "level": "UNKNOWN",
            "confidence": 0.0,
            "probabilities": {"NEUTRAL": 0.33, "MILD": 0.33, "STRESSED": 0.34},
            "feature_contributions": {},
            "insights": [message],
            "timestamp": time.time(),
            "typing_speed_wpm": 0.0,
            "rage_click_count": 0,
            "error_rate": 0.0,
            "click_count": 0,
            "mouse_speed_mean": 0.0,
            "mouse_reentry_count": 0.0,
            "mouse_reentry_latency_ms": 0.0,
        }


# Singleton
engine = InferenceEngine()
