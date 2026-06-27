import re
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from config import REQUIRED_COLUMNS
import re as _re

def _detect_header_row(file_source, engine="openpyxl") -> int:
    try:
        if isinstance(file_source, str):
            preview = pd.read_excel(file_source, header=None, nrows=30, engine=engine)
        else:
            preview = pd.read_excel(file_source, header=None, nrows=30, engine=engine)
            file_source.seek(0)

        keywords = ["ibc", "contract", "customer", "billing", "cash", "dues", "cycle"]
        best_row, best_score = 0, 0
        for i, row in preview.iterrows():
            row_str = " ".join([str(v).lower() for v in row.values if pd.notna(v)])
            score = sum(1 for kw in keywords if kw in row_str)
            if score > best_score:
                best_score = score
                best_row = i
        return best_row
    except Exception:
        return 0


def _get_engine(name: str) -> str:
    if name.endswith(".xlsb"):  return "pyxlsb"
    if name.endswith(".xlsx"):  return "openpyxl"
    if name.endswith(".xls"):   return "xlrd"
    return "openpyxl"


def _dedup_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate columns — keep first occurrence."""
    return df.loc[:, ~df.columns.duplicated(keep="first")]

@st.cache_data(ttl=30)
def load_data(file_source) -> pd.DataFrame:

    # ── Read file 
    if isinstance(file_source, str):
        path = Path(file_source)
        if not path.exists():
            return _generate_sample_data()
        engine     = _get_engine(path.name.lower())
        header_row = _detect_header_row(file_source, engine=engine)
        df = pd.read_csv(path) if path.suffix == ".csv" else pd.read_excel(path, header=header_row, engine=engine)
    else:
        name    = file_source.name.lower()
        allowed = (".xlsx", ".xls", ".xlsb", ".csv")
        if not any(name.endswith(ext) for ext in allowed):
            st.error("❌ Unsupported file. Please upload: xlsx, xls, xlsb, or csv")
            return _generate_sample_data()
        engine     = _get_engine(name)
        header_row = _detect_header_row(file_source, engine=engine)
        file_source.seek(0)
        df = pd.read_csv(file_source) if name.endswith(".csv") else pd.read_excel(file_source, header=header_row, engine=engine)

    # ── Strip column names 
    df.columns = [str(c).strip() for c in df.columns]

    # ── Drop empty / unnamed columns
    df = df[[c for c in df.columns if not c.startswith("Unnamed") and c.strip() != ""]]
    df = df.dropna(axis=1, how="all").dropna(how="all")

    # ── Remove duplicate columns RIGHT HERE
    df = _dedup_columns(df)


    # ── Detect month columns BEFORE rename
    MONTHS = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    billing_cols = sorted([c for c in df.columns if re.search(rf"billing.*{MONTHS}", c.lower())])
    cash_cols    = sorted([c for c in df.columns if re.search(rf"^cash.*{MONTHS}", c.lower()) and "date" not in c.lower()])
    stubs_cols   = sorted([c for c in df.columns if re.search(rf"^stubs.*{MONTHS}", c.lower()) and "uni" not in c.lower()])

    df.attrs["billing_cols"]        = billing_cols
    df.attrs["cash_cols"]           = cash_cols
    df.attrs["stubs_cols"]          = stubs_cols
    df.attrs["current_billing_col"] = billing_cols[-1] if len(billing_cols) >= 1 else None
    df.attrs["prev_billing_col"]    = billing_cols[-2] if len(billing_cols) >= 2 else None
    df.attrs["current_cash_col"]    = cash_cols[-1]    if len(cash_cols)    >= 1 else None
    df.attrs["prev_cash_col"]       = cash_cols[-2]    if len(cash_cols)    >= 2 else None
    df.attrs["current_stubs_col"]   = stubs_cols[-1]   if len(stubs_cols)   >= 1 else None
    df.attrs["prev_stubs_col"]      = stubs_cols[-2]   if len(stubs_cols)   >= 2 else None

    # ── Coerce all month columns to numeric 
    for col in billing_cols + cash_cols + stubs_cols:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(r"[^\d.\-]", "", regex=True)
                .replace("", "0")
                .pipe(pd.to_numeric, errors="coerce")
                .fillna(0)
            )

    # ── Rename columns 
    rename_map = {"Consumer No.": "Contract Account"}
    for col in df.columns:
        col_lower = col.lower()
        if "cash date" in col_lower or ("cash" in col_lower and "date" in col_lower):
            rename_map[col] = "Cash Date"
        elif "issue date" in col_lower:
            rename_map[col] = "Assigned Date"
        elif col_lower == "due status":
            rename_map[col] = "Status"

    df.rename(columns=rename_map, inplace=True)

    # ── Remove duplicates again after rename 
    df = _dedup_columns(df)

    # ── Set current month as main Amount columns
    if billing_cols:
        df["Amount Billed"] = df[billing_cols[-1]].values
    if cash_cols:
        df["Amount Recovered"] = df[cash_cols[-1]].values
    if stubs_cols:
        df["Stub Collected"] = df[stubs_cols[-1]].astype(int).values
    elif "Amount Recovered" in df.columns:
        df["Stub Collected"] = (df["Amount Recovered"] > 0).astype(int)
    else:
        df["Stub Collected"] = 0

    # ── Coerce other numeric columns
    for col in ["Amount Billed", "Amount Recovered", "Dues", "LPA"]:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(r"[^\d.\-]", "", regex=True)
                .replace("", "0")
                .pipe(pd.to_numeric, errors="coerce")
                .fillna(0)
            )

    # ── Case Assigned = 1 per row
    df["Case Assigned"] = 1

    # ── Cycle Day: clean integer string 
    if "Cycle Day" in df.columns:
        df["Cycle Day"] = (
            pd.to_numeric(df["Cycle Day"], errors="coerce")
            .fillna(0).astype(int).astype(str)
        )

    # ── Drop rows where IBC Name is null 
    if "IBC Name" in df.columns:
        df = df[df["IBC Name"].notna() & (df["IBC Name"].astype(str).str.strip() != "")]

    # ── Final dedup before return 
    df = _dedup_columns(df)

    return df


def _generate_sample_data() -> pd.DataFrame:
    rng        = np.random.default_rng(42)
    n          = 5_000
    ibcs       = ["Bahadurabad", "Tipu Sultan", "Garden", "Clifton", "Saddar", "Defence"]
    chosen     = rng.choice(ibcs, size=n)
    billed_apr = rng.uniform(500, 200_000, size=n).round(2)
    billed_may = rng.uniform(500, 200_000, size=n).round(2)
    dues       = rng.uniform(10_000, 2_000_000, size=n).round(2)
    cash_apr   = np.where(rng.random(n) > 0.70, rng.uniform(500, 50_000, n), 0).round(2)
    cash_may   = np.where(rng.random(n) > 0.70, rng.uniform(500, 50_000, n), 0).round(2)
    stubs_apr  = (cash_apr > 0).astype(int)
    stubs_may  = (cash_may > 0).astype(int)

    df = pd.DataFrame({
        "Contract":          [f"3{i:07d}" for i in range(n)],
        "Contract Account":  [f"40000{i:07d}" for i in range(n)],
        "Customer Name":     [f"Customer {i+1}" for i in range(n)],
        "Customer Address":  [f"Address {i+1}, Karachi" for i in range(n)],
        "IBC Name":          chosen,
        "Agency":            ["SSP"] * n,
        "Cycle Day":         rng.integers(1, 21, size=n).astype(str),
        "Billing Apr'26":    billed_apr,
        "Cash Apr'26":       cash_apr,
        "Stubs Apr'26":      stubs_apr,
        "Billing May'26":    billed_may,
        "Cash May'26":       cash_may,
        "Stubs May'26":      stubs_may,
        "Dues":              dues,
        "LPA":               rng.uniform(0, 50_000, size=n).round(2),
        "LPD":               pd.date_range("2020-01-01", periods=n, freq="D").strftime("%d-%b-%y"),
        "Due Status":        rng.choice(["Not Due", "Overdue", "Paid"], size=n),
        "Issue Date":        pd.date_range("2025-01-01", periods=n, freq="D").strftime("%d-%b-%y"),
        "Cash Date May'26":  pd.date_range("2024-06-01", periods=n, freq="D").strftime("%d-%b-%y"),
        "Rebate Offer":      rng.choice(["Upto 50% with 06 Installments", ""], size=n),
        "REMARKS":           rng.choice(["Eligible in Scheme", "Registered in Scheme",
                                         "WO Scheme", "Fully Settled & Locked"], size=n),
    })

    df.attrs["billing_cols"]        = ["Billing Apr'26", "Billing May'26"]
    df.attrs["cash_cols"]           = ["Cash Apr'26",    "Cash May'26"]
    df.attrs["stubs_cols"]          = ["Stubs Apr'26",   "Stubs May'26"]
    df.attrs["current_billing_col"] = "Billing May'26"
    df.attrs["prev_billing_col"]    = "Billing Apr'26"
    df.attrs["current_cash_col"]    = "Cash May'26"
    df.attrs["prev_cash_col"]       = "Cash Apr'26"
    df.attrs["current_stubs_col"]   = "Stubs May'26"
    df.attrs["prev_stubs_col"]      = "Stubs Apr'26"

    df["Amount Billed"]    = df["Billing May'26"]
    df["Amount Recovered"] = df["Cash May'26"]
    df["Stub Collected"]   = df["Stubs May'26"]
    df["Case Assigned"]    = 1

    return df


def fmt_currency(val: float) -> str:
    if val >= 1_000_000: return f"PKR {val/1_000_000:.2f}M"
    if val >= 1_000:     return f"PKR {val/1_000:.1f}K"
    return f"PKR {val:.0f}"


def badge_class(rate: float) -> str:
    if rate >= 0.80: return ""
    if rate >= 0.55: return "warn"
    return "danger"