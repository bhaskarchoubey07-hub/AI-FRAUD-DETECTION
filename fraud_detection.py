"""
Fraud Detection Engine for AI Financial Statement Fraud Detector.
Uses Isolation Forest when available, falls back to statistical anomaly detection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any

# Optional sklearn - fallback if DLL/import fails (e.g. Windows App Control)
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Financial ratio benchmarks (typical healthy ranges for detection)
RATIO_BENCHMARKS = {
    "profit_margin": {"low": 0.05, "high": 0.25, "abnormal_low": -0.1, "abnormal_high": 0.5},
    "debt_to_equity": {"low": 0.3, "high": 2.0, "abnormal_low": -0.5, "abnormal_high": 5.0},
    "current_ratio": {"low": 1.0, "high": 3.0, "abnormal_low": 0.3, "abnormal_high": 10.0},
    "asset_turnover": {"low": 0.5, "high": 3.0, "abnormal_low": 0.1, "abnormal_high": 10.0},
}

# Format for ratio display (True = percentage)
RATIO_FORMAT_PCT = {"profit_margin": True, "debt_to_equity": False, "current_ratio": False, "asset_turnover": False}


def _format_ratio_val(name: str, val: float) -> str:
    """Format ratio value for display in findings."""
    if RATIO_FORMAT_PCT.get(name, False):
        return f"{val:.2%}"
    return f"{val:.2f}x"


def compute_financial_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Compute key financial ratios for each period."""
    ratios_df = df.copy()
    
    ratios_df["profit_margin"] = np.where(ratios_df["revenue"] != 0, ratios_df["profit"] / ratios_df["revenue"], np.nan)
    ratios_df["debt_to_equity"] = np.where(ratios_df["equity"] != 0, ratios_df["liabilities"] / ratios_df["equity"], np.nan)
    ratios_df["current_ratio"] = np.where(ratios_df["liabilities"] != 0, ratios_df["assets"] / ratios_df["liabilities"], np.nan)
    ratios_df["asset_turnover"] = np.where(ratios_df["assets"] != 0, ratios_df["revenue"] / ratios_df["assets"], np.nan)
    
    return ratios_df


def _run_statistical_anomaly_detection(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Fallback: Use z-score based anomaly detection (no sklearn)."""
    ratios_df = compute_financial_ratios(df)
    feature_cols = ["revenue", "expenses", "profit", "assets", "liabilities", "equity"]
    ratio_cols = [c for c in ratios_df.columns if c not in feature_cols]
    all_features = feature_cols + ratio_cols
    
    X = ratios_df[all_features].fillna(0).replace([np.inf, -np.inf], 0).values
    X_mean = np.mean(X, axis=0)
    X_std = np.std(X, axis=0) + 1e-8
    
    z_scores = np.abs((X - X_mean) / X_std)
    max_z = np.max(z_scores, axis=1)
    
    # Normalize to 0-1 (higher = more anomalous)
    score_min, score_max = max_z.min(), max_z.max()
    if score_max - score_min > 0:
        anomaly_scores = (max_z - score_min) / (score_max - score_min)
    else:
        anomaly_scores = np.zeros(len(df))
    
    # Flag top ~20% as anomalies
    threshold = np.percentile(anomaly_scores, 80)
    anomaly_labels = np.where(anomaly_scores >= threshold, -1, 1)
    
    return anomaly_scores.astype(np.float64), anomaly_labels


def _run_isolation_forest(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Run Isolation Forest (sklearn)."""
    feature_cols = ["revenue", "expenses", "profit", "assets", "liabilities", "equity"]
    ratios_df = compute_financial_ratios(df)
    ratio_cols = [c for c in ratios_df.columns if c not in feature_cols]
    all_features = feature_cols + ratio_cols
    feature_df = ratios_df[all_features].fillna(0).replace([np.inf, -np.inf], 0)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(feature_df)
    
    n_samples = len(df)
    contamination = min(0.2, max(0.05, 2 / n_samples)) if n_samples > 0 else 0.1
    iso_forest = IsolationForest(n_estimators=100, contamination=contamination, random_state=42, max_samples=min(256, n_samples))
    
    anomaly_labels = iso_forest.fit_predict(X_scaled)
    anomaly_scores = -iso_forest.score_samples(X_scaled)
    
    score_min, score_max = anomaly_scores.min(), anomaly_scores.max()
    if score_max - score_min > 0:
        anomaly_scores = (anomaly_scores - score_min) / (score_max - score_min)
    else:
        anomaly_scores = np.zeros_like(anomaly_scores)
    
    return anomaly_scores.astype(np.float64), anomaly_labels


def run_isolation_forest_analysis(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Run anomaly detection (Isolation Forest or statistical fallback)."""
    ratios_df = compute_financial_ratios(df)
    
    if HAS_SKLEARN:
        try:
            iso_scores, iso_labels = _run_isolation_forest(df)
        except Exception:
            iso_scores, iso_labels = _run_statistical_anomaly_detection(df)
    else:
        iso_scores, iso_labels = _run_statistical_anomaly_detection(df)
    
    result_df = ratios_df.copy()
    result_df["anomaly_score"] = iso_scores
    result_df["is_anomaly"] = iso_labels == -1
    
    return iso_scores, iso_labels, result_df


def detect_ratio_anomalies(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect abnormal financial ratio values."""
    findings = []
    ratios_df = compute_financial_ratios(df)
    
    for ratio_name, benchmarks in RATIO_BENCHMARKS.items():
        if ratio_name not in ratios_df.columns:
            continue
        values = ratios_df[ratio_name].dropna()
        if len(values) == 0:
            continue
        for idx, val in values.items():
            if np.isinf(val) or np.isnan(val):
                continue
            formatted = _format_ratio_val(ratio_name, val)
            if val < benchmarks["abnormal_low"]:
                findings.append({"type": "ratio_abnormal", "ratio": ratio_name, "period": idx + 1, "value": round(val, 4),
                    "message": f"{ratio_name.replace('_', ' ').title()} = {formatted} is abnormally low", "risk": "high"})
            elif val > benchmarks["abnormal_high"]:
                findings.append({"type": "ratio_abnormal", "ratio": ratio_name, "period": idx + 1, "value": round(val, 4),
                    "message": f"{ratio_name.replace('_', ' ').title()} = {formatted} is abnormally high", "risk": "high"})
    
    return findings


def detect_manipulation_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect common fraud manipulation patterns."""
    findings = []
    if len(df) < 3:
        return findings
    
    profit_change = df["profit"].pct_change()
    revenue_change = df["revenue"].pct_change()
    
    if revenue_change.abs().max() > 0.01:
        profit_revenue_ratio = profit_change / revenue_change.replace(0, np.nan)
        for idx in profit_revenue_ratio[profit_revenue_ratio > 3].dropna().index:
            if pd.notna(profit_change.iloc[idx]) and pd.notna(revenue_change.iloc[idx]):
                findings.append({"type": "expense_suppression", "period": idx + 1,
                    "message": f"Profit growth ({profit_change.iloc[idx]:.1%}) far exceeds revenue growth ({revenue_change.iloc[idx]:.1%}) - possible expense suppression", "risk": "high"})
    
    for idx in range(1, len(revenue_change)):
        if pd.notna(revenue_change.iloc[idx]) and revenue_change.iloc[idx] > 0.5:
            findings.append({"type": "revenue_manipulation", "period": idx + 1,
                "message": f"Unusual revenue spike of {revenue_change.iloc[idx]:.1%} in single period", "risk": "medium"})
    
    asset_change = df["assets"].pct_change()
    if asset_change.abs().max() > 0.01:
        for idx in range(1, len(df)):
            if pd.notna(asset_change.iloc[idx]) and pd.notna(revenue_change.iloc[idx]):
                if asset_change.iloc[idx] > 0.3 and revenue_change.iloc[idx] < 0.1:
                    findings.append({"type": "asset_inflation", "period": idx + 1,
                        "message": f"Assets grew {asset_change.iloc[idx]:.1%} while revenue grew only {revenue_change.iloc[idx]:.1%}", "risk": "medium"})
    
    liability_change = df["liabilities"].pct_change()
    equity_change = df["equity"].pct_change()
    for idx in range(1, len(df)):
        if pd.notna(liability_change.iloc[idx]) and pd.notna(equity_change.iloc[idx]):
            if liability_change.iloc[idx] < -0.2 and equity_change.iloc[idx] > 0.2:
                findings.append({"type": "liability_hiding", "period": idx + 1,
                    "message": "Sharp decrease in liabilities with increase in equity - verify off-balance-sheet items", "risk": "high"})
    
    return findings


def calculate_fraud_score(ratio_findings: List[Dict], manipulation_findings: List[Dict],
                          iso_scores: np.ndarray, iso_labels: np.ndarray) -> Tuple[float, str, Dict[str, Any]]:
    """Calculate composite fraud risk score (0-100) and risk category."""
    n_anomalies = int(np.sum(iso_labels == -1))
    avg_anomaly = float(np.mean(iso_scores))
    
    anomaly_component = min(40, avg_anomaly * 40 + n_anomalies * 5)
    high_risk_ratios = sum(1 for f in ratio_findings if f.get("risk") == "high")
    ratio_component = min(30, high_risk_ratios * 8 + len(ratio_findings) * 3)
    high_manip = sum(1 for f in manipulation_findings if f.get("risk") == "high")
    med_manip = sum(1 for f in manipulation_findings if f.get("risk") == "medium")
    manip_component = min(30, high_manip * 12 + med_manip * 5)
    
    fraud_score = min(100, round(anomaly_component + ratio_component + manip_component, 1))
    risk_category = "Low Risk" if fraud_score < 30 else "Medium Risk" if fraud_score < 60 else "High Risk"
    
    breakdown = {
        "fraud_score": fraud_score, "risk_category": risk_category,
        "components": {"anomaly_detection": round(anomaly_component, 1), "ratio_anomalies": round(ratio_component, 1),
                      "manipulation_patterns": round(manip_component, 1)},
        "anomaly_periods": n_anomalies, "ratio_flags": len(ratio_findings), "manipulation_flags": len(manipulation_findings),
    }
    return fraud_score, risk_category, breakdown


def run_full_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Run complete fraud analysis pipeline."""
    ratio_findings = detect_ratio_anomalies(df)
    manipulation_findings = detect_manipulation_patterns(df)
    iso_scores, iso_labels, result_df = run_isolation_forest_analysis(df)
    
    fraud_score, risk_category, breakdown = calculate_fraud_score(
        ratio_findings, manipulation_findings, iso_scores, iso_labels
    )
    
    return {
        "fraud_score": fraud_score, "risk_category": risk_category, "breakdown": breakdown,
        "ratios_df": result_df, "findings": ratio_findings + manipulation_findings,
        "iso_scores": iso_scores, "iso_labels": iso_labels,
    }
