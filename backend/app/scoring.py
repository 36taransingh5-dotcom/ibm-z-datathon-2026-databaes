"""Feature extraction, transparent placeholder rules and optional model loading."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# MODEL TEAMMATE: train model.pkl on exactly these columns, in exactly this order.
# extract_features() builds the vector in this order and the model is called with it.
FEATURES = [
    "amount",
    "amount_ratio",  # amount / avg_payment_amount
    "new_payee",  # 0/1
    "account_age_days",
    "payments_last_24h",
    "hour_of_day",
    "night_time",  # 1 if hour < 6 or hour >= 23
    "scam_keyword",  # 1 if reference contains any SCAM_KEYWORDS (case-insensitive)
]

SCAM_KEYWORDS = [
    "safe account",
    "hmrc",
    "tax refund",
    "crypto",
    "bitcoin",
    "investment",
    "urgent",
    "police",
    "bank security",
    "gift card",
]

PLACEHOLDER_VERSION = "placeholder-rules-v1"
MODEL_VERSION = "model.pkl"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "model.pkl"

logger = logging.getLogger(__name__)


def _resolve_hour(payment) -> int:
    return payment.hour_of_day if payment.hour_of_day is not None else datetime.now().hour


def find_scam_keyword(reference: Optional[str]) -> Optional[str]:
    text = (reference or "").lower()
    for keyword in SCAM_KEYWORDS:
        if keyword in text:
            return keyword
    return None


def extract_features(payment) -> List[float]:
    """Return the feature vector in FEATURES order."""
    hour = _resolve_hour(payment)
    return [
        float(payment.amount),
        float(payment.amount / payment.avg_payment_amount),
        1.0 if payment.new_payee else 0.0,
        float(payment.account_age_days),
        float(payment.payments_last_24h),
        float(hour),
        1.0 if hour < 6 or hour >= 23 else 0.0,
        1.0 if find_scam_keyword(payment.reference) else 0.0,
    ]


def rule_score(payment) -> Tuple[float, List[str]]:
    """Transparent weighted rules. Each rule that fires adds weight and a reason."""
    f = dict(zip(FEATURES, extract_features(payment)))
    score = 0.0
    reasons: List[str] = []

    if f["new_payee"]:
        score += 0.2
        reasons.append("This is a new payee you have never paid before")

    ratio = f["amount_ratio"]
    if ratio >= 10:
        score += 0.35
        reasons.append(f"This payment is {ratio:.0f}x your usual amount")
    elif ratio >= 3:
        score += 0.15
        reasons.append(f"This payment is {ratio:.0f}x your usual amount")

    keyword = find_scam_keyword(payment.reference)
    if keyword:
        score += 0.35
        reasons.append(f"The reference mentions '{keyword}', a common scam phrase")

    if f["night_time"]:
        score += 0.1
        reasons.append("This payment is being made late at night, when scams are more common")

    if f["payments_last_24h"] >= 5:
        score += 0.15
        reasons.append(f"You have made {int(f['payments_last_24h'])} payments in the last 24 hours")

    if f["account_age_days"] < 30:
        score += 0.15
        reasons.append("Your account was opened very recently")

    if not reasons:
        reasons.append("No warning signs found")

    return min(score, 1.0), reasons


class Scorer:
    """Holds the optional ML model; loaded once at startup so requests do no disk I/O."""

    def __init__(self) -> None:
        self.model = None
        self.model_version = PLACEHOLDER_VERSION

    @property
    def model_loaded(self) -> bool:
        return self.model is not None

    def load(self, path: Optional[str] = None) -> None:
        path = path or os.environ.get("MODEL_PATH") or str(DEFAULT_MODEL_PATH)
        self.model = None
        self.model_version = PLACEHOLDER_VERSION
        if not os.path.exists(path):
            logger.info("No model at %s; using %s", path, PLACEHOLDER_VERSION)
            return
        try:
            import joblib

            self.model = joblib.load(path)
            self.model_version = MODEL_VERSION
            logger.info("Loaded model from %s", path)
        except Exception as exc:  # noqa: BLE001 - any load failure falls back to rules
            logger.warning("Failed to load model from %s (%s); using placeholder rules", path, exc)

    def score(self, payment) -> Tuple[float, List[str], str]:
        rules, reasons = rule_score(payment)
        if self.model is not None:
            try:
                prob = float(self.model.predict_proba([extract_features(payment)])[0][1])
                return round(prob, 3), reasons, MODEL_VERSION
            except Exception as exc:  # noqa: BLE001
                logger.warning("Model prediction failed (%s); using placeholder rules", exc)
        return round(rules, 3), reasons, PLACEHOLDER_VERSION
