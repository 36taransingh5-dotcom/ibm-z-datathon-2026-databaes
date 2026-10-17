"""FastAPI payment scam prevention demo for SSF2026."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from audit import get_entry, initialise, list_entries, record, update_status
from risk_engine import assess_payment


ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=ROOT / "templates")


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialise()
    yield


app = FastAPI(title="Payment Shield", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/assess", response_class=HTMLResponse)
async def assess(
    request: Request,
    payee: str = Form(...),
    amount: float = Form(..., gt=0),
    usual_amount: float = Form(..., gt=0),
    new_payee: bool = Form(False),
    payee_age_hours: float = Form(720, ge=0),
    hour: int = Form(..., ge=0, le=23),
    device_change: bool = Form(False),
    typing_time_seconds: float = Form(8, ge=0),
    pasted_payee: bool = Form(False),
    on_call: bool = Form(False),
):
    payment = {
        "amount": amount,
        "usual_amount": usual_amount,
        "new_payee": new_payee,
        "payee_age_hours": payee_age_hours,
        "hour": hour,
        "device_change": device_change,
        "typing_time_seconds": typing_time_seconds,
        "pasted_payee": pasted_payee,
        "on_call": on_call,
    }
    assessment = assess_payment(payment)
    entry_id = uuid4().hex[:12]
    status = "paused" if assessment["flagged"] else "approved"
    record(entry_id, payee.strip() or "Unnamed recipient", payment, assessment, status)

    if assessment["flagged"]:
        return templates.TemplateResponse(
            request,
            "review.html",
            {
                "entry_id": entry_id,
                "payee": payee,
                "payment": payment,
                "assessment": assessment,
            },
        )
    return templates.TemplateResponse(request, "outcome.html", {
        "entry_id": entry_id, "payee": payee, "status": "approved"
    })


@app.post("/decision/{entry_id}", response_class=HTMLResponse)
async def decision(request: Request, entry_id: str, action: str = Form(...)):
    if action not in {"confirm", "cancel"}:
        raise HTTPException(status_code=400, detail="Unknown action")
    entry = get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    status = "confirmed" if action == "confirm" else "cancelled"
    update_status(entry_id, status)
    return templates.TemplateResponse(request, "outcome.html", {
        "entry_id": entry_id, "payee": entry["payee"], "status": status
    })


@app.get("/audit", response_class=HTMLResponse)
async def audit_page(request: Request):
    return templates.TemplateResponse(
        request, "audit.html", {"entries": list_entries()}
    )


@app.get("/health")
async def health():
    return {"status": "ok", "event": "SSF2026"}
