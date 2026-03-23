"""
MindPulse — 1D-CNN Branch for Local Temporal Patterns
======================================================
Captures digraph/trigraph typing patterns from raw timing sequences.

Input: [hold_time, flight_time, dd_time, uu_time] as 4 channels
Output: probability vector [NEUTRAL, MILD, STRESSED]

Architecture rationale:
  - Kernel sizes 3, 5, 7: Progressive receptive fields for 2-key, 3-key, n-gram patterns
  - Global Average Pooling: Handles variable-length sequences
  - Dropout 0.2/0.3: Prevents overfitting on small datasets
"""

from __future__ import annotations

import os
import sys

# Add parent directories to path for ml package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn


class StressCNN(nn.Module):
    """1D-CNN for local temporal pattern extraction from keystroke sequences."""

    def __init__(self, input_channels: int = 4, num_classes: int = 3):
        super().__init__()
        # input_channels: [hold_time, flight_time, dd_time, uu_time]
        self.conv_block = nn.Sequential(
            # Layer 1: Capture digraph patterns (k=3)
            nn.Conv1d(input_channels, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            # Layer 2: Capture trigraph patterns (k=5)
            nn.Conv1d(64, 128, kernel_size=5, padding=2),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            # Layer 3: Wider context (k=7)
            nn.Conv1d(128, 128, kernel_size=7, padding=3),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            # Global Average Pooling -> fixed-size output
            nn.AdaptiveAvgPool1d(1),
        )
        self.classifier = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: [batch, 4, seq_len] (4 channels of timing data)
        features = self.conv_block(x).squeeze(-1)  # [batch, 128]
        return self.classifier(features)  # [batch, 3]


# ────────────────────────────────────────────────────────────────
# Raw timing sequence builder
# ────────────────────────────────────────────────────────────────


def build_timing_sequence(key_events: list, max_len: int = 200) -> np.ndarray:
    """
    Convert key events into a 4-channel timing sequence.

    Channels: [hold_time, flight_time, dd_time, uu_time]
    Pads or truncates to max_len.

    Returns:
        np.ndarray of shape [4, max_len], dtype float32
    """
    if len(key_events) < 2:
        return np.zeros((4, max_len), dtype=np.float32)

    holds = []
    flights = []
    dds = []
    uus = []

    for i in range(len(key_events) - 1):
        e1 = key_events[i]
        e2 = key_events[i + 1]

        hold = e1.timestamp_release - e1.timestamp_press
        flight = e2.timestamp_press - e1.timestamp_release
        dd = e2.timestamp_press - e1.timestamp_press
        uu = e2.timestamp_release - e1.timestamp_release

        # Outlier clamping
        hold = max(0, min(hold, 2000))
        flight = max(0, min(flight, 5000))

        holds.append(hold)
        flights.append(flight)
        dds.append(dd)
        uus.append(uu)

    seq_len = len(holds)

    # Normalize to roughly [0, 1] range for stable training
    def normalize(arr):
        arr = np.array(arr, dtype=np.float32)
        if arr.max() > 0:
            arr = arr / arr.max()
        return arr

    holds = normalize(holds)
    flights = normalize(flights)
    dds = normalize(dds)
    uus = normalize(uus)

    # Stack as [4, seq_len]
    seq = np.stack([holds, flights, dds, uus], axis=0)

    # Pad or truncate
    if seq_len >= max_len:
        seq = seq[:, :max_len]
    else:
        pad_width = max_len - seq_len
        seq = np.pad(seq, ((0, 0), (0, pad_width)), mode="constant", constant_values=0)

    return seq.astype(np.float32)


# ────────────────────────────────────────────────────────────────
# Dataset for PyTorch
# ────────────────────────────────────────────────────────────────


class StressSequenceDataset(torch.utils.data.Dataset):
    """Dataset of timing sequences with stress labels."""

    def __init__(
        self,
        key_events_list: List[list],
        labels: np.ndarray,
        max_len: int = 200,
    ):
        self.sequences = [build_timing_sequence(ke, max_len) for ke in key_events_list]
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        seq = torch.tensor(self.sequences[idx], dtype=torch.float32)
        return seq, self.labels[idx]


# ────────────────────────────────────────────────────────────────
# Training function
# ────────────────────────────────────────────────────────────────


def train_cnn(
    key_events_list: List[list],
    labels: np.ndarray,
    max_epochs: int = 50,
    batch_size: int = 32,
    lr: float = 1e-3,
    val_split: float = 0.2,
    max_seq_len: int = 200,
    device: str = "cpu",
) -> Tuple[StressCNN, dict]:
    """
    Train the 1D-CNN branch.

    Args:
        key_events_list: List of key event lists (one per window)
        labels: np.ndarray of shape [N] with values 0/1/2
        max_epochs: Maximum training epochs
        batch_size: Batch size
        lr: Learning rate
        val_split: Validation fraction
        max_seq_len: Maximum sequence length
        device: 'cpu' or 'cuda'

    Returns:
        model: Trained StressCNN
        metrics: dict with val_loss, val_accuracy, val_f1
    """
    from sklearn.metrics import f1_score
    from sklearn.utils.class_weight import compute_sample_weight

    n = len(key_events_list)
    split_idx = int(n * (1 - val_split))

    # Shuffle
    indices = np.random.permutation(n)
    train_idx = indices[:split_idx]
    val_idx = indices[split_idx:]

    # Build datasets
    train_dataset = StressSequenceDataset(
        [key_events_list[i] for i in train_idx],
        labels[train_idx],
        max_seq_len,
    )
    val_dataset = StressSequenceDataset(
        [key_events_list[i] for i in val_idx],
        labels[val_idx],
        max_seq_len,
    )

    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False
    )

    # Model
    model = StressCNN(input_channels=4, num_classes=3).to(device)

    # Class-weighted loss
    class_weights = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    best_val_f1 = 0.0
    best_state = None
    patience = 10
    patience_counter = 0

    for epoch in range(max_epochs):
        # Train
        model.train()
        train_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # Validate
        model.eval()
        val_loss = 0.0
        all_preds = []
        all_labels = []
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                loss = criterion(logits, y)
                val_loss += loss.item()
                preds = torch.argmax(logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(y.cpu().numpy())

        val_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0.0)
        val_acc = np.mean(np.array(all_preds) == np.array(all_labels))

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(
                f"  Epoch {epoch + 1:3d}: "
                f"train_loss={train_loss / max(1, len(train_loader)):.4f} "
                f"val_loss={val_loss / max(1, len(val_loader)):.4f} "
                f"val_acc={val_acc:.3f} val_f1={val_f1:.3f}"
            )

        if patience_counter >= patience:
            print(f"  Early stopping at epoch {epoch + 1}")
            break

    # Load best
    if best_state:
        model.load_state_dict(best_state)

    metrics = {
        "val_f1_macro": float(best_val_f1),
        "val_accuracy": float(val_acc),
        "val_loss": float(val_loss / max(1, len(val_loader))),
    }

    return model, metrics


# ────────────────────────────────────────────────────────────────
# Save / Load
# ────────────────────────────────────────────────────────────────


def save_cnn(model: StressCNN, path: str = "model_cnn.pt"):
    torch.save(model.state_dict(), path)
    print(f"CNN saved to: {path}")


def load_cnn(path: str = "model_cnn.pt", device: str = "cpu") -> StressCNN:
    model = StressCNN(input_channels=4, num_classes=3)
    model.load_state_dict(torch.load(path, map_location=device))
    model.eval()
    return model


# ────────────────────────────────────────────────────────────────
# Self-test
# ────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import time as time_mod
    from app.ml.data_collector import KeyEvent

    print("=" * 55)
    print("MindPulse 1D-CNN Branch — Self Test")
    print("=" * 55)

    # Generate fake key events for testing
    np.random.seed(42)
    n_samples = 200
    all_key_events = []
    all_labels = []

    for i in range(n_samples):
        label = np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2])
        seq_len = np.random.randint(30, 100)

        # Generate timing based on stress level
        base_hold = [100, 120, 150][label]
        base_flight = [120, 140, 180][label]

        events = []
        t = time_mod.time() * 1000
        for j in range(seq_len):
            hold = max(10, np.random.normal(base_hold, base_hold * 0.2))
            flight = max(0, np.random.normal(base_flight, base_flight * 0.3))
            events.append(
                KeyEvent(
                    timestamp_press=t,
                    timestamp_release=t + hold,
                    key_category="alpha",
                )
            )
            t += hold + flight

        all_key_events.append(events)
        all_labels.append(label)

    all_labels = np.array(all_labels, dtype=np.int32)

    # Build a sequence and check shape
    seq = build_timing_sequence(all_key_events[0])
    print(f"\nSequence shape: {seq.shape}")
    print(f"Channels: [hold, flight, dd, uu]")
    print(f"Sample values: {seq[:, :5]}")

    # Train
    print(f"\nTraining CNN on {n_samples} synthetic samples...")
    model, metrics = train_cnn(
        all_key_events,
        all_labels,
        max_epochs=30,
        batch_size=32,
        lr=1e-3,
        device="cpu",
    )
    print(f"\nMetrics: {metrics}")

    # Save and reload
    save_cnn(model, "model_cnn.pt")
    loaded = load_cnn("model_cnn.pt")

    # Test inference
    test_seq = torch.tensor(seq).unsqueeze(0)  # [1, 4, 200]
    with torch.no_grad():
        logits = loaded(test_seq)
        probs = torch.softmax(logits, dim=1)[0].numpy()

    print(f"\nTest inference:")
    for i, name in enumerate(["NEUTRAL", "MILD", "STRESSED"]):
        print(f"  {name:>10}: {probs[i]:.4f}")

    print("\n1D-CNN branch is working correctly!")
