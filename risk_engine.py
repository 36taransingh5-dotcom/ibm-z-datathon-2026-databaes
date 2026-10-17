"""Combine the trained model with transparent safety rules."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "artifacts" / "payment_scam_model.joblib"


@lru_cache(maxsize=1)
def load_bundle() -> dict:
    if not MODEL_PATH.exists():
        raise RuntimeError("Model missing. Run: python3 generate_and_train.py")
    return joblib.load(MODEL_PATH)


def _feature_values(payment: dict) -> dict:
    values = {
        "amount": float(payment["amount"]),
        "new_payee": int(bool(payment["new_payee"])),
        "payee_age_hours": float(payment["payee_age_hours"]),
        "hour": int(payment["hour"]),
        "device_change": int(bool(payment["device_change"])),
        "typing_time_seconds": float(payment["typing_time_seconds"]),
        "pasted_payee": int(bool(payment["pasted_payee"])),
        "on_call": int(bool(payment["on_call"])),
        "usual_amount": float(payment["usual_amount"]),
    }
    values["amount_ratio"] = values["amount"] / max(values["usual_amount"], 1)
    return values


def assess_payment(payment: dict) -> dict:
    bundle = load_bundle()
    values = _feature_values(payment)
    frame = pd.DataFrame([values], columns=bundle["features"])
    model_probability = float(bundle["model"].predict_proba(frame)[0, 1])

    rules = []

    def add(feature: str, points: int, reason: str) -> None:
        rules.append({"feature": feature, "points": points, "reason": reason})

    if values["new_payee"] and values["payee_age_hours"] < 24:
        add("payee_age_hours", 18, "the recipient was added less than 24 hours ago")
    if values["amount_ratio"] >= 3:
        add("amount_ratio", 24, "the amount is over three times your usual payment")
    elif values["amount_ratio"] >= 1.75:
        add("amount_ratio", 13, "the amount is well above your usual payment")
    if values["on_call"]:
        add("on_call", 20, "you indicated that someone is currently on the phone with you")
    if values["pasted_payee"]:
        add("pasted_payee", 11, "the recipient details were pasted rather than typed")
    if values["device_change"]:
        add("device_change", 13, "this payment is being made from a changed device")
    if values["typing_time_seconds"] >= 30:
        add("typing_time_seconds", 8, "there was an unusually long hesitation while entering it")
    if values["hour"] <= 3 or values["hour"] >= 22:
        add("hour", 6, "the payment is being made at an unusual hour")

    rule_score = min(100, sum(rule["points"] for rule in rules))
    score = round(min(100, (model_probability * 70) + (rule_score * 0.30)))
    flagged = score >= 55

    importance = bundle["feature_importances"]
    ranked = sorted(rules, key=lambda rule: importance.get(rule["feature"], 0), reverse=True)
    top_reasons = [rule["reason"] for rule in ranked[:3]]
    if flagged and top_reasons:
        reason = "We paused this payment because " + "; ".join(top_reasons) + "."
    elif flagged:
        reason = "We paused this payment because its overall pattern differs from your usual behaviour."
    else:
        reason = "No strong scam pattern was detected."

    return {
        "risk_score": score,
        "risk_level": "high" if flagged else "low",
        "flagged": flagged,
        "reason": reason,
        "top_reasons": top_reasons,
        "model_probability": round(model_probability, 4),
        "rule_score": rule_score,
    }
