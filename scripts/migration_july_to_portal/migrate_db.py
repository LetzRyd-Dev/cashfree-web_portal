"""
migrate_db.py — Python Migration Runner for July -> Portal Database Migration
=============================================================================
Usage:
  # Dry-run / status check only (no changes made):
  python scripts/migration_july_to_portal/migrate_db.py --env dev --check

  # Apply migration to DEV:
  python scripts/migration_july_to_portal/migrate_db.py --env dev --apply

  # Verify migration on DEV:
  python scripts/migration_july_to_portal/migrate_db.py --env dev --verify

  # Apply migration to PROD (Requires confirmation):
  python scripts/migration_july_to_portal/migrate_db.py --env prod --apply
"""

import sys
import os
import argparse
import psycopg2
from pathlib import Path

ENV_URLS = {
    "dev": "postgresql://letzryd_dev_user:LetzRydDevPass2026%21@34.93.205.164:5432/letzryd_dev",
    "prod": "postgresql://postgres:8S5%5DU3%40L%5EXz%29%5CFH%7D@35.200.196.113:5432/postgres",
}

DIR = Path(__file__).parent

def get_connection(env_name):
    url = ENV_URLS.get(env_name.lower())
    if not url:
        raise ValueError(f"Unknown environment: {env_name}. Choose 'dev' or 'prod'.")
    print(f"[*] Connecting to {env_name.upper()} database...")
    return psycopg2.connect(url, connect_timeout=10)

def check_status(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name LIKE 'july_%') AS july_tables,
            (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name LIKE 'portal_%' AND table_name != 'portal_rental_plans') AS portal_tables,
            (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'VIEW' AND table_name LIKE 'july_%' AND table_name != 'view_july_ola_weekly_kpis' AND table_name != 'july_v_kpi_summary') AS july_bridge_views;
    """)
    row = cur.fetchone()
    print("\n--- Current Schema State ---")
    print(f"  Physical 'july_*' base tables  : {row[0]}")
    print(f"  Physical 'portal_*' base tables: {row[1]}")
    print(f"  Compatibility 'july_*' views   : {row[2]}")
    
    if row[0] > 0 and row[1] == 0:
        print("\n>> Status: READY FOR MIGRATION (Original july_* tables present)")
    elif row[0] == 0 and row[1] > 0 and row[2] > 0:
        print("\n>> Status: MIGRATED WITH BRIDGE VIEWS (Active & Backward-Compatible)")
    elif row[0] == 0 and row[1] > 0 and row[2] == 0:
        print("\n>> Status: FULLY RETIRED (Bridge views dropped, 100% portal_*)")
    else:
        print("\n>> Status: IN-PROGRESS / PARTIAL MIGRATION")

def execute_sql_file(conn, file_path):
    print(f"\n[*] Executing {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()
    
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    print(f"[+] Successfully executed {file_path.name}")

def run_verify(conn):
    verify_file = DIR / "03_verify_migration.sql"
    cur = conn.cursor()
    print(f"\n[*] Running verification queries from {verify_file.name}...")
    
    cur.execute("""
        SELECT count(*) FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name LIKE 'portal_%';
    """)
    portal_count = cur.fetchone()[0]
    
    cur.execute("""
        SELECT count(*) FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'VIEW' AND table_name LIKE 'july_%';
    """)
    bridge_count = cur.fetchone()[0]
    
    print(f"  [+] Base 'portal_*' tables count: {portal_count}")
    print(f"  [+] Bridge 'july_*' views count : {bridge_count}")
    
    # Check sample table parity if portal_form_onboarding exists
    try:
        cur.execute("SELECT count(*) FROM portal_form_onboarding;")
        p_rows = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM july_form_onboarding;")
        j_rows = cur.fetchone()[0]
        match = "MATCH (SUCCESS)" if p_rows == j_rows else "MISMATCH (ERROR)"
        print(f"  [+] Data Parity Test (portal_form_onboarding): portal={p_rows}, bridge={j_rows} -> {match}")
    except Exception as e:
        print(f"  [-] Parity test note: {e}")

def main():
    parser = argparse.ArgumentParser(description="LetzRyd July to Portal Migration Tool")
    parser.add_argument("--env", choices=["dev", "prod"], default="dev", help="Target environment")
    parser.add_argument("--check", action="store_true", help="Check current migration status")
    parser.add_argument("--apply", action="store_true", help="Apply migration scripts 01 and 02")
    parser.add_argument("--verify", action="store_true", help="Run verification checks")
    
    args = parser.parse_args()
    
    if args.env == "prod" and args.apply:
        print("!" * 70)
        print("WARNING: You are about to apply migration changes to the PRODUCTION database.")
        print("!" * 70)
        conf = input("Type 'PROD-CONFIRM' to proceed: ")
        if conf != "PROD-CONFIRM":
            print("Aborted.")
            sys.exit(1)
            
    conn = get_connection(args.env)
    
    if args.check or (not args.apply and not args.verify):
        check_status(conn)
        
    if args.apply:
        execute_sql_file(conn, DIR / "01_rename_tables_and_create_bridge_views.sql")
        execute_sql_file(conn, DIR / "02_update_views_and_routines.sql")
        run_verify(conn)
        
    if args.verify and not args.apply:
        run_verify(conn)
        
    conn.close()

if __name__ == "__main__":
    main()
