import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def fix_db():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ Error: DATABASE_URL not found.")
        return
        
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Check if source exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='job_listings' AND column_name='source'"))
            if not result.fetchone():
                print("Adding missing 'source' column...")
                conn.execute(text("ALTER TABLE job_listings ADD COLUMN source TEXT NOT NULL DEFAULT 'unknown'"))
                conn.commit()
                print("✅ Column 'source' added successfully.")
            else:
                print("✅ Column 'source' already exists.")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_db()
