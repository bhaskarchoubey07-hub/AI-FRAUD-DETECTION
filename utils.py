"""
Utility functions for AI Financial Statement Fraud Detector.
Handles file loading, validation, and data preprocessing.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import io


# Expected column names (case-insensitive matching)
EXPECTED_COLUMNS = [
    "revenue", "expenses", "profit",
    "assets", "liabilities", "equity"
]

# Alternative column names mapping for flexibility
COLUMN_ALIASES = {
    "revenue": ["revenue", "revenues", "sales", "total_revenue", "income"],
    "expenses": ["expenses", "expense", "total_expenses", "costs"],
    "profit": ["profit", "profits", "net_income", "net_profit", "earnings"],
    "assets": ["assets", "total_assets", "total_assets"],
    "liabilities": ["liabilities", "total_liabilities", "debt"],
    "equity": ["equity", "total_equity", "shareholders_equity", "net_worth"],
}


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to standard format.
    Supports case-insensitive matching and common aliases.
    """
    df = df.copy()
    column_map = {}
    
    for col in df.columns:
        col_lower = str(col).strip().lower()
        
        for standard_name, aliases in COLUMN_ALIASES.items():
            if col_lower in [a.lower() for a in aliases]:
                column_map[col] = standard_name
                break
    
    if column_map:
        df = df.rename(columns=column_map)
    
    return df


def load_financial_data(file, filename: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load financial data from uploaded Excel or CSV file.
    
    Args:
        file: File-like object (e.g. BytesIO) or path
        filename: Optional filename for extension detection (used when file has no .name)
    
    Returns:
        Tuple of (DataFrame, error_message).
        If successful, error_message is None.
    """
    try:
        file_extension = ""
        if filename:
            file_extension = filename.lower().split(".")[-1]
        elif hasattr(file, "name") and file.name:
            file_extension = str(file.name).lower().split(".")[-1]
        # Default to csv if extension unknown (e.g. BytesIO without name)
        if not file_extension:
            file_extension = "csv"
        
        if file_extension == "csv":
            df = pd.read_csv(io.BytesIO(file.read()))
        elif file_extension in ["xlsx", "xls"]:
            df = pd.read_excel(io.BytesIO(file.read()), engine="openpyxl" if file_extension == "xlsx" else "xlrd")
        else:
            return None, f"Unsupported file format: {file_extension}. Use CSV or Excel."
        
        if df.empty:
            return None, "The uploaded file is empty."
        
        # Normalize column names
        df = normalize_column_names(df)
        
        # Validate required columns
        missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
        if missing:
            return None, f"Missing required columns: {', '.join(missing)}. Found: {list(df.columns)}"
        
        # Extract only required columns
        df = df[EXPECTED_COLUMNS].copy()
        
        # Convert to numeric
        for col in EXPECTED_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Drop rows with all NaN
        df = df.dropna(how="all")
        
        if df.empty:
            return None, "No valid numeric data found in the file."
        
        # Sort by period if there's an index (assume rows are time-ordered)
        df = df.reset_index(drop=True)
        
        return df, None
        
    except Exception as e:
        return None, str(e)


def validate_financial_logic(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Validate basic accounting logic and flag inconsistencies.
    Returns list of validation findings.
    """
    findings = []
    
    # Assets = Liabilities + Equity (Balance Sheet equation)
    if "assets" in df.columns and "liabilities" in df.columns and "equity" in df.columns:
        balance_check = df["assets"] - (df["liabilities"] + df["equity"])
        tolerance = 0.01 * df["assets"].abs()
        violations = (balance_check.abs() > tolerance) & df["assets"].notna()
        if violations.any():
            findings.append({
                "type": "balance_sheet",
                "severity": "high",
                "message": f"Balance sheet equation violation: Assets ≠ Liabilities + Equity in {violations.sum()} period(s)"
            })
    
    # Revenue - Expenses ≈ Profit
    if all(c in df.columns for c in ["revenue", "expenses", "profit"]):
        calc_profit = df["revenue"] - df["expenses"]
        diff = (df["profit"] - calc_profit).abs()
        tolerance = 0.01 * df["revenue"].abs().replace(0, 1)
        violations = (diff > tolerance) & df["revenue"].notna()
        if violations.any():
            findings.append({
                "type": "income_statement",
                "severity": "medium",
                "message": f"Income statement inconsistency: Profit ≠ Revenue - Expenses in {violations.sum()} period(s)"
            })
    
    return findings


def format_currency(value: float) -> str:
    """Format number as currency string."""
    if pd.isna(value) or np.isinf(value):
        return "N/A"
    abs_val = abs(value)
    if abs_val >= 1e9:
        return f"${value/1e9:.2f}B"
    if abs_val >= 1e6:
        return f"${value/1e6:.2f}M"
    if abs_val >= 1e3:
        return f"${value/1e3:.2f}K"
    return f"${value:,.2f}"


def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics for the loaded data."""
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "date_range": f"Periods 1 to {len(df)}",
        "revenue_range": (df["revenue"].min(), df["revenue"].max()) if "revenue" in df.columns else (None, None),
        "profit_range": (df["profit"].min(), df["profit"].max()) if "profit" in df.columns else (None, None),
    }
