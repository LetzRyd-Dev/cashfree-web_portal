import os, psycopg2
from dotenv import load_dotenv

load_dotenv('cashfree-web_portal-main/.env')
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

sql = """
CREATE OR REPLACE PROCEDURE public.sp_ensure_active_settlement_week()
LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_curr_monday DATE;
    v_curr_sunday DATE;
    v_week_num INT;
    v_year INT;
    v_week_id VARCHAR(20);
BEGIN
    v_curr_monday := DATE_TRUNC('week', CURRENT_DATE)::DATE;
    v_curr_sunday := (v_curr_monday + INTERVAL '6 days')::DATE;
    v_week_num := EXTRACT(WEEK FROM v_curr_monday)::INT;
    v_year := EXTRACT(YEAR FROM v_curr_monday)::INT;
    v_week_id := 'CY' || SUBSTRING(v_year::TEXT FROM 3 FOR 2) || 'WK' || LPAD(v_week_num::TEXT, 2, '0');

    INSERT INTO public.hisaab_settlement_weeks (
        week_id, settlement_year, settlement_week, week_start, week_end, lock_cutoff_at, is_locked, created_at, updated_at
    ) VALUES (
        v_week_id, v_year, v_week_num, v_curr_monday, v_curr_sunday, 
        (v_curr_monday + INTERVAL '7 days' + TIME '05:30:00')::TIMESTAMPTZ,
        FALSE, NOW(), NOW()
    )
    ON CONFLICT (settlement_year, settlement_week) DO UPDATE
    SET is_locked = FALSE, week_start = EXCLUDED.week_start, week_end = EXCLUDED.week_end, updated_at = NOW();
END;
$procedure$;
"""

cur.execute(sql)
conn.commit()
print("Procedure created!")

cur.execute("CALL public.sp_ensure_active_settlement_week();")
conn.commit()
print("Procedure called!")

try:
    cur.execute("""
        SELECT cron.schedule(
            'ensure-active-settlement-week',
            '1 0 * * 1',
            'CALL public.sp_ensure_active_settlement_week();'
        );
    """)
    conn.commit()
    print("Cron scheduled!")
except Exception as e:
    conn.rollback()
    print("pg_cron note:", e)

cur.close()
conn.close()
