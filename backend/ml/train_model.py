"""
train_model.py
──────────────
Location : backend/ml/train_model.py
Run      : python backend/ml/train_model.py
Purpose  : Load PaySim CSV → engineer features → train XGBoost →
           evaluate → save fraud_model.pkl

Connects to: explain.py (loads the pkl), detection_agent.py (loads pkl)
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    f1_score,
)
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "fraud_model.pkl"
DATA_PATH  = Path(os.getenv("PAYSIM_CSV", BASE_DIR.parent.parent / "data" / "paysim.csv"))

# ── 1. LOAD DATA ─────────────────────────────────────────────────────────────
def load_data(path: Path, sample_frac: float = 1.0) -> pd.DataFrame:
    logger.info(f"Loading dataset from {path}")
    df = pd.read_csv(path)
    logger.info(f"Raw shape: {df.shape}")
    if sample_frac < 1.0:
        df = df.sample(frac=sample_frac, random_state=42)
        logger.info(f"Sampled shape: {df.shape}")
    return df


# ── 2. FEATURE ENGINEERING ───────────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Engineering features …")

    # Balance error: how much did balance change vs expected
    df["errorBalanceOrig"] = (
        df["newbalanceOrig"] + df["amount"] - df["oldbalanceOrg"]
    )
    df["errorBalanceDest"] = (
        df["oldbalanceDest"] + df["amount"] - df["newbalanceDest"]
    )

    # Flag zero-balance destination (common in fraud)
    df["destZeroBalance"] = (df["newbalanceDest"] == 0).astype(int)

    # Flag if origin drained to zero
    df["origDrainedToZero"] = (df["newbalanceOrig"] == 0).astype(int)

    # Ratio of amount to origin balance (avoid div/0)
    df["amountRatioOrig"] = df["amount"] / (df["oldbalanceOrg"] + 1e-9)

    # Encode transaction type
    le = LabelEncoder()
    df["type_encoded"] = le.fit_transform(df["type"])

    logger.info(f"Feature engineered shape: {df.shape}")
    return df, le


# ── 3. PREPARE X / y ─────────────────────────────────────────────────────────
FEATURE_COLS = [
    "step",
    "type_encoded",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "errorBalanceOrig",
    "errorBalanceDest",
    "destZeroBalance",
    "origDrainedToZero",
    "amountRatioOrig",
]

TARGET_COL = "isFraud"


def prepare_xy(df: pd.DataFrame):
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]
    logger.info(f"Class distribution:\n{y.value_counts()}")
    return X, y


# ── 4. TRAIN ─────────────────────────────────────────────────────────────────
def train(X_train, y_train):
    logger.info("Applying SMOTE to balance classes …")
    smote = SMOTE(random_state=42, sampling_strategy=0.1)
    X_res, y_res = smote.fit_resample(X_train, y_train)
    logger.info(f"After SMOTE: {pd.Series(y_res).value_counts().to_dict()}")

    logger.info("Training XGBoost …")
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=1,          # SMOTE already balanced
        use_label_encoder=False,
        eval_metric="aucpr",
        random_state=42,
        n_jobs=-1,
        tree_method="hist",          # fast on CPU; use 'gpu_hist' if NVIDIA GPU available
    )
    model.fit(
        X_res, y_res,
        eval_set=[(X_res, y_res)],
        verbose=50,
    )
    return model


# ── 5. EVALUATE ──────────────────────────────────────────────────────────────
def evaluate(model, X_test, y_test):
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    roc_auc  = roc_auc_score(y_test, y_proba)
    pr_auc   = average_precision_score(y_test, y_proba)
    f1       = f1_score(y_test, y_pred)

    logger.info("─── Evaluation Report ───────────────────────────────")
    logger.info(f"ROC-AUC  : {roc_auc:.4f}")
    logger.info(f"PR-AUC   : {pr_auc:.4f}   ← key metric for imbalanced fraud")
    logger.info(f"F1 Score : {f1:.4f}")
    logger.info("\n" + classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))
    logger.info(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
    logger.info("─────────────────────────────────────────────────────")

    return {"roc_auc": roc_auc, "pr_auc": pr_auc, "f1": f1}


# ── 6. SAVE ──────────────────────────────────────────────────────────────────
def save_model(model, label_encoder, feature_cols, metrics):
    artifact = {
        "model":        model,
        "label_encoder": label_encoder,
        "feature_cols": feature_cols,
        "metrics":      metrics,
    }
    joblib.dump(artifact, MODEL_PATH)
    logger.success(f"Model saved → {MODEL_PATH}")


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    # Allow passing CSV path as CLI arg
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_PATH

    df = load_data(csv_path)
    df, label_encoder = engineer_features(df)
    X, y = prepare_xy(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model   = train(X_train, y_train)
    metrics = evaluate(model, X_test, y_test)
    save_model(model, label_encoder, FEATURE_COLS, metrics)

    logger.success("Training pipeline complete ✓")


if __name__ == "__main__":
    main()
