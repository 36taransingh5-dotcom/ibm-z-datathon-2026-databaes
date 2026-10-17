"""FastAPI app: score payments before they are sent and keep an audit log.

Run from the backend folder:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import os
import platform
import time
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import audit
from .schemas import (
    ActionRequest,
    ActionResponse,
    AuditEntry,
    HealthResponse,
    PaymentRequest,
    ScoreResponse,
)
from .scoring import Scorer

scorer = Scorer()


def pause_threshold() -> float:
    return float(os.environ.get("PAUSE_THRESHOLD", "0.5"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    audit.init_db()
    scorer.load()
    yield


app = FastAPI(title="databaes payment scam prevention API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/score", response_model=ScoreResponse)
def score_payment(payment: PaymentRequest) -> ScoreResponse:
    start = time.perf_counter()
    risk_score, reasons, model_version = scorer.score(payment)
    decision = "pause" if risk_score >= pause_threshold() else "allow"
    transaction_id = str(uuid.uuid4())
    audit.record_decision(
        transaction_id=transaction_id,
        amount=payment.amount,
        payee_name=payment.payee_name,
        payee_account=payment.payee_account,
        new_payee=payment.new_payee,
        risk_score=risk_score,
        decision=decision,
        reasons=reasons,
        model_version=model_version,
    )
    latency_ms = round((time.perf_counter() - start) * 1000, 3)
    return ScoreResponse(
        transaction_id=transaction_id,
        risk_score=risk_score,
        decision=decision,
        reasons=reasons,
        model_version=model_version,
        latency_ms=latency_ms,
    )


@app.post("/audit/{transaction_id}/action", response_model=ActionResponse)
def record_action(transaction_id: str, body: ActionRequest) -> ActionResponse:
    if not audit.record_action(transaction_id, body.action):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return ActionResponse(transaction_id=transaction_id, user_action=body.action)


@app.get("/audit", response_model=List[AuditEntry])
def get_audit(limit: int = Query(50, ge=1, le=1000)) -> List[dict]:
    return audit.recent_entries(limit)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=scorer.model_loaded,
        model_version=scorer.model_version,
        platform=platform.machine(),
        python=platform.python_version(),
    )
