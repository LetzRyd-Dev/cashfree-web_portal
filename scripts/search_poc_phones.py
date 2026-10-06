from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== SEARCHING EMPLOYEES ===")
    names = ['Faizan', 'Deepak', 'Durga', 'Kiran', 'Manjunath', 'Vikram', 'Ramesh']
    for n in names:
        res = conn.execute(text(f"SELECT * FROM july_employees WHERE first_name ILIKE '%{n}%' OR last_name ILIKE '%{n}%'")).mappings().fetchall()
        print(f"Match for {n}:")
        for r in res:
            print(" ", dict(r))
