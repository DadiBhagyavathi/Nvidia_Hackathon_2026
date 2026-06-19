# 🏦 Explainable Fraud Investigation Agent
### NVIDIA Agentic AI Hackathon Project

> Multi-agent financial fraud detection with XGBoost + SHAP + ChromaDB RAG + NVIDIA NIM (Nemotron 3 Ultra)

A production-style web application that analyzes financial transactions, detects fraud using machine learning, explains *why* using SHAP, retrieves supporting RBI/AML regulatory evidence via RAG, generates a professional investigation report using an LLM, and lets investigators chat with an AI assistant about the case.

---

## 📋 Table of Contents

1. [Features](#-features)
2. [Tech Stack](#-tech-stack)
3. [Architecture](#-architecture)
4. [Project Structure](#-project-structure)
5. [Prerequisites](#-prerequisites)
6. [Quick Start](#-quick-start-local-development)
7. [API Endpoints](#-api-endpoints)
8. [Environment Variables](#-environment-variables)
9. [NVIDIA NIM Integration](#-nvidia-nim-integration)
10. [Deployment](#-deployment)
11. [Dataset](#-dataset)
12. [Troubleshooting](#-troubleshooting)

---

## ✨ Features

| # | Feature | Description |
|---|---------|--------------|
| 1 | **Fraud Detection** | XGBoost model predicts fraud probability + confidence score on each transaction |
| 2 | **Explainability** | SHAP values surface the top reasons behind every prediction, in plain English |
| 3 | **Detection Agent** | Receives a raw transaction, returns a structured risk score |
| 4 | **Investigation Agent** | Converts SHAP output into a human-readable investigative narrative (NVIDIA NIM) |
| 5 | **Evidence Agent** | Searches indexed RBI/AML/PMLA documents (ChromaDB) for supporting regulation |
| 6 | **Report Agent** | Generates a full, structured Suspicious Transaction Report (NVIDIA NIM) |
| 7 | **AI Investigator Chat** | RAG + NVIDIA NIM-powered chat for ad-hoc fraud & compliance questions |
| 8 | **Dashboard** | Banking-style UI — transaction form, risk gauge, explanation panel, evidence panel, report panel, chat panel |

---

## 🛠 Tech Stack

**Frontend** — Next.js (App Router) · TypeScript · Tailwind CSS · Recharts
**Backend** — Python · FastAPI
**Machine Learning** — XGBoost · Scikit-learn · SHAP · SMOTE
**RAG** — ChromaDB · Sentence Transformers · PDF ingestion
**LLM** — NVIDIA NIM (`nemotron-3-ultra-550b-a55b`)
**Database** — Supabase (Postgres)
**Deployment** — Vercel (frontend) · Render (backend) · Supabase (database)

---

## 🏗 Architecture

```
Transaction Input
       │
       ▼
┌─────────────────┐
│ Detection Agent │ ← XGBoost + SHAP
└────────┬────────┘
         │ fraud_probability + top_reasons
         ▼
┌──────────────────────┐
│ Investigation Agent  │ ← NVIDIA NIM (Nemotron 3 Ultra)
└──────────┬───────────┘
           │ narrative
           ▼
┌──────────────────┐
│  Evidence Agent  │ ← ChromaDB + Sentence Transformers (RAG)
└────────┬─────────┘
         │ regulatory passages
         ▼
┌──────────────────┐
│  Report Agent    │ ← NVIDIA NIM (Nemotron 3 Ultra)
└────────┬─────────┘
         │ full markdown report
         ▼
    Supabase DB  ──────► Next.js Dashboard
                              │
                              ▼
                    AI Investigator Chat
                    (RAG + NVIDIA NIM)
```

Each agent is a single-responsibility Python class (`backend/agents/`) orchestrated by one FastAPI endpoint (`POST /analyze`), so the pipeline is easy to demo, debug, and extend.

---

## 📁 Project Structure

```
fraud-investigation-agent/
├── backend/
│   ├── agents/
│   │   ├── detection_agent.py        # Agent 1: ML risk scoring
│   │   ├── investigation_agent.py    # Agent 2: SHAP → narrative (NIM)
│   │   ├── evidence_agent.py         # Agent 3: RAG evidence retrieval
│   │   └── report_agent.py           # Agent 4: Final report (NIM)
│   ├── ml/
│   │   ├── train_model.py            # Training pipeline
│   │   ├── explain.py                # SHAP explainability
│   │   └── fraud_model.pkl           # ← generated after training
│   ├── rag/
│   │   ├── rag_pipeline.py           # ChromaDB + embeddings
│   │   ├── ingest_docs.py            # PDF ingestion script
│   │   └── docs/                     # Place RBI/AML PDFs here
│   ├── db/
│   │   └── database.py               # Supabase read/write
│   ├── api.py                        # FastAPI app (all endpoints)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                  # Redirects to /dashboard
│   │   └── dashboard/page.tsx        # Main dashboard
│   ├── components/
│   │   ├── TransactionForm.tsx
│   │   ├── FraudScoreGauge.tsx
│   │   ├── ExplanationPanel.tsx
│   │   ├── EvidencePanel.tsx
│   │   ├── ReportPanel.tsx
│   │   └── ChatPanel.tsx
│   ├── lib/api.ts                    # Typed API client
│   ├── package.json
│   └── .env.local
├── supabase/
│   └── schema.sql                    # Database schema
├── data/
│   └── paysim.csv                    # ← place dataset here
├── .github/workflows/deploy.yml      # CI/CD
├── render.yaml                       # Render deployment config
└── README.md
```

---

## ✅ Prerequisites
- Python 3.11+
- Node.js 18+
- A free [NVIDIA NIM API key](https://build.nvidia.com)
- A free [Supabase](https://supabase.com) project
- The PaySim dataset (`paysim.csv`)

---

## 🚀 Quick Start (Local Development)

### Step 1 — Clone and set up the project

```bash
git clone https://github.com/YOUR_USERNAME/fraud-investigation-agent
cd fraud-investigation-agent
```

---

### Step 2 — Get your NVIDIA NIM API key

1. Go to [build.nvidia.com](https://build.nvidia.com) and sign up (free, no credit card)
2. Open any model card (e.g. search "Nemotron 3 Ultra") → click **Get API Key**
3. Copy the key — it starts with `nvapi-...`

---

### Step 3 — Set up Supabase

1. Go to [supabase.com](https://supabase.com) → **Start your project** → sign in with GitHub (free)
2. Click **New Project**, name it, set a database password, pick a region → **Create new project** (~2 min to provision)
3. Once ready, go to **Project Settings → API** in the left sidebar. You'll need two values:

   | Dashboard field | Goes into `.env` as |
   |---|---|
   | **Project URL** | `SUPABASE_URL` |
   | **Project API keys → `anon` `public`** | `SUPABASE_KEY` |

   ⚠️ Use the `anon` key, **not** `service_role` — `service_role` bypasses Row Level Security and shouldn't be used in app code.

4. Go to **SQL Editor** → paste the full contents of `supabase/schema.sql` → **Run**. This creates the `investigation_reports` and `chat_history` tables (with one sample row pre-seeded so the dashboard isn't empty on first load).
5. Verify in **Table Editor** that both tables exist.

---

### Step 4 — Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env
# Edit .env with your NVIDIA_API_KEY, SUPABASE_URL, SUPABASE_KEY
```

---

### Step 5 — Train the ML model

```bash
# Copy PaySim CSV to data/
cp /path/to/paysim.csv ../data/paysim.csv

# From project root:
python backend/ml/train_model.py ../data/paysim.csv

# This creates: backend/ml/fraud_model.pkl
# Training takes ~5-10 minutes on CPU for the full 6.3M-row dataset
# For quick testing, sample first: df.sample(frac=0.1) inside load_data()
```

---

### Step 6 — Ingest regulatory documents (optional but recommended)

```bash
# Download RBI / PMLA / AML PDFs and place them in:
#   backend/rag/docs/

# Then run:
python backend/rag/ingest_docs.py

# Built-in fallback guidelines (RBI KYC, PMLA, AML/CFT, FATF) work
# even without PDFs, so this step can be skipped for a quick demo.
```

---

### Step 7 — Start the backend

```bash
# From project root:
uvicorn backend.api:app --reload --port 8000

# Test it:
curl http://localhost:8000/health
```

---

### Step 8 — Frontend setup

```bash
cd frontend
npm install

# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
# Open http://localhost:3000
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/analyze` | Run full 4-agent pipeline on a transaction |
| GET | `/reports` | List recent investigation reports |
| GET | `/reports/{case_id}` | Get a single report |
| POST | `/chat` | AI investigator chat (RAG + NIM) |

---

## 🔑 Environment Variables

### Backend (`backend/.env`)
```bash
# NVIDIA NIM
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NIM_MODEL=nvidia/nemotron-3-ultra-550b-a55b
NIM_ENABLE_THINKING=false   # keep false for clean narrative/report output

# Supabase
SUPABASE_URL=https://xxxxxxxxxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ChromaDB / Embeddings
CHROMA_DIR=backend/rag/chroma_db
EMBED_MODEL=all-MiniLM-L6-v2

# Dataset
PAYSIM_CSV=data/paysim.csv

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app
```

### Frontend (`frontend/.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🎯 NVIDIA NIM Integration

This project uses **NVIDIA NIM** (NVIDIA Inference Microservices) via its OpenAI-compatible API.

- **Model**: `nvidia/nemotron-3-ultra-550b-a55b` — a 550B-parameter (55B active) hybrid Mamba-Transformer MoE reasoning model, well suited to multi-step agentic workflows like this one.
- **Investigation Agent**: Converts SHAP outputs → human-readable narrative
- **Report Agent**: Generates the full structured Suspicious Transaction Report
- **Chat Agent**: RAG-grounded Q&A on fraud patterns and regulation

**Reasoning model note**: Nemotron 3 Ultra can emit a separate internal "thinking" trace before its final answer. The code disables this (`NIM_ENABLE_THINKING=false`) so responses are clean and concise, and reads only `message.content` (never `message.reasoning_content`) for narratives, reports, and chat replies. If you want to inspect the model's reasoning for debugging, flip the flag to `true` and read `reasoning_content` separately — don't mix it into user-facing text.

Get your free API key at [build.nvidia.com](https://build.nvidia.com).

---

## 🚢 Deployment

### Backend → Render
1. Push your repo to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo (Render auto-reads `render.yaml`)
4. Add environment variables in the Render dashboard (same as `backend/.env`)
5. Deploy — note the resulting URL (e.g. `https://fraud-investigation-backend.onrender.com`)

### Frontend → Vercel
1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repo → set **Root Directory** to `frontend/`
3. Add environment variable: `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`
4. Deploy

### Database → Supabase
Already hosted — no separate deployment step. Just make sure `ALLOWED_ORIGINS` on the backend includes your final Vercel URL.

---

## 📊 Dataset

[PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1) — a synthetic financial transaction dataset modeling mobile money transfers:

| Property | Value |
|---|---|
| Rows | ~6.36 million |
| Columns | 11 |
| Target | `isFraud` (binary) |
| Transaction types | `PAYMENT`, `CASH_OUT`, `CASH_IN`, `TRANSFER`, `DEBIT` |
| Fraud rate | ~0.13% (highly imbalanced — handled with SMOTE) |
| Fraud-eligible types | Only `TRANSFER` and `CASH_OUT` ever carry fraud in this dataset |

Place the CSV at `data/paysim.csv` before running `train_model.py`.

---

## 🩺 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `FileNotFoundError: fraud_model.pkl` | Model not trained yet | Run `python backend/ml/train_model.py ../data/paysim.csv` |
| `/analyze` returns 503 | Model file missing or backend can't find it | Check `backend/ml/fraud_model.pkl` exists |
| `/analyze` or `/chat` returns 502 | NVIDIA NIM API key invalid/missing, or rate-limited | Verify `NVIDIA_API_KEY` in `.env`; free tier is ~40 req/min |
| Empty narrative or report text | Reasoning model spent its token budget "thinking" | Confirm `NIM_ENABLE_THINKING=false`; increase `max_tokens` if needed |
| Supabase insert fails silently | Wrong key type or schema not run | Use the `anon` key, not `service_role`; re-run `supabase/schema.sql` |
| CORS errors in browser console | Frontend origin not whitelisted | Add your frontend URL to `ALLOWED_ORIGINS` in backend `.env` |
| Evidence panel only shows 4 generic sources | No PDFs ingested yet | Add PDFs to `backend/rag/docs/` and run `python backend/rag/ingest_docs.py` (built-in fallback guidelines still work without this) |