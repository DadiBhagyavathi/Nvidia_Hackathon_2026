"""
database.py
───────────
Location : backend/db/database.py
Purpose  : All Supabase read/write operations for investigation reports
           and chat history.

Connects to: report_agent.py (saves reports), api.py (called by endpoints)
"""

import os
from datetime import datetime
from typing import Optional
from loguru import logger
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized.")
    return _client


# ── Reports ───────────────────────────────────────────────────────────────────

def save_report(
    case_id:             str,
    transaction:         dict,
    fraud_probability:   float,
    risk_level:          str,
    recommended_action:  str,
    report_markdown:     str,
    top_reasons:         list,
    narrative:           str,
) -> dict:
    """Insert a new investigation report row into Supabase."""
    db   = get_client()
    data = {
        "case_id":            case_id,
        "transaction_type":   transaction.get("type"),
        "amount":             transaction.get("amount"),
        "sender_id":          transaction.get("nameOrig"),
        "receiver_id":        transaction.get("nameDest"),
        "fraud_probability":  round(fraud_probability, 4),
        "risk_level":         risk_level,
        "recommended_action": recommended_action,
        "report_markdown":    report_markdown,
        "top_reasons":        top_reasons,          # stored as JSONB
        "narrative":          narrative,
        "created_at":         datetime.utcnow().isoformat(),
    }
    result = db.table("investigation_reports").insert(data).execute()
    logger.success(f"Report saved: {case_id}")
    return result.data[0] if result.data else data


def get_reports(limit: int = 20, offset: int = 0) -> list:
    """Fetch recent investigation reports."""
    db     = get_client()
    result = (
        db.table("investigation_reports")
        .select("*")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data or []


def get_report_by_case_id(case_id: str) -> Optional[dict]:
    """Fetch a single report by case ID."""
    db     = get_client()
    result = (
        db.table("investigation_reports")
        .select("*")
        .eq("case_id", case_id)
        .single()
        .execute()
    )
    return result.data


# ── Chat History ──────────────────────────────────────────────────────────────

def save_chat_message(session_id: str, role: str, content: str) -> dict:
    """Save a single chat message."""
    db   = get_client()
    data = {
        "session_id": session_id,
        "role":       role,
        "content":    content,
        "created_at": datetime.utcnow().isoformat(),
    }
    result = db.table("chat_history").insert(data).execute()
    return result.data[0] if result.data else data


def get_chat_history(session_id: str, limit: int = 20) -> list:
    """Retrieve recent messages for a chat session."""
    db     = get_client()
    result = (
        db.table("chat_history")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data or []
