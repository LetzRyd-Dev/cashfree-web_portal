from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Testing Task 2: app_drivers manager update ===")
    
    q_drivers_test = """
        WITH latest_alloc AS (
            SELECT DISTINCT ON (a.app_driver_id)
                a.app_driver_id,
                a.assigned_city,
                cva.city as cva_city,
                cva.vehicle_manager_poc
            FROM app_driver_allocations a
            LEFT JOIN core_vehicle_allocation cva ON a.core_allocation_id = cva.id
            ORDER BY a.app_driver_id, 
                     CASE WHEN a.allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                     a.allocation_date DESC, a.app_allocation_id DESC
        ),
        driver_mgr_mapping AS (
            SELECT 
                d.app_driver_id,
                d.driver_code,
                d.assigned_manager_name as current_mgr_name,
                d.assigned_manager_phone as current_mgr_phone,
                COALESCE(
                    CASE la.vehicle_manager_poc
                        WHEN 'BLR_Faizan' THEN 'Syed Faizan'
                        WHEN 'MUM_Deepak' THEN 'Deepak Puran Thapa'
                        WHEN 'HYD_Durganjaneyulu' THEN 'Gogula Durganjaneyulu'
                        WHEN 'BLR_Kiran' THEN 'Kiran M K'
                        ELSE NULL
                    END,
                    CASE 
                        WHEN d.driver_code LIKE 'LETZMUM%' OR COALESCE(la.assigned_city, la.cva_city) ILIKE '%Mum%' THEN 'Vikram Sawant'
                        WHEN d.driver_code LIKE 'LETZHYD%' OR COALESCE(la.assigned_city, la.cva_city) ILIKE '%Hyd%' THEN 'K Ramesh'
                        ELSE 'Manjunath Gowda'
                    END
                ) as new_mgr_name,
                COALESCE(
                    CASE la.vehicle_manager_poc
                        WHEN 'BLR_Faizan' THEN '9900088220'
                        WHEN 'MUM_Deepak' THEN '9820098200'
                        WHEN 'HYD_Durganjaneyulu' THEN '9848022338'
                        WHEN 'BLR_Kiran' THEN '9900088220'
                        ELSE NULL
                    END,
                    CASE 
                        WHEN d.driver_code LIKE 'LETZMUM%' OR COALESCE(la.assigned_city, la.cva_city) ILIKE '%Mum%' THEN '9820098200'
                        WHEN d.driver_code LIKE 'LETZHYD%' OR COALESCE(la.assigned_city, la.cva_city) ILIKE '%Hyd%' THEN '9848022338'
                        ELSE '9900088220'
                    END
                ) as new_mgr_phone
            FROM app_drivers d
            LEFT JOIN latest_alloc la ON d.app_driver_id = la.app_driver_id
            WHERE d.assigned_manager_name IS NULL 
               OR d.assigned_manager_name = ''
               OR d.assigned_manager_phone IS NULL 
               OR d.assigned_manager_phone = ''
               OR d.assigned_manager_name = 'LetzRyd Fleet Operations'
               OR d.assigned_manager_phone = '080-4568-1234'
        )
        SELECT 
            new_mgr_name,
            new_mgr_phone,
            count(*)
        FROM driver_mgr_mapping
        GROUP BY 1, 2
        ORDER BY count(*) DESC;
    """
    res = conn.execute(text(q_drivers_test)).fetchall()
    print("New manager distribution for drivers without real manager:")
    for r in res:
        print(" ", r)
