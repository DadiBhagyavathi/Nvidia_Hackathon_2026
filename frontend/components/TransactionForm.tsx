"use client";
// frontend/components/TransactionForm.tsx

import { useState } from "react";
import { Transaction } from "@/lib/api";

const TRANSACTION_TYPES = ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"];

// Demo presets for hackathon demo
const PRESETS = {
  "High Fraud (TRANSFER)": {
    step: 1, type: "TRANSFER", amount: 181000,
    nameOrig: "C1305486145", oldbalanceOrg: 181000, newbalanceOrig: 0,
    nameDest: "C553264065", oldbalanceDest: 0, newbalanceDest: 0,
  },
  "Legit Payment": {
    step: 5, type: "PAYMENT", amount: 9839.64,
    nameOrig: "C1231006815", oldbalanceOrg: 170136, newbalanceOrig: 160296.36,
    nameDest: "M1979787155", oldbalanceDest: 0, newbalanceDest: 0,
  },
  "Suspicious CASH_OUT": {
    step: 3, type: "CASH_OUT", amount: 500000,
    nameOrig: "C840083671", oldbalanceOrg: 500000, newbalanceOrig: 0,
    nameDest: "C38997010", oldbalanceDest: 0, newbalanceDest: 0,
  },
};

interface Props {
  onSubmit: (txn: Transaction) => void;
  loading: boolean;
}

export default function TransactionForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<Transaction>({
    step: 1, type: "TRANSFER", amount: 0,
    nameOrig: "", oldbalanceOrg: 0, newbalanceOrig: 0,
    nameDest: "", oldbalanceDest: 0, newbalanceDest: 0,
  });

  function set(key: keyof Transaction, value: string | number) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function applyPreset(key: string) {
    setForm(PRESETS[key as keyof typeof PRESETS] as Transaction);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit(form);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Presets */}
      <div>
        <p className="text-xs text-gray-500 mb-2">Quick presets:</p>
        <div className="flex flex-wrap gap-2">
          {Object.keys(PRESETS).map((k) => (
            <button
              key={k} type="button"
              onClick={() => applyPreset(k)}
              className="text-xs px-3 py-1 rounded-full border border-gray-700 hover:border-blue-500 hover:text-blue-400 transition-colors"
            >
              {k}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Step (Hour)</label>
          <input type="number" className="input-field" value={form.step}
            onChange={(e) => set("step", +e.target.value)} required />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Type</label>
          <select className="input-field" value={form.type}
            onChange={(e) => set("type", e.target.value)}>
            {TRANSACTION_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label className="text-xs text-gray-400 mb-1 block">Amount (₹)</label>
        <input type="number" className="input-field" value={form.amount}
          onChange={(e) => set("amount", +e.target.value)} min={0} step={0.01} required />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Sender ID</label>
          <input type="text" className="input-field" value={form.nameOrig}
            onChange={(e) => set("nameOrig", e.target.value)} placeholder="C1234567890" required />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Receiver ID</label>
          <input type="text" className="input-field" value={form.nameDest}
            onChange={(e) => set("nameDest", e.target.value)} placeholder="C0987654321" required />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Sender Balance Before</label>
          <input type="number" className="input-field" value={form.oldbalanceOrg}
            onChange={(e) => set("oldbalanceOrg", +e.target.value)} min={0} step={0.01} />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Sender Balance After</label>
          <input type="number" className="input-field" value={form.newbalanceOrig}
            onChange={(e) => set("newbalanceOrig", +e.target.value)} min={0} step={0.01} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Receiver Balance Before</label>
          <input type="number" className="input-field" value={form.oldbalanceDest}
            onChange={(e) => set("oldbalanceDest", +e.target.value)} min={0} step={0.01} />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Receiver Balance After</label>
          <input type="number" className="input-field" value={form.newbalanceDest}
            onChange={(e) => set("newbalanceDest", +e.target.value)} min={0} step={0.01} />
        </div>
      </div>

      <button type="submit" disabled={loading} className="btn-primary w-full">
        {loading ? "Analyzing…" : "Analyze Transaction"}
      </button>
    </form>
  );
}
