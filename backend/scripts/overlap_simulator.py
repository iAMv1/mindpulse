"""
MindPulse — Realistic Overlapping Stress Simulator
====================================================
KEY INSIGHT: In real data, stress classes OVERLAP heavily.
A stressed person's typing speed might be 45 WPM, but a relaxed
person might also type 45 WPM on a lazy afternoon.

The ONLY way to detect stress is DEVIATION FROM YOUR OWN BASELINE,
not absolute feature values.

This simulator creates realistic overlap:
- 60-70% of feature space is shared between classes
- Stress manifests as subtle shifts, not dramatic changes
- Individual baselines differ more than stress effects
"""

from __future__ import annotations
import os
import sys

# Add parent directories to path for ml package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from typing import Tuple
from app.ml.feature_extractor import FEATURE_NAMES, NUM_RAW_FEATURES


def generate_realistic_user(
    user_id: str,
    n_samples: int = 200,
    rng: np.random.Generator = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate one user's data with HEAVY class overlap.

    Key design: Each user has a personal baseline. Stress causes
    subtle deviations (~10-20%) from that baseline, NOT dramatic changes.
    The deviation is smaller than the natural variation within each class.
    """
    if rng is None:
        rng = np.random.default_rng(hash(user_id) % 2**31)

    # Personal baseline (unique per user, varies ±30% from population mean)
    baseline = {
        "hold_mean": rng.normal(100, 30),  # 70-130ms typical
        "hold_std": rng.normal(25, 8),
        "hold_median": rng.normal(95, 28),
        "flight_mean": rng.normal(130, 40),  # 90-170ms typical
        "flight_std": rng.normal(40, 15),
        "wpm": rng.normal(60, 15),  # 45-75 WPM typical
        "err_rate": rng.normal(0.05, 0.02),  # 0.03-0.07
        "pause_freq": rng.normal(3, 1.5),
        "pause_dur": rng.normal(3000, 800),
        "burst_len": rng.normal(20, 6),
        "rhythm_ent": rng.normal(2.5, 0.6),
        "mouse_speed": rng.normal(350, 100),
        "mouse_std": rng.normal(120, 40),
        "dir_change": rng.normal(0.35, 0.1),
        "click_count": rng.normal(18, 6),
        "rage_clicks": rng.normal(0.5, 0.4),
        "scroll_std": rng.normal(8, 3),
        "tab_freq": rng.normal(5, 2.5),
        "switch_ent": rng.normal(1.5, 0.5),
        "frag": rng.normal(0.4, 0.15),
    }

    # Class distribution
    n_neutral = int(n_samples * 0.45)
    n_mild = int(n_samples * 0.30)
    n_stressed = n_samples - n_neutral - n_mild
    labels = np.array([0] * n_neutral + [1] * n_mild + [2] * n_stressed, dtype=np.int32)
    rng.shuffle(labels)

    X = np.zeros((n_samples, NUM_RAW_FEATURES), dtype=np.float32)

    for i in range(n_samples):
        label = labels[i]

        # Stress effect: only 10-20% shift from baseline
        # This is MUCH smaller than natural variation (30%+)
        if label == 0:  # NEUTRAL
            stress_mult = rng.normal(1.0, 0.08)  # ±8% natural variation
        elif label == 1:  # MILD
            stress_mult = rng.normal(1.08, 0.10)  # +8% shift, ±10% noise
        else:  # STRESSED
            stress_mult = rng.normal(1.15, 0.12)  # +15% shift, ±12% noise

        # Generate features with heavy overlap
        # Each feature gets: baseline * stress_mult * feature_noise
        noise = lambda scale=0.15: rng.normal(1.0, scale)

        hour = rng.choice([9, 10, 11, 14, 15, 16])
        circadian = 1.0 + rng.normal(0, 0.05)  # Small circadian effect

        hold_m = max(10, baseline["hold_mean"] * stress_mult * circadian * noise(0.2))
        hold_s = max(5, baseline["hold_std"] * noise(0.25))
        hold_md = max(10, baseline["hold_median"] * stress_mult * noise(0.18))

        # Stress INCREASES flight time variance more than mean
        flight_m = max(
            10, baseline["flight_mean"] * (1 + (stress_mult - 1) * 0.5) * noise(0.2)
        )
        flight_s = max(
            5, baseline["flight_std"] * (1 + (stress_mult - 1) * 1.5) * noise(0.3)
        )

        # Stress DECREASES WPM slightly
        wpm = max(
            10, min(120, baseline["wpm"] / (1 + (stress_mult - 1) * 0.3) * noise(0.15))
        )

        # Stress INCREASES error rate
        err = max(
            0, min(0.5, baseline["err_rate"] * (1 + (stress_mult - 1) * 2) * noise(0.3))
        )

        pause_f = max(0, baseline["pause_freq"] * stress_mult * noise(0.3))
        pause_d = max(0, baseline["pause_dur"] * (2 - stress_mult) * noise(0.25))
        burst_l = max(1, baseline["burst_len"] / stress_mult * noise(0.2))
        rhythm_e = max(0.5, baseline["rhythm_ent"] * stress_mult * noise(0.2))

        mouse_s = max(
            50, baseline["mouse_speed"] * (1 + (stress_mult - 1) * 0.5) * noise(0.2)
        )
        mouse_s_std = max(10, baseline["mouse_std"] * stress_mult * noise(0.25))
        dir_c = max(0, min(1, baseline["dir_change"] * stress_mult * noise(0.2)))
        click_c = max(0, baseline["click_count"] * stress_mult * noise(0.25))
        rage_c = max(
            0, baseline["rage_clicks"] * (1 + (stress_mult - 1) * 3) * noise(0.4)
        )
        scroll_s = max(1, baseline["scroll_std"] * stress_mult * noise(0.3))

        tab_f = max(0, baseline["tab_freq"] * stress_mult * noise(0.25))
        switch_e = max(0.2, baseline["switch_ent"] * stress_mult * noise(0.2))
        frag_v = max(0, min(1.5, baseline["frag"] * stress_mult * noise(0.2)))

        session_dur = max(5, rng.normal(45 + label * 10, 20))

        X[i] = [
            hold_m,
            hold_s,
            hold_md,
            flight_m,
            flight_s,
            wpm,
            err,
            pause_f,
            pause_d,
            burst_l,
            rhythm_e,
            mouse_s,
            mouse_s_std,
            dir_c,
            click_c,
            rage_c,
            scroll_s,
            tab_f,
            switch_e,
            frag_v,
            hour,
            rng.integers(0, 7),
            session_dur,
        ]

    perm = rng.permutation(n_samples)
    return X[perm], labels[perm]


def generate_dataset(
    n_users: int = 18,
    n_per_user: int = 200,
    seed: int = 42,
    output: str = "overlap_dataset.csv",
) -> pd.DataFrame:
    """Generate multi-user dataset with realistic class overlap."""
    rng = np.random.default_rng(seed)

    all_X, all_y, all_users = [], [], []

    user_names = [
        "alex_dev",
        "benji_support",
        "charlie_mgr",
        "diana_design",
        "ethan_junior",
        "fiona_senior",
        "george_sales",
        "hana_writer",
        "ivan_intern",
        "julia_qa",
        "kevin_ops",
        "lisa_hr",
        "marcus_data",
        "nadia_mkt",
        "oscar_student",
        "priya_lead",
        "quinn_freelance",
        "rosa_cs",
    ]

    print(f"Generating {n_users} users with OVERLAPPING stress classes...")
    print(f"{'User':<18} {'N':>4} {'M':>4} {'S':>4} {'Overlap':>8}")
    print(f"{'-' * 18} {'-' * 4} {'-' * 4} {'-' * 4} {'-' * 8}")

    for i in range(min(n_users, len(user_names))):
        uid = user_names[i]
        X, y = generate_realistic_user(uid, n_per_user, rng)
        all_X.append(X)
        all_y.append(y)
        all_users.extend([uid] * n_per_user)

        # Measure overlap: how well can a simple classifier separate classes?
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.model_selection import cross_val_score

        lda = LinearDiscriminantAnalysis()
        scores = cross_val_score(lda, X, y, cv=3, scoring="f1_macro")

        print(
            f"{uid:<18} {np.sum(y == 0):>4} {np.sum(y == 1):>4} {np.sum(y == 2):>4} {scores.mean() * 100:>7.1f}%"
        )

    X_all = np.vstack(all_X)
    y_all = np.concatenate(all_y)

    df = pd.DataFrame(X_all, columns=pd.Index(FEATURE_NAMES))
    df["stress_label"] = y_all
    df["stress_level"] = df["stress_label"].map(
        {0: "NEUTRAL", 1: "MILD", 2: "STRESSED"}
    )
    df["user_id"] = all_users
    df.to_csv(output, index=False)

    # Global overlap measurement
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import cross_val_score

    lda = LinearDiscriminantAnalysis()
    global_scores = cross_val_score(lda, X_all, y_all, cv=5, scoring="f1_macro")

    print(f"\n{'=' * 50}")
    print(f"DATASET SUMMARY (with class overlap)")
    print(f"{'=' * 50}")
    print(f"Users: {n_users}")
    print(f"Total samples: {len(df)}")
    print(
        f"Label distribution: N={np.sum(y_all == 0)} M={np.sum(y_all == 1)} S={np.sum(y_all == 2)}"
    )
    print(
        f"Global LDA F1 (5-fold): {global_scores.mean():.3f} ± {global_scores.std():.3f}"
    )
    print(f"This shows classes overlap — LDA can't cleanly separate them")
    print(f"Saved to: {output}")

    return df


if __name__ == "__main__":
    df = generate_dataset(
        n_users=18, n_per_user=200, seed=42, output="overlap_dataset.csv"
    )
