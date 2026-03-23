"""
MindPulse — Synthetic Data Generator
======================================
Generates realistic synthetic behavioral data to bootstrap the ML model
before real user data is available.

Fulfills Objective 2: To collect, preprocess, and structure
stress-related datasets for model training and evaluation.

Strategy:
  We mathematically model what stressed vs neutral behavior looks like
  based on the research literature (ETH Zurich, CMU, VTT Finland):
    - Stressed users: type slower, more erratic, more errors, more rage clicks
    - Neutral users: smooth, rhythmic typing, steady mouse, fewer switches

  The synthetic data preserves realistic correlations between features
  so the model learns genuine behavioral patterns, not random noise.
"""

import numpy as np
import pandas as pd
from .feature_extractor import FEATURE_NAMES, NUM_RAW_FEATURES

# Label encoding
LABELS = {0: "NEUTRAL", 1: "MILD", 2: "STRESSED"}


def generate_synthetic_dataset(n_samples: int = 3000, random_seed: int = 42) -> tuple:
    """
    Generate a synthetic dataset of behavioral feature vectors with
    stress labels based on research-backed correlations.

    Args:
        n_samples: Total number of samples to generate
        random_seed: For reproducibility

    Returns:
        X: np.ndarray of shape [n_samples, 23] (raw features)
        y: np.ndarray of shape [n_samples] (labels: 0=NEUTRAL, 1=MILD, 2=STRESSED)
        df: pd.DataFrame with features + label for inspection
    """
    np.random.seed(random_seed)

    # ── Class distribution ─────────────────────────────────
    # Realistic imbalance: most time is neutral, stress is rarer
    n_neutral = int(n_samples * 0.50)  # 50%
    n_mild = int(n_samples * 0.30)  # 30%
    n_stressed = n_samples - n_neutral - n_mild  # 20%

    y = np.array([0] * n_neutral + [1] * n_mild + [2] * n_stressed, dtype=np.int32)

    # ── Feature Generation per Class ───────────────────────
    # Each feature has a (mean, std) pair per class derived from literature.
    # Format: feature_name → {0: (mean, std), 1: (mean, std), 2: (mean, std)}

    feature_profiles = {
        # === KEYBOARD (11 features) ===
        # Hold time increases under stress (neuromotor noise)
        "hold_time_mean": {0: (100, 20), 1: (120, 25), 2: (150, 35)},
        "hold_time_std": {0: (15, 5), 1: (25, 8), 2: (40, 12)},
        "hold_time_median": {0: (95, 18), 1: (115, 22), 2: (145, 30)},
        # Flight time variance increases (fits-and-starts pattern)
        "flight_time_mean": {0: (120, 30), 1: (140, 40), 2: (180, 60)},
        "flight_time_std": {0: (40, 10), 1: (70, 20), 2: (110, 30)},
        # WPM decreases under stress
        "typing_speed_wpm": {0: (65, 15), 1: (50, 12), 2: (35, 10)},
        # Error rate increases (more backspaces)
        "error_rate": {0: (0.05, 0.02), 1: (0.10, 0.04), 2: (0.18, 0.06)},
        # More frequent but shorter pauses under stress
        "pause_frequency": {0: (2, 1), 1: (5, 2), 2: (9, 3)},
        "pause_duration_mean": {0: (3000, 800), 1: (2500, 600), 2: (2200, 500)},
        # Burst length decreases (shorter continuous typing runs)
        "burst_length_mean": {0: (25, 8), 1: (15, 5), 2: (8, 3)},
        # Rhythm entropy increases (chaotic timing)
        "rhythm_entropy": {0: (2.0, 0.5), 1: (3.0, 0.7), 2: (4.2, 0.9)},
        # === MOUSE (6 features) ===
        # Speed and variance increase under stress
        "mouse_speed_mean": {0: (300, 80), 1: (450, 120), 2: (600, 150)},
        "mouse_speed_std": {0: (100, 30), 1: (180, 50), 2: (280, 70)},
        # Direction changes increase (indecision/anxiety)
        "direction_change_rate": {0: (0.3, 0.1), 1: (0.5, 0.12), 2: (0.7, 0.15)},
        # Click count relatively stable
        "click_count": {0: (15, 5), 1: (20, 8), 2: (30, 12)},
        # Rage clicks are rare for neutral, more for stressed
        "rage_click_count": {0: (0, 0.3), 1: (1, 0.8), 2: (3, 1.5)},
        # Scroll variance increases (doom-scrolling)
        "scroll_velocity_std": {0: (5, 2), 1: (12, 5), 2: (22, 8)},
        # === CONTEXT SWITCHING (3 features) ===
        # Switching frequency increases under stress
        "tab_switch_freq": {0: (3, 1.5), 1: (8, 3), 2: (15, 5)},
        # Entropy increases (random scattered switching)
        "switch_entropy": {0: (1.0, 0.3), 1: (1.8, 0.5), 2: (2.5, 0.6)},
        # Fragmentation increases
        "session_fragmentation": {0: (0.3, 0.1), 1: (0.6, 0.2), 2: (0.9, 0.25)},
        # === TEMPORAL (3 features) ===
        # These are context, not stress signals — randomized uniformly
        "hour_of_day": {0: (12, 4), 1: (13, 4), 2: (14, 4)},
        "day_of_week": {0: (2, 1.5), 1: (2, 1.5), 2: (2, 1.5)},
        "session_duration_min": {0: (45, 20), 1: (60, 25), 2: (80, 30)},
    }

    # ── Generate samples ───────────────────────────────────
    X = np.zeros((n_samples, NUM_RAW_FEATURES), dtype=np.float32)

    for feat_idx, feat_name in enumerate(FEATURE_NAMES):
        profile = feature_profiles[feat_name]
        for label in [0, 1, 2]:
            mask = y == label
            mean, std = profile[label]
            X[mask, feat_idx] = np.random.normal(mean, std, mask.sum())

    # ── Clamp non-negative features ────────────────────────
    # Many features can't physically be negative
    non_negative = [
        "hold_time_mean",
        "hold_time_std",
        "hold_time_median",
        "flight_time_mean",
        "flight_time_std",
        "typing_speed_wpm",
        "error_rate",
        "pause_frequency",
        "pause_duration_mean",
        "burst_length_mean",
        "rhythm_entropy",
        "mouse_speed_mean",
        "mouse_speed_std",
        "direction_change_rate",
        "click_count",
        "rage_click_count",
        "scroll_velocity_std",
        "tab_switch_freq",
        "switch_entropy",
        "session_fragmentation",
        "session_duration_min",
    ]
    for name in non_negative:
        idx = FEATURE_NAMES.index(name)
        X[:, idx] = np.maximum(X[:, idx], 0)

    # Clamp error_rate to [0, 1]
    err_idx = FEATURE_NAMES.index("error_rate")
    X[:, err_idx] = np.clip(X[:, err_idx], 0, 1)

    # Clamp hour_of_day to [0, 23]
    hour_idx = FEATURE_NAMES.index("hour_of_day")
    X[:, hour_idx] = np.clip(X[:, hour_idx], 0, 23).astype(int)

    # Clamp day_of_week to [0, 6]
    day_idx = FEATURE_NAMES.index("day_of_week")
    X[:, day_idx] = np.clip(X[:, day_idx], 0, 6).astype(int)

    # ── Shuffle ────────────────────────────────────────────
    shuffle_idx = np.random.permutation(n_samples)
    X = X[shuffle_idx]
    y = y[shuffle_idx]

    # ── Create DataFrame for inspection ────────────────────
    df = pd.DataFrame(X, columns=pd.Index(FEATURE_NAMES))
    df["stress_label"] = y
    df["stress_level"] = df["stress_label"].map(lambda x: LABELS.get(int(x), "UNKNOWN"))

    return X, y, df


def compute_global_stats(X: np.ndarray) -> dict:
    """Compute global mean and std for z-score normalization."""
    return {
        "mean": np.mean(X, axis=0).astype(np.float32),
        "std": np.std(X, axis=0).astype(np.float32),
    }


# ─── Self-Test removed — use scripts/ directory ────────────────
# Relative imports don't work in __main__ blocks.
