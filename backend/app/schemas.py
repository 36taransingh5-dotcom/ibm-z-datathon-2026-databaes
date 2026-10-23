"""Pydantic request/response models. Field names are the API contract shared
with the frontend and model teammates; do not rename them."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount in GBP")
    payee_name: str = Field(..., min_length=1)
    payee_account: Optional[str] = None
    new_payee: bool
    reference: Optional[str] = None
    account_age_days: int = Field(365, ge=0)
    payments_last_24h: int = Field(0, ge=0)
    avg_payment_amount: float = Field(100.0, gt=0)
    hour_of_day: Optional[int] = Field(None, ge=0, le=23, description="Defaults to the current server hour")


class ScoreResponse(BaseModel):
    transaction_id: str
    risk_score: float
    decision: Literal["allow", "pause"]
    reasons: List[str]
    model_version: str
    latency_ms: float


class ActionRequest(BaseModel):
    action: Literal["confirmed", "cancelled"]


class ActionResponse(BaseModel):
    transaction_id: str
    user_action: str


class AuditEntry(BaseModel):
    transaction_id: str
    timestamp: str
    amount: float
    payee_name: str
    payee_account: Optional[str]
    new_payee: bool
    risk_score: float
    decision: str
    reasons: List[str]
    model_version: str
    user_action: Optional[str]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
    platform: str
    python: str
