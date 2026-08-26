"""
load_to_postgres.py
===================
Stage 3 of the Ola sync pipeline.

Responsibilities
----------------
- CREATE TABLE IF NOT EXISTS for july_ola_raw and july_ola_incentive
  (idempotent — same table names every run, every month, forever).
- Bulk upsert raw_df and incentive_df using psycopg2.extras.execute_values
  with ON CONFLICT DO UPDATE so re-running corrects rows instead of duplicating.
- Best-effort city_name backfill from july_vehicle_onboarding.
- Write final counts (inserted / updated / skipped) back to ola_import_log.

Usage
-----
    from load_to_postgres import load_to_postgres
    load_to_postgres(log_id, raw_df, incentive_df, week_start, week_end)
"""

import json
import os
import traceback
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import psycopg2
import psycopg2.extras

# ── Load .env (same logic as fetch_ola_statement.py) ─────────────────────────
_env_path = Path(__file__).parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _get_db_conn():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return psycopg2.connect(dsn=db_url)
    
    # GCP Cloud SQL Unix domain socket support
    cloud_sql_instance = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
    if cloud_sql_instance:
        db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
        return psycopg2.connect(
            host=f"{db_socket_dir}/{cloud_sql_instance}",
            dbname=os.environ.get("DB_NAME", "postgres"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASS"),
        )

    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "35.200.196.113"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "postgres"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS"),
    )


# ── Table DDL ─────────────────────────────────────────────────────────
_ENSURE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS july_ola_raw (
    id                             SERIAL PRIMARY KEY,
    stmt_date                      DATE,
    week_start                     DATE,
    week_end                       DATE,
    vehicle_number                 VARCHAR(50)   NOT NULL,
    driver_name                    VARCHAR(255),
    driver_number                  VARCHAR(50),
    crn                            VARCHAR(100),
    completion_status              VARCHAR(50),
    customer_bill_raw              NUMERIC(12,2) DEFAULT 0,
    paid_by_ola_money_raw          NUMERIC(12,2) DEFAULT 0,
    operator_bill_raw              NUMERIC(12,2) DEFAULT 0,
    peak_pricing_raw               NUMERIC(12,2) DEFAULT 0,
    ride_earnings_raw              NUMERIC(12,2) DEFAULT 0,
    tds_raw                        NUMERIC(12,2) DEFAULT 0,
    toll_parking_raw               NUMERIC(12,2) DEFAULT 0,
    cash_collected_by_driver_raw   NUMERIC(12,2) DEFAULT 0,
    ola_to_pay                     NUMERIC(12,2) DEFAULT 0,
    category                       VARCHAR(100),
    pickup_time                    VARCHAR(100),
    actual_kms_raw                 NUMERIC(10,2) DEFAULT 0,
    trip_time_raw                  NUMERIC(10,2) DEFAULT 0,
    fare_raw                       NUMERIC(12,2) DEFAULT 0,
    share_osns                     VARCHAR(255),
    number_of_share_osns           INTEGER      DEFAULT 0,
    bookings_completed_raw         INTEGER      DEFAULT 0,
    ride_type                      VARCHAR(100),
    pickup_location                TEXT,
    drop_location                  TEXT,
    raw_json                       JSONB,
    created_at                     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at                     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_aor_vehicle_crn ON july_ola_raw (vehicle_number, crn);
CREATE INDEX IF NOT EXISTS idx_aor_vehicle ON july_ola_raw (vehicle_number);
CREATE INDEX IF NOT EXISTS idx_aor_date    ON july_ola_raw (stmt_date DESC);
CREATE INDEX IF NOT EXISTS idx_aor_week    ON july_ola_raw (week_start, week_end);

CREATE TABLE IF NOT EXISTS july_ola_incentive (
    id                  SERIAL PRIMARY KEY,
    week_start          DATE,
    week_end            DATE,
    vehicle_number      VARCHAR(50) NOT NULL,
    trips               INTEGER      DEFAULT 0,
    received_incentive  NUMERIC(12,2) DEFAULT 0,
    expected_incentive  NUMERIC(12,2) DEFAULT 0,
    difference          NUMERIC(12,2) DEFAULT 0,
    slab                VARCHAR(255),
    slab_amount         NUMERIC(12,2) DEFAULT 0,
    after_tds           NUMERIC(12,2) DEFAULT 0,
    raw_json            JSONB,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (vehicle_number, week_start, week_end)
);
ALTER TABLE july_ola_incentive ALTER COLUMN slab TYPE VARCHAR(255);
ALTER TABLE july_ola_incentive ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
CREATE INDEX IF NOT EXISTS idx_aoi_vehicle ON july_ola_incentive (vehicle_number);
CREATE INDEX IF NOT EXISTS idx_aoi_week    ON july_ola_incentive (week_start, week_end);

CREATE TABLE IF NOT EXISTS july_ola_weekly_summary (
    id                  SERIAL PRIMARY KEY,
    vehicle_number      VARCHAR(50)   NOT NULL,
    week_start          DATE          NOT NULL,
    week_end            DATE          NOT NULL,
    trips               INTEGER       DEFAULT 0,
    revenue             NUMERIC(12,2) DEFAULT 0,
    cash_collection     NUMERIC(12,2) DEFAULT 0,
    toll                NUMERIC(12,2) DEFAULT 0,
    incentive           NUMERIC(12,2) DEFAULT 0,
    subscription        NUMERIC(12,2) DEFAULT 0,
    km                  NUMERIC(12,2) DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (vehicle_number, week_start, week_end)
);
CREATE INDEX IF NOT EXISTS idx_jows_vehicle ON july_ola_weekly_summary (vehicle_number);
CREATE INDEX IF NOT EXISTS idx_jows_week    ON july_ola_weekly_summary (week_start, week_end);

CREATE TABLE IF NOT EXISTS july_driver_users (
    id                     SERIAL PRIMARY KEY,
    driver_id              VARCHAR(50)   UNIQUE NOT NULL,
    phone                  VARCHAR(20)   UNIQUE NOT NULL,
    name                   VARCHAR(250)  NOT NULL,
    operator_code          VARCHAR(50),
    vehicle_number         VARCHAR(50),
    joined_date            DATE,
    deposit_total_required NUMERIC(12,2) DEFAULT 6000,
    deposit_paid_so_far    NUMERIC(12,2) DEFAULT 5000,
    deposit_pending        NUMERIC(12,2) DEFAULT 1000,
    cumulative_owed        NUMERIC(12,2) DEFAULT 0,
    is_active              BOOLEAN DEFAULT TRUE,
    created_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS july_operator_users (
    id                     SERIAL PRIMARY KEY,
    operator_code          VARCHAR(50)   UNIQUE NOT NULL,
    phone                  VARCHAR(20)   UNIQUE NOT NULL,
    operator_name          VARCHAR(250)  NOT NULL,
    operator_type          VARCHAR(100)  DEFAULT 'Individual Driver',
    deposit_total_required NUMERIC(12,2) DEFAULT 25000,
    deposit_paid_so_far    NUMERIC(12,2) DEFAULT 20000,
    deposit_pending        NUMERIC(12,2) DEFAULT 5000,
    created_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

# ── Upsert SQL ────────────────────────────────────────────────────────────────
_RAW_UPSERT_SQL = """
INSERT INTO july_ola_raw
    (stmt_date, week_start, week_end, vehicle_number,
     driver_name, driver_number, crn, completion_status,
     customer_bill_raw, paid_by_ola_money_raw, operator_bill_raw,
     peak_pricing_raw, ride_earnings_raw, tds_raw, toll_parking_raw,
     cash_collected_by_driver_raw, ola_to_pay, category, pickup_time,
     actual_kms_raw, trip_time_raw, fare_raw, share_osns,
     number_of_share_osns, bookings_completed_raw, ride_type,
     pickup_location, drop_location, raw_json)
VALUES %s
ON CONFLICT (vehicle_number, crn)
DO UPDATE SET
    stmt_date                    = EXCLUDED.stmt_date,
    week_start                   = EXCLUDED.week_start,
    week_end                     = EXCLUDED.week_end,
    driver_name                  = COALESCE(EXCLUDED.driver_name,                  july_ola_raw.driver_name),
    driver_number                = COALESCE(EXCLUDED.driver_number,                july_ola_raw.driver_number),
    completion_status            = COALESCE(EXCLUDED.completion_status,            july_ola_raw.completion_status),
    customer_bill_raw            = COALESCE(EXCLUDED.customer_bill_raw,            july_ola_raw.customer_bill_raw),
    paid_by_ola_money_raw        = COALESCE(EXCLUDED.paid_by_ola_money_raw,        july_ola_raw.paid_by_ola_money_raw),
    operator_bill_raw            = COALESCE(EXCLUDED.operator_bill_raw,            july_ola_raw.operator_bill_raw),
    peak_pricing_raw             = COALESCE(EXCLUDED.peak_pricing_raw,             july_ola_raw.peak_pricing_raw),
    ride_earnings_raw            = COALESCE(EXCLUDED.ride_earnings_raw,            july_ola_raw.ride_earnings_raw),
    tds_raw                      = COALESCE(EXCLUDED.tds_raw,                      july_ola_raw.tds_raw),
    toll_parking_raw             = COALESCE(EXCLUDED.toll_parking_raw,             july_ola_raw.toll_parking_raw),
    cash_collected_by_driver_raw = COALESCE(EXCLUDED.cash_collected_by_driver_raw, july_ola_raw.cash_collected_by_driver_raw),
    ola_to_pay                   = COALESCE(EXCLUDED.ola_to_pay,                   july_ola_raw.ola_to_pay),
    category                     = COALESCE(EXCLUDED.category,                     july_ola_raw.category),
    pickup_time                  = COALESCE(EXCLUDED.pickup_time,                  july_ola_raw.pickup_time),
    actual_kms_raw               = COALESCE(EXCLUDED.actual_kms_raw,               july_ola_raw.actual_kms_raw),
    trip_time_raw                = COALESCE(EXCLUDED.trip_time_raw,                july_ola_raw.trip_time_raw),
    fare_raw                     = COALESCE(EXCLUDED.fare_raw,                     july_ola_raw.fare_raw),
    share_osns                   = COALESCE(EXCLUDED.share_osns,                   july_ola_raw.share_osns),
    number_of_share_osns         = COALESCE(EXCLUDED.number_of_share_osns,         july_ola_raw.number_of_share_osns),
    bookings_completed_raw       = COALESCE(EXCLUDED.bookings_completed_raw,       july_ola_raw.bookings_completed_raw),
    ride_type                    = COALESCE(EXCLUDED.ride_type,                    july_ola_raw.ride_type),
    pickup_location              = COALESCE(EXCLUDED.pickup_location,              july_ola_raw.pickup_location),
    drop_location                = COALESCE(EXCLUDED.drop_location,                july_ola_raw.drop_location),
    raw_json                     = EXCLUDED.raw_json,
    updated_at                   = NOW();
"""

_INCENTIVE_UPSERT_SQL = """
INSERT INTO july_ola_incentive
    (week_start, week_end, vehicle_number,
     trips, received_incentive, expected_incentive, difference,
     slab, slab_amount, after_tds, raw_json)
VALUES %s
ON CONFLICT (vehicle_number, week_start, week_end)
DO UPDATE SET
    trips               = EXCLUDED.trips,
    received_incentive  = EXCLUDED.received_incentive,
    expected_incentive  = EXCLUDED.expected_incentive,
    difference          = EXCLUDED.difference,
    slab                = COALESCE(EXCLUDED.slab,        july_ola_incentive.slab),
    slab_amount         = COALESCE(EXCLUDED.slab_amount, july_ola_incentive.slab_amount),
    after_tds           = COALESCE(EXCLUDED.after_tds,   july_ola_incentive.after_tds),
    raw_json            = EXCLUDED.raw_json,
    updated_at          = NOW();
"""

_SUMMARY_UPSERT_SQL = """
INSERT INTO july_ola_weekly_summary
    (vehicle_number, week_start, week_end, trips, revenue, cash_collection, toll, incentive, subscription, km)
VALUES %s
ON CONFLICT (vehicle_number, week_start, week_end)
DO UPDATE SET
    trips           = EXCLUDED.trips,
    revenue         = EXCLUDED.revenue,
    cash_collection = EXCLUDED.cash_collection,
    toll            = EXCLUDED.toll,
    incentive       = EXCLUDED.incentive,
    subscription    = EXCLUDED.subscription,
    km              = EXCLUDED.km,
    updated_at      = NOW();
"""


# ── Main function ─────────────────────────────────────────────────────────────
def load_to_postgres(
    raw_df: pd.DataFrame,
    incentive_df: pd.DataFrame,
    summary_df: Optional[pd.DataFrame] = None,
    week_start: Optional[date] = None,
    week_end: Optional[date] = None,
    logger=print,
) -> dict:

    """
    Upsert raw and incentive DataFrames into Postgres.

    Returns
    -------
    dict  — {inserted_raw, updated_raw, inserted_incentive, updated_incentive, skipped}
    """
    conn = _get_db_conn()
    stats = {
        "inserted_raw": 0, "updated_raw": 0,
        "inserted_incentive": 0, "updated_incentive": 0,
        "skipped": 0,
    }

    try:
        with conn:
            cur = conn.cursor()

            # Ensure tables exist (idempotent)
            cur.execute(_ENSURE_TABLES_SQL)
            logger("[LOAD] Tables verified.")

            # ── Load raw rows ─────────────────────────────────────────────────
            if not raw_df.empty:
                raw_before = _count_table(cur, "july_ola_raw")

                raw_values = []
                for idx, row in raw_df.iterrows():
                    vnum      = row.get("vehicle_number") or ""
                    crn_val   = row.get("crn") or f"NO_CRN_{vnum}_{row.get('stmt_date')}_{idx}"
                    raw_values.append((
                        row.get("stmt_date"),
                        row.get("week_start") or week_start,
                        row.get("week_end") or week_end,
                        vnum,
                        row.get("driver_name"),
                        row.get("driver_number"),
                        crn_val,
                        row.get("completion_status"),
                        row.get("customer_bill_raw"),
                        row.get("paid_by_ola_money_raw"),
                        row.get("operator_bill_raw"),
                        row.get("peak_pricing_raw"),
                        row.get("ride_earnings_raw"),
                        row.get("tds_raw"),
                        row.get("toll_parking_raw"),
                        row.get("cash_collected_by_driver_raw"),
                        row.get("ola_to_pay"),
                        row.get("category"),
                        row.get("pickup_time"),
                        row.get("actual_kms_raw"),
                        row.get("trip_time_raw"),
                        row.get("fare_raw"),
                        row.get("share_osns"),
                        row.get("number_of_share_osns"),
                        row.get("bookings_completed_raw"),
                        row.get("ride_type"),
                        row.get("pickup_location"),
                        row.get("drop_location"),
                        row.get("raw_json"),
                    ))

                psycopg2.extras.execute_values(cur, _RAW_UPSERT_SQL, raw_values, page_size=200)
                raw_after = _count_table(cur, "july_ola_raw")
                stats["inserted_raw"] = raw_after - raw_before
                stats["updated_raw"]  = len(raw_values) - stats["inserted_raw"]
                logger(f"[LOAD] Raw: {stats['inserted_raw']} inserted, {stats['updated_raw']} updated")

            # ── Load incentive rows ────────────────────────────────────────────
            if not incentive_df.empty:
                inc_before = _count_table(cur, "july_ola_incentive")

                inc_values = []
                for _, row in incentive_df.iterrows():
                    vnum = row.get("vehicle_number") or ""
                    inc_values.append((
                        row.get("week_start") or week_start,
                        row.get("week_end") or week_end,
                        vnum,
                        row.get("trips") or 0,
                        row.get("received_incentive"),
                        row.get("expected_incentive"),
                        row.get("difference"),
                        row.get("slab"),
                        row.get("slab_amount"),
                        row.get("after_tds"),
                        row.get("raw_json"),
                    ))

                psycopg2.extras.execute_values(cur, _INCENTIVE_UPSERT_SQL, inc_values, page_size=200)
                inc_after = _count_table(cur, "july_ola_incentive")
                stats["inserted_incentive"] = inc_after - inc_before
                stats["updated_incentive"]  = len(inc_values) - stats["inserted_incentive"]
                logger(f"[LOAD] Incentive: {stats['inserted_incentive']} inserted, {stats['updated_incentive']} updated")

            # ── Load weekly summary rows ───────────────────────────────────────
            if summary_df is not None and not summary_df.empty:
                sum_before = _count_table(cur, "july_ola_weekly_summary")

                sum_values = []
                for _, row in summary_df.iterrows():
                    vnum = row.get("vehicle_number") or ""
                    sum_values.append((
                        vnum,
                        row.get("week_start") or week_start,
                        row.get("week_end") or week_end,
                        int(row.get("trips") or 0),
                        float(row.get("revenue") or 0.0),
                        float(row.get("cash_collection") or 0.0),
                        float(row.get("toll") or 0.0),
                        float(row.get("incentive") or 0.0),
                        float(row.get("subscription") or 0.0),
                        float(row.get("km") or 0.0),
                    ))

                psycopg2.extras.execute_values(cur, _SUMMARY_UPSERT_SQL, sum_values, page_size=200)
                sum_after = _count_table(cur, "july_ola_weekly_summary")
                stats["inserted_summary"] = sum_after - sum_before
                stats["updated_summary"]  = len(sum_values) - stats["inserted_summary"]
                logger(f"[LOAD] Weekly Summary: {stats['inserted_summary']} inserted, {stats['updated_summary']} updated")

            total_inserted = stats["inserted_raw"] + stats["inserted_incentive"] + stats.get("inserted_summary", 0)
            total_updated  = stats["updated_raw"]  + stats["updated_incentive"] + stats.get("updated_summary", 0)
            logger(f"[LOAD] ✓ Done. Inserted={total_inserted} Updated={total_updated}")
            return stats

    except Exception as e:
        logger(f"[LOAD] ERROR: {e}")
        traceback.print_exc()
        raise
    finally:
        conn.close()


def _count_table(cur, table: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {table};")
    return cur.fetchone()[0]
