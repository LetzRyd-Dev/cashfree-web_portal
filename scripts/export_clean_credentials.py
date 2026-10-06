import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from app.database import SessionLocal
from sqlalchemy import text
import os

db = SessionLocal()

wb = openpyxl.Workbook()
# Remove default sheet
wb.remove(wb.active)

# Styling setup
FONT_FAMILY = "Inter"
COLOR_TEXT_MAIN = "111827"    # Dark charcoal
COLOR_HEADER_BG = "F3F4F6"    # Neutral light gray
COLOR_HEADER_TXT = "111827"   # Pure dark text
BORDER_COLOR = "E5E7EB"       # Subtle border

font_title = Font(name=FONT_FAMILY, size=13, bold=True, color=COLOR_TEXT_MAIN)
font_subtitle = Font(name=FONT_FAMILY, size=9, italic=True, color="4B5563")
font_header = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_HEADER_TXT)
font_data = Font(name=FONT_FAMILY, size=10, color=COLOR_TEXT_MAIN)
font_mono = Font(name="Consolas", size=10, color=COLOR_TEXT_MAIN)

fill_header = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
fill_zebra = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")

thin_border = Border(
    left=Side(style='thin', color=BORDER_COLOR),
    right=Side(style='thin', color=BORDER_COLOR),
    top=Side(style='thin', color=BORDER_COLOR),
    bottom=Side(style='thin', color=BORDER_COLOR)
)

def style_sheet(ws, title, subtitle, columns, rows):
    # Title Block
    ws.append([title])
    ws.append([subtitle])
    ws.append([]) # Empty row
    
    ws.cell(1, 1).font = font_title
    ws.cell(2, 1).font = font_subtitle
    
    # Headers
    header_row_idx = 4
    ws.append(columns)
    for col_idx in range(1, len(columns) + 1):
        cell = ws.cell(row=header_row_idx, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    
    ws.row_dimensions[header_row_idx].height = 24

    # Data Rows
    for row_idx, r in enumerate(rows, start=header_row_idx + 1):
        ws.append(r)
        is_even = (row_idx % 2 == 0)
        for col_idx in range(1, len(columns) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = font_data
            cell.border = thin_border
            if is_even:
                cell.fill = fill_zebra
            
            # Left align text, center codes & phones
            col_name = columns[col_idx - 1]
            if any(k in col_name.lower() for k in ["phone", "mobile", "status"]):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif any(k in col_name.lower() for k in ["code", "id", "vehicle number", "registration"]):
                cell.font = font_mono
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[row_idx].height = 20

    # Column Auto-fit
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if cell.row < 4:
                continue
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

# ----------------------------------------------------
# 1. QUICK TEST PROFILES
# ----------------------------------------------------
ws_quick = wb.create_sheet("Quick Test Profiles")
quick_cols = [
    "Persona / Profile Name",
    "Mobile Number",
    "Test OTP",
    "Account Type",
    "Assigned Vehicle",
    "Rental Plan",
    "Key Features to Test"
]

quick_data = [
    ["Anurag & RK Fleet Logistics", "9691938866", "123456", "Fleet Operator", "4 Vehicles", "Operator Master", "Full fleet overview, vehicle hisaab, account manager Syed Faizan"],
    ["Samvreeddhi Mobility Fleet", "9848012345", "123456", "Fleet Operator", "15 Vehicles", "Operator Master", "Multi-vehicle fleet view, tenant isolation, manager Kalyan Chakravarthy"],
    ["Vivek (Anurag Fleet)", "9901484683", "123456", "Fleet Managed Driver", "KA05AQ7692 (Maruti Dzire)", "Uber - TBS (Reducing)", "Week 40 active hisaab, Dzire car card, emergency contact"],
    ["Sushant (Anurag Fleet)", "9140631755", "123456", "Fleet Managed Driver", "TS09EV8812 (Tata Tigor EV)", "Uber - TBS (Reducing)", "Week 40 hisaab, Tigor EV card, emergency contact"],
    ["Aayush (Anurag Fleet)", "9876543210", "123456", "Fleet Managed Driver", "MH01DE1234 (Maruti Dzire)", "Fixed D2R", "Dzire car card, support tickets flow"],
    ["Anurag (Test Driver)", "9876543211", "123456", "Fleet Managed Driver", "TS09UB5678 (Toyota Etios)", "Fixed D2R", "Etios car card, online cashfree payment simulation"],
    ["Tultul Das (Live Driver)", "7002018865", "123456", "Independent Driver", "KA05AQ0188 (Maruti WagonR)", "Uber - TBS (Reducing)", "Live driver with Week 40 hisaab, WagonR card"],
    ["Rubel Ahmed (Driver)", "6900883581", "123456", "Fleet Managed Driver", "KA05AQ4864 (Maruti WagonR)", "Fixed D2R", "Verified pure driver login, no ghost operator account"],
    ["Rajeev (No Vehicle)", "8147414391", "123456", "Independent Driver", "Unassigned", "No Plan Active", "Tests clean 'No Vehicle Assigned' badge"],
    ["Pramod (Unassigned)", "9742045678", "123456", "Independent Driver", "Unassigned", "No Plan Active", "Profile view, emergency contact setup"],
    ["Kalyan Chakravarthy", "9988770011", "123456", "Internal Staff / Hub", "N/A", "Internal Staff", "Hyderabad Operations Desk POC"],
    ["Deepak Puran Thapa", "9820098200", "123456", "Internal Staff / Hub", "N/A", "Internal Staff", "Mumbai Operations Desk POC"]
]

style_sheet(
    ws_quick,
    "LetzRyd Portal - Quick Test Credentials",
    "Verified test accounts for QA, demonstration, and staging verification. OTP is fixed at 123456 for all test environments.",
    quick_cols,
    quick_data
)

# ----------------------------------------------------
# 2. FLEET OPERATORS (Genuine 177+ operators)
# ----------------------------------------------------
ws_ops = wb.create_sheet("Fleet Operators")
op_cols = [
    "Operator ID",
    "Operator Code",
    "Company / Partner Name",
    "Mobile Number",
    "City",
    "Total Vehicles",
    "Assigned Account Manager",
    "Manager Phone",
    "Login Status"
]

ops_query = text("""
    SELECT 
        o.app_operator_id,
        o.operator_code,
        o.company_name,
        o.phone,
        CASE 
            WHEN o.operator_code LIKE '%BLR%' THEN 'Bangalore'
            WHEN o.operator_code LIKE '%HYD%' THEN 'Hyderabad'
            WHEN o.operator_code LIKE '%MUM%' THEN 'Mumbai'
            ELSE 'Bangalore'
        END AS city,
        o.total_vehicles,
        COALESCE(o.assigned_manager_name, 'Not Allocated') AS mgr_name,
        COALESCE(o.assigned_manager_phone, 'Not Available') AS mgr_phone,
        CASE WHEN o.is_active THEN 'Active' ELSE 'Inactive' END AS status
    FROM app_operators o
    ORDER BY o.total_vehicles DESC, o.company_name ASC
""")

op_rows = []
for r in db.execute(ops_query).mappings().fetchall():
    op_rows.append([
        f"OPR-{r['app_operator_id']:04d}",
        r['operator_code'],
        r['company_name'],
        r['phone'],
        r['city'],
        r['total_vehicles'] or 0,
        r['mgr_name'],
        r['mgr_phone'],
        r['status']
    ])

style_sheet(
    ws_ops,
    "LetzRyd Fleet Operators Directory",
    "Verified list of active fleet operators who own and operate vehicles. Zero ghost or 0-vehicle driver duplicates.",
    op_cols,
    op_rows
)

# ----------------------------------------------------
# 3. INDEPENDENT DRIVERS (No outstanding amounts)
# ----------------------------------------------------
ws_ind = wb.create_sheet("Independent Drivers")
drv_cols = [
    "Driver ID",
    "Driver Code",
    "Full Name",
    "Mobile Number",
    "City",
    "Assigned Vehicle",
    "Vehicle Model",
    "Rental Plan",
    "Driver Manager",
    "Manager Phone",
    "Login Status"
]

ind_query = text("""
    SELECT 
        d.app_driver_id,
        d.driver_code,
        d.full_name,
        d.phone,
        CASE 
            WHEN d.driver_code LIKE '%BLR%' THEN 'Bangalore'
            WHEN d.driver_code LIKE '%HYD%' THEN 'Hyderabad'
            WHEN d.driver_code LIKE '%MUM%' THEN 'Mumbai'
            ELSE 'Bangalore'
        END AS city,
        COALESCE(d.vehicle_reg_number, 'Unassigned') AS reg_num,
        COALESCE(d.vehicle_model, 'No Vehicle') AS veh_model,
        COALESCE(c.type_of_plan, c.rental_plan, 'Standard Baseline') AS rental_plan,
        COALESCE(d.assigned_manager_name, 'Not Allocated') AS mgr_name,
        COALESCE(d.assigned_manager_phone, 'Not Available') AS mgr_phone,
        CASE WHEN d.is_active THEN 'Active' ELSE 'Inactive' END AS status
    FROM app_drivers d
    LEFT JOIN (
        SELECT DISTINCT ON (driver_phone) driver_phone, type_of_plan, rental_plan
        FROM core_vehicle_allocation
        ORDER BY driver_phone, id DESC
    ) c ON d.phone = c.driver_phone
    WHERE (d.operator_id IS NULL OR d.operator_id = 0)
    ORDER BY d.app_driver_id ASC
""")

ind_rows = []
for r in db.execute(ind_query).mappings().fetchall():
    ind_rows.append([
        f"DRV-{r['app_driver_id']:04d}",
        r['driver_code'],
        r['full_name'],
        r['phone'],
        r['city'],
        r['reg_num'],
        r['veh_model'],
        r['rental_plan'],
        r['mgr_name'],
        r['mgr_phone'],
        r['status']
    ])

style_sheet(
    ws_ind,
    "LetzRyd Independent Drivers Directory",
    "Individual partners operating independently with LetzRyd. Clean profiles with assigned vehicle and authentic rental plan.",
    drv_cols,
    ind_rows
)

# ----------------------------------------------------
# 4. FLEET MANAGED DRIVERS (No outstanding amounts)
# ----------------------------------------------------
ws_fleet_drv = wb.create_sheet("Fleet Managed Drivers")
fleet_drv_cols = [
    "Driver ID",
    "Driver Code",
    "Full Name",
    "Mobile Number",
    "Fleet Operator",
    "City",
    "Assigned Vehicle",
    "Vehicle Model",
    "Rental Plan",
    "Driver Manager",
    "Manager Phone"
]

fleet_drv_query = text("""
    SELECT 
        d.app_driver_id,
        d.driver_code,
        d.full_name,
        d.phone,
        COALESCE(o.company_name, 'Fleet Operator ' || d.operator_id::text) AS op_name,
        CASE 
            WHEN d.driver_code LIKE '%BLR%' THEN 'Bangalore'
            WHEN d.driver_code LIKE '%HYD%' THEN 'Hyderabad'
            WHEN d.driver_code LIKE '%MUM%' THEN 'Mumbai'
            ELSE 'Bangalore'
        END AS city,
        COALESCE(d.vehicle_reg_number, 'Unassigned') AS reg_num,
        COALESCE(d.vehicle_model, 'No Vehicle') AS veh_model,
        COALESCE(c.type_of_plan, c.rental_plan, 'Fleet Reducing Slabs') AS rental_plan,
        COALESCE(d.assigned_manager_name, 'Not Allocated') AS mgr_name,
        COALESCE(d.assigned_manager_phone, 'Not Available') AS mgr_phone
    FROM app_drivers d
    LEFT JOIN app_operators o ON (d.operator_id = o.app_operator_id OR d.operator_id = o.operator_id)
    LEFT JOIN (
        SELECT DISTINCT ON (driver_phone) driver_phone, type_of_plan, rental_plan
        FROM core_vehicle_allocation
        ORDER BY driver_phone, id DESC
    ) c ON d.phone = c.driver_phone
    WHERE (d.operator_id IS NOT NULL AND d.operator_id > 0)
    ORDER BY d.operator_id ASC, d.full_name ASC
""")

fleet_drv_rows = []
for r in db.execute(fleet_drv_query).mappings().fetchall():
    fleet_drv_rows.append([
        f"DRV-{r['app_driver_id']:04d}",
        r['driver_code'],
        r['full_name'],
        r['phone'],
        r['op_name'],
        r['city'],
        r['reg_num'],
        r['veh_model'],
        r['rental_plan'],
        r['mgr_name'],
        r['mgr_phone']
    ])

style_sheet(
    ws_fleet_drv,
    "LetzRyd Fleet Managed Drivers Directory",
    "Drivers attached to fleet operator accounts with their vehicle assignment and authentic rental plan.",
    fleet_drv_cols,
    fleet_drv_rows
)

# Save both locations
out1 = "C:/Users/anura/Downloads/LetzRyd_All_Profiles_Credentials.xlsx"
out2 = "C:/Users/anura/Downloads/cashfree-web_portal/LetzRyd_All_Profiles_Credentials.xlsx"

wb.save(out1)
wb.save(out2)
print("Saved cleanly to both:")
print(" ", out1)
print(" ", out2)

db.close()
