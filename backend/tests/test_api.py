import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from app.main import app
from app.scoring import FEATURES

NORMAL_PAYMENT = {
    "amount": 95.0,
    "payee_name": "Jane Smith",
    "payee_account": "12345678",
    "new_payee": False,
    "reference": "Rent share",
    "avg_payment_amount": 100.0,
    "hour_of_day": 14,
}

SCAM_PAYMENT = {
    "amount": 1000.0,
    "payee_name": "Secure Holdings Ltd",
    "payee_account": "87654321",
    "new_payee": True,
    "reference": "move money to safe account",
    "avg_payment_amount": 100.0,
    "hour_of_day": 14,
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "audit.db"))
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "missing_model.pkl"))
    monkeypatch.delenv("PAUSE_THRESHOLD", raising=False)
    with TestClient(app) as c:  # context manager runs startup (DB init + model load)
        yield c


def test_normal_payment_is_allowed(client):
    r = client.post("/score", json=NORMAL_PAYMENT)
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "allow"
    assert body["reasons"] == ["No warning signs found"]
    assert body["model_version"] == "placeholder-rules-v1"
    assert 0 <= body["risk_score"] <= 1
    assert set(body) == {"transaction_id", "risk_score", "decision", "reasons", "model_version", "latency_ms"}


def test_scam_payment_is_paused(client):
    r = client.post("/score", json=SCAM_PAYMENT)
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "pause"
    assert len(body["reasons"]) >= 2
    assert any("safe account" in reason for reason in body["reasons"])
    assert any("10x" in reason for reason in body["reasons"])


@pytest.mark.parametrize(
    "override",
    [{"amount": -5}, {"amount": 0}, {"hour_of_day": 24}, {"hour_of_day": -1}],
)
def test_invalid_input_returns_422(client, override):
    r = client.post("/score", json={**NORMAL_PAYMENT, **override})
    assert r.status_code == 422


def test_audit_newest_first_and_masked(client):
    first = client.post("/score", json=NORMAL_PAYMENT).json()["transaction_id"]
    second = client.post("/score", json=SCAM_PAYMENT).json()["transaction_id"]

    r = client.get("/audit", params={"limit": 50})
    assert r.status_code == 200
    entries = r.json()
    assert [e["transaction_id"] for e in entries] == [second, first]
    assert entries[0]["payee_account"] == "****4321"
    assert entries[1]["payee_account"] == "****5678"
    assert entries[1]["user_action"] == "auto_sent"
    assert entries[0]["user_action"] is None
    assert isinstance(entries[0]["reasons"], list)
    assert "87654321" not in r.text


def test_full_account_never_stored(client, tmp_path):
    import sqlite3

    client.post("/score", json=SCAM_PAYMENT)
    conn = sqlite3.connect(tmp_path / "audit.db")
    stored = conn.execute("SELECT payee_account FROM audit_log").fetchall()
    conn.close()
    assert stored == [("****4321",)]


def test_record_action(client):
    tid = client.post("/score", json=SCAM_PAYMENT).json()["transaction_id"]
    r = client.post(f"/audit/{tid}/action", json={"action": "confirmed"})
    assert r.status_code == 200
    entry = client.get("/audit").json()[0]
    assert entry["transaction_id"] == tid
    assert entry["user_action"] == "confirmed"

    r = client.post("/audit/does-not-exist/action", json={"action": "cancelled"})
    assert r.status_code == 404

    r = client.post(f"/audit/{tid}/action", json={"action": "maybe"})
    assert r.status_code == 422


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is False
    assert isinstance(body["platform"], str) and body["platform"]
    assert body["python"]


def test_model_is_used_when_present(tmp_path, monkeypatch):
    # Tiny model trained on the FEATURES columns: label 1 when scam_keyword is set.
    X, y = [], []
    for i in range(40):
        scam = i % 2
        X.append([50.0 + i, 1.0 + scam * 9, scam, 365, 0, 14, 0, scam])
        y.append(scam)
    assert len(X[0]) == len(FEATURES)
    model_path = tmp_path / "model.pkl"
    joblib.dump(LogisticRegression(max_iter=1000).fit(X, y), model_path)

    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "audit.db"))
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    with TestClient(app) as c:
        health = c.get("/health").json()
        assert health["model_loaded"] is True
        assert health["model_version"] == "model.pkl"

        body = c.post("/score", json=SCAM_PAYMENT).json()
        assert body["model_version"] == "model.pkl"
        assert 0 <= body["risk_score"] <= 1
        assert any("safe account" in reason for reason in body["reasons"])
