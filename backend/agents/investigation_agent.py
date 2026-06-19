"""
investigation_agent.py
──────────────────────
Location : backend/agents/investigation_agent.py
Purpose  : Agent #2 — takes SHAP top_reasons and converts them into a
           clear, human-readable investigation narrative using NVIDIA NIM.

Connects to: detection_agent.py (input), report_agent.py (output),
             api.py (called by endpoint)
"""

import os
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


SYSTEM_PROMPT = """You are a senior financial fraud investigator at a major Indian bank.
Your role is to analyze machine learning model outputs (SHAP values) and translate them
into clear, professional investigation findings that a compliance officer can act on.

Rules:
- Write in formal investigative language.
- Be concise but thorough (4-6 sentences).
- Reference specific numbers from the transaction data.
- End with a clear risk verdict sentence.
- Do NOT fabricate any information beyond what is provided.
- Mention RBI / PMLA / AML regulations where relevant.
"""


class InvestigationAgent:
    name = "InvestigationAgent"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def run(self, detection_result: dict) -> dict:
        """
        Parameters
        ----------
        detection_result : dict
            Output from DetectionAgent.run()

        Returns
        -------
        dict with keys:
            narrative (str), risk_level, fraud_probability, agent
        """
        logger.info(f"[{self.name}] Generating investigation narrative …")

        txn       = detection_result["transaction"]
        prob      = detection_result["fraud_probability"]
        risk      = detection_result["risk_level"]
        reasons   = detection_result["top_reasons"]

        # Build a compact prompt from SHAP reasons
        reasons_txt = "\n".join(
            f"  • {r['label']}: {r['value']} "
            f"({'↑ raises risk' if r['direction'] == 'increases_risk' else '↓ lowers risk'}, "
            f"SHAP={r['shap_value']})"
            for r in reasons
        )

        user_prompt = f"""
Transaction Details:
  Type    : {txn.get('type')}
  Amount  : ₹{txn.get('amount'):,.2f}
  Sender  : {txn.get('nameOrig')} (Balance before: ₹{txn.get('oldbalanceOrg'):,.2f}, after: ₹{txn.get('newbalanceOrig'):,.2f})
  Receiver: {txn.get('nameDest')} (Balance before: ₹{txn.get('oldbalanceDest'):,.2f}, after: ₹{txn.get('newbalanceDest'):,.2f})

ML Model Output:
  Fraud Probability : {prob:.2%}
  Risk Level        : {risk}

Top Risk Factors (SHAP Explanation):
{reasons_txt}

Write a professional investigation narrative explaining why this transaction was flagged.
"""

        client = _get_client()
        response = client.chat.completions.create(
            model=NIM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=400,
        )

        narrative = response.choices[0].message.content.strip()
        logger.info(f"[{self.name}] Narrative generated ({len(narrative)} chars).")

        return {
            "narrative":         narrative,
            "risk_level":        risk,
            "fraud_probability": prob,
            "agent":             self.name,
        }


investigation_agent = InvestigationAgent()
