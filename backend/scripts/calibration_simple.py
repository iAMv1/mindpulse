"""
MindPulse — Simple Calibration Evaluation
===========================================
The correct approach: train on N-1 users + calibration samples from test user.
This is how real deployment works — you collect some labeled data, then predict.
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
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.utils.class_weight import compute_sample_weight
from app.ml.feature_extractor import FEATURE_NAMES


def run_evaluation(csv_path="overlap_dataset.csv", cal_samples=40):
    df = pd.read_csv(csv_path)
    X_raw = df[FEATURE_NAMES].values.astype(np.float32)
    y = df["stress_label"].values.astype(np.int32)
    users = df["user_id"].values
    unique_users = np.unique(users)

    print("=" * 60)
    print("HONEST EVALUATION: WITH CALIBRATION")
    print("=" * 60)

    results = []

    for test_user in unique_users:
        test_mask = users == test_user
        train_mask = ~test_mask

        X_tr = X_raw[train_mask]
        y_tr = y[train_mask]
        X_te = X_raw[test_mask]
        y_te = y[test_mask]

        # Normalize
        mean, std = X_tr.mean(0), X_tr.std(0) + 1e-8
        X_tr_n = (X_tr - mean) / std
        X_te_n = (X_te - mean) / std

        # Split test into calibration + eval
        n_cal = min(cal_samples, len(X_te) // 2)
        X_cal, y_cal = X_te_n[:n_cal], y_te[:n_cal]
        X_eval, y_eval = X_te_n[n_cal:], y_te[n_cal:]

        if len(X_eval) < 10:
            continue

        # NO CALIBRATION: train on other users only
        sw = compute_sample_weight("balanced", y_tr)
        model = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            max_depth=6,
            learning_rate=0.08,
            n_estimators=200,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            tree_method="hist",
        )
        model.fit(X_tr_n, y_tr, sample_weight=sw, verbose=False)
        yp_no_cal = model.predict(X_eval)
        f1_no_cal = f1_score(y_eval, yp_no_cal, average="macro", zero_division=0)

        # WITH CALIBRATION: add calibration samples to training
        X_comb = np.vstack([X_tr_n, X_cal])
        y_comb = np.concatenate([y_tr, y_cal])
        sw_comb = compute_sample_weight("balanced", y_comb)
        model_cal = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            max_depth=6,
            learning_rate=0.08,
            n_estimators=200,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            tree_method="hist",
        )
        model_cal.fit(X_comb, y_comb, sample_weight=sw_comb, verbose=False)
        yp_cal = model_cal.predict(X_eval)
        f1_cal = f1_score(y_eval, yp_cal, average="macro", zero_division=0)

        acc_no = accuracy_score(y_eval, yp_no_cal)
        acc_cal = accuracy_score(y_eval, yp_cal)

        results.append(
            {
                "user": str(test_user),
                "f1_no_cal": float(f1_no_cal),
                "f1_cal": float(f1_cal),
                "acc_no_cal": float(acc_no),
                "acc_cal": float(acc_cal),
                "delta": float(f1_cal - f1_no_cal),
            }
        )

    # Print
    print(f"\n{'User':>18} {'No Cal':>8} {'Cal':>8} {'Delta':>8}")
    print(f"{'-' * 18} {'-' * 8} {'-' * 8} {'-' * 8}")
    for r in sorted(results, key=lambda x: x["delta"], reverse=True):
        print(
            f"{r['user']:>18} {r['f1_no_cal'] * 100:>7.1f}% {r['f1_cal'] * 100:>7.1f}% {r['delta'] * 100:>+7.1f}%"
        )

    f1s_no = [r["f1_no_cal"] for r in results]
    f1s_cal = [r["f1_cal"] for r in results]
    deltas = [r["delta"] for r in results]

    print(
        f"\n{'Mean':>18} {np.mean(f1s_no) * 100:>7.1f}% {np.mean(f1s_cal) * 100:>7.1f}% {np.mean(deltas) * 100:>+7.1f}%"
    )
    print(f"{'Std':>18} {np.std(f1s_no) * 100:>7.1f}% {np.std(f1s_cal) * 100:>7.1f}%")

    print(f"\n{'=' * 60}")
    print(f"FINAL HONEST NUMBERS")
    print(f"{'=' * 60}")
    print(
        f"Universal (no calibration):  F1 = {np.mean(f1s_no):.3f} +/- {np.std(f1s_no):.3f}"
    )
    print(
        f"Calibrated ({cal_samples} samples):  F1 = {np.mean(f1s_cal):.3f} +/- {np.std(f1s_cal):.3f}"
    )
    print(f"Improvement:                 +{np.mean(deltas) * 100:.1f}%")
    print(f"\nResearch benchmarks:")
    print(f"  ETH Zurich 2025 universal: F1 ~ 0.078 (rho)")
    print(f"  ETH Zurich 2023 lab:       F1 = 0.625")
    print(f"  Pepa 2021 in-the-wild:     F1 = 0.60")
    print(f"  MindPulse universal:       F1 = {np.mean(f1s_no):.3f}")
    print(f"  MindPulse calibrated:      F1 = {np.mean(f1s_cal):.3f}")

    # Save
    with open("eval_calibration.json", "w") as f:
        json.dump(
            {
                "universal_f1": {
                    "mean": float(np.mean(f1s_no)),
                    "std": float(np.std(f1s_no)),
                },
                "calibrated_f1": {
                    "mean": float(np.mean(f1s_cal)),
                    "std": float(np.std(f1s_cal)),
                },
                "improvement": float(np.mean(deltas)),
                "fold_results": results,
            },
            f,
            indent=2,
        )
    print("\nSaved to eval_calibration.json")


if __name__ == "__main__":
    run_evaluation()
