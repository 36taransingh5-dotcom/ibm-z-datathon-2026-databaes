"""Generate a labelled synthetic payments dataset and train the demo model."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ARTIFACT_DIR = ROOT / "artifacts"
EVIDENCE_DIR = ROOT / "evidence"

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


def rules_only_predictions(frame: pd.DataFrame, threshold: int = 55) -> np.ndarray:
    """Apply the app's transparent point rules without using model output."""
    score = np.zeros(len(frame), dtype=int)
    new_recent = (frame["new_payee"] == 1) & (frame["payee_age_hours"] < 24)
    amount_on_call = (frame["amount_ratio"] >= 3) & (frame["on_call"] == 1)
    score += np.where(new_recent, 18, 0)
    score += np.where(amount_on_call, 60, 0)

    without_interaction = ~amount_on_call
    score += np.where(without_interaction & (frame["amount_ratio"] >= 3), 24, 0)
    score += np.where(
        without_interaction
        & (frame["amount_ratio"] >= 1.75)
        & (frame["amount_ratio"] < 3),
        13,
        0,
    )
    score += np.where(without_interaction & (frame["on_call"] == 1), 20, 0)
    score += np.where(frame["pasted_payee"] == 1, 11, 0)
    score += np.where(frame["device_change"] == 1, 13, 0)
    score += np.where(frame["typing_time_seconds"] >= 30, 8, 0)
    score += np.where((frame["hour"] <= 3) | (frame["hour"] >= 22), 6, 0)
    return (np.minimum(score, 100) >= threshold).astype(int)


def classification_metrics(y_true: pd.Series, predictions: np.ndarray) -> dict:
    return {
        "precision": round(float(precision_score(y_true, predictions)), 4),
        "recall": round(float(recall_score(y_true, predictions)), 4),
        "f1": round(float(f1_score(y_true, predictions)), 4),
        "macro_f1": round(float(f1_score(y_true, predictions, average="macro")), 4),
    }


def measure_single_decision_latency(
    model: GradientBoostingClassifier, x_test: pd.DataFrame, samples: int = 2_000
) -> dict:
    """Measure individual predict_proba calls and return milliseconds."""
    rows = [x_test.iloc[[index]] for index in range(min(samples, len(x_test)))]
    for row in rows[:100]:
        model.predict_proba(row)

    latencies_ms = []
    for row in rows:
        started_ns = time.perf_counter_ns()
        model.predict_proba(row)
        latencies_ms.append((time.perf_counter_ns() - started_ns) / 1_000_000)

    return {
        "median": round(float(np.median(latencies_ms)), 4),
        "p99": round(float(np.percentile(latencies_ms, 99)), 4),
        "unit": "milliseconds",
        "samples": len(latencies_ms),
        "measurement": "single-row model.predict_proba calls on LinuxONE",
    }


def save_evidence(
    y_test: pd.Series,
    predictions: np.ndarray,
    feature_importances: dict[str, float],
) -> list[list[int]]:
    EVIDENCE_DIR.mkdir(exist_ok=True)
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])

    fig, axis = plt.subplots(figsize=(6.4, 5.4))
    image = axis.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    axis.set(
        xticks=[0, 1],
        yticks=[0, 1],
        xticklabels=["Legit", "Scam"],
        yticklabels=["Legit", "Scam"],
        xlabel="Predicted label",
        ylabel="Actual label",
        title="Gradient boosting confusion matrix\nSynthetic test set (10,000 payments)",
    )
    cutoff = matrix.max() / 2
    for row in range(2):
        for column in range(2):
            axis.text(
                column,
                row,
                f"{matrix[row, column]:,}",
                ha="center",
                va="center",
                color="white" if matrix[row, column] > cutoff else "#0F172A",
                fontsize=13,
                fontweight="bold",
            )
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "confusion_matrix.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    ordered = sorted(feature_importances.items(), key=lambda item: item[1])
    labels = [name.replace("_", " ") for name, _ in ordered]
    values = [value for _, value in ordered]
    fig, axis = plt.subplots(figsize=(8, 5.8))
    axis.barh(labels, values, color="#0F62FE")
    axis.set(
        xlabel="Relative importance",
        title="Gradient boosting feature importance\nTrained on synthetic payment data",
    )
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="x", alpha=0.2)
    axis.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(EVIDENCE_DIR / "feature_importance.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return matrix.astype(int).tolist()


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
    rules_threshold = 55
    rules_predictions = rules_only_predictions(x_test, rules_threshold)
    feature_importances = dict(zip(FEATURES, model.feature_importances_.tolist()))
    matrix = save_evidence(y_test, predictions, feature_importances)

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
        "metrics": {
            "gradient_boosting_model": classification_metrics(y_test, predictions),
            "rules_only_baseline": {
                "decision_threshold": rules_threshold,
                **classification_metrics(y_test, rules_predictions),
            },
        },
        "milliseconds_per_decision": measure_single_decision_latency(model, x_test),
        "confusion_matrix": {
            "labels": ["legit", "scam"],
            "values": matrix,
        },
    }
    bundle = {
        "model": model,
        "features": FEATURES,
        "threshold": threshold,
        "feature_importances": feature_importances,
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
