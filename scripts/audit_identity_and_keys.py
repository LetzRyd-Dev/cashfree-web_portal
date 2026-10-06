import os
import sys
import json
import psycopg2
import psycopg2.extras
from app.config import settings

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def get_conn():
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    return conn

def run_full_audit():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    results = {
        "section_1_drivers": {},
        "section_2_operators": {},
        "section_3_relations_and_other_tables": {},
        "section_4_frontend_and_api": {}
    }
    
    print("=" * 80)
    print("SECTION 1: AUDIT APP_DRIVERS")
    print("=" * 80)
    
    # 1. Total counts & null/uniqueness
    cur.execute("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(app_driver_id) as count_app_driver_id,
            COUNT(DISTINCT app_driver_id) as uniq_app_driver_id,
            COUNT(driver_id) as count_driver_id,
            COUNT(DISTINCT driver_id) as uniq_driver_id,
            COUNT(driver_code) as count_driver_code,
            COUNT(DISTINCT driver_code) as uniq_driver_code,
            COUNT(CASE WHEN driver_code IS NULL OR TRIM(driver_code) = '' THEN 1 END) as empty_driver_code,
            COUNT(phone) as count_phone,
            COUNT(DISTINCT phone) as uniq_phone,
            COUNT(CASE WHEN phone IS NULL OR TRIM(phone) = '' THEN 1 END) as empty_phone,
            COUNT(operator_id) as count_operator_id,
            COUNT(DISTINCT operator_id) as uniq_operator_id
        FROM app_drivers;
    """)
    drv_stats = dict(cur.fetchone())
    results["section_1_drivers"]["stats"] = drv_stats
    print("app_drivers summary stats:", drv_stats)
    
    # Check duplicate driver_id
    cur.execute("""
        SELECT driver_id, COUNT(*) as count, 
               array_agg(app_driver_id) as app_driver_ids, 
               array_agg(full_name) as names, 
               array_agg(phone) as phones
        FROM app_drivers
        WHERE driver_id IS NOT NULL
        GROUP BY driver_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC;
    """)
    dup_driver_ids = [dict(r) for r in cur.fetchall()]
    results["section_1_drivers"]["duplicate_driver_ids_count"] = len(dup_driver_ids)
    results["section_1_drivers"]["duplicate_driver_ids"] = dup_driver_ids
    print(f"\nTotal duplicate driver_id values in app_drivers: {len(dup_driver_ids)}")
    for d in dup_driver_ids[:10]:
        print(f"  driver_id={d['driver_id']} count={d['count']} app_driver_ids={d['app_driver_ids']} names={d['names']}")

    # Check duplicate driver_code
    cur.execute("""
        SELECT driver_code, COUNT(*) as count, 
               array_agg(app_driver_id) as app_driver_ids, 
               array_agg(full_name) as names, 
               array_agg(phone) as phones
        FROM app_drivers
        WHERE driver_code IS NOT NULL AND TRIM(driver_code) != ''
        GROUP BY driver_code
        HAVING COUNT(*) > 1
        ORDER BY count DESC;
    """)
    dup_driver_codes = [dict(r) for r in cur.fetchall()]
    results["section_1_drivers"]["duplicate_driver_codes_count"] = len(dup_driver_codes)
    results["section_1_drivers"]["duplicate_driver_codes"] = dup_driver_codes
    print(f"\nTotal duplicate driver_code values in app_drivers: {len(dup_driver_codes)}")
    for d in dup_driver_codes:
        print(f"  driver_code={d['driver_code']} count={d['count']} app_driver_ids={d['app_driver_ids']}")

    # Check duplicate phones
    cur.execute("""
        SELECT phone, COUNT(*) as count, 
               array_agg(app_driver_id) as app_driver_ids, 
               array_agg(full_name) as names, 
               array_agg(driver_code) as driver_codes
        FROM app_drivers
        WHERE phone IS NOT NULL AND TRIM(phone) != ''
        GROUP BY phone
        HAVING COUNT(*) > 1
        ORDER BY count DESC;
    """)
    dup_driver_phones = [dict(r) for r in cur.fetchall()]
    results["section_1_drivers"]["duplicate_driver_phones_count"] = len(dup_driver_phones)
    print(f"\nTotal duplicate phones in app_drivers: {len(dup_driver_phones)}")

    # Rows with NULL or empty driver_code or empty phone
    cur.execute("""
        SELECT app_driver_id, driver_id, full_name, phone, driver_code, operator_id, joined_date, is_active
        FROM app_drivers
        WHERE driver_code IS NULL OR TRIM(driver_code) = '' OR phone IS NULL OR TRIM(phone) = ''
        ORDER BY app_driver_id;
    """)
    null_drivers = [dict(r) for r in cur.fetchall()]
    for nd in null_drivers:
        if nd['joined_date']: nd['joined_date'] = str(nd['joined_date'])
    results["section_1_drivers"]["null_code_or_phone_drivers"] = null_drivers
    print(f"\nDrivers with NULL/empty driver_code or phone: {len(null_drivers)}")
    for nd in null_drivers:
        print(f"  app_driver_id={nd['app_driver_id']} driver_id={nd['driver_id']} name='{nd['full_name']}' phone='{nd['phone']}' code='{nd['driver_code']}' op_id={nd['operator_id']}")

    # Dummy or test accounts
    cur.execute("""
        SELECT app_driver_id, driver_id, full_name, phone, driver_code, operator_id, is_active
        FROM app_drivers
        WHERE full_name ILIKE '%test%' 
           OR full_name ILIKE '%audit%' 
           OR full_name ILIKE '%dummy%'
           OR full_name ILIKE '%sample%'
           OR phone LIKE '99999%' 
           OR phone LIKE '00000%' 
           OR phone LIKE '12345%' 
           OR driver_code ILIKE '%test%'
           OR driver_code ILIKE '%audit%'
           OR driver_code = 'SYSTEM_ONBOARDED'
        ORDER BY app_driver_id;
    """)
    test_drivers = [dict(r) for r in cur.fetchall()]
    results["section_1_drivers"]["test_dummy_drivers"] = test_drivers
    print(f"\nDummy/Test driver accounts identified: {len(test_drivers)}")
    for td in test_drivers:
        print(f"  app_driver_id={td['app_driver_id']} driver_id={td['driver_id']} name='{td['full_name']}' phone='{td['phone']}' code='{td['driver_code']}' active={td['is_active']}")

    # Breakdown of driver_code prefixes and formats across cities
    cur.execute("""
        SELECT 
            CASE 
                WHEN driver_code LIKE 'LETZBLR%' THEN 'LETZBLR (Bangalore)'
                WHEN driver_code LIKE 'LETZHYD%' THEN 'LETZHYD (Hyderabad)'
                WHEN driver_code LIKE 'LETZMUM%' THEN 'LETZMUM (Mumbai)'
                WHEN driver_code LIKE 'LETZDEL%' THEN 'LETZDEL (Delhi)'
                WHEN driver_code LIKE 'DRV-AL-%' THEN 'DRV-AL- (Allocation Form)'
                WHEN driver_code LIKE 'DRV-%' THEN 'DRV- (Generic ID)'
                WHEN driver_code LIKE 'LR-DRV-%' THEN 'LR-DRV- (Standard Portal ID)'
                WHEN driver_code = 'SYSTEM_ONBOARDED' THEN 'SYSTEM_ONBOARDED'
                WHEN driver_code IS NULL THEN 'NULL'
                ELSE 'OTHER: ' || SUBSTRING(driver_code FROM 1 FOR 10)
            END as pattern_prefix,
            COUNT(*) as count
        FROM app_drivers
        GROUP BY pattern_prefix
        ORDER BY count DESC;
    """)
    driver_code_dist = [dict(r) for r in cur.fetchall()]
    results["section_1_drivers"]["code_prefix_distribution"] = driver_code_dist
    print("\nDriver code prefix distribution across cities:")
    for dcd in driver_code_dist:
        print(f"  {dcd['pattern_prefix']:<35} : {dcd['count']}")

    # Check city-coded driver_codes with sub-patterns (e.g. LETZBLR<phone> vs LETZBLRIP<phone> vs others)
    cur.execute("""
        SELECT 
            CASE 
                WHEN driver_code ~ '^LETZ[A-Z]{3}[0-9]{10}$' THEN 'LETZ<CITY><10-digit-phone>'
                WHEN driver_code ~ '^LETZ[A-Z]{3}IP[0-9]{10}$' THEN 'LETZ<CITY>IP<10-digit-phone>'
                WHEN driver_code ~ '^DRV-AL-[0-9]+$' THEN 'DRV-AL-<int>'
                WHEN driver_code ~ '^DRV-[0-9]+$' THEN 'DRV-<int>'
                WHEN driver_code ~ '^LR-DRV-[0-9]+$' THEN 'LR-DRV-<int>'
                WHEN driver_code = 'SYSTEM_ONBOARDED' THEN 'SYSTEM_ONBOARDED'
                WHEN driver_code IS NULL THEN 'NULL'
                ELSE 'UNMATCHED: ' || driver_code
            END as regex_pattern,
            COUNT(*) as count
        FROM app_drivers
        GROUP BY regex_pattern
        ORDER BY count DESC;
    """)
    regex_dist = [dict(r) for r in cur.fetchall()]
    results["section_1_drivers"]["code_regex_distribution"] = regex_dist
    print("\nDriver code regex pattern classification:")
    for rd in regex_dist:
        print(f"  {rd['regex_pattern']:<35} : {rd['count']}")

    # Check operator_id reference integrity from app_drivers
    cur.execute("""
        SELECT d.app_driver_id, d.driver_id, d.full_name, d.operator_id, d.phone
        FROM app_drivers d
        WHERE d.operator_id IS NOT NULL 
          AND d.operator_id != 0
          AND NOT EXISTS (
              SELECT 1 FROM app_operators o 
              WHERE o.app_operator_id = d.operator_id
          );
    """)
    unmapped_driver_operators = [dict(r) for r in cur.fetchall()]
    results["section_1_drivers"]["unmapped_operator_ids"] = unmapped_driver_operators
    print(f"\napp_drivers referencing non-existent app_operator_id (excluding 0/NULL): {len(unmapped_driver_operators)}")
    for udo in unmapped_driver_operators[:10]:
        print(f"  app_driver_id={udo['app_driver_id']} name='{udo['full_name']}' operator_id={udo['operator_id']}")

    print("\n" + "=" * 80)
    print("SECTION 2: AUDIT APP_OPERATORS")
    print("=" * 80)

    cur.execute("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(app_operator_id) as count_app_operator_id,
            COUNT(DISTINCT app_operator_id) as uniq_app_operator_id,
            COUNT(operator_id) as count_operator_id,
            COUNT(DISTINCT operator_id) as uniq_operator_id,
            COUNT(operator_code) as count_operator_code,
            COUNT(DISTINCT operator_code) as uniq_operator_code,
            COUNT(CASE WHEN operator_code IS NULL OR TRIM(operator_code) = '' THEN 1 END) as empty_operator_code,
            COUNT(phone) as count_phone,
            COUNT(DISTINCT phone) as uniq_phone,
            COUNT(CASE WHEN phone IS NULL OR TRIM(phone) = '' THEN 1 END) as empty_phone,
            COUNT(app_driver_id) as count_app_driver_id,
            COUNT(DISTINCT app_driver_id) as uniq_app_driver_id
        FROM app_operators;
    """)
    op_stats = dict(cur.fetchone())
    results["section_2_operators"]["stats"] = op_stats
    print("app_operators summary stats:", op_stats)

    # Duplicate operator_code
    cur.execute("""
        SELECT operator_code, COUNT(*) as count, 
               array_agg(app_operator_id) as app_operator_ids, 
               array_agg(operator_id) as operator_ids, 
               array_agg(company_name) as company_names, 
               array_agg(phone) as phones
        FROM app_operators
        WHERE operator_code IS NOT NULL AND TRIM(operator_code) != ''
        GROUP BY operator_code
        HAVING COUNT(*) > 1
        ORDER BY count DESC;
    """)
    dup_op_codes = [dict(r) for r in cur.fetchall()]
    results["section_2_operators"]["duplicate_operator_codes"] = dup_op_codes
    print(f"\nDuplicate operator_code in app_operators: {len(dup_op_codes)}")
    for doc in dup_op_codes:
        print(f"  code={doc['operator_code']} count={doc['count']} app_op_ids={doc['app_operator_ids']} names={doc['company_names']} phones={doc['phones']}")

    # Detailed inspection of OP-501
    cur.execute("""
        SELECT app_operator_id, operator_id, app_driver_id, operator_code, operator_type, phone, company_name, contact_person_name, total_vehicles, active_vehicles, is_active, created_at
        FROM app_operators
        WHERE operator_code = 'OP-501' OR app_operator_id IN (2, 940) OR company_name ILIKE '%Samvreeddhi%';
    """)
    op_501_details = [dict(r) for r in cur.fetchall()]
    for opd in op_501_details:
        if opd['created_at']: opd['created_at'] = str(opd['created_at'])
    results["section_2_operators"]["op_501_investigation"] = op_501_details
    print(f"\nDeep-dive OP-501 records:")
    for opd in op_501_details:
        print(f"  app_op_id={opd['app_operator_id']} op_id={opd['operator_id']} code={opd['operator_code']} name='{opd['company_name']}' phone='{opd['phone']}' active={opd['is_active']} vehicles={opd['total_vehicles']} created={opd['created_at']}")

    # Duplicate operator_id
    cur.execute("""
        SELECT operator_id, COUNT(*) as count, 
               array_agg(app_operator_id) as app_operator_ids, 
               array_agg(operator_code) as operator_codes, 
               array_agg(company_name) as company_names,
               array_agg(phone) as phones
        FROM app_operators
        WHERE operator_id IS NOT NULL
        GROUP BY operator_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC;
    """)
    dup_op_ids = [dict(r) for r in cur.fetchall()]
    results["section_2_operators"]["duplicate_operator_ids"] = dup_op_ids
    print(f"\nDuplicate operator_id values in app_operators: {len(dup_op_ids)}")
    for doi in dup_op_ids:
        print(f"  operator_id={doi['operator_id']} count={doi['count']} app_op_ids={doi['app_operator_ids']} codes={doi['operator_codes']} names={doi['company_names']}")

    # Operator code patterns
    cur.execute("""
        SELECT 
            CASE 
                WHEN operator_code LIKE 'LETZBLR%' THEN 'LETZBLR (Bangalore)'
                WHEN operator_code LIKE 'LETZHYD%' THEN 'LETZHYD (Hyderabad)'
                WHEN operator_code LIKE 'LETZMUM%' THEN 'LETZMUM (Mumbai)'
                WHEN operator_code LIKE 'LETZDEL%' THEN 'LETZDEL (Delhi)'
                WHEN operator_code LIKE 'OP-%' THEN 'OP-###'
                WHEN operator_code LIKE 'OPR-%' THEN 'OPR-###'
                WHEN operator_code LIKE 'LR-OPR-%' THEN 'LR-OPR-###'
                WHEN operator_code IS NULL THEN 'NULL'
                ELSE 'OTHER: ' || SUBSTRING(operator_code FROM 1 FOR 10)
            END as pattern_prefix,
            COUNT(*) as count
        FROM app_operators
        GROUP BY pattern_prefix
        ORDER BY count DESC;
    """)
    op_code_dist = [dict(r) for r in cur.fetchall()]
    results["section_2_operators"]["code_prefix_distribution"] = op_code_dist
    print("\nOperator code distribution:")
    for ocd in op_code_dist:
        print(f"  {ocd['pattern_prefix']:<35} : {ocd['count']}")

    # Consistency between app_operators and app_drivers where phones match
    cur.execute("""
        SELECT 
            o.app_operator_id, o.operator_id, o.operator_code, o.company_name, o.phone as op_phone, o.app_driver_id as op_driver_fk,
            d.app_driver_id, d.driver_id, d.driver_code, d.full_name, d.phone as drv_phone, d.operator_id as drv_operator_fk
        FROM app_operators o
        JOIN app_drivers d ON o.phone = d.phone;
    """)
    matched_phones = [dict(r) for r in cur.fetchall()]
    results["section_2_operators"]["matched_phones_with_drivers_count"] = len(matched_phones)
    results["section_2_operators"]["matched_phones_sample"] = matched_phones[:20]
    print(f"\nPhone number matches between app_operators and app_drivers: {len(matched_phones)}")
    # Analyze why they match: are they attached drivers?
    mismatch_fks = [m for m in matched_phones if m['drv_operator_fk'] != m['app_operator_id']]
    print(f"  Of those {len(matched_phones)}, where driver's operator_id does NOT point to app_operator_id: {len(mismatch_fks)}")
    for mf in mismatch_fks[:10]:
        print(f"    Phone={mf['op_phone']} drv_name='{mf['full_name']}' op_name='{mf['company_name']}' drv_op_fk={mf['drv_operator_fk']} app_op_id={mf['app_operator_id']}")

    print("\n" + "=" * 80)
    print("SECTION 3: AUDIT HISAABS, PAYMENTS, TICKETS, ALLOCATIONS")
    print("=" * 80)

    # 3.1 APP_HISAABS
    cur.execute("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(app_hisaab_id) as count_app_hisaab_id,
            COUNT(DISTINCT app_hisaab_id) as uniq_app_hisaab_id,
            COUNT(hisaab_number) as count_hisaab_number,
            COUNT(DISTINCT hisaab_number) as uniq_hisaab_number,
            COUNT(CASE WHEN hisaab_number IS NULL OR TRIM(hisaab_number) = '' THEN 1 END) as empty_hisaab_number,
            COUNT(DISTINCT app_driver_id) as distinct_drivers,
            COUNT(DISTINCT app_operator_id) as distinct_operators
        FROM app_hisaabs;
    """)
    hisaab_stats = dict(cur.fetchone())
    results["section_3_relations_and_other_tables"]["app_hisaabs_stats"] = hisaab_stats
    print("app_hisaabs summary stats:", hisaab_stats)

    # Hisaab number patterns
    cur.execute("""
        SELECT 
            CASE 
                WHEN hisaab_number ~ '^HSB-[0-9]+$' THEN 'HSB-<seq>'
                WHEN hisaab_number ~ '^HSB-[0-9]{4}-W[0-9]+-[0-9]+$' THEN 'HSB-<year>-W<week>-<id>'
                WHEN hisaab_number ~ '^LR-HSB-[0-9]+$' THEN 'LR-HSB-<id>'
                WHEN hisaab_number ~ '^W[0-9]+-[0-9]{4}-[0-9]+$' THEN 'W<week>-<year>-<id>'
                WHEN hisaab_number IS NULL THEN 'NULL'
                ELSE 'OTHER: ' || SUBSTRING(hisaab_number FROM 1 FOR 15)
            END as pattern,
            COUNT(*) as count
        FROM app_hisaabs
        GROUP BY pattern
        ORDER BY count DESC;
    """)
    hsb_patterns = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["hisaab_number_patterns"] = hsb_patterns
    print("\nHisaab number pattern distribution:")
    for hp in hsb_patterns:
        print(f"  {hp['pattern']:<35} : {hp['count']}")

    # Orphaned app_driver_id in app_hisaabs
    cur.execute("""
        SELECT h.app_driver_id, COUNT(*) as count
        FROM app_hisaabs h
        LEFT JOIN app_drivers d ON h.app_driver_id = d.app_driver_id
        WHERE d.app_driver_id IS NULL
        GROUP BY h.app_driver_id;
    """)
    orphaned_hisaab_drivers = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["orphaned_hisaab_drivers"] = orphaned_hisaab_drivers
    print(f"\nOrphaned app_driver_id in app_hisaabs: {len(orphaned_hisaab_drivers)}")
    for ohd in orphaned_hisaab_drivers:
        print(f"  app_driver_id={ohd['app_driver_id']} count={ohd['count']}")

    # Orphaned app_operator_id in app_hisaabs
    cur.execute("""
        SELECT h.app_operator_id, COUNT(*) as count
        FROM app_hisaabs h
        LEFT JOIN app_operators o ON h.app_operator_id = o.app_operator_id
        WHERE o.app_operator_id IS NULL
        GROUP BY h.app_operator_id;
    """)
    orphaned_hisaab_operators = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["orphaned_hisaab_operators"] = orphaned_hisaab_operators
    print(f"\nOrphaned app_operator_id in app_hisaabs: {len(orphaned_hisaab_operators)}")
    for oho in orphaned_hisaab_operators:
        print(f"  app_operator_id={oho['app_operator_id']} count={oho['count']}")

    # Check allocation_id references from app_hisaabs
    cur.execute("""
        SELECT COUNT(*) as unmapped_allocations
        FROM app_hisaabs h
        WHERE h.allocation_id IS NOT NULL 
          AND NOT EXISTS (SELECT 1 FROM app_driver_allocations a WHERE a.app_allocation_id = h.allocation_id);
    """)
    unmapped_alloc_hsb = cur.fetchone()['unmapped_allocations']
    results["section_3_relations_and_other_tables"]["unmapped_hisaab_allocations"] = unmapped_alloc_hsb
    print(f"app_hisaabs with allocation_id not in app_driver_allocations: {unmapped_alloc_hsb}")

    # 3.2 APP_PAYMENTS
    cur.execute("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(app_payment_id) as count_app_payment_id,
            COUNT(DISTINCT app_payment_id) as uniq_app_payment_id,
            COUNT(cf_order_id) as count_cf_order_id,
            COUNT(DISTINCT cf_order_id) as uniq_cf_order_id,
            COUNT(CASE WHEN cf_order_id IS NULL OR TRIM(cf_order_id) = '' THEN 1 END) as empty_cf_order_id,
            COUNT(cf_payment_id) as count_cf_payment_id,
            COUNT(DISTINCT cf_payment_id) as uniq_cf_payment_id,
            COUNT(app_hisaab_id) as count_app_hisaab_id
        FROM app_payments;
    """)
    pmt_stats = dict(cur.fetchone())
    results["section_3_relations_and_other_tables"]["app_payments_stats"] = pmt_stats
    print("\napp_payments summary stats:", pmt_stats)

    # Duplicate cf_order_id
    cur.execute("""
        SELECT cf_order_id, COUNT(*) as count, 
               array_agg(app_payment_id) as app_payment_ids, 
               array_agg(status) as statuses
        FROM app_payments
        WHERE cf_order_id IS NOT NULL AND TRIM(cf_order_id) != ''
        GROUP BY cf_order_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC;
    """)
    dup_cf_orders = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["duplicate_cf_orders"] = dup_cf_orders
    print(f"Duplicate cf_order_id values in app_payments: {len(dup_cf_orders)}")
    for dco in dup_cf_orders:
        print(f"  cf_order_id={dco['cf_order_id']} count={dco['count']} pmt_ids={dco['app_payment_ids']}")

    # cf_order_id patterns
    cur.execute("""
        SELECT 
            CASE 
                WHEN cf_order_id ~ '^LR-ORD-[0-9]+$' THEN 'LR-ORD-<seq>'
                WHEN cf_order_id ~ '^CF-ORD-[0-9]+$' THEN 'CF-ORD-<seq>'
                WHEN cf_order_id ~ '^order_[0-9]+' THEN 'order_<id>'
                WHEN cf_order_id IS NULL THEN 'NULL'
                ELSE 'OTHER: ' || SUBSTRING(cf_order_id FROM 1 FOR 15)
            END as pattern,
            COUNT(*) as count
        FROM app_payments
        GROUP BY pattern
        ORDER BY count DESC;
    """)
    cf_patterns = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["cf_order_patterns"] = cf_patterns
    print("CF Order ID patterns:")
    for cp in cf_patterns:
        print(f"  {cp['pattern']:<35} : {cp['count']}")

    # Orphaned app_hisaab_id in app_payments
    cur.execute("""
        SELECT p.app_payment_id, p.app_hisaab_id, p.amount, p.status
        FROM app_payments p
        LEFT JOIN app_hisaabs h ON p.app_hisaab_id = h.app_hisaab_id
        WHERE p.app_hisaab_id IS NOT NULL AND h.app_hisaab_id IS NULL;
    """)
    orphaned_pmt_hisaabs = [dict(r) for r in cur.fetchall()]
    for oph in orphaned_pmt_hisaabs:
        if oph['amount']: oph['amount'] = float(oph['amount'])
    results["section_3_relations_and_other_tables"]["orphaned_payment_hisaabs"] = orphaned_pmt_hisaabs
    print(f"app_payments referencing non-existent app_hisaab_id: {len(orphaned_pmt_hisaabs)}")

    # Orphaned payers in app_payments
    cur.execute("""
        SELECT p.app_payment_id, p.payer_type, p.payer_id, p.amount, p.status
        FROM app_payments p
        WHERE p.payer_id IS NOT NULL 
          AND (
            (p.payer_type = 'driver' AND NOT EXISTS (SELECT 1 FROM app_drivers d WHERE d.app_driver_id = p.payer_id)) OR
            (p.payer_type = 'operator' AND NOT EXISTS (SELECT 1 FROM app_operators o WHERE o.app_operator_id = p.payer_id))
          );
    """)
    orphaned_payers = [dict(r) for r in cur.fetchall()]
    for op in orphaned_payers:
        if op['amount']: op['amount'] = float(op['amount'])
    results["section_3_relations_and_other_tables"]["orphaned_payers"] = orphaned_payers
    print(f"app_payments with orphaned payer_id: {len(orphaned_payers)}")

    # 3.3 APP_SUPPORT_TICKETS
    cur.execute("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(app_ticket_id) as count_app_ticket_id,
            COUNT(DISTINCT app_ticket_id) as uniq_app_ticket_id,
            COUNT(ticket_number) as count_ticket_number,
            COUNT(DISTINCT ticket_number) as uniq_ticket_number,
            COUNT(CASE WHEN ticket_number IS NULL OR TRIM(ticket_number) = '' THEN 1 END) as empty_ticket_number
        FROM app_support_tickets;
    """)
    tkt_stats = dict(cur.fetchone())
    results["section_3_relations_and_other_tables"]["app_support_tickets_stats"] = tkt_stats
    print("\napp_support_tickets summary stats:", tkt_stats)

    # Ticket number patterns
    cur.execute("""
        SELECT 
            CASE 
                WHEN ticket_number ~ '^TKT-[0-9]+$' THEN 'TKT-<seq>'
                WHEN ticket_number ~ '^LR-TKT-[0-9]+$' THEN 'LR-TKT-<seq>'
                WHEN ticket_number IS NULL THEN 'NULL'
                ELSE 'OTHER: ' || SUBSTRING(ticket_number FROM 1 FOR 15)
            END as pattern,
            COUNT(*) as count
        FROM app_support_tickets
        GROUP BY pattern
        ORDER BY count DESC;
    """)
    tkt_patterns = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["ticket_patterns"] = tkt_patterns
    print("Ticket number patterns:")
    for tp in tkt_patterns:
        print(f"  {tp['pattern']:<35} : {tp['count']}")

    # Duplicate ticket_number
    cur.execute("""
        SELECT ticket_number, COUNT(*) as count, array_agg(app_ticket_id) as app_ticket_ids
        FROM app_support_tickets
        WHERE ticket_number IS NOT NULL AND TRIM(ticket_number) != ''
        GROUP BY ticket_number
        HAVING COUNT(*) > 1;
    """)
    dup_tickets = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["duplicate_tickets"] = dup_tickets
    print(f"Duplicate ticket_numbers in app_support_tickets: {len(dup_tickets)}")

    # Orphaned creator_id in app_support_tickets
    cur.execute("""
        SELECT t.app_ticket_id, t.creator_type, t.creator_id, t.ticket_number
        FROM app_support_tickets t
        WHERE t.creator_id IS NOT NULL 
          AND (
            (t.creator_type = 'driver' AND NOT EXISTS (SELECT 1 FROM app_drivers d WHERE d.app_driver_id = t.creator_id)) OR
            (t.creator_type = 'operator' AND NOT EXISTS (SELECT 1 FROM app_operators o WHERE o.app_operator_id = t.creator_id))
          );
    """)
    orphaned_creators = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["orphaned_creators"] = orphaned_creators
    print(f"app_support_tickets with orphaned creator_id: {len(orphaned_creators)}")

    # 3.4 APP_DRIVER_ALLOCATIONS
    cur.execute("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(app_allocation_id) as count_app_allocation_id,
            COUNT(DISTINCT app_allocation_id) as uniq_app_allocation_id,
            COUNT(core_allocation_id) as count_core_allocation_id,
            COUNT(DISTINCT core_allocation_id) as uniq_core_allocation_id,
            COUNT(DISTINCT app_driver_id) as distinct_drivers,
            COUNT(DISTINCT app_operator_id) as distinct_operators,
            COUNT(DISTINCT vehicle_number) as distinct_vehicles,
            COUNT(CASE WHEN vehicle_number IS NULL OR TRIM(vehicle_number) = '' THEN 1 END) as empty_vehicles
        FROM app_driver_allocations;
    """)
    alloc_stats = dict(cur.fetchone())
    results["section_3_relations_and_other_tables"]["app_driver_allocations_stats"] = alloc_stats
    print("\napp_driver_allocations summary stats:", alloc_stats)

    # Duplicate core_allocation_id
    cur.execute("""
        SELECT core_allocation_id, COUNT(*) as count, array_agg(app_allocation_id) as app_alloc_ids
        FROM app_driver_allocations
        WHERE core_allocation_id IS NOT NULL
        GROUP BY core_allocation_id
        HAVING COUNT(*) > 1;
    """)
    dup_core_alloc = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["duplicate_core_allocations"] = dup_core_alloc
    print(f"Duplicate core_allocation_id in app_driver_allocations: {len(dup_core_alloc)}")

    # Orphaned app_driver_id in app_driver_allocations
    cur.execute("""
        SELECT a.app_driver_id, COUNT(*) as count
        FROM app_driver_allocations a
        LEFT JOIN app_drivers d ON a.app_driver_id = d.app_driver_id
        WHERE d.app_driver_id IS NULL
        GROUP BY a.app_driver_id;
    """)
    orphaned_alloc_drivers = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["orphaned_alloc_drivers"] = orphaned_alloc_drivers
    print(f"Orphaned app_driver_id in app_driver_allocations: {len(orphaned_alloc_drivers)}")

    # Orphaned app_operator_id in app_driver_allocations
    cur.execute("""
        SELECT a.app_operator_id, COUNT(*) as count
        FROM app_driver_allocations a
        LEFT JOIN app_operators o ON a.app_operator_id = o.app_operator_id
        WHERE a.app_operator_id IS NOT NULL AND o.app_operator_id IS NULL
        GROUP BY a.app_operator_id;
    """)
    orphaned_alloc_operators = [dict(r) for r in cur.fetchall()]
    results["section_3_relations_and_other_tables"]["orphaned_alloc_operators"] = orphaned_alloc_operators
    print(f"Orphaned app_operator_id in app_driver_allocations: {len(orphaned_alloc_operators)}")

    # Save to JSON
    with open("scripts/audit_identity_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nFull audit findings saved to scripts/audit_identity_results.json")

    conn.close()

if __name__ == '__main__':
    run_full_audit()
