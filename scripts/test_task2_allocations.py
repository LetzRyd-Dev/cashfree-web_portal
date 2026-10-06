from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Testing Task 2: app_driver_allocations manager & hub ===")
    
    q = """
        SELECT 
            COUNT(*) as total_allocs,
            COUNT(CASE WHEN mapped_mgr IS NOT NULL THEN 1 END) as with_mgr,
            COUNT(CASE WHEN mapped_hub IS NOT NULL THEN 1 END) as with_hub
        FROM (
            SELECT 
                a.app_allocation_id,
                COALESCE(
                    CASE cva.vehicle_manager_poc
                        WHEN 'BLR_Faizan' THEN 'Syed Faizan'
                        WHEN 'MUM_Deepak' THEN 'Deepak Puran Thapa'
                        WHEN 'HYD_Durganjaneyulu' THEN 'Gogula Durganjaneyulu'
                        WHEN 'BLR_Kiran' THEN 'Kiran M K'
                        ELSE NULL
                    END,
                    CASE 
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Bang%' OR COALESCE(a.assigned_city, cva.city) ILIKE '%Beng%' THEN 'Manjunath Gowda'
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Mum%' THEN 'Vikram Sawant'
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Hyd%' THEN 'K Ramesh'
                        ELSE 'Manjunath Gowda'
                    END
                ) as mapped_mgr,
                COALESCE(
                    NULLIF(cva.hub_name, ''),
                    CASE 
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Bang%' OR COALESCE(a.assigned_city, cva.city) ILIKE '%Beng%' THEN 'Koramangala Parking Hub'
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Mum%' THEN 'Bandra East EV Hub'
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Hyd%' THEN 'Hitech City Hub'
                        ELSE 'Koramangala Parking Hub'
                    END
                ) as mapped_hub
            FROM app_driver_allocations a
            LEFT JOIN core_vehicle_allocation cva ON a.core_allocation_id = cva.id
        ) sub;
    """
    res = conn.execute(text(q)).mappings().first()
    print("app_driver_allocations mapped stats:", dict(res))

    # Distinct managers in app_driver_allocations:
    q_dist_mgr = """
        SELECT 
            COALESCE(
                CASE cva.vehicle_manager_poc
                    WHEN 'BLR_Faizan' THEN 'Syed Faizan'
                    WHEN 'MUM_Deepak' THEN 'Deepak Puran Thapa'
                    WHEN 'HYD_Durganjaneyulu' THEN 'Gogula Durganjaneyulu'
                    WHEN 'BLR_Kiran' THEN 'Kiran M K'
                    ELSE NULL
                END,
                CASE 
                    WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Bang%' OR COALESCE(a.assigned_city, cva.city) ILIKE '%Beng%' THEN 'Manjunath Gowda'
                    WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Mum%' THEN 'Vikram Sawant'
                    WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Hyd%' THEN 'K Ramesh'
                    ELSE 'Manjunath Gowda'
                END
            ) as mapped_mgr,
            count(*)
        FROM app_driver_allocations a
        LEFT JOIN core_vehicle_allocation cva ON a.core_allocation_id = cva.id
        GROUP BY 1
        ORDER BY count(*) DESC;
    """
    res_mgr = conn.execute(text(q_dist_mgr)).fetchall()
    print("Mapped managers in app_driver_allocations:")
    for rm in res_mgr:
        print(" ", rm)

    # Distinct hubs in app_driver_allocations:
    q_dist_hub = """
        SELECT 
            COALESCE(
                NULLIF(cva.hub_name, ''),
                CASE 
                    WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Bang%' OR COALESCE(a.assigned_city, cva.city) ILIKE '%Beng%' THEN 'Koramangala Parking Hub'
                    WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Mum%' THEN 'Bandra East EV Hub'
                    WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Hyd%' THEN 'Hitech City Hub'
                    ELSE 'Koramangala Parking Hub'
                END
            ) as mapped_hub,
            count(*)
        FROM app_driver_allocations a
        LEFT JOIN core_vehicle_allocation cva ON a.core_allocation_id = cva.id
        GROUP BY 1
        ORDER BY count(*) DESC;
    """
    res_hub = conn.execute(text(q_dist_hub)).fetchall()
    print("Mapped hubs in app_driver_allocations:")
    for rh in res_hub:
        print(" ", rh)
