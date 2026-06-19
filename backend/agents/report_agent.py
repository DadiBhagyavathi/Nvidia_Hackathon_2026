"""
report_agent.py
───────────────
Location : backend/agents/report_agent.py
Purpose  : Agent #4 — synthesizes detection + investigation + evidence
           outputs into a final, structured fraud investigation report
           using NVIDIA NIM.

Connects to: evidence_agent.py (input), database.py (saves report),
             api.py (called by endpoint)
"""

import os
from datetime import datetime
from openai import OpenAI
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

NVIDIA_API_KEY  = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_MODEL       = os.getenv("NIM_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=NVIDIA_API_KEY,
            base_url=NVIDIA_BASE_URL,
        )
    return _client


REPORT_SYSTEM_PROMPT = """You are a senior compliance officer at an Indian bank generating
formal Suspicious Transaction Reports (STR) in accordance with RBI/PMLA guidelines.

Generate a structured investigation report with these EXACT sections (use markdown headers):

## INVESTIGATION REPORT

**Case ID**: [provided]
**Date**: [provided]
**Risk Level**: [provided]

## 1. EXECUTIVE SUMMARY
(2-3 sentences: what happened, what was detected, recommendation)

## 2. TRANSACTION DETAILS
(tabular summary of the transaction)

## 3. FRAUD INDICATORS
(bulleted list of ML-detected risk factors with explanations)

## 4. INVESTIGATOR'S FINDINGS
(narrative from investigation agent)

## 5. REGULATORY EVIDENCE
(cite the retrieved RBI/AML guidelines supporting the finding)

## 6. RECOMMENDED ACTION
(one of: CLEAR | MONITOR | ESCALATE | FILE STR | FREEZE ACCOUNT)
Provide reasoning for the recommendation.

## 7. COMPLIANCE NOTES
(relevant PMLA/RBI regulation references)

Be professional, precise, and actionable.
"""


class ReportAgent:
    name = "ReportAgent"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def run(
        self,
        detection_result:     dict,
        investigation_result: dict,
        evidence_result:      dict,
        case_id:              str | None = None,
    ) -> dict:
        """
        Returns
        -------
        dict with keys:
            report_markdown (str), case_id, recommended_action, agent
        """
        if case_id is None:
            case_id = f"FIA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        logger.info(f"[{self.name}] Generating report for case {case_id} …")

        txn       = detection_result["transaction"]
        prob      = detection_result["fraud_probability"]
        risk      = detection_result["risk_level"]
        reasons   = detection_result["top_reasons"]
        narrative = investigation_result["narrative"]
        passages  = evidence_result["evidence_passages"]

        # Format evidence
        evidence_txt = "\n".join(
            f"  [{i+1}] (Source: {p.get('source','?')}) {p.get('text','')[:300]}"
            for i, p in enumerate(passages[:4])
        ) or "  No regulatory documents indexed yet. Add PDFs to backend/rag/docs/."

        # Format reasons
        reasons_txt = "\n".join(
            f"  - {r['label']}: {r['value']} "
            f"({'⬆ Risk' if r['direction'] == 'increases_risk' else '⬇ Risk'})"
            for r in reasons
        )

        user_prompt = f"""
Case ID  : {case_id}
Date     : {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
Risk Level: {risk} ({prob:.2%} fraud probability)

Transaction:
  Type    : {txn.get('type')}
  Amount  : ₹{txn.get('amount'):,.2f}
  From    : {txn.get('nameOrig')}
  To      : {txn.get('nameDest')}
  Sender Balance Before/After: ₹{txn.get('oldbalanceOrg'):,.2f} / ₹{txn.get('newbalanceOrig'):,.2f}
  Receiver Balance Before/After: ₹{txn.get('oldbalanceDest'):,.2f} / ₹{txn.get('newbalanceDest'):,.2f}

ML Risk Factors:
{reasons_txt}

Investigation Narrative:
{narrative}

Regulatory Evidence Retrieved:
{evidence_txt}

Generate the full investigation report now.
"""

        client   = _get_client()
        response = client.chat.completions.create(
            model=NIM_MODEL,
            messages=[
                {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1200,
        )

        report_md = response.choices[0].message.content.strip()

        # Extract recommended action from report
        action = "REVIEW"
        for keyword in ["FREEZE ACCOUNT", "FILE STR", "ESCALATE", "MONITOR", "CLEAR"]:
            if keyword in report_md.upper():
                action = keyword
                break

        logger.success(f"[{self.name}] Report generated. Action: {action}")

        return {
            "report_markdown":    report_md,
            "case_id":            case_id,
            "recommended_action": action,
            "risk_level":         risk,
            "fraud_probability":  prob,
            "agent":              self.name,
        }


report_agent = ReportAgent()
