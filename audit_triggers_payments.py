import psycopg2

conn = psycopg2.connect(
    host='35.200.196.113', port=5432, dbname='postgres',
    user='postgres', password='8S5]U3@L^Xz)\\FH}'
)
cur = conn.cursor()

print("="*60)
print("PAYMENTS COLUMNS & DATA")
print("="*60)
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'app_payments'")
cols = [r[0] for r in cur.fetchall()]
print("Columns in app_payments:", cols)

cur.execute("SELECT * FROM app_payments ORDER BY initiated_at DESC LIMIT 10")
for r in cur.fetchall():
    print("Payment row:", r)

print("\n" + "="*60)
print("TRIGGERS ON DATABASE TABLES")
print("="*60)
cur.execute("""
    SELECT event_object_table, trigger_name, event_manipulation, action_statement, action_timing
    FROM information_schema.triggers
    WHERE trigger_schema = 'public'
    ORDER BY event_object_table, trigger_name
""")
for t in cur.fetchall():
    print(f"Table: {t[0]:<30} Trigger: {t[1]:<35} Event: {t[2]:<8} Timing: {t[4]}")

print("\n" + "="*60)
print("STORED PROCEDURES & TRIGGER FUNCTIONS")
print("="*60)
cur.execute("""
    SELECT proname, prosrc 
    FROM pg_proc 
    WHERE proname IN (
        'trg_sync_partner_to_app_driver', 
        'trg_sync_core_partner_to_app', 
        'trg_sync_allocation_to_app', 
        'trg_sync_hisaab_to_app',
        'trg_sync_dropoff_to_app',
        'sp_populate_all_app_tables',
        'fn_cdc_core_partner_onboarding',
        'fn_cdc_core_vehicle_allocation',
        'fn_cdc_core_dropoffs',
        'fn_cdc_hisaab_vehicle_weekly'
    )
""")
funcs = cur.fetchall()
for f in funcs:
    print(f"\n--- Function / Proc: {f[0]} ---")
    print(f[1][:300], "..." if len(f[1]) > 300 else "")

conn.close()
