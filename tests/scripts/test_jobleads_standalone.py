import os
import json
import sys
import time
import logging
from dotenv import load_dotenv
from supabase import create_client

# Add the project root to sys.path for imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scrapers.spiders.job_leads import (
    JobleadsClient, 
    JobExtractor, 
    map_listing_response, 
    map_details_response, 
    map_canonical_response,
    iter_classic_search
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def run_standalone(country="USA", limit=5):
    # 1. Load Environment & Credentials
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    load_dotenv(os.path.join(base_dir, 'scrapers/.env'))
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials missing.")
        return

    supabase = create_client(supabase_url, supabase_key)
    
    creds_path = os.path.join(base_dir, "config/jobleads_creds.json")
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f).get(country.upper())
            if not creds:
                logger.error(f"No credentials for {country}")
                return
            email = creds.get('email')
            password = creds.get('password')
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        return

    # 2. Initialize Clients
    client = JobleadsClient(email, password)
    extractor = JobExtractor()
    
    # 3. Start Search
    logger.info(f"Starting standalone scrape for {country} (limit: {limit})")
    payload = {"country": country.upper(), "maxSalary": -1, "startIndex": 0, "limit": limit, "filters": {"daysReleased": "1"}}
    headers = {"accept": "application/json", "content-type": "application/json", "user-agent": "Mozilla/5.0"}
    
    count = 0
    for job_listing in iter_classic_search(client, payload, headers):
        if count >= limit:
            break
            
        job_id = job_listing.get("id")
        if not job_id:
            continue
            
        logger.info(f"--- Processing {job_id}: {job_listing.get('title')} ---")
        
        try:
            # Step A: Listing
            mapped_listing = map_listing_response(job_listing)
            
            # Step B: Details
            mapped_details = {}
            details_resp = client.get_job_details(job_id)
            if details_resp:
                mapped_details = map_details_response(details_resp)
            
            # Step C: Canonical & Source URL
            mapped_canonical = {}
            if details_resp:
                canonical_sub = details_resp.get('payload', {}).get('content', {}).get('canonicalUrl', "")
                if canonical_sub:
                    url = f"https://www.jobleads.com/{canonical_sub.lstrip('/')}"
                    logger.info(f"Fetching canonical: {url}")
                    html = client.fetch_job_page_html(url)
                    job_data = extractor.extract(html, hostname_hint=mapped_details.get("hostname_origin"))
                    mapped_canonical = map_canonical_response(job_data)
            
            # Step D: Merge & Push
            item = {**mapped_listing, **mapped_details, **mapped_canonical}
            
            # Final field fixes (unified company)
            final_company = item.get('company_name') or item.get('company')
            item['company_name'] = final_company
            item['company'] = final_company
            
            if mapped_canonical.get('location_parsed'):
                 item['location_parsed'] = mapped_canonical.get('location_parsed')

            # Verification: Source URL
            source_url = item.get('source_url')
            logger.info(f"Found Source URL: {source_url}")
            
            # Prepare Supabase Payload
            payload = {
                "external_id": item.get("external_id"),
                "source_domain": item.get("source_domain", "jobleads.com"),
                "url": item.get("url"),
                "source_url": source_url,
                "title": item.get("title"),
                "company_name": final_company,
                "location_raw": item.get("location"),
                "city": item.get("location_parsed", {}).get("city"),
                "region": item.get("region") or item.get("location_parsed", {}).get("state"),
                "country_code": item.get("country_code"),
                "employment_type": item.get("employment_type"),
                "remote_modality": item.get("remote_modality"),
                "salary_raw": item.get("salary_raw"),
                "salary_min": item.get("salary_min"),
                "salary_max": item.get("salary_max"),
                "salary_currency": item.get("salary_currency"),
                "salary_period": item.get("salary_period"),
                "description_short": item.get("description_short"),
                "description_html": item.get("description_html"),
                "description_text": item.get("description_text"),
                "benefits": item.get("benefits"),
                "skills": item.get("skills"),
                "qualifications": item.get("qualifications"),
                "responsibilities": item.get("responsibilities"),
                "education": item.get("education"),
                "tools": item.get("tools"),
                "meta_flags": item.get("meta_flags"),
                "scraped_source": item.get("scraped_source") or item.get("source"),
                "hostname_origin": item.get("hostname_origin"),
                "raw_data": {
                     "listing": item.get("_raw_listing", {}),
                     "details": item.get("_raw_details", {}),
                     "canonical": item.get("_raw_canonical", {})
                },
                "posted_at": item.get("posted_at"),
                "expires_at": item.get("expires_at"),
                "last_scraped_at": item.get("scraped_at")
            }
            
            # Add meta_flags if present
            if item.get("meta_flags"):
                payload["meta_flags"] = item.get("meta_flags")

            # Store in Supabase
            try:
                supabase.table("job_listings").upsert(
                    payload, 
                    on_conflict="external_id, source_domain"
                ).execute()
                logger.info(f"Stored in Supabase: {item.get('title')}")
            except Exception as e:
                logger.error(f"Supabase error: {e}")

            count += 1
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            
    logger.info(f"Standalone scrape complete. Processed {count} jobs.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", default="USA")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    
    run_standalone(country=args.country, limit=args.limit)
