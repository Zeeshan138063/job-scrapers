import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

# Try to load .env from current directory or parent
load_dotenv()

def check_db():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ Error: DATABASE_URL not found in environment.")
        return False
        
    print(f"🔍 Testing connection to: {db_url.split('@')[-1]}") # Don't print password
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("✅ Successfully connected to PostgreSQL.")
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"📊 Tables found: {tables}")
            
            if 'job_listings' in tables:
                print("✅ Table 'job_listings' exists.")
                columns = [c['name'] for c in inspector.get_columns('job_listings')]
                print(f"📝 Columns in 'job_listings': {columns}")
                
                # Check for composite index or constraint
                # In SQLModel/SQLAlchemy we can't easily check the composite uniqueness without more code,
                # but we can see the indexes.
                indexes = inspector.get_indexes('job_listings')
                print(f"⚡ Indexes: {[idx['name'] for idx in indexes]}")
            else:
                print("❌ Table 'job_listings' NOT found!")
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    check_db()
