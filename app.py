"""
AI Financial Statement Fraud Detector - Main Application
Streamlit dashboard for financial fraud risk analysis.
"""

import streamlit as st
import traceback
from pathlib import Path

st.set_page_config(
    page_title="AI Fraud Detector | Financial Statement Analysis",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import after page config
try:
    import pandas as pd
    import plotly.graph_objects as go
    import io
    from utils import load_financial_data, validate_financial_logic
    from fraud_detection import run_full_analysis
    from report_generator import generate_ai_audit_report
except Exception as e:
    st.error(f"**Import error:** {e}")
    st.code(traceback.format_exc())
    st.stop()

# Premium finance dashboard styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Header area */
    h1 {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 50%, #0ea5e9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        margin-bottom: 0 !important;
    }
    
    /* Fraud score hero card */
    .fraud-hero {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        color: white;
        margin: 1.5rem 0;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(14, 165, 233, 0.2);
    }
    
    .fraud-score-val { font-size: 4rem; font-weight: 800; letter-spacing: -2px; }
    .fraud-score-low { color: #34d399 !important; }
    .fraud-score-med { color: #fbbf24 !important; }
    .fraud-score-high { color: #f87171 !important; }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: white;
        padding: 1.25rem;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07);
        border: 1px solid #e2e8f0;
    }
    
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.75rem !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }
    
    /* Section headers */
    h2 {
        color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 1.35rem !important;
        margin-top: 2rem !important;
    }
    
    /* Report area */
    .stTextArea textarea {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #34d399 0%, #fbbf24 50%, #f87171 100%) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Info box styling */
    .stAlert {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


def render_fraud_score(score: float, category: str):
    risk_class = "fraud-score-low" if score < 30 else "fraud-score-med" if score < 60 else "fraud-score-high"
    st.markdown(f"""
    <div class="fraud-hero">
        <div style="font-size: 0.85rem; letter-spacing: 4px; opacity: 0.8; margin-bottom: 0.5rem;">FRAUD RISK SCORE</div>
        <div class="fraud-score-val {risk_class}">{score:.0f}<span style="font-size: 2rem; opacity: 0.7;">/100</span></div>
        <div style="font-size: 1.2rem; margin-top: 0.75rem; font-weight: 500;">{category}</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(score / 100, text="Risk Level")


def main():
    st.title("🛡️ AI Financial Statement Fraud Detector")
    st.caption("Professional fraud risk analysis • Anomaly detection • Audit reporting")

    with st.sidebar:
        st.markdown("### 📁 Data Input")
        st.markdown("Upload Excel or CSV with financial data.")
        
        uploaded_file = st.file_uploader("Choose file", type=["csv", "xlsx", "xls"],
            help="Required: Revenue, Expenses, Profit, Assets, Liabilities, Equity")
        
        sample_path = Path(__file__).parent / "sample_data" / "sample_financials.csv"
        use_sample = st.checkbox("Use sample data", value=True, help="Demo with built-in sample")
        
        st.markdown("---")
        st.markdown("**Required columns:**")
        st.markdown("Revenue, Expenses, Profit, Assets, Liabilities, Equity")
    
    df = None
    if use_sample and sample_path.exists():
        with open(sample_path, "rb") as f:
            df, error = load_financial_data(io.BytesIO(f.read()), filename="sample_financials.csv")
        if error:
            st.error(error)
            return
    elif uploaded_file:
        df, error = load_financial_data(uploaded_file)
        if error:
            st.error(f"**Error:** {error}")
            return
    else:
        st.info("👆 Upload a file or enable **Use sample data** to analyze.")
        st.markdown("""
        ### Required Columns
        - **Revenue** (or Sales, Income)
        - **Expenses** (or Costs)
        - **Profit** (or Net Income, Earnings)
        - **Assets** (or Total Assets)
        - **Liabilities** (or Total Liabilities, Debt)
        - **Equity** (or Shareholders Equity)
        """)
        return

    for v in validate_financial_logic(df):
        st.warning(f"⚠️ {v['message']}")

    with st.spinner("Analyzing financial statements..."):
        try:
            results = run_full_analysis(df)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            return

    fraud_score = results["fraud_score"]
    risk_category = results["risk_category"]
    breakdown = results["breakdown"]
    findings = results["findings"]
    ratios_df = results["ratios_df"]

    st.header("📊 Fraud Risk Assessment")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        render_fraud_score(fraud_score, risk_category)

    bc = breakdown.get("components", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anomaly Detection", f"{bc.get('anomaly_detection', 0):.0f} pts", help="Statistical anomaly score")
    c2.metric("Ratio Anomalies", f"{bc.get('ratio_anomalies', 0):.0f} pts", help="Abnormal financial ratios")
    c3.metric("Manipulation Patterns", f"{bc.get('manipulation_patterns', 0):.0f} pts", help="Detected fraud patterns")
    c4.metric("Anomaly Periods", breakdown.get("anomaly_periods", 0), help="Flagged periods")

    st.header("📈 Financial Trends & Anomalies")
    col_left, col_right = st.columns(2)

    is_anomaly = ratios_df["is_anomaly"].values if "is_anomaly" in ratios_df.columns else [False] * len(df)
    
    with col_left:
        fig_rev = go.Figure()
        fig_rev.add_trace(go.Scatter(
            x=list(range(1, len(df) + 1)), y=df["revenue"].values,
            mode="lines+markers", name="Revenue",
            line=dict(color="#3b82f6", width=2.5),
            marker=dict(
                size=[12 if is_anomaly[i] else 6 for i in range(len(df))],
                color=["#ef4444" if is_anomaly[i] else "#3b82f6" for i in range(len(df))],
                line=dict(width=2, color="white"),
            ),
        ))
        fig_rev.update_layout(title="Revenue Trend", xaxis_title="Period", yaxis_title="Revenue",
            template="plotly_white", height=340, margin=dict(l=50, r=30, t=50, b=40),
            font=dict(family="Outfit"), plot_bgcolor="rgba(248,250,252,1)")
        st.plotly_chart(fig_rev, use_container_width=True)

    with col_right:
        fig_profit = go.Figure()
        fig_profit.add_trace(go.Scatter(
            x=list(range(1, len(df) + 1)), y=df["profit"].values,
            mode="lines+markers", name="Profit",
            line=dict(color="#10b981", width=2.5),
            marker=dict(
                size=[12 if is_anomaly[i] else 6 for i in range(len(df))],
                color=["#ef4444" if is_anomaly[i] else "#10b981" for i in range(len(df))],
                line=dict(width=2, color="white"),
            ),
        ))
        fig_profit.update_layout(title="Profit Trend", xaxis_title="Period", yaxis_title="Profit",
            template="plotly_white", height=340, margin=dict(l=50, r=30, t=50, b=40),
            font=dict(family="Outfit"), plot_bgcolor="rgba(248,250,252,1)")
        st.plotly_chart(fig_profit, use_container_width=True)

    ratio_cols = ["profit_margin", "debt_to_equity", "current_ratio", "asset_turnover"]
    avail = [c for c in ratio_cols if c in ratios_df.columns]
    avg_ratios = ratios_df[avail].mean().fillna(0) if avail else pd.Series(dtype=float)
    
    if len(avg_ratios) > 0:
        colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b"][:len(avail)]
        fig_ratios = go.Figure(data=[go.Bar(
            x=[r.replace("_", " ").title() for r in avail],
            y=avg_ratios.values.astype(float),
            marker_color=colors,
        )])
        fig_ratios.update_layout(title="Average Financial Ratios", yaxis_title="Value",
            template="plotly_white", height=300, font=dict(family="Outfit"))
        st.plotly_chart(fig_ratios, use_container_width=True)

    st.header("🚩 Red Flags & Findings")
    if findings:
        for f in findings:
            risk = f.get("risk", "medium")
            icon = "🔴" if risk == "high" else "🟡"
            st.markdown(f"{icon} **{f.get('message', str(f))}**")
    else:
        st.success("No significant red flags detected.")

    st.header("📋 AI Audit Report")
    with st.spinner("Generating report..."):
        report_text = generate_ai_audit_report(
            fraud_score, risk_category, breakdown, findings, ratios_df, df
        )

    st.text_area("Report", report_text, height=380, disabled=True)
    st.download_button("📥 Download Report (TXT)", data=report_text, file_name="fraud_audit_report.txt", mime="text/plain")


if __name__ == "__main__":
    main()
