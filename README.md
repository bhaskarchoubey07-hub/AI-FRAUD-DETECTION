# AI Financial Statement Fraud Detector

A production-ready web application that analyzes financial statements to detect fraud risk, anomalies, manipulation patterns, and audit red flags. Generates a fraud risk score and detailed AI-powered audit report.

![Screenshots placeholder - Add your dashboard screenshot here]

## Features

- **File Upload** — Support for Excel (.xlsx, .xls) and CSV files with financial data
- **Fraud Detection** — Isolation Forest algorithm for anomaly detection, plus pattern-based rules
- **Financial Ratio Analysis** — Profit margin, debt-to-equity, current ratio, asset turnover
- **Manipulation Detection** — Revenue manipulation, expense suppression, asset inflation, liability hiding
- **AI Audit Report** — OpenAI-powered professional audit report with risk summary, red flags, opinion, and recommendations
- **Dashboard** — Clean finance-style UI with fraud score gauge, trend charts, and anomaly highlighting
- **Export** — Download audit report as TXT file

## Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python 3.11, Pandas, NumPy, Scikit-learn, Plotly
- **AI:** OpenAI API (GPT-4o-mini) for audit report generation

## Required Data Columns

Your uploaded file must contain these columns (case-insensitive, aliases supported):

| Standard   | Aliases                          |
|-----------|-----------------------------------|
| Revenue   | Sales, Income, Total Revenue     |
| Expenses  | Expense, Costs, Total Expenses   |
| Profit    | Net Income, Earnings, Net Profit |
| Assets    | Total Assets                     |
| Liabilities | Total Liabilities, Debt       |
| Equity    | Total Equity, Shareholders Equity, Net Worth |

## Installation

### 1. Clone or create project directory

```bash
cd fraud-detector
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure OpenAI API key (optional, for AI audit report)

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edit `.env`:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

> **Note:** The app works without an API key but will generate a template audit report instead of an AI-enhanced one.

## How to Run

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Example Output

- **Fraud Score:** 0–100 scale (Low / Medium / High risk)
- **Score Breakdown:** Anomaly detection, ratio anomalies, manipulation patterns
- **Charts:** Revenue and profit trends with anomaly points highlighted
- **Red Flags:** List of detected issues (e.g., expense suppression, unusual spikes)
- **Audit Report:** Executive summary, risk assessment, red flags, audit opinion, recommendations

## Project Structure

```
fraud-detector/
├── app.py                 # Streamlit main application
├── fraud_detection.py     # Isolation Forest + ratio analysis + manipulation detection
├── report_generator.py    # OpenAI audit report generation
├── utils.py               # File loading, validation, helpers
├── requirements.txt
├── README.md
├── .env.example
└── sample_data/
    └── sample_financials.csv
```

## Future Improvements

- [ ] Support for multi-entity / consolidated statements
- [ ] Time-series forecasting for trend-based anomaly detection
- [ ] PDF report export
- [ ] User authentication and report history
- [ ] Custom ratio thresholds and industry benchmarks
- [ ] Benford's Law analysis for digit distribution checks
- [ ] Database storage for audit trails
