"""
RoadGuard AI — Machine Learning Module
=======================================================================
Task    : Accident RISK classification — predicts LOW / MEDIUM / HIGH risk
          given that an accident occurs under these road/environment conditions.

Risk mapping (justified by injury severity):
  Damage Only                    → LOW RISK
  Simple Injury                  → MEDIUM RISK
  Grievous Injury / Fatal        → HIGH RISK

This is conditional risk estimation — NOT a prediction of whether an
accident will occur (the dataset contains only accident records, not
traffic exposure or non-accident observations).

Features: 11 road/environment columns (all ≥99% populated).
Model   : Random Forest (200 trees, balanced class weights).
Baseline: Majority-class DummyClassifier.
=======================================================================
"""

import os
import pandas as pd
import numpy as np
import joblib
import streamlit as st

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score, classification_report,
    confusion_matrix, f1_score,
)

MODEL_PATH   = "roadguard_model.pkl"
METRICS_PATH = "model_metrics.pkl"

# ── Feature list — identical at train AND predict time ───────────────────────
FEATURES = [
    "DISTRICTNAME",
    "Weather",
    "Road_Type",
    "Surface_Condition",
    "Road_Character",
    "Road_Condition",
    "Main_Cause",
    "Accident_Location",
    "Accident_Spot",
    "Junction_Control",
    "Hit_Run",
]

TARGET         = "RiskLevel"          # new 3-class target
VALID_SEVERITY = ["Damage Only", "Simple Injury", "Grievous Injury", "Fatal"]
RISK_LEVELS    = ["LOW RISK", "MEDIUM RISK", "HIGH RISK"]

# Risk tier mapping — justified by injury outcome
SEVERITY_TO_RISK = {
    "Damage Only":    "LOW RISK",
    "Simple Injury":  "MEDIUM RISK",
    "Grievous Injury":"HIGH RISK",
    "Fatal":          "HIGH RISK",
}

RISK_COLORS = {
    "LOW RISK":    "#22c55e",
    "MEDIUM RISK": "#eab308",
    "HIGH RISK":   "#ef4444",
}
RISK_EMOJI = {
    "LOW RISK":    "🟢",
    "MEDIUM RISK": "🟡",
    "HIGH RISK":   "🔴",
}
RISK_CSS = {
    "LOW RISK":    "pred-damage",
    "MEDIUM RISK": "pred-simple",
    "HIGH RISK":   "pred-fatal",
}


def _clean_X(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Apply identical cleaning at train and predict time."""
    X = df_raw[FEATURES].copy()
    for col in FEATURES:
        X[col] = (
            X[col].fillna("Unknown").astype(str).str.strip()
             .replace({"nan": "Unknown", "": "Unknown", "Not Applicable": "Unknown"})
        )
    return X


def train_and_save_model(df: pd.DataFrame):
    """Train RF on the 3-class risk target and save pipeline + metrics."""
    # Filter to valid severity rows, map to risk level
    df = df[df["Severity"].astype(str).isin(VALID_SEVERITY)].copy()
    df[TARGET] = df["Severity"].astype(str).map(SEVERITY_TO_RISK)

    X = _clean_X(df)
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer([
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OrdinalEncoder(
                handle_unknown="use_encoded_value",
                unknown_value=-1,
            )),
        ]), FEATURES),
    ])

    rf_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=200,
            max_depth=25,
            min_samples_leaf=4,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        )),
    ])

    # Baseline
    baseline = DummyClassifier(strategy="most_frequent", random_state=42)
    baseline.fit(X_train, y_train)
    base_acc = accuracy_score(y_test, baseline.predict(X_test))

    # Train
    rf_pipeline.fit(X_train, y_train)
    rf_preds = rf_pipeline.predict(X_test)

    rf_acc    = accuracy_score(y_test, rf_preds)
    macro_f1  = f1_score(y_test, rf_preds, average="macro", zero_division=0)
    report    = classification_report(
        y_test, rf_preds, labels=RISK_LEVELS,
        output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(y_test, rf_preds, labels=RISK_LEVELS)

    importances = rf_pipeline.named_steps["classifier"].feature_importances_
    feat_imp    = pd.Series(importances, index=FEATURES).sort_values(ascending=False)

    metrics = {
        "rf_accuracy":           rf_acc,
        "macro_f1":              macro_f1,
        "baseline_accuracy":     base_acc,
        "classification_report": report,
        "confusion_matrix":      cm,
        "labels":                RISK_LEVELS,
        "feature_importance":    feat_imp,
        "features":              FEATURES,
        "train_size":            len(X_train),
        "test_size":             len(X_test),
        "risk_mapping":          SEVERITY_TO_RISK,
        "class_distribution":    y.value_counts().to_dict(),
    }

    joblib.dump(rf_pipeline, MODEL_PATH)
    joblib.dump(metrics,     METRICS_PATH)
    return rf_pipeline, metrics


@st.cache_resource(show_spinner=False)
def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


@st.cache_data(show_spinner=False)
def load_metrics():
    if os.path.exists(METRICS_PATH):
        return joblib.load(METRICS_PATH)
    return None


def predict_risk(model, inputs: dict):
    """
    inputs: dict with keys matching FEATURES.
    Returns (risk_label, confidence, proba_dict).
    risk_label is one of: "LOW RISK", "MEDIUM RISK", "HIGH RISK"
    """
    row = {f: str(inputs.get(f, "Unknown")).strip() or "Unknown" for f in FEATURES}
    row = {k: ("Unknown" if v in ("Not Applicable", "nan", "") else v)
           for k, v in row.items()}
    X    = pd.DataFrame([row])
    pred = model.predict(X)[0]
    proba= dict(zip(model.classes_, model.predict_proba(X)[0]))
    conf = float(proba.get(pred, 0.0))
    return pred, conf, proba


def get_unique_values(df: pd.DataFrame, col: str,
                      exclude=("Not Applicable", "nan", "")) -> list:
    vals = df[col].dropna().astype(str).unique().tolist()
    vals = [v.strip() for v in vals if v.strip() not in exclude]
    return sorted(set(vals))
