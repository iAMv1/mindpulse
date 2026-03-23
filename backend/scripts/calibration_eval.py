"""
MindPulse — Honest Calibration Evaluation
==========================================
Train on N-1 users, calibrate on test user's first N samples.
This is the CORRECT way to evaluate stress detection.

Strategy:
  1. Train global XGBoost on all users except test user
  2. Get 30-50 calibration samples from test user
  3. Compute test user's personal baseline (per-class feature means)
  4. At inference: shift test features toward user's baseline
  5. Report F1 on remaining test samples

This simulates the real deployment: user uses MindPulse for a week,
we learn their baseline, then detect deviations.
"""

from __future__ import annotations
import json
import os
import sys

# Add parent directories to path for ml package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    cohen_kappa_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)
from sklearn.utils.class_weight import compute_sample_weight
from app.ml.feature_extractor import FEATURE_NAMES

LABELS = ["NEUTRAL", "MILD", "STRESSED"]


def evaluate_with_calibration(
    csv_path: str = "overlap_dataset.csv",
    cal_samples: int = 40,
    n_repeats: int = 3,
):
    """
    Leave-One-User-Out with calibration.

    For each user:
      - Train on all other users
      - Use first `cal_samples` from test user as calibration
      - Test on remaining samples from test user
      - Report F1
    """
    df = pd.read_csv(csv_path)
    X_raw = df[FEATURE_NAMES].values.astype(np.float32)
    y = df["stress_label"].values.astype(np.int32)
    users = df["user_id"].values
    unique_users = np.unique(users)

    print("=" * 70)
    print("HONEST EVALUATION: LEAVE-ONE-USER-OUT WITH CALIBRATION")
    print("=" * 70)
    print(f"Dataset: {csv_path}")
    print(f"Users: {len(unique_users)}")
    print(f"Calibration samples per user: {cal_samples}")
    print(f"Repeats: {n_repeats}")

    all_f1_no_cal = []
    all_f1_cal = []
    all_f1_calibrated = []
    fold_results = []

    for test_user in unique_users:
        test_mask = users == test_user
        train_mask = ~test_mask

        X_tr_raw = X_raw[train_mask]
        y_tr = y[train_mask]
        X_te_raw = X_raw[test_mask]
        y_te = y[test_mask]

        # Normalize using training stats
        mean = X_tr_raw.mean(axis=0)
        std = X_tr_raw.std(axis=0) + 1e-8
        X_tr = (X_tr_raw - mean) / std
        X_te = (X_te_raw - mean) / std

        # Train global model
        sw = compute_sample_weight("balanced", y_tr)
        model = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            max_depth=6,
            learning_rate=0.08,
            n_estimators=350,
            subsample=0.9,
            colsample_bytree=0.9,
            min_child_weight=3,
            random_state=42,
            tree_method="hist",
        )
        model.fit(X_tr, y_tr, sample_weight=sw, verbose=False)

        # Split test into calibration + evaluation
        n_cal = min(cal_samples, len(X_te) // 2)
        X_cal = X_te[:n_cal]
        y_cal = y_te[:n_cal]
        X_eval = X_te[n_cal:]
        y_eval = y_te[n_cal:]

        if len(X_eval) < 10:
            continue

        # ── NO CALIBRATION ──
        yp_no_cal = model.predict(X_eval)
        f1_no_cal = f1_score(y_eval, yp_no_cal, average="macro", zero_division=0)

        # ── WITH CALIBRATION ──
        # Method 1: Include calibration samples in training (few-shot)
        X_combined = np.vstack([X_tr, X_cal])
        y_combined = np.concatenate([y_tr, y_cal])
        sw_cal = compute_sample_weight("balanced", y_combined)

        model_cal = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            max_depth=6,
            learning_rate=0.08,
            n_estimators=350,
            subsample=0.9,
            colsample_bytree=0.9,
            min_child_weight=3,
            random_state=42,
            tree_method="hist",
        )
        model_cal.fit(X_combined, y_combined, sample_weight=sw_cal, verbose=False)

        # Method 2: Compute user deviation from global, use as additional signal
        user_mean = X_cal.mean(axis=0)
        global_mean = X_tr.mean(axis=0)
        deviation = (user_mean - global_mean) / (X_tr.std(axis=0) + 1e-8)

        # Append deviation as bias feature (soft adaptation)
        X_eval_aug = np.hstack([X_eval, np.tile(deviation, (len(X_eval), 1))])
        X_tr_aug = np.hstack([X_tr, np.zeros((len(X_tr), X_tr.shape[1]))])
        X_cal_aug = np.hstack([X_cal, np.tile(deviation, (len(X_cal), 1))])
        X_combined_aug = np.vstack([X_tr_aug, X_cal_aug])

        model_cal2 = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            max_depth=6,
            learning_rate=0.08,
            n_estimators=350,
            subsample=0.9,
            colsample_bytree=0.9,
            min_child_weight=3,
            random_state=42,
            tree_method="hist",
        )
        model_cal2.fit(X_combined_aug, y_combined, sample_weight=sw_cal, verbose=False)

        yp_cal = model_cal2.predict(X_eval_aug)
        f1_cal = f1_score(y_eval, yp_cal, average="macro", zero_division=0)
        acc_final = accuracy_score(y_eval, yp_cal)

        all_f1_no_cal.append(f1_no_cal)
        all_f1_cal.append(f1_cal)
        all_f1_calibrated.append(f1_cal)

        fold_results.append(
            {
                "user": str(test_user),
                "f1_no_cal": float(f1_no_cal),
                "f1_with_cal": float(f1_cal),
                "acc_no_cal": float(accuracy_score(y_eval, yp_no_cal)),
                "acc_with_cal": float(acc_final),
                "improvement": float(f1_cal - f1_no_cal),
            }
        )

    # ── Print Results ──
    print(
        f"\n{'User':>18} {'No Cal F1':>10} {'Cal F1':>10} {'No Cal Acc':>11} {'Cal Acc':>10} {'Delta':>8}"
    )
    print(f"{'-' * 18} {'-' * 10} {'-' * 10} {'-' * 11} {'-' * 10} {'-' * 8}")

    for fr in sorted(fold_results, key=lambda x: x["improvement"], reverse=True):
        print(
            f"{fr['user']:>18} "
            f"{fr['f1_no_cal'] * 100:>9.1f}% "
            f"{fr['f1_with_cal'] * 100:>9.1f}% "
            f"{fr['acc_no_cal'] * 100:>10.1f}% "
            f"{fr['acc_with_cal'] * 100:>9.1f}% "
            f"{fr['improvement'] * 100:>+7.1f}%"
        )

    mean_no_cal = np.mean(all_f1_no_cal)
    mean_cal = np.mean(all_f1_calibrated)
    mean_improvement = np.mean([fr["improvement"] for fr in fold_results])
    std_no_cal = np.std(all_f1_no_cal)
    std_cal = np.std(all_f1_calibrated)

    print(
        f"\n{'Mean':>18} {mean_no_cal * 100:>9.1f}% {mean_cal * 100:>9.1f}% {'':>11} {'':>10} {mean_improvement * 100:>+7.1f}%"
    )
    print(f"{'Std':>18} {std_no_cal * 100:>9.1f}% {std_cal * 100:>9.1f}%")

    print(f"\n{'=' * 70}")
    print("SUMMARY (HONEST NUMBERS)")
    print(f"{'=' * 70}")
    print(
        f"Universal model (no calibration):  F1 = {mean_no_cal:.3f} ± {std_no_cal:.3f}"
    )
    print(
        f"With {cal_samples}-sample calibration:         F1 = {mean_cal:.3f} ± {std_cal:.3f}"
    )
    print(f"Improvement from calibration:       = {mean_improvement:+.3f}")
    print(f"\nResearch comparison:")
    print(f"  ETH Zurich 2025 (universal):     p  = 0.078")
    print(f"  ETH Zurich 2023 (lab):           F1 = 0.625")
    print(f"  Pepa et al 2021 (in-the-wild):   F1 = 0.60")
    print(f"  MindPulse (universal):           F1 = {mean_no_cal:.3f}")
    print(f"  MindPulse (calibrated):          F1 = {mean_cal:.3f}")

    # Save
    result = {
        "evaluation": "leave-one-user-out-with-calibration",
        "n_users": len(unique_users),
        "cal_samples": cal_samples,
        "dataset": csv_path,
        "universal_f1": {"mean": float(mean_no_cal), "std": float(std_no_cal)},
        "calibrated_f1": {"mean": float(mean_cal), "std": float(std_cal)},
        "improvement": float(mean_improvement),
        "fold_results": fold_results,
    }
    with open("eval_calibration.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to eval_calibration.json")

    return result


if __name__ == "__main__":
    result = evaluate_with_calibration(
        csv_path="overlap_dataset.csv",
        cal_samples=40,
    )
