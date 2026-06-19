"use client";
// frontend/components/ChatPanel.tsx

import { useState, useRef, useEffect } from "react";
import { MessageCircle, Send, Bot, User } from "lucide-react";
import { sendChatMessage } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

interface Props {
  sessionId: string;
  caseId?: string;
}

const STARTER_QUESTIONS = [
  "What are common red flags for money laundering?",
  "When must a bank file an STR under RBI guidelines?",
  "Explain the layering stage of money laundering.",
  "What is the threshold for cash transaction reporting in India?",
];

export default function ChatPanel({ sessionId, caseId }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your AI Fraud Investigator, trained on RBI and AML guidelines. Ask me anything about financial fraud, transaction patterns, or regulatory compliance.",
    },
  ]);
  const [input, setInput]     = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef             = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const msg = text || input.trim();
    if (!msg || loading) return;

    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const res = await sendChatMessage(msg, sessionId, caseId);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.reply, sources: res.sources },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Sorry, I couldn't connect to the AI model. Please check the backend." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card flex flex-col h-[700px]">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2 mb-4 shrink-0">
        <MessageCircle className="w-4 h-4" /> AI Investigator Chat
        {caseId && <span className="text-xs text-blue-400 font-mono ml-auto">{caseId}</span>}
      </h2>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center
              ${m.role === "assistant" ? "bg-blue-600" : "bg-gray-700"}`}>
              {m.role === "assistant" ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
            </div>
            <div className={`max-w-[85%] space-y-1 ${m.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
              <div className={`rounded-xl px-4 py-2.5 text-sm leading-relaxed
                ${m.role === "assistant"
                  ? "bg-gray-800 text-gray-200"
                  : "bg-blue-600 text-white"
                }`}>
                {m.role === "assistant" ? (
                  <div className="prose prose-invert prose-sm max-w-none prose-p:my-1">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                ) : m.content}
              </div>
              {m.sources && m.sources.length > 0 && (
                <p className="text-xs text-gray-500 px-1">
                  Sources: {m.sources.join(", ")}
                </p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-gray-800 rounded-xl px-4 py-3 flex items-center gap-1">
              {[0, 150, 300].map((d) => (
                <span key={d} className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: `${d}ms` }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Starter questions */}
      {messages.length === 1 && (
        <div className="shrink-0 flex flex-wrap gap-2 py-3 border-t border-gray-800">
          {STARTER_QUESTIONS.map((q) => (
            <button key={q} onClick={() => handleSend(q)}
              className="text-xs px-3 py-1.5 rounded-full border border-gray-700 hover:border-blue-500 hover:text-blue-400 transition-colors text-gray-400">
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="shrink-0 flex gap-2 pt-3 border-t border-gray-800">
        <input
          type="text"
          className="input-field flex-1"
          placeholder="Ask about fraud patterns, regulations, or this case…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          disabled={loading}
        />
        <button onClick={() => handleSend()} disabled={loading || !input.trim()}
          className="btn-primary px-3">
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
