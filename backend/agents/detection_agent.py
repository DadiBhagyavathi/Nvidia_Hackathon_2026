"""
detection_agent.py
──────────────────
Location : backend/agents/detection_agent.py
Purpose  : Agent #1 — receives a raw transaction dict, runs the ML model
           via explain.py, and returns a structured risk assessment.

Connects to: explain.py (ML), api.py (called by endpoint)
"""

from loguru import logger
from backend.ml.explain import explain_transaction


class DetectionAgent:
    """
    Stateless agent that wraps the XGBoost + SHAP pipeline.
    Called once per transaction analysis request.
    """

    name = "DetectionAgent"

    def run(self, transaction: dict) -> dict:
        """
        Parameters
        ----------
        transaction : dict
            Keys: step, type, amount, nameOrig, oldbalanceOrg,
                  newbalanceOrig, nameDest, oldbalanceDest, newbalanceDest

        Returns
        -------
        dict with keys:
            fraud_probability, risk_level, shap_values, top_reasons,
            transaction (echo), agent
        """
        logger.info(f"[{self.name}] Analyzing transaction: {transaction.get('nameOrig')} "
                    f"→ {transaction.get('nameDest')} | ₹{transaction.get('amount')}")

        try:
            result = explain_transaction(transaction, top_n=6)
        except FileNotFoundError as exc:
            logger.error(f"[{self.name}] Model not found: {exc}")
            raise RuntimeError(
                "Fraud model is not trained yet. "
                "Run: python backend/ml/train_model.py"
            ) from exc
        except Exception as exc:
            logger.error(f"[{self.name}] Prediction error: {exc}")
            raise

        output = {
            **result,
            "transaction": transaction,
            "agent": self.name,
        }

        logger.info(
            f"[{self.name}] Risk={result['risk_level']} "
            f"Prob={result['fraud_probability']:.2%}"
        )
        return output


# ── Singleton ─────────────────────────────────────────────────────────────────
detection_agent = DetectionAgent()
