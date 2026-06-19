"use client";
// frontend/components/FraudScoreGauge.tsx

import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from "recharts";

interface Props {
  probability: number;
  riskLevel: string;
  recommendedAction: string;
  caseId: string;
}

const RISK_COLORS: Record<string, string> = {
  LOW: "#22c55e", MEDIUM: "#eab308", HIGH: "#f97316", CRITICAL: "#ef4444",
};

const RISK_BG: Record<string, string> = {
  LOW: "bg-green-950 border-green-800",
  MEDIUM: "bg-yellow-950 border-yellow-800",
  HIGH: "bg-orange-950 border-orange-800",
  CRITICAL: "bg-red-950 border-red-800",
};

export default function FraudScoreGauge({ probability, riskLevel, recommendedAction, caseId }: Props) {
  const pct   = Math.round(probability * 100);
  const color = RISK_COLORS[riskLevel] || "#6b7280";
  const data  = [{ value: pct, fill: color }];

  return (
    <div className="text-center space-y-3">
      <p className="text-xs text-gray-400 uppercase tracking-wider">Fraud Risk Score</p>

      {/* Radial gauge */}
      <div className="relative h-44">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%" cy="70%"
            innerRadius="60%" outerRadius="90%"
            startAngle={180} endAngle={0}
            data={data}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar dataKey="value" cornerRadius={8} background={{ fill: "#1f2937" }} />
          </RadialBarChart>
        </ResponsiveContainer>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pt-10">
          <span className="text-4xl font-bold tabular-nums" style={{ color }}>
            {pct}%
          </span>
          <span className="text-xs text-gray-400">fraud probability</span>
        </div>
      </div>

      {/* Risk badge */}
      <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full border text-sm font-semibold ${RISK_BG[riskLevel]}`}
        style={{ color }}>
        <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: color }} />
        {riskLevel} RISK
      </div>

      {/* Action + Case ID */}
      <div className="space-y-1">
        <p className="text-sm font-semibold text-gray-200">
          Action: <span style={{ color }}>{recommendedAction}</span>
        </p>
        <p className="text-xs text-gray-500 font-mono">{caseId}</p>
      </div>
    </div>
  );
}
