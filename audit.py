"""Small SQLite-backed audit trail for demo decisions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "data" / "audit.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialise() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                payee TEXT NOT NULL,
                amount REAL NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT NOT NULL
            )
            """
        )


def record(entry_id: str, payee: str, payment: dict, assessment: dict, status: str) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO audit_log
            (id, created_at, payee, amount, risk_score, risk_level, reason, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                payee,
                payment["amount"],
                assessment["risk_score"],
                assessment["risk_level"],
                assessment["reason"],
                status,
                json.dumps({"payment": payment, "assessment": assessment}),
            ),
        )


def update_status(entry_id: str, status: str) -> bool:
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE audit_log SET status = ? WHERE id = ?", (status, entry_id)
        )
        return cursor.rowcount == 1


def get_entry(entry_id: str) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM audit_log WHERE id = ?", (entry_id,)
        ).fetchone()
    return dict(row) if row else None


def list_entries(limit: int = 100) -> list[dict]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]
