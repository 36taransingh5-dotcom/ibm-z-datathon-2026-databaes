import re

from fastapi.testclient import TestClient

from app import app
from risk_engine import assess_payment


def low_risk_payment():
    return {
        "amount": 75,
        "usual_amount": 80,
        "new_payee": False,
        "payee_age_hours": 720,
        "hour": 14,
        "device_change": False,
        "typing_time_seconds": 7,
        "pasted_payee": False,
        "on_call": False,
    }


def high_risk_payment():
    return {
        "amount": 2_000,
        "usual_amount": 100,
        "new_payee": True,
        "payee_age_hours": 1,
        "hour": 1,
        "device_change": True,
        "typing_time_seconds": 60,
        "pasted_payee": True,
        "on_call": True,
    }


def test_risk_engine_separates_obvious_cases():
    low = assess_payment(low_risk_payment())
    high = assess_payment(high_risk_payment())
    assert low["flagged"] is False
    assert high["flagged"] is True
    assert high["risk_score"] > low["risk_score"]
    assert high["top_reasons"]


def test_large_payment_on_call_is_high_risk_for_old_recipient():
    old_recipient = low_risk_payment()
    old_recipient.update(
        {
            "amount": 600,
            "usual_amount": 100,
            "on_call": True,
            "new_payee": False,
            "payee_age_hours": 8_760,
        }
    )
    on_call = assess_payment(old_recipient)

    old_recipient["on_call"] = False
    not_on_call = assess_payment(old_recipient)

    assert on_call["flagged"] is True
    assert on_call["risk_score"] >= 70
    assert on_call["risk_score"] > not_on_call["risk_score"]
    assert "while someone is on the phone" in on_call["reason"]
    assert "recipient was added" not in on_call["reason"]


def test_payment_flow_and_audit_page():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["event"] == "SSF2026"

        low = client.post("/assess", data={"payee": "Jamie", **low_risk_payment()})
        assert low.status_code == 200
        assert "PAYMENT APPROVED" in low.text

        high = client.post("/assess", data={"payee": "Unknown caller", **high_risk_payment()})
        assert high.status_code == 200
        assert "PAYMENT PAUSED" in high.text
        assert "Cancel payment" in high.text

        match = re.search(r'action="/decision/([a-f0-9]+)"', high.text)
        assert match
        cancelled = client.post(
            f"/decision/{match.group(1)}", data={"action": "cancel"}
        )
        assert cancelled.status_code == 200
        assert "PAYMENT CANCELLED" in cancelled.text

        audit = client.get("/audit")
        assert audit.status_code == 200
        assert "Unknown caller" in audit.text
        assert "cancelled" in audit.text
