"""
explain.py
──────────
Location : backend/ml/explain.py
Purpose  : Load trained model → compute SHAP values → return
           top-N human-readable explanations for a single transaction.

Connects to: detection_agent.py, investigation_agent.py
"""

import joblib
import shap
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger
from functools import lru_cache

MODEL_PATH = Path(__file__).resolve().parent / "fraud_model.pkl"

# ── Friendly names for features shown to end users ───────────────────────────
FEATURE_LABELS = {
    "step":               "Hour of transaction",
    "type_encoded":       "Transaction type",
    "amount":             "Transaction amount (₹)",
    "oldbalanceOrg":      "Sender's opening balance (₹)",
    "newbalanceOrig":     "Sender's closing balance (₹)",
    "oldbalanceDest":     "Receiver's opening balance (₹)",
    "newbalanceDest":     "Receiver's closing balance (₹)",
    "errorBalanceOrig":   "Sender balance discrepancy (₹)",
    "errorBalanceDest":   "Receiver balance discrepancy (₹)",
    "destZeroBalance":    "Receiver account zeroed out",
    "origDrainedToZero":  "Sender account drained to zero",
    "amountRatioOrig":    "Amount as fraction of sender's balance",
}


@lru_cache(maxsize=1)
def _load_artifact():
    """Load model artifact once and cache."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Run train_model.py first."
        )
    artifact = joblib.load(MODEL_PATH)
    logger.info("Model artifact loaded from cache.")
    return artifact


def get_model():
    return _load_artifact()["model"]


def get_label_encoder():
    return _load_artifact()["label_encoder"]


def get_feature_cols():
    return _load_artifact()["feature_cols"]


def preprocess_transaction(txn: dict) -> pd.DataFrame:
    """
    Convert a raw transaction dict (from API) into the feature DataFrame
    expected by the model.

    Expected keys in txn:
        step, type, amount, oldbalanceOrg, newbalanceOrig,
        oldbalanceDest, newbalanceDest
    """
    artifact = _load_artifact()
    le       = artifact["label_encoder"]
    cols     = artifact["feature_cols"]

    row = dict(txn)  # copy

    # Encode transaction type
    try:
        row["type_encoded"] = int(le.transform([row["type"].upper()])[0])
    except Exception:
        row["type_encoded"] = -1  # unknown type

    # Engineer features (same as train_model.py)
    row["errorBalanceOrig"]  = row["newbalanceOrig"] + row["amount"] - row["oldbalanceOrg"]
    row["errorBalanceDest"]  = row["oldbalanceDest"] + row["amount"] - row["newbalanceDest"]
    row["destZeroBalance"]   = int(row["newbalanceDest"] == 0)
    row["origDrainedToZero"] = int(row["newbalanceOrig"] == 0)
    row["amountRatioOrig"]   = row["amount"] / (row["oldbalanceOrg"] + 1e-9)

    df = pd.DataFrame([row])[cols]
    return df


def explain_transaction(txn: dict, top_n: int = 5) -> dict:
    """
    Run model + SHAP for a single transaction.

    Returns
    -------
    {
        "fraud_probability": float,
        "risk_level": str,
        "shap_values": [...],          # raw
        "top_reasons": [               # human-readable
            {"feature": str, "label": str, "value": any,
             "shap_value": float, "direction": "increases_risk" | "decreases_risk"}
        ]
    }
    """
    artifact = _load_artifact()
    model    = artifact["model"]
    cols     = artifact["feature_cols"]

    X = preprocess_transaction(txn)

    # ── Predict ──────────────────────────────────────────────────────────────
    prob = float(model.predict_proba(X)[0][1])

    # ── SHAP ─────────────────────────────────────────────────────────────────
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # shap_values shape: (1, n_features)
    sv_row = shap_values[0] if len(shap_values.shape) == 2 else shap_values[0]

    # Sort by absolute SHAP value descending
    indices = np.argsort(np.abs(sv_row))[::-1][:top_n]

    top_reasons = []
    for idx in indices:
        feat  = cols[idx]
        sv    = float(sv_row[idx])
        fval  = float(X.iloc[0][feat])
        top_reasons.append({
            "feature":    feat,
            "label":      FEATURE_LABELS.get(feat, feat),
            "value":      round(fval, 4),
            "shap_value": round(sv, 4),
            "direction":  "increases_risk" if sv > 0 else "decreases_risk",
        })

    # ── Risk Level ───────────────────────────────────────────────────────────
    if prob >= 0.80:
        risk_level = "CRITICAL"
    elif prob >= 0.50:
        risk_level = "HIGH"
    elif prob >= 0.25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "fraud_probability": round(prob, 4),
        "risk_level":        risk_level,
        "shap_values":       [round(float(v), 6) for v in sv_row],
        "top_reasons":       top_reasons,
    }
