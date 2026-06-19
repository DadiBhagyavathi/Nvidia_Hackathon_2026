"use client";
// frontend/components/EvidencePanel.tsx

import { EvidencePassage } from "@/lib/api";
import { BookOpen, ExternalLink } from "lucide-react";

interface Props {
  passages: EvidencePassage[];
}

export default function EvidencePanel({ passages }: Props) {
  if (!passages || passages.length === 0) return null;

  return (
    <div className="card space-y-4">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
        <BookOpen className="w-4 h-4" /> Regulatory Evidence (RAG)
      </h2>

      <div className="space-y-3">
        {passages.map((p, i) => (
          <div key={p.id || i} className="bg-gray-800 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-blue-400 font-medium flex items-center gap-1.5">
                <ExternalLink className="w-3 h-3" />
                {p.source}
              </span>
              <span className="text-xs text-gray-500">
                Relevance: {(p.score * 100).toFixed(0)}%
              </span>
            </div>
            {/* Relevance bar */}
            <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${p.score * 100}%` }}
              />
            </div>
            <p className="text-xs text-gray-300 leading-relaxed line-clamp-4">{p.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
