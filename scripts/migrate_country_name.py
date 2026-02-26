import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://scraper_user:scraper_pass@localhost:5432/scraper_staging')

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Migrating: Adding country_name column...")
        try:
            conn.execute(text("ALTER TABLE scraper_job_listings ADD COLUMN IF NOT EXISTS country_name TEXT;"))
            conn.commit()
            print("Successfully checked/added country_name column.")
        except Exception as e:
            if "already exists" in str(e):
                print("Column country_name already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
