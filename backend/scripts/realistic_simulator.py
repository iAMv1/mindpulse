"""
MindPulse — Realistic Human Behavior Simulator
=================================================
Simulates 15-20 users with MESSY, REALISTIC human behavior.

Key design principles (research-backed from ETH Zurich, Pepa et al.):
  1. NO clean class boundaries — stressed people sometimes type calmly
  2. Self-report noise — people mislabel their stress ~15-20% of the time
  3. Circadian drift — same person behaves differently at 9am vs 2pm vs 8pm
  4. Day-to-day variability — Monday person ≠ Friday person
  5. Individual quirks — unique "fingerprints" per person
  6. Session fatigue — typing degrades over long sessions
  7. Micro-interruptions — thinking pauses, phone checks
  8. Gradual mood transitions — stress doesn't flip instantly
  9. Context effects — meeting → worse typing for 20 min
  10. Skill differences — senior dev vs junior vs manager
"""

from __future__ import annotations

import os
import sys

# Add parent directories to path for ml package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

from app.ml.feature_extractor import FEATURE_NAMES, NUM_RAW_FEATURES


# ────────────────────────────────────────────────────────────────
# User Profile
# ────────────────────────────────────────────────────────────────


@dataclass
class UserProfile:
    name: str
    role: str  # developer, manager, designer, support, student

    # Typing baseline (neutral state)
    hold_base: float = 95.0  # ms
    hold_var: float = 25.0  # daily variation
    flight_base: float = 120.0
    flight_var: float = 35.0
    wpm_base: float = 60.0
    wpm_var: float = 12.0
    err_base: float = 0.05
    err_var: float = 0.02

    # Mouse baseline
    mouse_speed_base: float = 300.0
    mouse_speed_var: float = 80.0
    click_base: float = 15.0

    # Context switching
    switch_base: float = 5.0
    switch_var: float = 3.0

    # Behavioral quirks
    backspace_heavy: bool = False  # Always corrects a lot
    bursty_typer: bool = False  # Types in bursts, then pauses
    perfectionist: bool = False  # Slow but accurate
    multitasker: bool = False  # Switches apps constantly
    night_owl: bool = False  # Better at night
    morning_person: bool = False  # Better in morning
    stress_hider: bool = False  # Types normally when stressed (hides it)
    stress_amplifier: bool = False  # Types much worse when stressed

    # Circadian pattern
    peak_hours: List[int] = field(default_factory=lambda: [9, 10, 11])
    trough_hours: List[int] = field(default_factory=lambda: [14, 15])

    # Stress response magnitudes
    stress_hold_mult: float = 1.2  # How much hold time increases under stress
    stress_flight_mult: float = 1.3
    stress_wpm_mult: float = 0.8
    stress_err_mult: float = 1.5
    stress_switch_mult: float = 1.3
    stress_rage_mult: float = 2.0

    # Self-report reliability (how accurately they report stress)
    report_accuracy: float = 0.80  # 80% accurate

    # Session-to-session variability
    day_drift: float = 0.15  # 15% variation day to day


# ────────────────────────────────────────────────────────────────
# Realistic User Profiles
# ────────────────────────────────────────────────────────────────

PROFILES = [
    UserProfile(
        name="alex_dev",
        role="developer",
        hold_base=80,
        flight_base=95,
        wpm_base=78,
        err_base=0.03,
        backspace_heavy=True,
        bursty_typer=True,
        peak_hours=[10, 11, 14],
        stress_hider=True,
        stress_hold_mult=1.1,
        stress_wpm_mult=0.9,
        report_accuracy=0.75,  # Hides stress, under-reports
    ),
    UserProfile(
        name="benji_support",
        role="support",
        hold_base=90,
        flight_base=110,
        wpm_base=65,
        err_base=0.06,
        multitasker=True,
        stress_amplifier=True,
        switch_base=12,
        stress_switch_mult=2.5,
        peak_hours=[9, 10, 11],
        stress_hold_mult=1.4,
        report_accuracy=0.85,
    ),
    UserProfile(
        name="charlie_manager",
        role="manager",
        hold_base=100,
        flight_base=130,
        wpm_base=55,
        err_base=0.04,
        bursty_typer=True,
        switch_base=8,
        peak_hours=[9, 10, 14, 15],
        night_owl=True,
        stress_hold_mult=1.25,
        report_accuracy=0.70,
    ),
    UserProfile(
        name="diana_designer",
        role="designer",
        hold_base=110,
        flight_base=140,
        wpm_base=48,
        err_base=0.03,
        perfectionist=True,
        peak_hours=[14, 15, 16],
        night_owl=True,
        stress_hold_mult=1.15,
        stress_wpm_mult=0.85,
        report_accuracy=0.90,  # Very self-aware
    ),
    UserProfile(
        name="ethan_junior",
        role="junior_dev",
        hold_base=130,
        flight_base=170,
        wpm_base=40,
        err_base=0.10,
        backspace_heavy=True,
        stress_amplifier=True,
        peak_hours=[10, 11],
        trough_hours=[14, 15, 16],
        stress_hold_mult=1.5,
        stress_err_mult=2.5,
        report_accuracy=0.65,  # Doesn't always realize when stressed
    ),
    UserProfile(
        name="fiona_senior",
        role="senior_dev",
        hold_base=75,
        flight_base=85,
        wpm_base=85,
        err_base=0.02,
        perfectionist=True,
        stress_hider=True,
        peak_hours=[9, 10, 11, 14],
        stress_hold_mult=1.05,
        stress_wpm_mult=0.95,
        report_accuracy=0.80,
    ),
    UserProfile(
        name="george_sales",
        role="sales",
        hold_base=85,
        flight_base=100,
        wpm_base=72,
        err_base=0.07,
        multitasker=True,
        bursty_typer=True,
        switch_base=15,
        stress_switch_mult=2.0,
        peak_hours=[10, 11, 14, 15],
        stress_hold_mult=1.3,
        report_accuracy=0.72,
    ),
    UserProfile(
        name="hana_writer",
        role="writer",
        hold_base=105,
        flight_base=125,
        wpm_base=58,
        err_base=0.02,
        perfectionist=True,
        peak_hours=[14, 15, 16, 17],
        night_owl=True,
        stress_hold_mult=1.2,
        stress_wpm_mult=0.7,
        report_accuracy=0.88,
    ),
    UserProfile(
        name="ivan_intern",
        role="intern",
        hold_base=140,
        flight_base=180,
        wpm_base=35,
        err_base=0.12,
        backspace_heavy=True,
        stress_amplifier=True,
        peak_hours=[11, 14],
        stress_hold_mult=1.6,
        stress_err_mult=3.0,
        report_accuracy=0.60,  # Very unreliable self-report
        day_drift=0.25,  # Highly variable day to day
    ),
    UserProfile(
        name="julia_qa",
        role="qa_engineer",
        hold_base=95,
        flight_base=115,
        wpm_base=62,
        err_base=0.04,
        backspace_heavy=True,
        perfectionist=True,
        peak_hours=[10, 11, 14],
        stress_hold_mult=1.2,
        stress_err_mult=1.8,
        report_accuracy=0.82,
    ),
    UserProfile(
        name="kevin_ops",
        role="devops",
        hold_base=88,
        flight_base=105,
        wpm_base=70,
        err_base=0.05,
        multitasker=True,
        bursty_typer=True,
        switch_base=10,
        peak_hours=[9, 10, 14, 15],
        stress_hold_mult=1.3,
        stress_switch_mult=1.8,
        report_accuracy=0.78,
    ),
    UserProfile(
        name="lisa_hr",
        role="hr",
        hold_base=100,
        flight_base=130,
        wpm_base=55,
        err_base=0.05,
        morning_person=True,
        peak_hours=[9, 10, 11],
        trough_hours=[14, 15, 16],
        stress_hold_mult=1.25,
        report_accuracy=0.85,
    ),
    UserProfile(
        name="marcus_data",
        role="data_scientist",
        hold_base=90,
        flight_base=110,
        wpm_base=68,
        err_base=0.04,
        bursty_typer=True,
        night_owl=True,
        peak_hours=[15, 16, 17],
        trough_hours=[9, 10],
        stress_hold_mult=1.2,
        report_accuracy=0.80,
    ),
    UserProfile(
        name="nadia_marketing",
        role="marketing",
        hold_base=95,
        flight_base=120,
        wpm_base=60,
        err_base=0.06,
        multitasker=True,
        morning_person=True,
        switch_base=8,
        peak_hours=[9, 10, 11],
        stress_hold_mult=1.3,
        stress_switch_mult=2.0,
        report_accuracy=0.75,
    ),
    UserProfile(
        name="oscar_student",
        role="student",
        hold_base=120,
        flight_base=150,
        wpm_base=45,
        err_base=0.08,
        backspace_heavy=True,
        night_owl=True,
        peak_hours=[15, 16, 17, 20, 21],
        trough_hours=[9, 10, 11],
        stress_hold_mult=1.4,
        stress_err_mult=2.0,
        report_accuracy=0.65,
        day_drift=0.20,
    ),
    UserProfile(
        name="priya_lead",
        role="tech_lead",
        hold_base=82,
        flight_base=98,
        wpm_base=75,
        err_base=0.03,
        stress_hider=True,
        multitasker=True,
        switch_base=7,
        peak_hours=[10, 11, 14],
        stress_hold_mult=1.1,
        stress_wpm_mult=0.9,
        report_accuracy=0.72,
    ),
    UserProfile(
        name="quinn_freelance",
        role="freelancer",
        hold_base=100,
        flight_base=130,
        wpm_base=55,
        err_base=0.05,
        night_owl=True,
        bursty_typer=True,
        peak_hours=[14, 15, 16, 17, 20],
        stress_hold_mult=1.3,
        report_accuracy=0.80,
        day_drift=0.22,  # Very variable schedule
    ),
    UserProfile(
        name="rosa_customer",
        role="customer_success",
        hold_base=90,
        flight_base=110,
        wpm_base=65,
        err_base=0.05,
        multitasker=True,
        stress_amplifier=True,
        switch_base=12,
        peak_hours=[9, 10, 11, 14],
        stress_hold_mult=1.35,
        stress_switch_mult=2.2,
        report_accuracy=0.78,
    ),
]


# ────────────────────────────────────────────────────────────────
# Human-like noise generators
# ────────────────────────────────────────────────────────────────


def _circadian_modifier(
    hour: int, profile: UserProfile, rng: np.random.Generator
) -> float:
    """Returns a multiplier based on circadian rhythm. Not perfect — has noise."""
    if hour in profile.peak_hours:
        base = 1.0
    elif hour in profile.trough_hours:
        base = 0.85
    elif 0 <= hour < 6:
        base = 0.7
    else:
        base = 0.95

    # Add noise — sometimes you're alert at weird times
    noise = rng.normal(0, 0.05)
    return max(0.6, min(1.1, base + noise))


def _day_drift(profile: UserProfile, rng: np.random.Generator) -> Dict[str, float]:
    """Simulate day-to-day variation. Some days you're just 'off'."""
    drift = profile.day_drift
    return {
        "hold": rng.normal(1.0, drift),
        "flight": rng.normal(1.0, drift),
        "wpm": rng.normal(1.0, drift),
        "err": rng.normal(1.0, drift * 1.5),
        "mouse": rng.normal(1.0, drift),
        "switch": rng.normal(1.0, drift),
    }


def _mood_transition(
    current_stress: int, target_stress: int, rng: np.random.Generator
) -> int:
    """
    Stress transitions aren't instant. You don't go from NEUTRAL to STRESSED in 1 minute.
    Gradual transitions with occasional sudden jumps (panic moments).
    """
    diff = target_stress - current_stress
    if diff == 0:
        return current_stress

    # 70% chance of moving one step toward target
    # 15% chance of staying (sticky)
    # 10% chance of jumping directly (sudden stressor)
    # 5% chance of going opposite (relief moment)
    r = rng.random()
    if r < 0.15:
        return current_stress  # Sticky
    elif r < 0.25:
        return target_stress  # Sudden jump
    elif r < 0.30:
        return max(0, current_stress - 1)  # Relief
    else:
        # Gradual
        step = 1 if diff > 0 else -1
        return max(0, min(2, current_stress + step))


def _generate_quirk_noise(
    profile: UserProfile, rng: np.random.Generator
) -> Dict[str, float]:
    """Generate per-user quirk-based noise."""
    noise = {}

    if profile.backspace_heavy:
        noise["err_mult"] = rng.uniform(1.3, 2.0)
    else:
        noise["err_mult"] = 1.0

    if profile.bursty_typer:
        noise["pause_mult"] = rng.uniform(1.5, 3.0)
        noise["burst_mult"] = rng.uniform(0.5, 0.8)
    else:
        noise["pause_mult"] = 1.0
        noise["burst_mult"] = 1.0

    if profile.multitasker:
        noise["switch_mult"] = rng.uniform(1.3, 2.0)
    else:
        noise["switch_mult"] = 1.0

    if profile.perfectionist:
        noise["err_mult"] *= 0.5
        noise["hold_mult"] = rng.uniform(1.1, 1.3)
    else:
        noise["hold_mult"] = 1.0

    return noise


# ────────────────────────────────────────────────────────────────
# Main simulation
# ────────────────────────────────────────────────────────────────


def simulate_user(
    profile: UserProfile,
    n_windows: int = 200,
    stress_ratio: Tuple[float, float, float] = (0.45, 0.30, 0.25),
    seed: int = None,
) -> Tuple[np.ndarray, np.ndarray, List[str], np.ndarray]:
    """
    Simulate realistic user behavior with:
    - Gradual mood transitions
    - Self-report noise
    - Circadian drift
    - Day-to-day variation
    - Individual quirks
    - Micro-interruptions
    - Session fatigue

    Returns:
        X: [n_windows, 23] features
        y_true: [n_windows] actual stress
        y_reported: [n_windows] self-reported stress (noisy)
        hours: [n_windows] hour of day
    """
    if seed is None:
        seed = hash(profile.name) % 2**31
    rng = np.random.default_rng(seed)

    # Day drift
    day = _day_drift(profile, rng)
    quirks = _generate_quirk_noise(profile, rng)

    # Generate target stress distribution
    n_neutral = int(n_windows * stress_ratio[0])
    n_mild = int(n_windows * stress_ratio[1])
    n_stressed = n_windows - n_neutral - n_mild

    # Create base stress labels with gradual transitions
    target_stress = np.concatenate(
        [
            np.zeros(n_neutral, dtype=np.int32),
            np.ones(n_mild, dtype=np.int32),
            np.full(n_stressed, 2, dtype=np.int32),
        ]
    )
    rng.shuffle(target_stress)

    # Apply gradual mood transitions
    actual_stress = np.zeros(n_windows, dtype=np.int32)
    actual_stress[0] = target_stress[0]
    for i in range(1, n_windows):
        actual_stress[i] = _mood_transition(actual_stress[i - 1], target_stress[i], rng)

    # Generate hours with realistic work patterns
    if profile.night_owl:
        hours = rng.choice([14, 15, 16, 17, 18, 19, 20, 21], size=n_windows)
    elif profile.morning_person:
        hours = rng.choice([8, 9, 10, 11, 12], size=n_windows)
    else:
        hours = rng.choice([9, 10, 11, 14, 15, 16], size=n_windows)

    # Generate features for each window
    X = np.zeros((n_windows, NUM_RAW_FEATURES), dtype=np.float32)

    for i in range(n_windows):
        label = actual_stress[i]
        hour = int(hours[i])
        circadian = _circadian_modifier(hour, profile, rng)

        # Stress multipliers (with quirk modifications)
        if label == 0:
            s_hold, s_flight, s_wpm, s_err, s_switch, s_rage = (
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            )
        elif label == 1:
            s_hold = 1 + (profile.stress_hold_mult - 1) * 0.5
            s_flight = 1 + (profile.stress_flight_mult - 1) * 0.5
            s_wpm = 1 + (profile.stress_wpm_mult - 1) * 0.5
            s_err = 1 + (profile.stress_err_mult - 1) * 0.5
            s_switch = 1 + (profile.stress_switch_mult - 1) * 0.5
            s_rage = 1 + (profile.stress_rage_mult - 1) * 0.5
        else:
            s_hold = profile.stress_hold_mult
            s_flight = profile.stress_flight_mult
            s_wpm = profile.stress_wpm_mult
            s_err = profile.stress_err_mult
            s_switch = profile.stress_switch_mult
            s_rage = profile.stress_rage_mult

        # Apply day drift, circadian, quirks
        hold_mean = rng.normal(
            profile.hold_base * day["hold"] * circadian * s_hold * quirks["hold_mult"],
            profile.hold_var * (1 + label * 0.3),
        )
        hold_std = rng.normal(abs(hold_mean) * 0.25, abs(hold_mean) * 0.08)
        hold_median = hold_mean * rng.normal(0.95, 0.06)

        flight_mean = rng.normal(
            profile.flight_base * day["flight"] * circadian * s_flight,
            profile.flight_var * (1 + label * 0.4),
        )
        flight_std = rng.normal(abs(flight_mean) * 0.3, abs(flight_mean) * 0.1)

        wpm = rng.normal(
            profile.wpm_base * day["wpm"] * s_wpm / circadian,
            profile.wpm_var * (1 + label * 0.2),
        )

        err = rng.normal(
            profile.err_base * day["err"] * s_err * quirks["err_mult"],
            profile.err_var * (1 + label * 0.5),
        )

        # Session fatigue (later in day = more tired)
        fatigue_factor = 1.0 + max(0, (hour - 12)) * 0.02
        pause_freq = rng.normal(
            (2 + label * 3) * quirks["pause_mult"] * fatigue_factor,
            1.5 + label,
        )
        pause_dur = rng.normal(3000 - label * 500, 800) * fatigue_factor
        burst_len = rng.normal(
            (25 - label * 8) * quirks["burst_mult"],
            6 + label * 2,
        )
        rhythm_ent = rng.normal(2.0 + label * 1.2, 0.6)

        # Mouse (stress → faster, less precise movements)
        mouse_speed = rng.normal(
            profile.mouse_speed_base * day["mouse"] + label * 150,
            profile.mouse_speed_var + label * 50,
        )
        mouse_std = rng.normal(100 + label * 90, 35 + label * 25)
        dir_change = rng.normal(0.3 + label * 0.2, 0.12)
        click_count = rng.normal(
            profile.click_base + label * 7,
            5 + label * 3,
        )
        rage_clicks = max(
            0,
            rng.normal(
                label * 1.5 * quirks.get("switch_mult", 1.0),
                label * 0.8 + 0.3,
            ),
        )
        scroll_std = rng.normal(5 + label * 8, 3 + label * 2)

        # Context switching (with multitasker quirk)
        tab_freq = rng.normal(
            profile.switch_base * day["switch"] * s_switch * quirks["switch_mult"],
            profile.switch_var,
        )
        switch_ent = rng.normal(1.0 + label * 0.75, 0.35)
        frag = rng.normal(0.3 + label * 0.3, 0.12)

        session_dur = rng.normal(45 + label * 15, 25)

        # Micro-interruptions (random spikes in pause/burst)
        if rng.random() < 0.05:  # 5% chance of micro-interruption
            pause_freq *= rng.uniform(2, 4)
            pause_dur *= rng.uniform(1.5, 3)
            burst_len *= rng.uniform(0.3, 0.6)

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

    # Generate noisy self-reports (people misreport ~15-20% of the time)
    y_reported = actual_stress.copy()
    n_misreport = int(n_windows * (1 - profile.report_accuracy))
    misreport_idx = rng.choice(n_windows, size=n_misreport, replace=False)
    for idx in misreport_idx:
        true_label = actual_stress[idx]
        # People tend to under-report stress
        if true_label == 2:
            y_reported[idx] = rng.choice([0, 1], p=[0.3, 0.7])
        elif true_label == 1:
            y_reported[idx] = rng.choice([0, 2], p=[0.6, 0.4])
        else:
            y_reported[idx] = rng.choice([1, 2], p=[0.7, 0.3])

    # Shuffle windows (time order preserved in hours)
    perm = rng.permutation(n_windows)
    X = X[perm]
    actual_stress = actual_stress[perm]
    y_reported = y_reported[perm]
    hours = hours[perm]

    return X, actual_stress, y_reported, list(hours)


def generate_realistic_dataset(
    n_users: int = 18,
    windows_per_user: int = 200,
    seed: int = 42,
    output_csv: str = "realistic_dataset.csv",
) -> pd.DataFrame:
    """Generate a realistic multi-user dataset with all the human messiness."""
    rng = np.random.default_rng(seed)
    n_profiles = min(n_users, len(PROFILES))

    all_X, all_true, all_reported, all_users, all_hours = [], [], [], [], []

    print(f"{'=' * 70}")
    print(f"GENERATING REALISTIC HUMAN BEHAVIOR DATASET")
    print(f"{'=' * 70}")
    print(
        f"{'Name':<18} {'Role':<14} {'Acc':>4} {'Quirks':<30} {'N':>4} {'M':>4} {'S':>4}"
    )
    print(f"{'-' * 18} {'-' * 14} {'-' * 4} {'-' * 30} {'-' * 4} {'-' * 4} {'-' * 4}")

    for idx in range(n_profiles):
        p = PROFILES[idx]
        seed_i = rng.integers(0, 2**31)

        # Vary stress ratio per user (some people are more stressed overall)
        base_ratio = [0.45, 0.30, 0.25]
        user_stress_level = rng.uniform(-0.1, 0.1)
        ratio = [
            max(0.2, base_ratio[0] - user_stress_level),
            base_ratio[1],
            max(0.1, base_ratio[2] + user_stress_level),
        ]
        # Normalize
        total = sum(ratio)
        ratio = [r / total for r in ratio]

        X, y_true, y_reported, hours = simulate_user(
            p, n_windows=windows_per_user, stress_ratio=tuple(ratio), seed=seed_i
        )

        all_X.append(X)
        all_true.append(y_true)
        all_reported.append(y_reported)
        all_users.extend([p.name] * windows_per_user)
        all_hours.extend(hours)

        quirks = []
        if p.backspace_heavy:
            quirks.append("backspace_heavy")
        if p.bursty_typer:
            quirks.append("bursty")
        if p.perfectionist:
            quirks.append("perfectionist")
        if p.multitasker:
            quirks.append("multitasker")
        if p.stress_hider:
            quirks.append("stress_hider")
        if p.stress_amplifier:
            quirks.append("stress_amp")
        if p.night_owl:
            quirks.append("night_owl")
        if p.morning_person:
            quirks.append("morning")

        n_n = np.sum(y_true == 0)
        n_m = np.sum(y_true == 1)
        n_s = np.sum(y_true == 2)

        print(
            f"{p.name:<18} {p.role:<14} {p.report_accuracy:.0%} {','.join(quirks):<30} {n_n:>4} {n_m:>4} {n_s:>4}"
        )

    X_all = np.vstack(all_X)
    y_true_all = np.concatenate(all_true)
    y_reported_all = np.concatenate(all_reported)

    # Build DataFrame with BOTH true and reported labels
    df = pd.DataFrame(X_all, columns=pd.Index(FEATURE_NAMES))
    df["stress_label"] = y_true_all  # Ground truth
    df["stress_reported"] = y_reported_all  # Noisy self-report
    df["stress_level"] = df["stress_label"].map(
        {0: "NEUTRAL", 1: "MILD", 2: "STRESSED"}
    )
    df["user_id"] = all_users
    df["hour"] = all_hours

    # Agreement rate between true and reported
    agreement = np.mean(y_true_all == y_reported_all)

    df.to_csv(output_csv, index=False)

    print(f"\n{'=' * 70}")
    print(f"DATASET SUMMARY")
    print(f"{'=' * 70}")
    print(f"Users: {n_profiles}")
    print(f"Total samples: {len(df)}")
    print(f"Self-report accuracy: {agreement:.1%} (true vs reported)")
    print(f"\nTrue label distribution:")
    for label, name in {0: "NEUTRAL", 1: "MILD", 2: "STRESSED"}.items():
        count = (df["stress_label"] == label).sum()
        print(f"  {name:>10}: {count:>5} ({count / len(df) * 100:.1f}%)")
    print(f"\nReported label distribution:")
    for label, name in {0: "NEUTRAL", 1: "MILD", 2: "STRESSED"}.items():
        count = (df["stress_reported"] == label).sum()
        print(f"  {name:>10}: {count:>5} ({count / len(df) * 100:.1f}%)")
    print(f"\nSaved to: {output_csv}")

    return df


if __name__ == "__main__":
    df = generate_realistic_dataset(
        n_users=18,
        windows_per_user=200,
        seed=42,
        output_csv="realistic_dataset.csv",
    )
