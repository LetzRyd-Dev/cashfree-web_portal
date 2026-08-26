"""
parse_ola_statement.py
======================
Stage 2 of the Ola sync pipeline.

Responsibilities
----------------
- Load the downloaded .xlsx / .csv statement.
- Auto-detect which sheet is the raw statement and which is incentive
  (falls back to configured sheet names if auto-detection fails).
- Apply the column mapping from ola_column_map.json.
- Coerce types: dates → date, money columns → Decimal, strip symbols/commas.
- Normalize vehicle_number: uppercase, strip whitespace.
- Keep the full original row as `raw_json` per record.
- Return two DataFrames: one for july_ola_raw, one for july_ola_incentive.

Usage
-----
    from parse_ola_statement import parse_statement
    raw_df, incentive_df = parse_statement("/path/to/file.xlsx", week_start, week_end)
"""

import json
import os
import re
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd

# ── Load column map ────────────────────────────────────────────────────────────
_MAP_FILE = Path(__file__).parent / "ola_column_map.json"
with open(_MAP_FILE, encoding="utf-8") as _f:
    _COL_MAP = json.load(_f)

RAW_COL_MAP       = {k: v for k, v in _COL_MAP.get("raw_sheet", {}).items()  if not k.startswith("_")}
INCENTIVE_COL_MAP = {k: v for k, v in _COL_MAP.get("incentive_sheet", {}).items() if not k.startswith("_")}

# Keywords used to identify which sheet is which when the file has multiple sheets
_RAW_SHEET_HINTS       = ["rawcrns", "raw crns", "dailysummary", "daily summary", "rawpayments", "ola raw", "ola_raw", "driver performance", "raw", "statement"]
_INCENTIVE_SHEET_HINTS = ["ola incentive", "ola_incentive", "ola incentives"]


# ── Helpers ────────────────────────────────────────────────────────────────────
def _coerce_numeric(val) -> Optional[float]:
    """Strip ₹, commas, spaces and convert to float. Returns None on failure."""
    if hasattr(val, 'iloc'):
        valid_series = val.dropna()
        val = valid_series.iloc[0] if not valid_series.empty else None
    if pd.isna(val) or val == "" or val is None:
        return None
    s = str(val).strip().replace(",", "").replace("₹", "").replace(" ", "")
    # Handle parentheses as negative: (1234.56) → -1234.56
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _coerce_date(val) -> Optional[date]:
    """Try pd.to_datetime first, then several date formats common in Ola exports."""
    if hasattr(val, 'iloc'):
        valid_series = val.dropna()
        val = valid_series.iloc[0] if not valid_series.empty else None
    if pd.isna(val) or val == "" or val is None:
        return None
    if isinstance(val, (date, datetime)):
        return val.date() if isinstance(val, datetime) else val
    try:
        dt = pd.to_datetime(val, errors="coerce")
        if pd.notna(dt):
            return dt.date()
    except Exception:
        pass
    s = str(val).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d-%b-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _normalize_vehicle(val) -> str:
    """Uppercase and strip all spaces from a vehicle registration number."""
    if pd.isna(val) or val is None:
        return ""
    return re.sub(r"\s+", "", str(val).strip().upper())


def _find_sheet(all_sheets: list, hints: list) -> Optional[str]:
    """Find the first sheet name matching the highest priority hint keyword."""
    for hint in hints:
        for sheet in all_sheets:
            if hint in sheet.lower():
                return sheet
    return None


def _read_sheet(file_path: str, sheet: Optional[str]) -> pd.DataFrame:
    """Read a sheet from xlsx/csv. If sheet is None and it's xlsx, read the first sheet."""
    ext = Path(file_path).suffix.lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path, sheet_name=sheet, dtype=str, na_values=["", "NA", "N/A", "-"])
    # CSV — ignore sheet name
    return pd.read_csv(file_path, dtype=str, na_values=["", "NA", "N/A", "-"])


# ── Public API ────────────────────────────────────────────────────────────────
def parse_statement(
    file_path: str,
    week_start: Optional[date] = None,
    week_end: Optional[date] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Parse the downloaded Ola statement.

    Parameters
    ----------
    file_path   : str   — path to the .xlsx or .csv file
    week_start  : date  — used to backfill week_start on every raw row
    week_end    : date  — used to backfill week_end on every raw row

    Returns
    -------
    (raw_df, incentive_df, summary_df)
    raw_df      : DataFrame ready for july_ola_raw
    incentive_df: DataFrame ready for july_ola_incentive
    summary_df  : DataFrame ready for july_ola_weekly_summary
    """
    print(f"[PARSE] Loading file: {file_path}")
    ext = Path(file_path).suffix.lower()

    if ext in (".xlsx", ".xls"):
        xl = pd.ExcelFile(file_path)
        all_sheets = xl.sheet_names
        print(f"[PARSE] Sheets in file: {all_sheets}")

        raw_sheet_name       = _find_sheet(all_sheets, _RAW_SHEET_HINTS)
        incentive_sheet_name = _find_sheet(all_sheets, _INCENTIVE_SHEET_HINTS)

        # If only one sheet, treat it as raw (incentive not in this file)
        if not raw_sheet_name and not incentive_sheet_name:
            raw_sheet_name = all_sheets[0]

        print(f"[PARSE] Raw sheet    → {raw_sheet_name!r}")
        print(f"[PARSE] Incentive sheet → {incentive_sheet_name!r}")

        raw_source       = _read_sheet(file_path, raw_sheet_name)       if raw_sheet_name       else pd.DataFrame()
        incentive_source = _read_sheet(file_path, incentive_sheet_name) if incentive_sheet_name else pd.DataFrame()
    else:
        # CSV — assume it's the raw sheet; no incentive data
        raw_source       = _read_sheet(file_path, None)
        incentive_source = pd.DataFrame()

    raw_df = _build_raw_df(raw_source, week_start, week_end)

    # Derive week_start and week_end if not provided
    if not raw_df.empty and (week_start is None or week_end is None):
        valid_dates = raw_df["stmt_date"].dropna()
        if not valid_dates.empty:
            if week_start is None:
                week_start = valid_dates.min()
            if week_end is None:
                week_end = valid_dates.max()

    incentive_df = _build_incentive_df(incentive_source, week_start, week_end)

    # If incentive_df is empty or missing required columns, generate using sample data formula
    if (incentive_df.empty or "trips" not in incentive_df.columns) and not raw_df.empty:
        print("[PARSE] Direct incentive summary sheet not found or empty. Computing incentive data via sample data formula...")
        incentive_df = _calculate_incentive_from_formula(file_path, raw_df, week_start, week_end)

    # Extract subscription fee data from RawTransactions / Deductions sheet
    sub_map = _extract_subscription_data(file_path)

    # Build weekly summary aggregation DataFrame for july_ola_weekly_summary
    summary_df = _build_weekly_summary_df(raw_df, incentive_df, sub_map, week_start, week_end)

    print(f"[PARSE] Raw rows parsed:       {len(raw_df)}")
    print(f"[PARSE] Incentive rows parsed: {len(incentive_df)}")
    print(f"[PARSE] Summary rows parsed:   {len(summary_df)}")
    return raw_df, incentive_df, summary_df


def _extract_subscription_data(file_path: str) -> dict:
    """Read RawTransactions / Deductions sheet to sum subscription_fee per vehicle."""
    sub_map = {}
    ext = Path(file_path).suffix.lower()
    if ext in (".xlsx", ".xls"):
        try:
            xl = pd.ExcelFile(file_path)
            hints = ["rawtransactions", "raw transactions", "deductions", "transaction", "transactions"]
            tx_sheet_name = _find_sheet(xl.sheet_names, hints)
            if tx_sheet_name:
                df = pd.read_excel(xl, sheet_name=tx_sheet_name, dtype=str)
                df = _normalize_headers(df, {"Car number": "vehicle_number", "Sub Category": "sub_category", "Amount": "amount"})

                vcol = next((c for c in df.columns if any(k in c.lower() for k in ["car number", "vehicle", "car_number", "vehicle_number"])), None)
                catcol = next((c for c in df.columns if any(k in c.lower() for k in ["sub category", "sub_category", "category", "type"])), None)
                amtcol = next((c for c in df.columns if any(k in c.lower() for k in ["amount", "debit", "fare"])), None)

                if vcol and catcol and amtcol:
                    for _, row in df.iterrows():
                        sub_cat = str(row.get(catcol, "")).lower()
                        if "subscription" in sub_cat:
                            vnum = _normalize_vehicle(row.get(vcol))
                            amt = _coerce_numeric(row.get(amtcol)) or 0.0
                            if vnum:
                                sub_map[vnum] = sub_map.get(vnum, 0.0) + amt
                    print(f"[PARSE] Extracted subscription fees for {len(sub_map)} vehicles from {tx_sheet_name!r}")
        except Exception as e:
            print(f"[PARSE] Non-fatal subscription extraction warning: {e}")
    return sub_map


def _build_weekly_summary_df(
    raw_df: pd.DataFrame,
    incentive_df: pd.DataFrame,
    sub_map: dict,
    week_start: Optional[date] = None,
    week_end: Optional[date] = None,
) -> pd.DataFrame:
    """Aggregate per vehicle for july_ola_weekly_summary."""
    if raw_df.empty:
        return pd.DataFrame()

    vnums = sorted(raw_df["vehicle_number"].dropna().unique())
    inc_map = {}
    if not incentive_df.empty and "received_incentive" in incentive_df.columns:
        for _, r in incentive_df.iterrows():
            vn = r.get("vehicle_number")
            if vn:
                inc_map[vn] = float(r.get("received_incentive") or 0.0)

    summary_rows = []
    for vnum in vnums:
        v_raw = raw_df[raw_df["vehicle_number"] == vnum]
        trips = int(v_raw["bookings_completed_raw"].sum() if "bookings_completed_raw" in v_raw.columns else len(v_raw))
        if trips == 0:
            trips = len(v_raw)

        revenue = float(v_raw["ride_earnings_raw"].fillna(0).sum()) if "ride_earnings_raw" in v_raw.columns else 0.0
        cash = float(v_raw["cash_collected_by_driver_raw"].fillna(0).sum()) if "cash_collected_by_driver_raw" in v_raw.columns else 0.0
        toll = float(v_raw["toll_parking_raw"].fillna(0).sum()) if "toll_parking_raw" in v_raw.columns else 0.0
        km = float(v_raw["actual_kms_raw"].fillna(0).sum()) if "actual_kms_raw" in v_raw.columns else 0.0
        inc = inc_map.get(vnum, 0.0)
        sub = sub_map.get(vnum, 0.0)

        ws = v_raw["week_start"].iloc[0] if "week_start" in v_raw.columns and not v_raw["week_start"].dropna().empty else week_start
        we = v_raw["week_end"].iloc[0] if "week_end" in v_raw.columns and not v_raw["week_end"].dropna().empty else week_end

        summary_rows.append({
            "vehicle_number": vnum,
            "week_start": ws,
            "week_end": we,
            "trips": trips,
            "revenue": round(revenue, 2),
            "cash_collection": round(cash, 2),
            "toll": round(toll, 2),
            "incentive": round(inc, 2),
            "subscription": round(sub, 2),
            "km": round(km, 2),
        })

    return pd.DataFrame(summary_rows)


def _normalize_headers(src: pd.DataFrame, target_map: dict) -> pd.DataFrame:
    """If src doesn't contain target headers in its column names, search all rows for target header row."""
    if src.empty:
        return src
    
    if any(k in src.columns for k in target_map.keys()):
        return src
    
    for idx in range(min(2500, len(src))):
        row_vals = [str(x).strip() for x in src.iloc[idx].values if pd.notna(x)]
        if any(k in row_vals for k in target_map.keys()):
            new_cols = [str(x).strip() if pd.notna(x) else f"Unnamed: {i}" for i, x in enumerate(src.iloc[idx].values)]
            new_df = src.iloc[idx + 1:].copy()
            new_df.columns = new_cols
            return new_df

    return src


def _build_raw_df(src: pd.DataFrame, week_start, week_end) -> pd.DataFrame:
    """Map, coerce, and validate rows for july_ola_raw."""
    if src.empty:
        return pd.DataFrame()

    src = _normalize_headers(src, RAW_COL_MAP)

    rename = {orig: dest for orig, dest in RAW_COL_MAP.items() if orig in src.columns}
    src = src.rename(columns=rename)
    src = src.loc[:, ~src.columns.duplicated()]

    rows = []
    for idx, row in src.iterrows():
        vnum = _normalize_vehicle(row.get("vehicle_number"))
        if not vnum:
            continue

        raw_json = row.to_dict()
        for k, v in raw_json.items():
            if pd.isna(v):
                raw_json[k] = None
            elif hasattr(v, "isoformat"):
                raw_json[k] = v.isoformat()
            else:
                raw_json[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v

        crn_val = str(row.get("crn", "")).strip() if pd.notna(row.get("crn")) else None
        if not crn_val or crn_val.lower() in ("nan", "none", ""):
            crn_val = f"NO_CRN_{vnum}_{row.get('stmt_date')}_{idx}"

        def _str_or_none(col):
            val = row.get(col)
            if pd.isna(val) or val is None:
                return None
            s = str(val).strip()
            return s if s and s.lower() not in ("nan", "none") else None

        def _int_or_none(col):
            num = _coerce_numeric(row.get(col))
            return int(num) if num is not None else None

        rows.append({
            "stmt_date":                      _coerce_date(row.get("stmt_date")),
            "week_start":                     week_start,
            "week_end":                       week_end,
            "vehicle_number":                 vnum,
            "driver_name":                    _str_or_none("driver_name"),
            "driver_number":                  _str_or_none("driver_number"),
            "crn":                            crn_val,
            "completion_status":              _str_or_none("completion_status"),
            "customer_bill_raw":              _coerce_numeric(row.get("customer_bill_raw")),
            "paid_by_ola_money_raw":          _coerce_numeric(row.get("paid_by_ola_money_raw")),
            "operator_bill_raw":              _coerce_numeric(row.get("operator_bill_raw")),
            "peak_pricing_raw":               _coerce_numeric(row.get("peak_pricing_raw")),
            "ride_earnings_raw":              _coerce_numeric(row.get("ride_earnings_raw")),
            "tds_raw":                        _coerce_numeric(row.get("tds_raw")),
            "toll_parking_raw":               _coerce_numeric(row.get("toll_parking_raw")),
            "cash_collected_by_driver_raw":   _coerce_numeric(row.get("cash_collected_by_driver_raw")),
            "ola_to_pay":                     _coerce_numeric(row.get("ola_to_pay")),
            "category":                       _str_or_none("category"),
            "pickup_time":                    _str_or_none("pickup_time"),
            "actual_kms_raw":                 _coerce_numeric(row.get("actual_kms_raw")),
            "trip_time_raw":                  _coerce_numeric(row.get("trip_time_raw")),
            "fare_raw":                       _coerce_numeric(row.get("fare_raw")),
            "share_osns":                     _str_or_none("share_osns"),
            "number_of_share_osns":           _int_or_none("number_of_share_osns"),
            "bookings_completed_raw":         _int_or_none("bookings_completed_raw"),
            "ride_type":                      _str_or_none("ride_type"),
            "pickup_location":                _str_or_none("pickup_location"),
            "drop_location":                  _str_or_none("drop_location"),
            "raw_json":                       json.dumps(raw_json),
        })

    return pd.DataFrame(rows)


def _build_incentive_df(src: pd.DataFrame, week_start, week_end) -> pd.DataFrame:
    """Map, coerce, and validate rows for july_ola_incentive."""
    if src.empty:
        return pd.DataFrame()

    src = _normalize_headers(src, INCENTIVE_COL_MAP)

    rename = {orig: dest for orig, dest in INCENTIVE_COL_MAP.items() if orig in src.columns}
    src = src.rename(columns=rename)
    src = src.loc[:, ~src.columns.duplicated()]

    rows = []
    for _, row in src.iterrows():
        vnum = _normalize_vehicle(row.get("vehicle_number"))
        if not vnum:
            continue

        raw_json = row.to_dict()
        for k, v in raw_json.items():
            if pd.isna(v):
                raw_json[k] = None
            elif hasattr(v, "isoformat"):
                raw_json[k] = v.isoformat()
            else:
                raw_json[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v

        rows.append({
            "week_start":          week_start,
            "week_end":            week_end,
            "vehicle_number":      vnum,
            "trips":               int(_coerce_numeric(row.get("trips")) or 0),
            "received_incentive":  _coerce_numeric(row.get("received_incentive")),
            "expected_incentive":  _coerce_numeric(row.get("expected_incentive")),
            "difference":          _coerce_numeric(row.get("difference")),
            "slab":                str(row.get("slab", "")).strip() or None,
            "slab_amount":         _coerce_numeric(row.get("slab_amount")),
            "after_tds":           _coerce_numeric(row.get("after_tds")),
            "raw_json":            json.dumps(raw_json),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    agg_rows = []
    for (vnum, ws, we), grp in df.groupby(["vehicle_number", "week_start", "week_end"], dropna=False):
        agg_rows.append({
            "week_start":          ws,
            "week_end":            we,
            "vehicle_number":      vnum,
            "trips":               int(grp["trips"].sum() or 0),
            "received_incentive":  float(grp["received_incentive"].fillna(0).sum()),
            "expected_incentive":  float(grp["expected_incentive"].fillna(0).sum()),
            "difference":          float(grp["difference"].fillna(0).sum()),
            "slab":                (", ".join(set(grp["slab"].dropna().astype(str))) or None)[:50] if grp["slab"].dropna().any() else None,
            "slab_amount":         float(grp["slab_amount"].fillna(0).sum()),
            "after_tds":           float(grp["after_tds"].fillna(0).sum()),
            "raw_json":            json.dumps(grp["raw_json"].tolist()),
        })

    return pd.DataFrame(agg_rows)


def _calculate_incentive_from_formula(
    file_path: str,
    raw_df: pd.DataFrame,
    week_start: Optional[date] = None,
    week_end: Optional[date] = None,
) -> pd.DataFrame:
    """
    Calculate incentive rows based on the sample data Excel formulas:
    - Vehicle Number: unique vehicles from raw statement
    - Trips: count of trips per vehicle in raw statement
    - Received Incentive: sum of 'rides_incentive' in 'Incentives & Other Earnings' sheet (if present)
    - Expected Incentive: 0.0 (or slab-based)
    - Difference: Received Incentive - Expected Incentive
    - After TDS: Received Incentive * 0.95 (5% TDS)
    """
    if raw_df.empty:
        return pd.DataFrame()

    vnums = sorted(raw_df["vehicle_number"].dropna().unique())

    # Try to extract rides_incentive from 'Incentives & Other Earnings' sheet if available
    inc_data = {}
    ext = Path(file_path).suffix.lower()
    if ext in (".xlsx", ".xls"):
        try:
            xl = pd.ExcelFile(file_path)
            inc_sheet_name = _find_sheet(xl.sheet_names, ["incentives & other earnings", "incentives", "other earnings"])
            if inc_sheet_name:
                inc_sheet = pd.read_excel(xl, sheet_name=inc_sheet_name, header=None)
                # Find header row containing Car number / Sub Category
                hdr_idx = None
                for idx in range(min(2500, len(inc_sheet))):
                    vals = [str(x).strip() for x in inc_sheet.iloc[idx].values if pd.notna(x)]
                    if any(k in vals for k in ["Car number", "Car Number", "Vehicle", "Sub Category"]):
                        hdr_idx = idx
                        break

                if hdr_idx is not None:
                    inc_sub_df = inc_sheet.iloc[hdr_idx + 1:].copy()
                    inc_sub_df.columns = [str(x).strip() for x in inc_sheet.iloc[hdr_idx].values]
                    
                    vcol = next((c for c in inc_sub_df.columns if c in ["Car number", "Car Number", "Vehicle"]), None)
                    subcat_col = next((c for c in inc_sub_df.columns if c in ["Sub Category", "Type"]), None)
                    amt_col = next((c for c in inc_sub_df.columns if c in ["Amount", "Amount Raw", "debit"]), None)

                    if vcol and amt_col:
                        inc_sub_df["vnum_norm"] = inc_sub_df[vcol].apply(_normalize_vehicle)
                        inc_sub_df["amt_norm"] = inc_sub_df[amt_col].apply(_coerce_numeric).fillna(0)

                        if subcat_col:
                            rides_df = inc_sub_df[(inc_sub_df[subcat_col].astype(str).str.lower().str.contains("rides_incentive|incentive"))]
                        else:
                            rides_df = inc_sub_df

                        for v, grp in rides_df.groupby("vnum_norm"):
                            inc_data[v] = float(grp["amt_norm"].sum())
        except Exception as e:
            print(f"[PARSE] Non-fatal error inspecting incentives sheet: {e}")

    rows = []
    for vnum in vnums:
        trips = int((raw_df["vehicle_number"] == vnum).sum())
        rec_inc = float(inc_data.get(vnum, 0.0))
        exp_inc = 0.0
        diff = rec_inc - exp_inc
        after_tds = round(rec_inc * 0.95, 2)
        raw_json = json.dumps({
            "source": "formula_calculated",
            "vehicle_number": vnum,
            "trips": trips,
            "received_incentive": rec_inc,
            "expected_incentive": exp_inc,
            "difference": diff,
            "after_tds": after_tds,
        })
        rows.append({
            "week_start":          week_start,
            "week_end":            week_end,
            "vehicle_number":      vnum,
            "trips":               trips,
            "received_incentive":  rec_inc,
            "expected_incentive":  exp_inc,
            "difference":          diff,
            "slab":                None,
            "slab_amount":         0.0,
            "after_tds":           after_tds,
            "raw_json":            raw_json,
        })

    return pd.DataFrame(rows)


# ── CLI entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_ola_statement.py <path_to_file.xlsx>")
        sys.exit(1)
    raw, inc, summary = parse_statement(sys.argv[1])
    print("\n── RAW sample ──")
    print(raw.head().to_string())
    print("\n── INCENTIVE sample ──")
    print(inc.head().to_string())
    print("\n── SUMMARY sample ──")
    print(summary.head().to_string())

