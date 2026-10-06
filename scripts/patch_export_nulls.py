with open("scripts/export_clean_credentials.py", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace("COALESCE(o.assigned_manager_name, 'LetzRyd Operations Desk')", "COALESCE(o.assigned_manager_name, 'Not Allocated')")
code = code.replace("COALESCE(o.assigned_manager_phone, '9988770011')", "COALESCE(o.assigned_manager_phone, 'Not Available')")
code = code.replace("COALESCE(d.assigned_manager_name, 'LetzRyd Operations Desk')", "COALESCE(d.assigned_manager_name, 'Not Allocated')")
code = code.replace("COALESCE(d.assigned_manager_phone, '9988770011')", "COALESCE(d.assigned_manager_phone, 'Not Available')")

with open("scripts/export_clean_credentials.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated fallback text in export script.")
