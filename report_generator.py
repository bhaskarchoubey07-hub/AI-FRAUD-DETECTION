"""
AI Audit Report Generator for AI Financial Statement Fraud Detector.
Uses OpenAI API to generate professional audit reports.
"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def get_openai_client() -> Optional[OpenAI]:
    """Initialize OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        return None
    return OpenAI(api_key=api_key)


def format_findings_for_prompt(findings: list) -> str:
    """Format findings list into readable text for the AI prompt."""
    if not findings:
        return "No specific red flags or anomalies were detected by the automated analysis."
    
    lines = []
    for i, f in enumerate(findings, 1):
        msg = f.get("message", str(f))
        risk = f.get("risk", "unknown")
        ftype = f.get("type", "general")
        period = f.get("period", "N/A")
        lines.append(f"{i}. [{ftype.upper()}] {msg} (Period: {period}, Risk: {risk})")
    
    return "\n".join(lines)


def format_ratios_summary(ratios_df) -> str:
    """Format financial ratios summary for the prompt."""
    if ratios_df is None or ratios_df.empty:
        return "No ratio data available."
    
    # Get average ratios (excluding NaN)
    summary_lines = []
    for col in ["profit_margin", "debt_to_equity", "current_ratio", "asset_turnover"]:
        if col in ratios_df.columns:
            vals = ratios_df[col].dropna()
            if len(vals) > 0:
                avg = vals.mean()
                if col == "profit_margin":
                    summary_lines.append(f"  - Profit Margin: {avg:.2%} (avg)")
                elif col == "debt_to_equity":
                    summary_lines.append(f"  - Debt to Equity: {avg:.2f}x (avg)")
                elif col == "current_ratio":
                    summary_lines.append(f"  - Current Ratio: {avg:.2f}x (avg)")
                elif col == "asset_turnover":
                    summary_lines.append(f"  - Asset Turnover: {avg:.2f}x (avg)")
    
    return "\n".join(summary_lines) if summary_lines else "No ratios computed."


def generate_ai_audit_report(
    fraud_score: float,
    risk_category: str,
    breakdown: Dict[str, Any],
    findings: list,
    ratios_df,
    raw_df,
) -> str:
    """
    Generate professional audit report using OpenAI API.
    Falls back to template report if API is unavailable.
    """
    client = get_openai_client()
    
    findings_text = format_findings_for_prompt(findings)
    ratios_text = format_ratios_summary(ratios_df)
    
    # Build summary stats
    n_periods = len(raw_df) if raw_df is not None else 0
    revenue_trend = ""
    profit_trend = ""
    if raw_df is not None and len(raw_df) >= 2:
        rev_change = (raw_df["revenue"].iloc[-1] - raw_df["revenue"].iloc[0]) / max(1, abs(raw_df["revenue"].iloc[0]))
        prof_change = (raw_df["profit"].iloc[-1] - raw_df["profit"].iloc[0]) / max(1, abs(raw_df["profit"].iloc[0]))
        revenue_trend = f"Revenue trend: {rev_change:.1%} change over period"
        profit_trend = f"Profit trend: {prof_change:.1%} change over period"
    
    system_prompt = """You are a senior forensic accountant and auditor. Write a concise, professional 
audit report based on the automated fraud analysis results provided. Use formal audit language. 
Structure: 1) Executive Summary, 2) Fraud Risk Assessment, 3) Red Flags Detected, 4) Audit Opinion, 
5) Recommendations. Keep each section brief (2-4 sentences). Be objective and professional."""

    user_prompt = f"""Based on the following automated fraud analysis of financial statements, generate a professional audit report.

ANALYSIS RESULTS:
- Fraud Risk Score: {fraud_score}/100
- Risk Category: {risk_category}
- Number of periods analyzed: {n_periods}
- Anomaly periods flagged: {breakdown.get('anomaly_periods', 0)}
- Ratio red flags: {breakdown.get('ratio_flags', 0)}
- Manipulation pattern flags: {breakdown.get('manipulation_flags', 0)}

{revenue_trend}
{profit_trend}

FINANCIAL RATIOS (averages):
{ratios_text}

RED FLAGS AND FINDINGS:
{findings_text}

Generate the audit report now."""

    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=800,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return _generate_fallback_report(
                fraud_score, risk_category, findings, str(e)
            )
    
    return _generate_fallback_report(
        fraud_score, risk_category, findings,
        "OpenAI API key not configured. Add OPENAI_API_KEY to .env file."
    )


def _generate_fallback_report(
    fraud_score: float,
    risk_category: str,
    findings: list,
    reason: str = "",
) -> str:
    """Generate a template audit report when OpenAI is unavailable."""
    report = []
    report.append("=" * 60)
    report.append("AUDIT REPORT - FRAUD RISK ASSESSMENT")
    report.append("(Generated from automated analysis - AI enhancement unavailable)")
    report.append("=" * 60)
    report.append("")
    
    report.append("1. EXECUTIVE SUMMARY")
    report.append("-" * 40)
    report.append(f"The automated fraud analysis has assessed the submitted financial statements with a fraud risk score of {fraud_score}/100, placing the entity in the {risk_category} category.")
    if reason:
        report.append(f"Note: {reason}")
    report.append("")
    
    report.append("2. FRAUD RISK ASSESSMENT")
    report.append("-" * 40)
    report.append(f"Fraud Risk Score: {fraud_score}/100")
    report.append(f"Risk Category: {risk_category}")
    report.append("")
    
    report.append("3. RED FLAGS DETECTED")
    report.append("-" * 40)
    if findings:
        for i, f in enumerate(findings, 1):
            report.append(f"  {i}. {f.get('message', str(f))}")
    else:
        report.append("  No significant red flags were identified by the automated analysis.")
    report.append("")
    
    report.append("4. AUDIT OPINION")
    report.append("-" * 40)
    if fraud_score < 30:
        report.append("Based on the automated analysis, the financial statements exhibit low fraud risk indicators. Standard audit procedures are recommended.")
    elif fraud_score < 60:
        report.append("The analysis indicates moderate fraud risk. Enhanced audit procedures and additional verification of flagged items are recommended.")
    else:
        report.append("The analysis indicates elevated fraud risk. Comprehensive forensic procedures and management inquiry are strongly recommended.")
    report.append("")
    
    report.append("5. RECOMMENDATIONS")
    report.append("-" * 40)
    report.append("  - Conduct detailed substantive testing on anomalous periods")
    report.append("  - Verify unusual revenue and expense patterns with source documentation")
    report.append("  - Review related-party transactions and off-balance-sheet items")
    report.append("  - Consider forensic accounting specialist involvement if risk persists")
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)


def export_report_to_txt(report_text: str, filename: str = "fraud_audit_report.txt") -> str:
    """
    Save report to a text file.
    Returns the file path.
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)
    return filename
