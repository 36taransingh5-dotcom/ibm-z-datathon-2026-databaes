"""Generate a labelled synthetic payments dataset and train the demo model."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ARTIFACT_DIR = ROOT / "artifacts"

FEATURES = [
    "amount",
    "new_payee",
    "payee_age_hours",
    "hour",
    "device_change",
    "typing_time_seconds",
    "pasted_payee",
    "on_call",
    "usual_amount",
    "amount_ratio",
]


def generate_dataset(rows: int = 50_000, seed: int = 2026) -> pd.DataFrame:
    """Create reproducible fake payment behaviour with exactly ~3% scam labels."""
    rng = np.random.default_rng(seed)

    usual_amount = np.clip(rng.lognormal(np.log(75), 0.7, rows), 5, 2_500)
    amount = np.clip(usual_amount * rng.lognormal(0, 0.48, rows), 1, 5_000)
    new_payee = rng.binomial(1, 0.15, rows)
    payee_age_hours = np.where(
        new_payee == 1,
        rng.gamma(2.0, 30.0, rows),
        rng.uniform(72, 8_760, rows),
    )
    hour = rng.integers(0, 24, rows)
    device_change = rng.binomial(1, 0.055, rows)
    typing_time = np.clip(rng.gamma(2.2, 4.0, rows), 1, 80)
    pasted_payee = rng.binomial(1, 0.07, rows)
    on_call = rng.binomial(1, 0.035, rows)

    scam_count = round(rows * 0.03)
    scam_indices = rng.choice(rows, scam_count, replace=False)
    is_scam = np.zeros(rows, dtype=int)
    is_scam[scam_indices] = 1

    # Scam rows overlap with legitimate behaviour but are more likely to show
    # coercion, urgency, new recipients and unusual values.
    s = scam_indices
    amount[s] = np.clip(
        usual_amount[s] * rng.lognormal(np.log(3.1), 0.65, scam_count), 15, 5_000
    )
    new_payee[s] = rng.binomial(1, 0.84, scam_count)
    payee_age_hours[s] = np.where(
        new_payee[s] == 1,
        np.clip(rng.exponential(13, scam_count), 0.05, 96),
        rng.uniform(72, 720, scam_count),
    )
    unusual_hours = rng.choice([0, 1, 2, 3, 22, 23], scam_count)
    hour[s] = np.where(rng.random(scam_count) < 0.58, unusual_hours, hour[s])
    device_change[s] = rng.binomial(1, 0.48, scam_count)
    typing_time[s] = np.clip(rng.gamma(2.3, 16.0, scam_count), 3, 180)
    pasted_payee[s] = rng.binomial(1, 0.61, scam_count)
    on_call[s] = rng.binomial(1, 0.72, scam_count)

    frame = pd.DataFrame(
        {
            "amount": np.round(amount, 2),
            "new_payee": new_payee,
            "payee_age_hours": np.round(payee_age_hours, 2),
            "hour": hour,
            "device_change": device_change,
            "typing_time_seconds": np.round(typing_time, 2),
            "pasted_payee": pasted_payee,
            "on_call": on_call,
            "usual_amount": np.round(usual_amount, 2),
            "label": np.where(is_scam == 1, "scam", "legit"),
        }
    )
    frame["amount_ratio"] = np.round(
        frame["amount"] / frame["usual_amount"].clip(lower=1), 3
    )
    return frame


def train(frame: pd.DataFrame, seed: int = 2026) -> tuple[dict, dict]:
    x = frame[FEATURES]
    y = (frame["label"] == "scam").astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=seed
    )

    model = GradientBoostingClassifier(
        n_estimators=120,
        learning_rate=0.06,
        max_depth=3,
        min_samples_leaf=12,
        subsample=0.85,
        random_state=seed,
    )
    sample_weight = np.where(y_train == 1, 5.0, 1.0)
    model.fit(x_train, y_train, sample_weight=sample_weight)

    threshold = 0.45
    probability = model.predict_proba(x_test)[:, 1]
    predictions = (probability >= threshold).astype(int)

    sample = x_test.iloc[: min(1_000, len(x_test))]
    timings = []
    for _ in range(20):
        started = time.perf_counter()
        model.predict_proba(sample)
        timings.append((time.perf_counter() - started) * 1_000 / len(sample))

    results = {
        "dataset": {
            "synthetic": True,
            "rows": int(len(frame)),
            "scam_rate": round(float(y.mean()), 4),
            "seed": seed,
        },
        "model": "sklearn.ensemble.GradientBoostingClassifier",
        "decision_threshold": threshold,
        "test_rows": int(len(y_test)),
        "precision": round(float(precision_score(y_test, predictions)), 4),
        "recall": round(float(recall_score(y_test, predictions)), 4),
        "macro_f1": round(float(f1_score(y_test, predictions, average="macro")), 4),
        "milliseconds_per_decision": round(float(np.median(timings)), 4),
    }
    bundle = {
        "model": model,
        "features": FEATURES,
        "threshold": threshold,
        "feature_importances": dict(zip(FEATURES, model.feature_importances_.tolist())),
    }
    return bundle, results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    ARTIFACT_DIR.mkdir(exist_ok=True)
    frame = generate_dataset(args.rows, args.seed)
    frame.to_csv(DATA_DIR / "payments.csv", index=False)
    bundle, results = train(frame, args.seed)
    joblib.dump(bundle, ARTIFACT_DIR / "payment_scam_model.joblib")
    (ROOT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
