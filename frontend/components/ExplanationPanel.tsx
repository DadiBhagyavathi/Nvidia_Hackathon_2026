"use client";
// frontend/components/ExplanationPanel.tsx

import { ShapReason } from "@/lib/api";
import { TrendingUp, TrendingDown, Brain } from "lucide-react";

interface Props {
  reasons: ShapReason[];
  narrative: string;
}

export default function ExplanationPanel({ reasons, narrative }: Props) {
  const maxAbs = Math.max(...reasons.map((r) => Math.abs(r.shap_value)), 0.01);

  return (
    <div className="card space-y-5">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
        <Brain className="w-4 h-4" /> AI Explanation (SHAP)
      </h2>

      {/* SHAP bar chart */}
      <div className="space-y-3">
        {reasons.map((r, i) => {
          const isRisk   = r.direction === "increases_risk";
          const barWidth = `${(Math.abs(r.shap_value) / maxAbs) * 100}%`;
          return (
            <div key={i} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-300 font-medium truncate max-w-[60%]">{r.label}</span>
                <span className={`flex items-center gap-1 font-mono ${isRisk ? "text-red-400" : "text-green-400"}`}>
                  {isRisk ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  {r.shap_value > 0 ? "+" : ""}{r.shap_value.toFixed(3)}
                </span>
              </div>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${isRisk ? "bg-red-500" : "bg-green-500"}`}
                  style={{ width: barWidth }}
                />
              </div>
              <p className="text-gray-500 text-xs">
                Value: <span className="text-gray-300">{r.value.toLocaleString()}</span>
              </p>
            </div>
          );
        })}
      </div>

      {/* Investigation narrative */}
      <div className="border-t border-gray-800 pt-4">
        <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Investigator Narrative</p>
        <p className="text-sm text-gray-300 leading-relaxed">{narrative}</p>
      </div>
    </div>
  );
}
