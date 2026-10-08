import psycopg2
import io
import time
import sys

PROD_HOST = "35.200.196.113"
PROD_DB = "postgres"
PROD_USER = "postgres"
PROD_PASS = "8S5]U3@L^Xz)\\FH}"

DEV_HOST = "34.93.205.164"
SNAPSHOT_DB = "letzryd_prod_snapshot"
DEV_USER = "letzryd_dev_user"
DEV_PASS = "LetzRydDevPass2026!"

start_time = time.time()
print("==================================================")
print("AUTOMATED PROD TO SNAPSHOT SYNC PIPELINE")
print("==================================================")

# 1. Connect to Prod DB
prod_conn = psycopg2.connect(host=PROD_HOST, dbname=PROD_DB, user=PROD_USER, password=PROD_PASS)
prod_cur = prod_conn.cursor()

# Get active base tables from Prod
prod_cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
      AND table_type = 'BASE TABLE'
      AND table_name NOT LIKE 'z_%' 
      AND table_name NOT LIKE '%_z'
    ORDER BY table_name;
""")
tables = [r[0] for r in prod_cur.fetchall()]
print(f"[1/3] Found {len(tables)} active base tables in Production DB.")

print(f"[2/3] Streaming schemas and data into {SNAPSHOT_DB}...")
success_count = 0

for i, table in enumerate(tables, 1):
    try:
        snap_conn = psycopg2.connect(host=DEV_HOST, dbname=SNAPSHOT_DB, user=DEV_USER, password=DEV_PASS)
        snap_cur = snap_conn.cursor()
        
        # Drop table if exists
        snap_cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
        
        # Get column definitions from Prod
        prod_cur.execute(f"""
            SELECT column_name, udt_name, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position;
        """, (table,))
        cols = prod_cur.fetchall()
        
        col_defs = []
        for c_name, udt_name, max_l in cols:
            if udt_name == 'varchar' and max_l:
                t_str = f"VARCHAR({max_l})"
            elif udt_name == 'bool':
                t_str = "BOOLEAN"
            elif udt_name in ('int4', 'integer'):
                t_str = "INTEGER"
            elif udt_name in ('int8', 'bigint'):
                t_str = "BIGINT"
            elif udt_name in ('float8', 'double precision'):
                t_str = "DOUBLE PRECISION"
            elif udt_name in ('numeric', 'decimal'):
                t_str = "NUMERIC"
            elif udt_name in ('timestamptz', 'timestamp with time zone'):
                t_str = "TIMESTAMPTZ"
            elif udt_name in ('timestamp', 'timestamp without time zone'):
                t_str = "TIMESTAMP"
            elif udt_name == 'jsonb':
                t_str = "JSONB"
            elif udt_name == 'json':
                t_str = "JSON"
            elif udt_name == 'date':
                t_str = "DATE"
            else:
                t_str = "TEXT"
            col_defs.append(f'"{c_name}" {t_str}')
        
        create_sql = f'CREATE TABLE "{table}" ({", ".join(col_defs)});'
        snap_cur.execute(create_sql)
        snap_conn.commit()
        
        # Binary stream data table by table
        buf = io.StringIO()
        prod_cur.copy_to(buf, table, sep='\t', null='\\N')
        buf.seek(0)
        snap_cur.copy_from(buf, table, sep='\t', null='\\N')
        snap_conn.commit()
        snap_conn.close()
        
        success_count += 1
        if i % 50 == 0 or i == len(tables):
            print(f"  -> Progress: [{i}/{len(tables)}] tables copied successfully...")
    except Exception as e:
        print(f"  [WARN] Table '{table}': {e}")
        try:
            prod_conn.rollback()
        except:
            pass

snap_conn = psycopg2.connect(host=DEV_HOST, dbname=SNAPSHOT_DB, user=DEV_USER, password=DEV_PASS)
snap_cur = snap_conn.cursor()

snap_cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
landed = snap_cur.fetchone()[0]

snap_conn.close()
prod_conn.close()

elapsed = time.time() - start_time
print(f"\n==================================================")
print(f"[SUCCESS] Snapshot Sync Completed in {elapsed:.1f} seconds!")
print(f"  - Host: {DEV_HOST}:5432")
print(f"  - Database: {SNAPSHOT_DB}")
print(f"  - Total Tables Landed: {landed} / {len(tables)}")
print(f"==================================================")
