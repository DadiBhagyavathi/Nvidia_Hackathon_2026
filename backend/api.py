"""
api.py
──────
Location : backend/api.py
Run      : uvicorn backend.api:app --reload --port 8000
Purpose  : Production-ready FastAPI application for the
           Explainable Fraud Investigation Agent.
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, Field

from backend.agents.detection_agent import detection_agent
from backend.agents.evidence_agent import evidence_agent
from backend.agents.investigation_agent import investigation_agent
from backend.agents.report_agent import report_agent
from backend.core.config import settings
from backend.core.logger import configure_logging
from backend.db.database import (
    save_report,
    get_reports,
    get_report_by_case_id,
    save_chat_message,
    get_chat_history,
)
from backend.rag.rag_pipeline import rag_query


configure_logging()

nim_client = OpenAI(
    api_key=settings.NVIDIA_API_KEY or "",
    base_url=settings.NVIDIA_BASE_URL,
)
NIM_MODEL = settings.NIM_MODEL

app = FastAPI(
    title="Explainable Fraud Investigation Agent",
    description="Production-ready FastAPI backend for agentic fraud investigation.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Transaction(BaseModel):
    step: int = Field(..., example=1)
    type: str = Field(..., example="TRANSFER")
    amount: float = Field(..., example=181000.0)
    nameOrig: str = Field(..., example="C1305486145")
    oldbalanceOrg: float = Field(..., example=181000.0)
    newbalanceOrig: float = Field(..., example=0.0)
    nameDest: str = Field(..., example="C553264065")
    oldbalanceDest: float = Field(..., example=0.0)
    newbalanceDest: float = Field(..., example=0.0)


class PredictionResponse(BaseModel):
    fraud_probability: float
    risk_level: str
    top_reasons: List[dict]


class ExplainResponse(BaseModel):
    fraud_probability: float
    risk_level: str
    shap_values: List[float]
    top_reasons: List[dict]


class InvestigateResponse(BaseModel):
    narrative: str
    risk_level: str
    fraud_probability: float


class EvidenceResponse(BaseModel):
    evidence_passages: List[dict]
    sources: List[str]


class ReportResponse(BaseModel):
    case_id: str
    report_markdown: str
    recommended_action: str
    risk_level: str
    fraud_probability: float


class EnvStatusResponse(BaseModel):
    nim_configured: bool
    supabase_configured: bool
    missing_variables: List[str]


class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    case_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    sources: List[str]


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/env", response_model=EnvStatusResponse)
def env_status():
    return {
        "nim_configured": settings.is_nim_configured,
        "supabase_configured": settings.is_supabase_configured,
        "missing_variables": settings.missing_environment(),
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(txn: Transaction):
    try:
        result = detection_agent.run(txn.model_dump())
        return {
            "fraud_probability": result["fraud_probability"],
            "risk_level": result["risk_level"],
            "top_reasons": result["top_reasons"],
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"/predict failed: {exc}")
        raise HTTPException(status_code=500, detail="Prediction failed") from exc


@app.post("/explain", response_model=ExplainResponse)
def explain(txn: Transaction):
    try:
        result = detection_agent.run(txn.model_dump())
        return {
            "fraud_probability": result["fraud_probability"],
            "risk_level": result["risk_level"],
            "shap_values": result["shap_values"],
            "top_reasons": result["top_reasons"],
        }
    except Exception as exc:
        logger.error(f"/explain failed: {exc}")
        raise HTTPException(status_code=500, detail="Explanation failed") from exc


@app.post("/investigate", response_model=InvestigateResponse)
def investigate(txn: Transaction):
    if not settings.is_nim_configured:
        raise HTTPException(
            status_code=503,
            detail="NVIDIA NIM is not configured. Set NVIDIA_API_KEY in environment.",
        )
    try:
        detection = detection_agent.run(txn.model_dump())
        investigation = investigation_agent.run(detection)
        return {
            "narrative": investigation["narrative"],
            "risk_level": investigation["risk_level"],
            "fraud_probability": investigation["fraud_probability"],
        }
    except Exception as exc:
        logger.error(f"/investigate failed: {exc}")
        raise HTTPException(status_code=500, detail="Investigation failed") from exc


@app.post("/evidence", response_model=EvidenceResponse)
def evidence(txn: Transaction):
    try:
        detection = detection_agent.run(txn.model_dump())
        investigation = investigation_agent.run(detection)
        evidence_result = evidence_agent.run(investigation)
        return {
            "evidence_passages": evidence_result["evidence_passages"],
            "sources": evidence_result["sources"],
        }
    except Exception as exc:
        logger.error(f"/evidence failed: {exc}")
        raise HTTPException(status_code=500, detail="Evidence retrieval failed") from exc


@app.post("/report", response_model=ReportResponse)
def report(txn: Transaction, background_tasks: BackgroundTasks):
    if not settings.is_supabase_configured:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY in environment.",
        )
    if not settings.is_nim_configured:
        raise HTTPException(
            status_code=503,
            detail="NVIDIA NIM is not configured. Set NVIDIA_API_KEY in environment.",
        )

    case_id = f"FIA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"
    try:
        detection = detection_agent.run(txn.model_dump())
        investigation = investigation_agent.run(detection)
        evidence_result = evidence_agent.run(investigation)
        report_result = report_agent.run(detection, investigation, evidence_result, case_id)

        background_tasks.add_task(
            save_report,
            case_id=case_id,
            transaction=txn.model_dump(),
            fraud_probability=report_result["fraud_probability"],
            risk_level=report_result["risk_level"],
            recommended_action=report_result["recommended_action"],
            report_markdown=report_result["report_markdown"],
            top_reasons=detection["top_reasons"],
            narrative=investigation["narrative"],
        )

        return {
            "case_id": report_result["case_id"],
            "report_markdown": report_result["report_markdown"],
            "recommended_action": report_result["recommended_action"],
            "risk_level": report_result["risk_level"],
            "fraud_probability": report_result["fraud_probability"],
        }
    except Exception as exc:
        logger.error(f"/report failed: {exc}")
        raise HTTPException(status_code=500, detail="Report generation failed") from exc


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not settings.is_nim_configured:
        raise HTTPException(
            status_code=503,
            detail="NVIDIA NIM is not configured. Set NVIDIA_API_KEY in environment.",
        )

    session_id = req.session_id
    user_msg = req.message

    rag_docs = rag_query(user_msg, top_k=3)
    context = (
        "\n\n".join(
            f"[Source: {d['source']}]\n{d['text']}"
            for d in rag_docs
        )
        if rag_docs
        else "No regulatory documents indexed yet."
    )

    history = get_chat_history(session_id, limit=10)
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert AI Fraud Investigator trained on RBI, PMLA, and AML guidelines. "
                "Answer questions about financial fraud, transaction patterns, and regulatory compliance. "
                "Use the provided context to ground your answers.\n\n"
                f"Regulatory Context:\n{context}"
            ),
        }
    ]

    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": user_msg})

    try:
        response = nim_client.chat.completions.create(
            model=NIM_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=600,
        )
        assistant_msg = response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error(f"NIM chat error: {exc}")
        raise HTTPException(status_code=502, detail="AI model error") from exc

    try:
        save_chat_message(session_id, "user", user_msg)
        save_chat_message(session_id, "assistant", assistant_msg)
    except Exception:
        logger.warning("Failed to persist chat history.")

    return {"session_id": session_id, "reply": assistant_msg, "sources": [d["source"] for d in rag_docs]}


@app.get("/reports")
def list_reports(limit: int = 20, offset: int = 0):
    try:
        reports = get_reports(limit=limit, offset=offset)
        return {"reports": reports, "count": len(reports)}
    except Exception as exc:
        logger.error(f"/reports failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports") from exc


@app.get("/reports/{case_id}")
def get_report(case_id: str):
    try:
        report_data = get_report_by_case_id(case_id)
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")
        return report_data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"/reports/{case_id} failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report") from exc
