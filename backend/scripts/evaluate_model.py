"""
MindPulse — Model Evaluation Script
===================================
Upgraded evaluator with support for:
1) Real CSV test data evaluation
2) Explicit synthetic fallback mode
3) CLI + environment configuration
4) Clear, reproducible metrics output

Usage examples:
  python evaluate_model.py
  python evaluate_model.py --mode synthetic --synthetic-samples 1200 --synthetic-seed 99
  python evaluate_model.py --mode real --test-csv data/test_windows.csv --label-column stress_label
  python evaluate_model.py --mode auto --test-csv data/test_windows.csv --label-column label

Environment variables (optional):
  MINDPULSE_EVAL_MODE=auto|real|synthetic
  MINDPULSE_EVAL_TEST_CSV=path/to/test.csv
  MINDPULSE_EVAL_LABEL_COLUMN=stress_label
  MINDPULSE_EVAL_SYNTHETIC_SAMPLES=1000
  MINDPULSE_EVAL_SYNTHETIC_SEED=99
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, Tuple

# Add parent directories to path for ml package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from app.ml.feature_extractor import FEATURE_NAMES
from app.ml.model import DualNormalizer, load_model
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from app.ml.synthetic_data import generate_synthetic_dataset

LABELS = ["NEUTRAL", "MILD", "STRESSED"]
LABEL_TO_INT = {"NEUTRAL": 0, "MILD": 1, "STRESSED": 2}


def _to_int_labels(values: np.ndarray) -> np.ndarray:
    """Convert label array (int or string) to int classes {0,1,2}."""
    arr = np.asarray(values)
    if np.issubdtype(arr.dtype, np.number):
        y = arr.astype(np.int32)
    else:
        y = np.array(
            [LABEL_TO_INT.get(str(v).strip().upper(), -1) for v in arr],
            dtype=np.int32,
        )
    return y


def load_real_test_data(
    csv_path: str, label_column: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load and validate real CSV test data.

    Required:
    - all FEATURE_NAMES columns present
    - label column present (int 0/1/2 or strings NEUTRAL/MILD/STRESSED)
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Test CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    missing = [c for c in FEATURE_NAMES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")

    if label_column not in df.columns:
        raise ValueError(
            f"Label column '{label_column}' not found. Available columns: {list(df.columns)}"
        )

    X = df[FEATURE_NAMES].to_numpy(dtype=np.float32)
    y = _to_int_labels(df[label_column].to_numpy())

    valid_mask = np.isin(y, [0, 1, 2])
    X = X[valid_mask]
    y = y[valid_mask]

    if len(X) == 0:
        raise ValueError("No valid rows found after label parsing/filtering.")

    return X, y


def normalize_features(X_raw: np.ndarray, normalizer: DualNormalizer) -> np.ndarray:
    """Apply dual normalization (global + zeroed user baseline for eval)."""
    hour_idx = FEATURE_NAMES.index("hour_of_day")
    X_norm = np.array(
        [
            normalizer.transform(X_raw[i], hour=int(X_raw[i, hour_idx]), baseline=None)
            for i in range(len(X_raw))
        ],
        dtype=np.float32,
    )
    return X_norm


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute core evaluation metrics."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(
            precision_score(y_true, y_pred, average="macro", zero_division=0.0)
        ),
        "recall_macro": float(
            recall_score(y_true, y_pred, average="macro", zero_division=0.0)
        ),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
    }


def print_report(
    source: str,
    n_samples: int,
    metrics: Dict[str, float],
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> None:
    """Pretty print full report."""
    print("=" * 70)
    print("MINDPULSE — MODEL EVALUATION REPORT")
    print("=" * 70)
    print(f"Evaluation source: {source}")
    print(f"Samples: {n_samples}")

    print(f"\n{'Metric':<22} {'Score':>10}")
    print(f"{'─' * 22} {'─' * 10}")
    print(f"{'Accuracy':<22} {metrics['accuracy'] * 100:>9.2f}%")
    print(f"{'Precision (Macro)':<22} {metrics['precision_macro'] * 100:>9.2f}%")
    print(f"{'Recall (Macro)':<22} {metrics['recall_macro'] * 100:>9.2f}%")
    print(f"{'F1-Score (Macro)':<22} {metrics['f1_macro'] * 100:>9.2f}%")

    print("\nDetailed Classification Report:")
    print(classification_report(y_true, y_pred, target_names=LABELS, zero_division="0"))

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    print("Confusion Matrix:")
    print(f"{'':>12} {'NEUTRAL':>10} {'MILD':>10} {'STRESSED':>10}")
    for i, label in enumerate(LABELS):
        print(f"{label:>12} {cm[i, 0]:>10} {cm[i, 1]:>10} {cm[i, 2]:>10}")

    print("=" * 70)


def evaluate(
    mode: str = "auto",
    test_csv: str | None = None,
    label_column: str = "stress_label",
    synthetic_samples: int = 1000,
    synthetic_seed: int = 99,
    save_json: str | None = None,
) -> Dict:
    """
    Evaluate model in one of three modes:
      - real: requires test_csv
      - synthetic: always uses synthetic data
      - auto: tries real if test_csv exists, else synthetic fallback
    """
    mode = mode.lower().strip()
    if mode not in {"auto", "real", "synthetic"}:
        raise ValueError("mode must be one of: auto, real, synthetic")

    model, stats = load_model()
    normalizer = DualNormalizer(stats)

    source = "synthetic"

    if mode == "real":
        if not test_csv:
            raise ValueError("mode='real' requires --test-csv")
        X_raw, y_true = load_real_test_data(test_csv, label_column)
        source = f"real_csv:{test_csv}"

    elif mode == "synthetic":
        X_raw, y_true, _ = generate_synthetic_dataset(
            n_samples=synthetic_samples, random_seed=synthetic_seed
        )
        source = f"synthetic(n={synthetic_samples},seed={synthetic_seed})"

    else:  # auto
        if test_csv and os.path.exists(test_csv):
            try:
                X_raw, y_true = load_real_test_data(test_csv, label_column)
                source = f"real_csv:{test_csv}"
            except Exception as e:
                print(
                    f"[WARN] Real CSV evaluation failed ({e}). Falling back to synthetic."
                )
                X_raw, y_true, _ = generate_synthetic_dataset(
                    n_samples=synthetic_samples, random_seed=synthetic_seed
                )
                source = (
                    f"synthetic_fallback(n={synthetic_samples},seed={synthetic_seed})"
                )
        else:
            X_raw, y_true, _ = generate_synthetic_dataset(
                n_samples=synthetic_samples, random_seed=synthetic_seed
            )
            source = f"synthetic_auto(n={synthetic_samples},seed={synthetic_seed})"

    X_norm = normalize_features(X_raw, normalizer)
    y_pred = model.predict(X_norm)

    metrics = compute_metrics(y_true, y_pred)
    print_report(source, len(y_true), metrics, y_true, y_pred)

    result = {
        "source": source,
        "num_samples": int(len(y_true)),
        "metrics": metrics,
    }

    if save_json:
        with open(save_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved JSON metrics to: {save_json}")

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MindPulse model evaluator with real CSV + synthetic fallback."
    )
    parser.add_argument(
        "--mode",
        type=str,
        default=os.getenv("MINDPULSE_EVAL_MODE", "auto"),
        choices=["auto", "real", "synthetic"],
        help="Evaluation mode.",
    )
    parser.add_argument(
        "--test-csv",
        type=str,
        default=os.getenv("MINDPULSE_EVAL_TEST_CSV", ""),
        help="Path to real CSV test set.",
    )
    parser.add_argument(
        "--label-column",
        type=str,
        default=os.getenv("MINDPULSE_EVAL_LABEL_COLUMN", "stress_label"),
        help="Label column name in real CSV.",
    )
    parser.add_argument(
        "--synthetic-samples",
        type=int,
        default=int(os.getenv("MINDPULSE_EVAL_SYNTHETIC_SAMPLES", "1000")),
        help="Synthetic sample count.",
    )
    parser.add_argument(
        "--synthetic-seed",
        type=int,
        default=int(os.getenv("MINDPULSE_EVAL_SYNTHETIC_SEED", "99")),
        help="Synthetic RNG seed.",
    )
    parser.add_argument(
        "--save-json",
        type=str,
        default="",
        help="Optional output JSON path for summary metrics.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    evaluate(
        mode=args.mode,
        test_csv=args.test_csv or None,
        label_column=args.label_column,
        synthetic_samples=args.synthetic_samples,
        synthetic_seed=args.synthetic_seed,
        save_json=args.save_json or None,
    )
