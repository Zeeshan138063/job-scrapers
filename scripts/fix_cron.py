import os
import sys
from sqlmodel import Session, create_engine, select

# Add project root to path
sys.path.append('/home/zeeshan/projects/job-scrapers')

from api.models import SpiderConfig

# Database Connection
DATABASE_URL = "postgresql://scraper_user:scraper_pass@localhost:5432/scraper_staging"
engine = create_engine(DATABASE_URL)

def fix_cron_schedules():
    try:
        with Session(engine) as session:
            # Find the specific invalid config
            statement = select(SpiderConfig).where(SpiderConfig.spider_id == "job_leads_v2")
            config = session.exec(statement).first()
            
            if config:
                print(f"Current config for {config.spider_id}: {config.cron_schedule}")
                if config.cron_schedule == "* * * *":
                    print("Found invalid cron '* * * *'. Updating to '*/5 * * * *'...")
                    config.cron_schedule = "*/5 * * * *"
                    session.add(config)
                    session.commit()
                    session.refresh(config)
                    print(f"Updated config for {config.spider_id}: {config.cron_schedule}")
                else:
                    print("Config does not match invalid pattern or already fixed.")
            else:
                print("Spider job_leads_v2 not found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_cron_schedules()
