# scripts/check_db.py
import os
from pathlib import Path
from sqlalchemy import create_engine, text

db_url = os.environ.get("DB_URL", "sqlite:///data/fares.db")
print("DB_URL:", db_url)

if db_url.startswith("sqlite:///"):
    rel = db_url.replace("sqlite:///", "")
    abs_path = (Path.cwd() / rel).resolve()
    print("SQLite file:", abs_path)

eng = create_engine(db_url, future=True)
with eng.connect() as c:
    try:
        total = c.execute(text("select count(*) from daily_prices")).scalar_one()
        print("Rows in daily_prices:", total)
        rows = c.execute(text("""
            select origin,destination,depart_date,price,captured_at
            from daily_prices
            order by captured_at desc
            limit 10
        """)).all()
        for r in rows:
            print(r)
    except Exception as e:
        print("DB query error:", e)