import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "db/nifty100.db"

conn = sqlite3.connect(DB_PATH)

companies = pd.read_sql(
    "SELECT id, company_name FROM companies",
    conn
)

rows = []

for _, row in companies.iterrows():
    company_id = int(row["id"])
    company_name = row["company_name"]

    basic_file = Path("data/raw") / company_name / "Basic_Info.csv"

    if not basic_file.exists():
        continue

    try:
        df = pd.read_csv(basic_file)

        if df.empty:
            continue

        sector = str(df.iloc[0]["Sector"]).strip()

        rows.append({
            "company_id": company_id,
            "sector": sector,
            "industry": sector
        })

    except Exception as e:
        print(f"Error: {company_name} -> {e}")

sector_df = pd.DataFrame(rows)

print(f"Loaded {len(sector_df)} sector mappings")

sector_df.to_sql(
    "sector_mapping",
    conn,
    if_exists="replace",
    index=False
)

conn.commit()
conn.close()

print("sector_mapping table created successfully")