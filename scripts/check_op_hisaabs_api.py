from app.database import SessionLocal
from sqlalchemy import text
from app.api.hisaabs import get_operator_hisaabs

db = SessionLocal()
res = get_operator_hisaabs(475, db)
print("Gaadylo (475) operator hisaabs count:", res['count'])
for d in res['data'][:5]:
    print(" ", d['week_number'], d['hisaab_number'], "gross:", d['total_gross_earnings'], "to_pay:", d['to_pay'], "to_collect:", d['to_collect'])

db.close()
