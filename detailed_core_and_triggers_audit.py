import psycopg2
import json

conn = psycopg2.connect(
    host='35.200.196.113', port=5432, dbname='postgres',
    user='postgres', password='8S5]U3@L^Xz)\\FH}'
)
cur = conn.cursor()

print("="*70)
print("1. CHECK TRIGGERS ON CORE TABLES")
print("="*70)
cur.execute("""
    SELECT event_object_table, trigger_name, event_manipulation, action_statement, action_timing
    FROM information_schema.triggers
    WHERE trigger_schema = 'public' AND event_object_table LIKE 'core_%'
    ORDER BY event_object_table, trigger_name
""")
rows = cur.fetchall()
print(f"Triggers on core_* tables ({len(rows)}):")
for r in rows:
    print(" ", r)

print("\n" + "="*70)
print("2. CHECK TRIGGERS ON HISAAB TABLES")
print("="*70)
cur.execute("""
    SELECT event_object_table, trigger_name, event_manipulation, action_statement, action_timing
    FROM information_schema.triggers
    WHERE trigger_schema = 'public' AND event_object_table LIKE 'hisaab_%'
    ORDER BY event_object_table, trigger_name
""")
rows = cur.fetchall()
print(f"Triggers on hisaab_* tables ({len(rows)}):")
for r in rows:
    print(" ", r)

print("\n" + "="*70)
print("3. CHECK ALL TRIGGERS SYNCING TO APP TABLES")
print("="*70)
cur.execute("""
    SELECT event_object_table, trigger_name, event_manipulation, action_statement, action_timing
    FROM information_schema.triggers
    WHERE trigger_schema = 'public' AND trigger_name LIKE '%app%'
    ORDER BY event_object_table, trigger_name
""")
rows = cur.fetchall()
print(f"Triggers syncing to app tables ({len(rows)}):")
for r in rows:
    print(" ", r)

print("\n" + "="*70)
print("4. CHECK PAYMENTS DATA IN APP_PAYMENTS")
print("="*70)
cur.execute("SELECT app_payment_id, payment_type, payer_type, payer_id, amount, payment_mode, status, cf_order_id, cf_payment_id, initiated_at, completed_at FROM app_payments ORDER BY initiated_at DESC")
rows = cur.fetchall()
print(f"Total rows in app_payments: {len(rows)}")
for r in rows:
    print(" ", r)

print("\n" + "="*70)
print("5. CHECK APP_DRIVERS VS CORE_PARTNER_ONBOARDING DETAILS")
print("="*70)
cur.execute("""
    SELECT 
        (SELECT count(*) FROM core_partner_onboarding) as total_core,
        (SELECT count(distinct phone_number) FROM core_partner_onboarding WHERE phone_number IS NOT NULL AND phone_number != '') as unique_core_phones,
        (SELECT count(*) FROM app_drivers) as total_app_drivers,
        (SELECT count(distinct phone) FROM app_drivers) as unique_app_phones,
        (SELECT count(*) FROM app_operators) as total_app_operators
""")
stats = cur.fetchone()
print(f"Core Partner Onboarding Total: {stats[0]}")
print(f"Core Unique Phone Numbers: {stats[1]}")
print(f"App Drivers Total: {stats[2]} (Unique Phones: {stats[3]})")
print(f"App Operators Total: {stats[4]}")

# Check matching between core and app
cur.execute("""
    SELECT count(*)
    FROM core_partner_onboarding c
    JOIN app_drivers a ON right(regexp_replace(c.phone_number, '[^0-9]', '', 'g'), 10) = right(regexp_replace(a.phone, '[^0-9]', '', 'g'), 10)
""")
matched_drivers = cur.fetchone()[0]
print(f"Core Onboarding rows matched to app_drivers by phone: {matched_drivers} / {stats[0]}")

print("\n" + "="*70)
print("6. CHECK DRIVERS WITH HISAAB IN APP_HISAABS")
print("="*70)
cur.execute("""
    SELECT 
        count(distinct d.app_driver_id) as drivers_with_hisaab,
        (SELECT count(*) FROM app_drivers) as total_drivers
    FROM app_drivers d
    JOIN app_hisaabs h ON d.app_driver_id = h.app_driver_id
""")
r = cur.fetchone()
print(f"Drivers with hisaabs in app_hisaabs: {r[0]} / {r[1]} ({r[0]/r[1]*100:.1f}%)")

# Why do some drivers have NO hisaab in app_hisaabs?
cur.execute("""
    SELECT count(*)
    FROM app_drivers d
    LEFT JOIN app_hisaabs h ON d.app_driver_id = h.app_driver_id
    WHERE h.app_hisaab_id IS NULL
""")
no_hisaab = cur.fetchone()[0]
print(f"Drivers with NO hisaab records: {no_hisaab}")

conn.close()
