import os
import csv
import io
import json
import redis
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query, Security, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from sqlmodel import Session, SQLModel, select, create_engine, or_
from .models import JobListing, SpiderConfig, SpiderRun, ScrapeRequest

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://scraper_user:scraper_pass@db:5432/scraper_staging")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-super-secret-key-123")

import re

# Setup
engine = create_engine(DATABASE_URL)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def discover_spiders():
    """Scans the spiders directory for Scrapy spider names."""
    spiders = []
    spider_dir = "/app/scrapers/spiders"  # Path inside Docker
    if not os.path.exists(spider_dir):
        # Fallback for local dev
        spider_dir = os.path.join(os.path.dirname(__file__), "..", "scrapers", "spiders")
    
    if os.path.exists(spider_dir):
        for filename in os.listdir(spider_dir):
            if filename.endswith(".py") and filename not in ["__init__.py", "base_spider.py"]:
                with open(os.path.join(spider_dir, filename), "r") as f:
                    content = f.read()
                    # Look for 'name = "..." ' or 'name = "..." '
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        spiders.append(match.group(1))
    return sorted(list(set(spiders)))

def get_session():
    with Session(engine) as session:
        yield session

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_SECRET_KEY:
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate API Key")

app = FastAPI(
    title="Job Scraper Staging API",
    dependencies=[Depends(get_api_key)]
)

# CORS Configuration
origins = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/", include_in_schema=False)
def read_root():
    return {"status": "ok", "message": "Scraper Staging API is running securely"}

# --- JOB ENDPOINTS ---

@app.get("/jobs", response_model=List[JobListing])
def list_jobs(
    offset: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    query: Optional[str] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    session: Session = Depends(get_session)
):
    statement = select(JobListing)
    if source:
        statement = statement.where(JobListing.source == source)
    if query:
        statement = statement.where(JobListing.title.ilike(f"%{query}%"))
    if location:
        statement = statement.where(JobListing.location.ilike(f"%{location}%"))
    if company:
        statement = statement.where(JobListing.company.ilike(f"%{company}%"))
    
    jobs = session.exec(statement.order_by(JobListing.scraped_at.desc()).offset(offset).limit(limit)).all()
    return jobs

@app.get("/jobs/export/json")
def export_json(
    source: Optional[str] = None,
    session: Session = Depends(get_session)
):
    statement = select(JobListing)
    if source:
        statement = statement.where(JobListing.source == source)
    
    jobs = session.exec(statement).all()
    return jobs

@app.get("/jobs/export/csv")
def export_csv(
    source: Optional[str] = None,
    session: Session = Depends(get_session)
):
    statement = select(JobListing)
    if source:
        statement = statement.where(JobListing.source == source)
    
    jobs = session.exec(statement).all()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "source", "title", "company", "location", "url", "posted_at", "salary_raw"
    ])
    writer.writeheader()
    
    for job in jobs:
        writer.writerow({
            "id": job.id,
            "source": job.source,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "posted_at": job.posted_at,
            "salary_raw": job.salary_raw
        })
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=jobs_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

# --- SCRAPER CONTROL ---

@app.post("/scraper/run")
def trigger_scrape(req: ScrapeRequest):
    """
    Manually push a scraping job to the Redis queue.
    """
    job_data = {
        "spider": req.spider_id,
        "search_queries": req.search_queries,
        "locations": req.locations,
        "max_pages": req.max_pages,
        "concurrent_requests": req.concurrent_requests,
        "filters": req.filters,
        "created_at": datetime.now().isoformat(),
        "manual": True
    }
    
    redis_client.rpush("scraping_queue", json.dumps(job_data))
    return {"status": "enqueued", "spider": req.spider_id, "queries": req.search_queries}

@app.get("/scraper/runs", response_model=List[SpiderRun])
def list_runs(
    limit: int = 50,
    session: Session = Depends(get_session)
):
    statement = select(SpiderRun).order_by(SpiderRun.created_at.desc()).limit(limit)
    return session.exec(statement).all()

@app.get("/spiders", response_model=List[str])
def list_spiders():
    return discover_spiders()

# --- CONFIG ENDPOINTS ---

@app.get("/configs", response_model=List[SpiderConfig])
def list_configs(session: Session = Depends(get_session)):
    return session.exec(select(SpiderConfig)).all()

@app.post("/configs", response_model=SpiderConfig)
def create_config(config: SpiderConfig, session: Session = Depends(get_session)):
    db_config = session.merge(config)
    session.commit()
    session.refresh(db_config)
    return db_config

@app.patch("/configs/{spider_id}", response_model=SpiderConfig)
def update_config(spider_id: str, updates: Dict, session: Session = Depends(get_session)):
    db_config = session.get(SpiderConfig, spider_id)
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    for key, value in updates.items():
        if hasattr(db_config, key):
            setattr(db_config, key, value)
    
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config
