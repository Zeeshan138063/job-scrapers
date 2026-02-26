import os
import sys
from sqlmodel import Session, create_engine, select, SQLModel

# Add project root to path
sys.path.append('/home/zeeshan/projects/job-scrapers')

from api.models import SpiderConfig

# Database Connection
DATABASE_URL = "postgresql://scraper_user:scraper_pass@localhost:5432/scraper_staging"
engine = create_engine(DATABASE_URL)

def check_cron_schedules():
    try:
        with Session(engine) as session:
            statement = select(SpiderConfig)
            results = session.exec(statement).all()
            
            print(f"Found {len(results)} configs.")
            for config in results:
                print(f"Spider: {config.spider_id}, Active: {config.is_active}, Cron: '{config.cron_schedule}'")
                
                # Simple validation check
                if config.cron_schedule:
                    parts = config.cron_schedule.split()
                    if len(parts) not in [5, 6]:
                        print(f"--> INVALID CRON: '{config.cron_schedule}' has {len(parts)} parts")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_cron_schedules()
