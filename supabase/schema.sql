-- ─────────────────────────────────────────────────────────────
-- supabase/schema.sql
-- Run this in: Supabase Dashboard → SQL Editor → Run
-- ─────────────────────────────────────────────────────────────

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Investigation Reports ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS investigation_reports (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id             TEXT NOT NULL UNIQUE,
    transaction_type    TEXT,
    amount              NUMERIC(18, 2),
    sender_id           TEXT,
    receiver_id         TEXT,
    fraud_probability   NUMERIC(6, 4),
    risk_level          TEXT CHECK (risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    recommended_action  TEXT,
    report_markdown     TEXT,
    top_reasons         JSONB,
    narrative           TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookup by risk level and date
CREATE INDEX IF NOT EXISTS idx_reports_risk_level  ON investigation_reports (risk_level);
CREATE INDEX IF NOT EXISTS idx_reports_created_at  ON investigation_reports (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_case_id     ON investigation_reports (case_id);

-- ── Chat History ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_history (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  TEXT NOT NULL,
    role        TEXT CHECK (role IN ('user', 'assistant', 'system')),
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history (session_id, created_at ASC);

-- ── Row Level Security (enable for production) ─────────────────
-- ALTER TABLE investigation_reports ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- ── Sample data to test dashboard ─────────────────────────────
INSERT INTO investigation_reports (
    case_id, transaction_type, amount, sender_id, receiver_id,
    fraud_probability, risk_level, recommended_action,
    report_markdown, top_reasons, narrative
) VALUES (
    'FIA-SAMPLE-001',
    'TRANSFER',
    950000.00,
    'C1234567890',
    'C0987654321',
    0.9423,
    'CRITICAL',
    'FILE STR',
    '## INVESTIGATION REPORT\n**Case ID**: FIA-SAMPLE-001\n**Risk Level**: CRITICAL\n\n## 1. EXECUTIVE SUMMARY\nThis transaction has been flagged as highly suspicious...',
    '[{"feature":"errorBalanceOrig","label":"Sender balance discrepancy","value":950000,"direction":"increases_risk","shap_value":1.234}]',
    'A TRANSFER of ₹9,50,000 was identified with a 94.23% fraud probability. The sender account was completely drained with a corresponding zero-balance destination account.'
) ON CONFLICT (case_id) DO NOTHING;
