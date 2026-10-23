"""SQLite audit log (stdlib sqlite3, parameterised queries only)."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "audit.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    transaction_id TEXT PRIMARY KEY,
    timestamp      TEXT NOT NULL,
    amount         REAL NOT NULL,
    payee_name     TEXT NOT NULL,
    payee_account  TEXT,
    new_payee      INTEGER NOT NULL,
    risk_score     REAL NOT NULL,
    decision       TEXT NOT NULL,
    reasons        TEXT NOT NULL,
    model_version  TEXT NOT NULL,
    user_action    TEXT
)
"""

COLUMNS = (
    "transaction_id, timestamp, amount, payee_name, payee_account, new_payee, "
    "risk_score, decision, reasons, model_version, user_action"
)


def mask_account(account: Optional[str]) -> Optional[str]:
    """Keep only the last 4 characters, e.g. '****1234'. Never store the full number."""
    if not account:
        return None
    cleaned = "".join(account.split())
    return "****" + cleaned[-4:]


def db_path() -> str:
    return os.environ.get("AUDIT_DB_PATH") or str(DEFAULT_DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(SCHEMA)


def record_decision(
    transaction_id: str,
    amount: float,
    payee_name: str,
    payee_account: Optional[str],
    new_payee: bool,
    risk_score: float,
    decision: str,
    reasons: List[str],
    model_version: str,
) -> None:
    user_action = "auto_sent" if decision == "allow" else None
    with _connect() as conn:
        conn.execute(
            f"INSERT INTO audit_log ({COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                transaction_id,
                datetime.now(timezone.utc).isoformat(),
                amount,
                payee_name,
                mask_account(payee_account),
                int(new_payee),
                risk_score,
                decision,
                json.dumps(reasons),
                model_version,
                user_action,
            ),
        )


def record_action(transaction_id: str, action: str) -> bool:
    """Returns False if the transaction does not exist."""
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE audit_log SET user_action = ? WHERE transaction_id = ?",
            (action, transaction_id),
        )
        return cur.rowcount > 0


def recent_entries(limit: int = 50) -> List[dict]:
    with _connect() as conn:
        # rowid breaks ties when two inserts share a timestamp
        rows = conn.execute(
            f"SELECT {COLUMNS} FROM audit_log ORDER BY timestamp DESC, rowid DESC LIMIT ?",
            (limit,),
        ).fetchall()
    entries = []
    for row in rows:
        entry = dict(row)
        entry["new_payee"] = bool(entry["new_payee"])
        entry["reasons"] = json.loads(entry["reasons"])
        entries.append(entry)
    return entries
