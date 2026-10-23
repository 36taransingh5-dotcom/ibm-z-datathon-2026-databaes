# Backend API

FastAPI service that scores a payment **before** it is sent. It returns a risk score, an `allow`/`pause` decision and plain-English reasons, and it records every decision in a SQLite audit log. It is built to run on the IBM LinuxONE VM (s390x).

## Run

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Tests: `python -m pytest -q` (from `backend/`).

| Env var           | Default              | Meaning                                          |
|-------------------|----------------------|--------------------------------------------------|
| `PAUSE_THRESHOLD` | `0.5`                | `risk_score >= threshold` → `"pause"`            |
| `MODEL_PATH`      | `backend/model.pkl`  | Loaded at startup if present, else placeholder rules |
| `AUDIT_DB_PATH`   | `backend/audit.db`   | SQLite audit log file                            |

## API contract

### `POST /score`

Request:

```json
{
  "amount": 250.0,                 // required, > 0, GBP
  "payee_name": "Jane Smith",      // required
  "payee_account": "12345678",     // optional, stored masked as ****5678
  "new_payee": true,               // required
  "reference": "Rent",             // optional
  "account_age_days": 365,         // optional, default 365
  "payments_last_24h": 0,          // optional, default 0
  "avg_payment_amount": 100.0,     // optional, default 100.0
  "hour_of_day": 14                // optional 0-23, default = current server hour
}
```

Response:

```json
{
  "transaction_id": "uuid",
  "risk_score": 0.9,
  "decision": "allow | pause",
  "reasons": ["This is a new payee you have never paid before", "..."],
  "model_version": "placeholder-rules-v1 | model.pkl",
  "latency_ms": 0.8
}
```

Bad input (for example a negative amount, or an hour outside 0-23) returns `422`.

### `POST /audit/{transaction_id}/action`

Body `{"action": "confirmed" | "cancelled"}`. This records the user's choice on the pause screen and returns `404` for an unknown id. Allowed payments are recorded as `auto_sent` automatically.

### `GET /audit?limit=50`

Returns the newest entries first. Each entry has these fields: `transaction_id`, `timestamp` (UTC ISO), `amount`, `payee_name`, `payee_account` (masked), `new_payee`, `risk_score`, `decision`, `reasons`, `model_version`, `user_action`.

### `GET /health`

`{"status": "ok", "model_loaded": false, "model_version": "placeholder-rules-v1", "platform": "s390x", "python": "3.x.y"}`

## Model features (for `model.pkl`)

Train on exactly these columns in this order (see `FEATURES` in `app/scoring.py`). The backend calls `predict_proba(X)[0][1]`:

```
amount, amount_ratio, new_payee, account_age_days, payments_last_24h, hour_of_day, night_time, scam_keyword
```

Reasons always come from the transparent rules, even when the model is loaded.

## curl examples

Allow:

```bash
curl -s -X POST http://localhost:8000/score -H 'Content-Type: application/json' \
  -d '{"amount":45,"payee_name":"Jane Smith","payee_account":"12345678","new_payee":false,"reference":"Dinner","hour_of_day":19}'
# {"decision":"allow","risk_score":0.0,"reasons":["No warning signs found"],...}
```

Pause:

```bash
curl -s -X POST http://localhost:8000/score -H 'Content-Type: application/json' \
  -d '{"amount":2500,"payee_name":"Secure Holdings Ltd","payee_account":"87654321","new_payee":true,"reference":"Move money to safe account - URGENT","avg_payment_amount":120,"hour_of_day":23}'
# {"decision":"pause","risk_score":1.0,"reasons":["This is a new payee you have never paid before","This payment is 21x your usual amount","The reference mentions 'safe account', a common scam phrase","This payment is being made late at night, when scams are more common"],...}
```

Record the user's choice, then view the log and health:

```bash
curl -s -X POST http://localhost:8000/audit/<transaction_id>/action -H 'Content-Type: application/json' -d '{"action":"cancelled"}'
curl -s "http://localhost:8000/audit?limit=10"
curl -s http://localhost:8000/health
```
