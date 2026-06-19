"use client";
// frontend/components/ReportPanel.tsx

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FileText, Copy, ChevronDown, ChevronUp } from "lucide-react";
import toast from "react-hot-toast";

interface Props {
  reportMarkdown: string;
  caseId: string;
}

export default function ReportPanel({ reportMarkdown, caseId }: Props) {
  const [expanded, setExpanded] = useState(true);

  function copyReport() {
    navigator.clipboard.writeText(reportMarkdown);
    toast.success("Report copied to clipboard");
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
          <FileText className="w-4 h-4" /> Investigation Report
        </h2>
        <div className="flex items-center gap-2">
          <button onClick={copyReport}
            className="text-xs flex items-center gap-1 text-gray-400 hover:text-gray-200 transition-colors px-2 py-1 rounded hover:bg-gray-800">
            <Copy className="w-3 h-3" /> Copy
          </button>
          <button onClick={() => setExpanded((e) => !e)}
            className="text-gray-400 hover:text-gray-200 transition-colors">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="prose prose-invert prose-sm max-w-none
          prose-headings:text-gray-200 prose-headings:font-semibold
          prose-p:text-gray-300 prose-li:text-gray-300
          prose-strong:text-gray-100 prose-code:text-blue-300
          prose-table:text-gray-300 prose-th:text-gray-200
          overflow-auto max-h-[600px] pr-1">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {reportMarkdown}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}
