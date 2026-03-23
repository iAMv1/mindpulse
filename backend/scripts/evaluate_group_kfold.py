"""
MindPulse — Group K-Fold / Leave-One-User-Out Evaluation
=========================================================
Honest evaluation: train on N-1 users, test on held-out user.
With 2 users, this is leave-one-user-out (2-fold).

Prevents data leakage from user-specific typing patterns.
"""

from __future__ import annotations

import json
import os
import sys

# Add parent directories to path for ml package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    cohen_kappa_score,
)
import xgboost as xgb
import joblib

from app.ml.feature_extractor import FEATURE_NAMES, NUM_RAW_FEATURES

LABELS = ["NEUTRAL", "MILD", "STRESSED"]


def load_real_data(csv_path: str):
    df = pd.read_csv(csv_path)
    X = df[FEATURE_NAMES].to_numpy(dtype=np.float32)
    y = df["stress_label"].to_numpy(dtype=np.int32)
    users = df["user_id"].values
    return X, y, users


def normalize_features(X_raw: np.ndarray, stats: dict) -> np.ndarray:
    mean = np.asarray(stats["mean"], dtype=np.float32)
    std = np.asarray(stats["std"], dtype=np.float32)
    return (X_raw - mean) / (std + 1e-8)


def compute_global_stats(X: np.ndarray) -> dict:
    return {
        "mean": np.mean(X, axis=0).astype(np.float32),
        "std": np.std(X, axis=0).astype(np.float32),
    }


def train_xgb(X_train, y_train, X_val, y_val):
    """Train XGBoost with class balancing."""
    from sklearn.utils.class_weight import compute_sample_weight

    sample_weights = compute_sample_weight("balanced", y_train)

    model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        max_depth=6,
        learning_rate=0.08,
        n_estimators=350,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=3,
        gamma=0.05,
        reg_alpha=0.01,
        reg_lambda=1.0,
        eval_metric="mlogloss",
        random_state=42,
        tree_method="hist",
    )
    model.fit(
        X_train,
        y_train,
        sample_weight=sample_weights,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    return model


def evaluate_group_kfold(csv_path: str = "real_dataset.csv"):
    """
    Leave-One-User-Out evaluation.
    For each user: train on all other users, test on this user.
    """
    X_raw, y, users = load_real_data(csv_path)
    unique_users = np.unique(users)

    print("=" * 70)
    print("MINDPULSE — LEAVE-ONE-USER-OUT EVALUATION (HONEST)")
    print("=" * 70)
    print(f"Total samples: {len(X_raw)}")
    print(f"Users: {list(unique_users)}")
    print(
        f"Label distribution: NEUTRAL={np.sum(y == 0)}, MILD={np.sum(y == 1)}, STRESSED={np.sum(y == 2)}"
    )

    all_y_true = []
    all_y_pred = []
    all_y_proba = []
    fold_results = []

    for test_user in unique_users:
        print(f"\n{'-' * 50}")
        print(f"Fold: Test on '{test_user}'")

        # Split by user (NO data leakage)
        test_mask = users == test_user
        train_mask = ~test_mask

        X_train_raw, X_test_raw = X_raw[train_mask], X_raw[test_mask]
        y_train, y_test = y[train_mask], y[test_mask]

        print(
            f"  Train: {len(X_train_raw)} samples from {list(unique_users[unique_users != test_user])}"
        )
        print(f"  Test:  {len(X_test_raw)} samples from [{test_user}]")
        print(
            f"  Train dist: N={np.sum(y_train == 0)} M={np.sum(y_train == 1)} S={np.sum(y_train == 2)}"
        )
        print(
            f"  Test dist:  N={np.sum(y_test == 0)} M={np.sum(y_test == 1)} S={np.sum(y_test == 2)}"
        )

        # Normalize using training stats only
        stats = compute_global_stats(X_train_raw)
        X_train = normalize_features(X_train_raw, stats)
        X_test = normalize_features(X_test_raw, stats)

        # Train
        model = train_xgb(X_train, y_train, X_test, y_test)

        # Predict
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)

        # Metrics for this fold
        fold_metrics = {
            "user": str(test_user),
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "f1_macro": float(
                f1_score(y_test, y_pred, average="macro", zero_division=0.0)
            ),
            "precision_macro": float(
                precision_score(y_test, y_pred, average="macro", zero_division=0.0)
            ),
            "recall_macro": float(
                recall_score(y_test, y_pred, average="macro", zero_division=0.0)
            ),
            "n_test": int(len(y_test)),
        }
        fold_results.append(fold_metrics)

        print(f"\n  Accuracy:   {fold_metrics['accuracy'] * 100:.1f}%")
        print(f"  F1-Macro:   {fold_metrics['f1_macro'] * 100:.1f}%")
        print(f"  Precision:  {fold_metrics['precision_macro'] * 100:.1f}%")
        print(f"  Recall:     {fold_metrics['recall_macro'] * 100:.1f}%")

        print(f"\n  Classification Report:")
        print(
            classification_report(y_test, y_pred, target_names=LABELS, zero_division=0)
        )

        cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])
        print(f"  Confusion Matrix:")
        print(f"  {'':>10} {'NEUTRAL':>10} {'MILD':>10} {'STRESSED':>10}")
        for i, label in enumerate(LABELS):
            print(f"  {label:>10} {cm[i, 0]:>10} {cm[i, 1]:>10} {cm[i, 2]:>10}")

        all_y_true.extend(y_test.tolist())
        all_y_pred.extend(y_pred.tolist())
        all_y_proba.extend(y_proba.tolist())

    # -- Aggregate Results ----------------------------------
    print(f"\n{'=' * 70}")
    print("AGGREGATE RESULTS (All Folds)")
    print(f"{'=' * 70}")

    all_y_true = np.array(all_y_true)
    all_y_pred = np.array(all_y_pred)
    all_y_proba = np.array(all_y_proba)

    agg = {
        "accuracy": float(accuracy_score(all_y_true, all_y_pred)),
        "f1_macro": float(
            f1_score(all_y_true, all_y_pred, average="macro", zero_division=0.0)
        ),
        "precision_macro": float(
            precision_score(all_y_true, all_y_pred, average="macro", zero_division=0.0)
        ),
        "recall_macro": float(
            recall_score(all_y_true, all_y_pred, average="macro", zero_division=0.0)
        ),
        "cohen_kappa": float(cohen_kappa_score(all_y_true, all_y_pred)),
    }

    try:
        agg["auc_roc_ovr"] = float(
            roc_auc_score(all_y_true, all_y_proba, multi_class="ovr")
        )
    except Exception:
        agg["auc_roc_ovr"] = None

    print(f"\n  {'Metric':<25} {'Score':>10}")
    print(f"  {'-' * 25} {'-' * 10}")
    print(f"  {'Accuracy':<25} {agg['accuracy'] * 100:>9.2f}%")
    print(f"  {'F1-Score (Macro)':<25} {agg['f1_macro'] * 100:>9.2f}%")
    print(f"  {'Precision (Macro)':<25} {agg['precision_macro'] * 100:>9.2f}%")
    print(f"  {'Recall (Macro)':<25} {agg['recall_macro'] * 100:>9.2f}%")
    print(f"  {'Cohen Kappa':<25} {agg['cohen_kappa']:>9.4f}")
    if agg["auc_roc_ovr"]:
        print(f"  {'AUC-ROC (OvR)':<25} {agg['auc_roc_ovr']:>9.4f}")

    print(f"\n  Per-Fold F1 Scores:")
    for fr in fold_results:
        print(f"    {fr['user']:>10}: {fr['f1_macro'] * 100:.1f}%")
    mean_f1 = np.mean([fr["f1_macro"] for fr in fold_results])
    std_f1 = np.std([fr["f1_macro"] for fr in fold_results])
    print(f"    {'Mean':>10}: {mean_f1 * 100:.1f}% ± {std_f1 * 100:.1f}%")

    print(f"\n  Aggregate Classification Report:")
    print(
        classification_report(
            all_y_true, all_y_pred, target_names=LABELS, zero_division=0
        )
    )

    agg_cm = confusion_matrix(all_y_true, all_y_pred, labels=[0, 1, 2])
    print(f"  Aggregate Confusion Matrix:")
    print(f"  {'':>10} {'NEUTRAL':>10} {'MILD':>10} {'STRESSED':>10}")
    for i, label in enumerate(LABELS):
        print(f"  {label:>10} {agg_cm[i, 0]:>10} {agg_cm[i, 1]:>10} {agg_cm[i, 2]:>10}")

    # Save results
    result = {
        "evaluation": "leave-one-user-out",
        "n_users": len(unique_users),
        "n_total_samples": int(len(all_y_true)),
        "fold_results": fold_results,
        "aggregate": agg,
    }

    with open("eval_group_kfold.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to: eval_group_kfold.json")

    return result


if __name__ == "__main__":
    evaluate_group_kfold("real_dataset.csv")
