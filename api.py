"""
api.py — Standalone Backend API Server for Cash Web App
=========================================================
Project: Cash Web App / Driver & Operator Settlement Portal
Location: cashfree-web_portal-main/api.py

Provides independent REST APIs for the Cash Web App frontend and mounts
static production assets (dist/). Connects directly to PostgreSQL Cloud SQL.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import psycopg2
from psycopg2 import pool

# ── Load .env ──────────────────────────────────────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent / "ola-sync" / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

app = FastAPI(
    title="Cash Web App API",
    description="Standalone Driver & Operator Settlement Backend API",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database Connection Pool ───────────────────────────────────────────────────
def init_db_pool():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return psycopg2.pool.SimpleConnectionPool(1, 20, dsn=db_url)
    
    return psycopg2.pool.SimpleConnectionPool(
        1, 20,
        host=os.environ.get("DB_HOST", "35.200.196.113"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "postgres"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "8S5]U3@L^Xz)\\FH}"),
    )

db_pool = init_db_pool()


# ── Ensure Required Tables ─────────────────────────────────────────────────────
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

@app.on_event("startup")
def startup_db_check():
    conn = db_pool.getconn()
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(_ENSURE_TABLES_SQL)
            print("[OK] Standalone Cash Web App DB tables verified!")
    finally:
        db_pool.putconn(conn)


# ── REST API Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Cash Web App API", "version": "1.0.0"}


@app.get("/api/ola/summary")
def get_ola_summary(
    vehicle_number: Optional[str] = None,
    week_start: Optional[str] = None,
    week_end: Optional[str] = None
):
    """Aggregate Ola earnings per vehicle from july_ola_weekly_summary."""
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        filters = []
        params = []

        if vehicle_number:
            filters.append("vehicle_number ILIKE %s")
            params.append(f"%{vehicle_number}%")
        if week_start:
            filters.append("week_start >= %s")
            params.append(week_start)
        if week_end:
            filters.append("week_end <= %s")
            params.append(week_end)

        where = ("WHERE " + " AND ".join(filters)) if filters else ""

        cur.execute(f"""
            SELECT
                vehicle_number,
                SUM(trips)           AS total_trips,
                SUM(revenue)         AS total_net_revenue,
                SUM(cash_collection) AS total_cash_collection,
                SUM(toll)            AS total_tolls,
                SUM(incentive)       AS total_received_incentive,
                SUM(subscription)    AS total_subscription,
                SUM(km)              AS total_kms
            FROM july_ola_weekly_summary
            {where}
            GROUP BY vehicle_number
            ORDER BY total_net_revenue DESC NULLS LAST;
        """, params)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        
        # Fallback to july_ola_raw if summary table is empty
        if not rows:
            cur.execute("""
                SELECT vehicle_number,
                       COUNT(bookings_completed_raw) AS total_trips,
                       SUM(ride_earnings_raw)        AS total_net_revenue,
                       SUM(cash_collected_by_driver_raw) AS total_cash_collection,
                       SUM(toll_parking_raw)         AS total_tolls,
                       0                            AS total_received_incentive,
                       0                            AS total_subscription,
                       SUM(actual_kms_raw)           AS total_kms
                FROM july_ola_raw
                GROUP BY vehicle_number;
            """)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]

        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_pool.putconn(conn)


@app.get("/api/ola/sync-status")
def get_ola_sync_status(limit: int = 10):
    """Return latest sync timestamp from july_ola_raw."""
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT MAX(updated_at) AS finished_at,
                   COUNT(*) AS total_records
            FROM july_ola_raw;
        """)
        row = cur.fetchone()
        last_sync = row[0].isoformat() if row and row[0] else None
        return [{
            "id": 1,
            "import_type": "fetch_and_parse",
            "target_table": "july_ola_raw",
            "file_name": "partners.olacabs.com",
            "status": "Completed" if last_sync else "Pending",
            "started_at": last_sync,
            "finished_at": last_sync,
            "raw_record_count": row[1] if row else 0
        }]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_pool.putconn(conn)


@app.get("/api/driver/profile")
def get_driver_profile(phone: str):
    """Fetch Driver Profile by mobile phone number."""
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM july_driver_users WHERE phone = %s;", (phone,))
        row = cur.fetchone()
        if not row:
            # Fallback to june/july_onboarding
            cur.execute("SELECT driver_name, phone_number, city, driver_plan, security_deposit FROM july_onboarding WHERE phone_number = %s LIMIT 1;", (phone,))
            onb_row = cur.fetchone()
            if onb_row:
                return {
                    "found": True,
                    "data": {
                        "name": onb_row[0],
                        "phone": onb_row[1],
                        "city": onb_row[2],
                        "plan": onb_row[3],
                        "deposit": onb_row[4]
                    }
                }
            return {"found": False, "message": "Driver user not found"}
        cols = [d[0] for d in cur.description]
        return {"found": True, "data": dict(zip(cols, row))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_pool.putconn(conn)


@app.get("/api/operator/profile")
def get_operator_profile(phone: str):
    """Fetch Operator Profile by mobile phone number."""
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM july_operator_users WHERE phone = %s;", (phone,))
        row = cur.fetchone()
        if not row:
            return {"found": False, "message": "Operator user not found"}
        cols = [d[0] for d in cur.description]
        return {"found": True, "data": dict(zip(cols, row))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_pool.putconn(conn)


@app.get("/api/hisaab/calculated")
def get_calculated_hisaab(vehicle_number: Optional[str] = None):
    """Compute live weekly Hisaab calculations joining platform earnings, rent, and deductions."""
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        params = []
        where = ""
        if vehicle_number:
            where = "WHERE s.vehicle_number ILIKE %s"
            params.append(f"%{vehicle_number}%")

        cur.execute(f"""
            SELECT s.vehicle_number, s.week_start, s.week_end,
                   s.trips, s.revenue, s.cash_collection, s.toll, s.incentive, s.subscription, s.km,
                   COALESCE(c.total_challan, 0) AS total_challan
            FROM july_ola_weekly_summary s
            LEFT JOIN (
                SELECT vehicle_number, SUM(challan_amount) AS total_challan
                FROM copy_traffic_challans
                GROUP BY vehicle_number
            ) c ON c.vehicle_number = s.vehicle_number
            {where}
            ORDER BY s.week_start DESC;
        """, params)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return {"success": True, "count": len(rows), "data": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_pool.putconn(conn)


# ── Mount Static Files (Production Build in dist/) ─────────────────────────────
if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
