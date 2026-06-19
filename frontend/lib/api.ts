// frontend/lib/api.ts
// Typed wrapper around the FastAPI backend

import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_URL, timeout: 60000 });

// ── Types ────────────────────────────────────────────────────────────────────

export interface Transaction {
  step: number;
  type: string;
  amount: number;
  nameOrig: string;
  oldbalanceOrg: number;
  newbalanceOrig: number;
  nameDest: string;
  oldbalanceDest: number;
  newbalanceDest: number;
}

export interface ShapReason {
  feature: string;
  label: string;
  value: number;
  shap_value: number;
  direction: "increases_risk" | "decreases_risk";
}

export interface EvidencePassage {
  id: string;
  text: string;
  source: string;
  score: number;
}

export interface AnalyzeResult {
  case_id: string;
  fraud_probability: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  top_reasons: ShapReason[];
  narrative: string;
  evidence_passages: EvidencePassage[];
  report_markdown: string;
  recommended_action: string;
  saved: boolean;
}

export interface Report {
  id: string;
  case_id: string;
  transaction_type: string;
  amount: number;
  sender_id: string;
  receiver_id: string;
  fraud_probability: number;
  risk_level: string;
  recommended_action: string;
  report_markdown: string;
  top_reasons: ShapReason[];
  narrative: string;
  created_at: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  sources: string[];
}

// ── API Functions ─────────────────────────────────────────────────────────────

export async function analyzeTransaction(txn: Transaction): Promise<AnalyzeResult> {
  const { data } = await client.post<AnalyzeResult>("/analyze", txn);
  return data;
}

export async function fetchReports(limit = 20, offset = 0): Promise<Report[]> {
  const { data } = await client.get<{ reports: Report[] }>("/reports", {
    params: { limit, offset },
  });
  return data.reports;
}

export async function fetchReport(caseId: string): Promise<Report> {
  const { data } = await client.get<Report>(`/reports/${caseId}`);
  return data;
}

export async function sendChatMessage(
  message: string,
  sessionId: string,
  caseId?: string
): Promise<ChatResponse> {
  const { data } = await client.post<ChatResponse>("/chat", {
    message,
    session_id: sessionId,
    case_id: caseId,
  });
  return data;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const { data } = await client.get("/health");
    return data.status === "ok";
  } catch {
    return false;
  }
}
