"""
MindPulse — Multi-User Synthetic Dataset Generator
====================================================
Generates 15-20 simulated users with DISTINCT behavioral profiles.
Each user has unique stress response patterns (like AlgoQuest personas).

Strategy:
  - Each user has a "baseline personality" affecting all features
  - Stress responses vary per user (some type faster when stressed, some slower)
  - Circadian rhythms differ (morning people vs night owls)
  - Session patterns differ (focused workers vs frequent switchers)

This simulates what real multi-user data would look like for Group K-Fold.
"""

from __future__ import annotations

import os
import sys

# Add parent directories to path for ml package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple

from app.ml.feature_extractor import FEATURE_NAMES, NUM_RAW_FEATURES


# ────────────────────────────────────────────────────────────────
# User Personas (inspired by AlgoQuest simulation personas)
# ────────────────────────────────────────────────────────────────

PERSONAS = [
    # (name, typing_style, stress_response, peak_hours, switch_tendency)
    ("alex_focused", "fast_accurate", "slow_down", [9, 10, 11], "low"),
    ("benji_erratic", "fast_sloppy", "speed_up_errors", [14, 15, 16], "high"),
    ("charlie_steady", "medium_consistent", "slight_slow", [10, 11, 14], "medium"),
    ("diana_nightowl", "slow_careful", "erratic", [20, 21, 22], "low"),
    ("ethan_anxious", "medium_fast", "panic_switch", [11, 12, 15], "very_high"),
    ("fiona_calm", "fast_precise", "maintains", [8, 9, 10], "low"),
    ("george_rushed", "very_fast", "rage_click", [13, 14, 16], "high"),
    ("hana_methodical", "slow_precise", "freeze", [10, 11, 14], "very_low"),
    ("ivan_creative", "variable", "scatter", [15, 16, 17], "high"),
    ("julia_newbie", "slow_uncertain", "slow_way_down", [9, 10, 11], "medium"),
    ("kevin_gamer", "fast_rhythmic", "faster_clicks", [20, 21, 22], "medium"),
    ("lisa_manager", "medium_burst", "more_switches", [9, 10, 11, 14, 15], "high"),
    ("marcus_coder", "fast_long_bursts", "shorter_bursts", [10, 11, 14, 15], "low"),
    ("nadia_writer", "medium_flowing", "pauses_more", [14, 15, 16], "very_low"),
    ("oscar_student", "variable_learning", "all_over", [11, 12, 15, 16], "medium"),
    ("priya_analyst", "fast_organized", "slight_increase", [9, 10, 14], "low"),
    ("quinn_designer", "slow_thoughtful", "random_movements", [10, 11, 15], "medium"),
    (
        "rosa_support",
        "fast_repetitive",
        "frustrated_clicks",
        [13, 14, 15, 16],
        "very_high",
    ),
]

STRESS_RESPONSES = {
    "slow_down": {
        "hold_mult": 1.3,
        "flight_mult": 1.4,
        "wpm_mult": 0.7,
        "err_mult": 1.2,
        "switch_mult": 0.8,
    },
    "speed_up_errors": {
        "hold_mult": 0.9,
        "flight_mult": 0.8,
        "wpm_mult": 1.1,
        "err_mult": 2.5,
        "switch_mult": 1.3,
    },
    "slight_slow": {
        "hold_mult": 1.1,
        "flight_mult": 1.15,
        "wpm_mult": 0.85,
        "err_mult": 1.3,
        "switch_mult": 1.1,
    },
    "erratic": {
        "hold_mult": 1.5,
        "flight_mult": 1.8,
        "wpm_mult": 0.6,
        "err_mult": 2.0,
        "switch_mult": 1.5,
    },
    "panic_switch": {
        "hold_mult": 1.2,
        "flight_mult": 1.3,
        "wpm_mult": 0.75,
        "err_mult": 1.5,
        "switch_mult": 3.0,
    },
    "maintains": {
        "hold_mult": 1.05,
        "flight_mult": 1.05,
        "wpm_mult": 0.95,
        "err_mult": 1.1,
        "switch_mult": 1.0,
    },
    "rage_click": {
        "hold_mult": 0.85,
        "flight_mult": 0.7,
        "wpm_mult": 1.2,
        "err_mult": 3.0,
        "switch_mult": 1.8,
    },
    "freeze": {
        "hold_mult": 1.8,
        "flight_mult": 2.5,
        "wpm_mult": 0.4,
        "err_mult": 0.8,
        "switch_mult": 0.3,
    },
    "scatter": {
        "hold_mult": 1.3,
        "flight_mult": 1.6,
        "wpm_mult": 0.65,
        "err_mult": 1.8,
        "switch_mult": 2.5,
    },
    "slow_way_down": {
        "hold_mult": 1.6,
        "flight_mult": 2.0,
        "wpm_mult": 0.5,
        "err_mult": 2.0,
        "switch_mult": 0.5,
    },
    "faster_clicks": {
        "hold_mult": 0.8,
        "flight_mult": 0.75,
        "wpm_mult": 1.15,
        "err_mult": 1.4,
        "switch_mult": 1.2,
    },
    "more_switches": {
        "hold_mult": 1.1,
        "flight_mult": 1.2,
        "wpm_mult": 0.8,
        "err_mult": 1.3,
        "switch_mult": 2.8,
    },
    "shorter_bursts": {
        "hold_mult": 1.15,
        "flight_mult": 1.4,
        "wpm_mult": 0.7,
        "err_mult": 1.5,
        "switch_mult": 1.6,
    },
    "pauses_more": {
        "hold_mult": 1.2,
        "flight_mult": 2.0,
        "wpm_mult": 0.6,
        "err_mult": 1.1,
        "switch_mult": 0.4,
    },
    "all_over": {
        "hold_mult": 1.4,
        "flight_mult": 1.7,
        "wpm_mult": 0.55,
        "err_mult": 2.2,
        "switch_mult": 2.0,
    },
    "slight_increase": {
        "hold_mult": 1.08,
        "flight_mult": 1.1,
        "wpm_mult": 0.9,
        "err_mult": 1.2,
        "switch_mult": 1.15,
    },
    "random_movements": {
        "hold_mult": 1.25,
        "flight_mult": 1.5,
        "wpm_mult": 0.7,
        "err_mult": 1.4,
        "switch_mult": 1.3,
    },
    "frustrated_clicks": {
        "hold_mult": 0.9,
        "flight_mult": 0.8,
        "wpm_mult": 1.0,
        "err_mult": 4.0,
        "switch_mult": 2.5,
    },
}


def generate_user_baseline(persona_idx: int, rng: np.random.Generator) -> dict:
    """
    Generate a user's baseline (neutral) feature values.
    Each user has a unique "fingerprint" of typing behavior.
    """
    name, style, response, peaks, switch_tend = PERSONAS[persona_idx]

    # Base values vary by style
    style_profiles = {
        "fast_accurate": {
            "hold_base": 85,
            "flight_base": 100,
            "wpm_base": 75,
            "err_base": 0.03,
        },
        "fast_sloppy": {
            "hold_base": 80,
            "flight_base": 90,
            "wpm_base": 80,
            "err_base": 0.08,
        },
        "medium_consistent": {
            "hold_base": 100,
            "flight_base": 120,
            "wpm_base": 60,
            "err_base": 0.05,
        },
        "slow_careful": {
            "hold_base": 120,
            "flight_base": 150,
            "wpm_base": 45,
            "err_base": 0.02,
        },
        "medium_fast": {
            "hold_base": 95,
            "flight_base": 110,
            "wpm_base": 65,
            "err_base": 0.06,
        },
        "fast_precise": {
            "hold_base": 88,
            "flight_base": 105,
            "wpm_base": 78,
            "err_base": 0.02,
        },
        "very_fast": {
            "hold_base": 75,
            "flight_base": 80,
            "wpm_base": 85,
            "err_base": 0.07,
        },
        "slow_precise": {
            "hold_base": 130,
            "flight_base": 160,
            "wpm_base": 40,
            "err_base": 0.015,
        },
        "variable": {
            "hold_base": 100,
            "flight_base": 130,
            "wpm_base": 55,
            "err_base": 0.07,
        },
        "slow_uncertain": {
            "hold_base": 140,
            "flight_base": 180,
            "wpm_base": 35,
            "err_base": 0.10,
        },
        "fast_rhythmic": {
            "hold_base": 82,
            "flight_base": 95,
            "wpm_base": 72,
            "err_base": 0.04,
        },
        "medium_burst": {
            "hold_base": 95,
            "flight_base": 115,
            "wpm_base": 62,
            "err_base": 0.05,
        },
        "fast_long_bursts": {
            "hold_base": 90,
            "flight_base": 100,
            "wpm_base": 70,
            "err_base": 0.035,
        },
        "medium_flowing": {
            "hold_base": 105,
            "flight_base": 125,
            "wpm_base": 58,
            "err_base": 0.04,
        },
        "variable_learning": {
            "hold_base": 110,
            "flight_base": 140,
            "wpm_base": 50,
            "err_base": 0.08,
        },
        "fast_organized": {
            "hold_base": 87,
            "flight_base": 102,
            "wpm_base": 73,
            "err_base": 0.03,
        },
        "slow_thoughtful": {
            "hold_base": 115,
            "flight_base": 145,
            "wpm_base": 48,
            "err_base": 0.035,
        },
        "fast_repetitive": {
            "hold_base": 78,
            "flight_base": 85,
            "wpm_base": 82,
            "err_base": 0.06,
        },
    }

    profile = style_profiles.get(style, style_profiles["medium_consistent"])

    # Add per-user noise (±15%)
    noise = lambda base: base * (1 + rng.normal(0, 0.15))

    switch_map = {"very_low": 1.5, "low": 3, "medium": 6, "high": 10, "very_high": 15}

    return {
        "user_idx": persona_idx,
        "name": name,
        "hold_base": max(50, noise(profile["hold_base"])),
        "flight_base": max(30, noise(profile["flight_base"])),
        "wpm_base": max(20, min(100, noise(profile["wpm_base"]))),
        "err_base": max(0.005, min(0.3, noise(profile["err_base"]))),
        "switch_base": max(0.5, noise(switch_map.get(switch_tend, 5))),
        "peak_hours": peaks,
        "stress_response": STRESS_RESPONSES.get(
            response, STRESS_RESPONSES["slight_slow"]
        ),
        "rng": rng,
    }


def generate_user_windows(
    user_baseline: dict,
    n_windows: int = 150,
    stress_ratio: Tuple[float, float, float] = (0.50, 0.30, 0.20),
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Generate feature windows for one simulated user.

    Returns:
        X: [n_windows, 23] features
        y: [n_windows] labels
        user_ids: list of user name strings
    """
    rng = user_baseline["rng"]
    b = user_baseline
    resp = b["stress_response"]

    # Class distribution
    n_neutral = int(n_windows * stress_ratio[0])
    n_mild = int(n_windows * stress_ratio[1])
    n_stressed = n_windows - n_neutral - n_mild
    labels = np.array([0] * n_neutral + [1] * n_mild + [2] * n_stressed, dtype=np.int32)

    X = np.zeros((n_windows, NUM_RAW_FEATURES), dtype=np.float32)

    for i in range(n_windows):
        label = labels[i]
        hour = (
            int(rng.choice(b["peak_hours"]))
            if rng.random() < 0.7
            else int(rng.integers(8, 23))
        )
        is_peak = hour in b["peak_hours"]

        # Stress multipliers based on label
        if label == 0:  # NEUTRAL
            h_mult, f_mult, w_mult, e_mult, s_mult = 1.0, 1.0, 1.0, 1.0, 1.0
        elif label == 1:  # MILD (half effect)
            h_mult = 1 + (resp["hold_mult"] - 1) * 0.5
            f_mult = 1 + (resp["flight_mult"] - 1) * 0.5
            w_mult = 1 + (resp["wpm_mult"] - 1) * 0.5
            e_mult = 1 + (resp["err_mult"] - 1) * 0.5
            s_mult = 1 + (resp["switch_mult"] - 1) * 0.5
        else:  # STRESSED
            h_mult = resp["hold_mult"]
            f_mult = resp["flight_mult"]
            w_mult = resp["wpm_mult"]
            e_mult = resp["err_mult"]
            s_mult = resp["switch_mult"]

        # Circadian adjustment (slower at night)
        circadian = 1.0 + 0.1 * (1 if not is_peak else 0)

        hold_mean = rng.normal(
            b["hold_base"] * h_mult * circadian, b["hold_base"] * 0.2
        )
        hold_std = rng.normal(abs(hold_mean) * 0.25, abs(hold_mean) * 0.05)
        hold_median = hold_mean * rng.normal(0.95, 0.05)

        flight_mean = rng.normal(
            b["flight_base"] * f_mult * circadian, b["flight_base"] * 0.3
        )
        flight_std = rng.normal(abs(flight_mean) * 0.3, abs(flight_mean) * 0.08)

        wpm = rng.normal(b["wpm_base"] * w_mult / circadian, b["wpm_base"] * 0.15)
        err = rng.normal(b["err_base"] * e_mult, b["err_base"] * 0.3)

        pause_freq = rng.normal(2 + label * 3 + (1 if not is_peak else 0), 1.5)
        pause_dur = rng.normal(3000 - label * 400, 600)
        burst_len = rng.normal(25 - label * 8, 6)
        rhythm_ent = rng.normal(2.0 + label * 1.1, 0.5)

        # Mouse features (also affected by stress)
        mouse_speed = rng.normal(300 + label * 150, 80 + label * 40)
        mouse_std = rng.normal(100 + label * 90, 30 + label * 20)
        dir_change = rng.normal(0.3 + label * 0.2, 0.1)
        click_count = rng.normal(15 + label * 7, 5 + label * 2)
        rage_clicks = max(0, rng.normal(label * 1.5, label * 0.8 + 0.3))
        scroll_std = rng.normal(5 + label * 8, 2 + label * 2)

        # Context switching
        tab_freq = rng.normal(b["switch_base"] * s_mult, b["switch_base"] * 0.4)
        switch_ent = rng.normal(1.0 + label * 0.75, 0.3)
        frag = rng.normal(0.3 + label * 0.3, 0.1)

        session_dur = rng.normal(45 + label * 15, 20)

        X[i] = [
            max(10, hold_mean),
            max(5, hold_std),
            max(10, hold_median),
            max(10, flight_mean),
            max(5, flight_std),
            max(10, min(120, wpm)),
            max(0, min(0.5, err)),
            max(0, pause_freq),
            max(0, pause_dur),
            max(1, burst_len),
            max(0.5, rhythm_ent),
            max(50, mouse_speed),
            max(10, mouse_std),
            max(0, min(1, dir_change)),
            max(0, click_count),
            max(0, rage_clicks),
            max(1, scroll_std),
            max(0, tab_freq),
            max(0.2, switch_ent),
            max(0, min(1.5, frag)),
            hour,
            rng.integers(0, 7),
            max(5, session_dur),
        ]

    # Shuffle
    perm = rng.permutation(n_windows)
    X = X[perm]
    labels = labels[perm]

    return X, labels, [b["name"]] * n_windows


def generate_multi_user_dataset(
    n_users: int = 18,
    windows_per_user: int = 150,
    seed: int = 42,
    output_csv: str = "synthetic_multi_user.csv",
) -> pd.DataFrame:
    """
    Generate a multi-user synthetic dataset with 15-20 distinct personas.
    """
    rng = np.random.default_rng(seed)

    all_X = []
    all_y = []
    all_users = []

    n_personas = min(n_users, len(PERSONAS))

    print(f"Generating {n_personas} synthetic users...")
    print(f"{'Name':<20} {'Style':<20} {'Response':<20} {'Windows':>8}")
    print(f"{'-' * 20} {'-' * 20} {'-' * 20} {'-' * 8}")

    for idx in range(n_personas):
        baseline = generate_user_baseline(idx, rng)
        X, y, user_ids = generate_user_windows(baseline, n_windows=windows_per_user)
        all_X.append(X)
        all_y.append(y)
        all_users.extend(user_ids)

        name, style, response, _, _ = PERSONAS[idx]
        dist = f"N={np.sum(y == 0)} M={np.sum(y == 1)} S={np.sum(y == 2)}"
        print(f"{name:<20} {style:<20} {response:<20} {dist:>8}")

    X_all = np.vstack(all_X)
    y_all = np.concatenate(all_y)

    # Build DataFrame
    df = pd.DataFrame(X_all, columns=pd.Index(FEATURE_NAMES))
    df["stress_label"] = y_all
    df["stress_level"] = df["stress_label"].map(
        {0: "NEUTRAL", 1: "MILD", 2: "STRESSED"}
    )
    df["user_id"] = all_users

    # Save
    df.to_csv(output_csv, index=False)

    print(f"\n{'=' * 60}")
    print(f"MULTI-USER SYNTHETIC DATASET")
    print(f"{'=' * 60}")
    print(f"Users: {n_personas}")
    print(f"Total samples: {len(df)}")
    print(f"Label distribution:")
    for label, name in {0: "NEUTRAL", 1: "MILD", 2: "STRESSED"}.items():
        count = (df["stress_label"] == label).sum()
        pct = count / len(df) * 100
        print(f"  {name:>10}: {count:>5} ({pct:.1f}%)")
    print(f"\nSaved to: {output_csv}")

    return df


if __name__ == "__main__":
    df = generate_multi_user_dataset(
        n_users=18,
        windows_per_user=150,
        seed=42,
        output_csv="synthetic_multi_user.csv",
    )
