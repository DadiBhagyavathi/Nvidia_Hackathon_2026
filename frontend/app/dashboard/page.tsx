"use client";
// frontend/app/dashboard/page.tsx
// Main dashboard — orchestrates all panels

import { useState, useId } from "react";
import toast from "react-hot-toast";
import { Shield, Activity, FileText, MessageCircle } from "lucide-react";
import TransactionForm from "@/components/TransactionForm";
import FraudScoreGauge from "@/components/FraudScoreGauge";
import ExplanationPanel from "@/components/ExplanationPanel";
import EvidencePanel from "@/components/EvidencePanel";
import ReportPanel from "@/components/ReportPanel";
import ChatPanel from "@/components/ChatPanel";
import { analyzeTransaction, AnalyzeResult, Transaction } from "@/lib/api";

type Tab = "analyze" | "reports" | "chat";

export default function Dashboard() {
  const [activeTab, setActiveTab]   = useState<Tab>("analyze");
  const [loading, setLoading]       = useState(false);
  const [result, setResult]         = useState<AnalyzeResult | null>(null);
  const sessionId                   = useId();

  async function handleAnalyze(txn: Transaction) {
    setLoading(true);
    setResult(null);
    try {
      const res = await analyzeTransaction(txn);
      setResult(res);
      toast.success(`Analysis complete — Risk: ${res.risk_level}`);
      if (res.risk_level === "CRITICAL" || res.risk_level === "HIGH") {
        toast.error(`⚠️ ${res.recommended_action} recommended`, { duration: 5000 });
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Analysis failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="border-b border-gray-800 bg-gray-950 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="text-blue-500 w-7 h-7" />
            <div>
              <h1 className="font-bold text-lg leading-tight">Fraud Investigation Agent</h1>
              <p className="text-gray-500 text-xs">Powered by NVIDIA NIM · XGBoost · SHAP · RAG</p>
            </div>
          </div>
          <nav className="flex gap-1">
            {(["analyze", "reports", "chat"] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium capitalize transition-colors
                  ${activeTab === tab
                    ? "bg-blue-600 text-white"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
                  }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8">

        {/* ── Analyze Tab ──────────────────────────────────────── */}
        {activeTab === "analyze" && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

            {/* Left column: form + gauge */}
            <div className="xl:col-span-1 space-y-6">
              <div className="card">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4" /> Transaction Input
                </h2>
                <TransactionForm onSubmit={handleAnalyze} loading={loading} />
              </div>

              {result && (
                <div className="card">
                  <FraudScoreGauge
                    probability={result.fraud_probability}
                    riskLevel={result.risk_level}
                    recommendedAction={result.recommended_action}
                    caseId={result.case_id}
                  />
                </div>
              )}
            </div>

            {/* Right columns: results */}
            {result ? (
              <div className="xl:col-span-2 space-y-6">
                <ExplanationPanel
                  reasons={result.top_reasons}
                  narrative={result.narrative}
                />
                <EvidencePanel passages={result.evidence_passages} />
                <ReportPanel
                  reportMarkdown={result.report_markdown}
                  caseId={result.case_id}
                />
              </div>
            ) : (
              <div className="xl:col-span-2 flex items-center justify-center min-h-64">
                <div className="text-center text-gray-600">
                  <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p className="text-sm">Submit a transaction to see the full investigation report</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Reports Tab ──────────────────────────────────────── */}
        {activeTab === "reports" && (
          <ReportsListView />
        )}

        {/* ── Chat Tab ─────────────────────────────────────────── */}
        {activeTab === "chat" && (
          <div className="max-w-2xl mx-auto">
            <ChatPanel sessionId={sessionId} caseId={result?.case_id} />
          </div>
        )}
      </main>
    </div>
  );
}

// ── Mini reports list (inline, no separate page needed) ───────────────────────
function ReportsListView() {
  const [reports, setReports] = useState<any[]>([]);
  const [loaded, setLoaded]   = useState(false);

  async function load() {
    const { fetchReports } = await import("@/lib/api");
    const r = await fetchReports(20);
    setReports(r);
    setLoaded(true);
  }

  if (!loaded) {
    return (
      <div className="text-center py-20">
        <button onClick={load} className="btn-primary">Load Recent Reports</button>
      </div>
    );
  }

  if (reports.length === 0) {
    return <p className="text-center text-gray-500 py-20">No reports yet. Analyze a transaction first.</p>;
  }

  const RISK_COLOR: Record<string, string> = {
    LOW: "text-green-400", MEDIUM: "text-yellow-400",
    HIGH: "text-orange-400", CRITICAL: "text-red-400",
  };

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold mb-4">Investigation Reports</h2>
      {reports.map((r) => (
        <div key={r.id} className="card flex items-center justify-between gap-4">
          <div>
            <p className="font-mono text-sm text-blue-400">{r.case_id}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {r.transaction_type} · ₹{Number(r.amount).toLocaleString("en-IN")} ·{" "}
              {new Date(r.created_at).toLocaleString()}
            </p>
          </div>
          <div className="text-right shrink-0">
            <span className={`font-bold text-sm ${RISK_COLOR[r.risk_level] || "text-gray-400"}`}>
              {r.risk_level}
            </span>
            <p className="text-xs text-gray-500 mt-0.5">{r.recommended_action}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
