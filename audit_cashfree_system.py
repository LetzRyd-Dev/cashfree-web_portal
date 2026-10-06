import psycopg2
import json

conn = psycopg2.connect(
    host='35.200.196.113', port=5432, dbname='postgres',
    user='postgres', password='8S5]U3@L^Xz)\\FH}'
)
cur = conn.cursor()

def q(sql, params=None):
    cur.execute(sql, params)
    return cur.fetchall()

print("="*60)
print("1. CORE TABLES vs APP TABLES AUDIT")
print("="*60)
core_partners_total = q("SELECT count(*) FROM core_partner_onboarding")[0][0]
print(f"Total rows in core_partner_onboarding: {core_partners_total}")

app_drivers_total = q("SELECT count(*) FROM app_drivers")[0][0]
app_operators_total = q("SELECT count(*) FROM app_operators")[0][0]
print(f"Total rows in app_drivers: {app_drivers_total}")
print(f"Total rows in app_operators: {app_operators_total}")

cur.execute("SELECT app_operator_id, company_name, contact_person_name, phone, total_vehicles, active_vehicles, cw_fleet_gross_earnings FROM app_operators LIMIT 5")
for r in cur.fetchall():
    print("  Operator:", r)

print("\n="*60)
print("2. HISAABS AUDIT")
print("="*60)
# inspect hisaab_vehicle_weekly columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'hisaab_vehicle_weekly'")
hisaab_cols = [r[0] for r in cur.fetchall()]
print(f"hisaab_vehicle_weekly columns ({len(hisaab_cols)}):", hisaab_cols[:15])

# find vehicle and week column names
veh_col = 'vehicle_number' if 'vehicle_number' in hisaab_cols else [c for c in hisaab_cols if 'veh' in c][0]
week_col = 'week_number' if 'week_number' in hisaab_cols else [c for c in hisaab_cols if 'week' in c][0]
print(f"Using vehicle column: {veh_col}, week column: {week_col}")

hisaab_core = q(f"SELECT count(*), count(distinct {veh_col}), count(distinct {week_col}) FROM hisaab_vehicle_weekly")[0]
print(f"hisaab_vehicle_weekly: total={hisaab_core[0]}, unique_vehicles={hisaab_core[1]}, unique_weeks={hisaab_core[2]}")

core_weeks = q(f"SELECT {week_col}, count(*) FROM hisaab_vehicle_weekly GROUP BY {week_col} ORDER BY {week_col} DESC LIMIT 10")
print("hisaab_vehicle_weekly weeks distribution:", core_weeks)

app_hisaabs_stats = q("SELECT count(*), count(distinct app_driver_id), count(distinct week_number) FROM app_hisaabs")[0]
print(f"app_hisaabs: total={app_hisaabs_stats[0]}, unique_drivers={app_hisaabs_stats[1]}, unique_weeks={app_hisaabs_stats[2]}")

app_weeks = q("SELECT week_number, count(*) FROM app_hisaabs GROUP BY week_number ORDER BY week_number")
print("app_hisaabs by week:", app_weeks)

cur.execute("""
    SELECT app_hisaab_id, app_driver_id, week_number, hisaab_number, vehicle_rent, current_period_os, 
           paid_amount, payment_status, is_locked 
    FROM app_hisaabs LIMIT 5
""")
for r in cur.fetchall():
    print("  app_hisaab sample:", r)

print("\n="*60)
print("3. PAYMENTS AUDIT")
print("="*60)
pay_total = q("SELECT count(*) FROM app_payments")[0][0]
print(f"Total rows in app_payments: {pay_total}")
if pay_total > 0:
    cur.execute("SELECT app_payment_id, driver_id, amount, status, gateway_order_id, payment_mode, created_at FROM app_payments ORDER BY created_at DESC LIMIT 10")
    for r in cur.fetchall():
        print("  Payment:", r)

print("\n="*60)
print("4. TRIGGERS & AUTO-CREATION ON ONBOARDING AUDIT")
print("="*60)
cur.execute("""
    SELECT trigger_name, event_manipulation, event_object_table, action_statement
    FROM information_schema.triggers
    WHERE trigger_schema = 'public'
""")
triggers = cur.fetchall()
print(f"Total triggers found: {len(triggers)}")
for t in triggers:
    print(f"  Trigger: {t[0]} on table {t[2]} (event: {t[1]})")

cur.execute("""
    SELECT proname, prosrc 
    FROM pg_proc 
    WHERE proname IN (
        'trg_sync_partner_to_app_driver', 
        'trg_sync_core_partner_to_app', 
        'trg_sync_allocation_to_app', 
        'trg_sync_hisaab_to_app',
        'sp_populate_all_app_tables'
    )
""")
funcs = cur.fetchall()
print(f"CDC / Sync functions found in pg_proc: {[f[0] for f in funcs]}")

conn.close()
