import os
import json
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# --- SETUP ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_schema")

# --- MOCK MAPPING FUNCTIONS (Simulate job_leads_v1.py behavior) ---
def map_listing_response(job_data: dict) -> dict:
    meta = {
        "is_featured": job_data.get("isFeatured"),
        "source_type": job_data.get("source"),
    }
    return {
        "external_id": job_data.get("id"),
        "source_domain": "jobleads.com",
        "scraped_source": "job_leads_v1",
        "title": job_data.get("title"),
        "city": job_data.get("location"),
        "location_raw": job_data.get("location"),
        "salary_raw": job_data.get("salary"),
        "employment_type": job_data.get("contractType")[0] if job_data.get("contractType") else None,
        "remote_modality": job_data.get("isRemote"),
        "meta_flags": meta,
        "_raw_listing": job_data
    }

def map_details_response(api_response: dict) -> dict:
    content = api_response.get("payload", {}).get("content", {})
    return {
        "salary_currency": content.get("currency"),
        "salary_min": content.get("salaryMin"),
        "region": content.get("locationRegion"),
        "description_short": content.get("jobSummary"),
        "skills": content.get("skills"),
        "posted_at": content.get("postedAt"),
        "_raw_details": content
    }

def map_canonical_response(normalized_data: dict) -> dict:
    return {
        "company_name": normalized_data.get("company"),
        "description_html": normalized_data.get("description_html"),
        "country_code": normalized_data.get("location", {}).get("country"),
        "_raw_canonical": normalized_data
    }

def test_connection():
    print(f"Connecting to {SUPABASE_URL}...")
    try:
        client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Client created successfully.")
        return client
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return None

def test_schema_insert(client):
    print("\n--- Testing Generic Schema Insert ---")
    
    # Mocks
    mock_listing = {
        "id": "gen_schema_test_001",
        "title": "Senior Python Developer",
        "salary": "USD 100k - 150k",
        "location": "San Francisco",
        "source": "jobboard",
        "isFeatured": True,
        "contractType": ["full_time"],
        "isRemote": "remote"
    }
    mock_details = {
        "payload": {
            "content": {
                "currency": "USD",
                "salaryMin": 100000,
                "locationRegion": "California",
                "jobSummary": "Great python job...",
                "skills": [{"text": "Django"}, {"text": "FastAPI"}],
                "postedAt": "2026-02-14"
            }
        }
    }
    mock_canonical = {
        "company": "Tech Corp",
        "description_html": "<p>Apply now!</p>",
        "location": {"country": "US"}
    }

    # Map
    p1 = map_listing_response(mock_listing)
    p2 = map_details_response(mock_details)
    p3 = map_canonical_response(mock_canonical)

    # Merge
    final_payload = {**p1, **p2, **p3}

    # Raw Data Logic
    raw_combined = {}
    if "_raw_listing" in final_payload: raw_combined["listing"] = final_payload.pop("_raw_listing")
    if "_raw_details" in final_payload: raw_combined["details"] = final_payload.pop("_raw_details")
    if "_raw_canonical" in final_payload: raw_combined["canonical"] = final_payload.pop("_raw_canonical")
    final_payload["raw_data"] = raw_combined

    print(f"Final Payload Keys: {list(final_payload.keys())}")
    print(f"External ID: {final_payload['external_id']}")

    # Insert
    try:
        # Constraint: external_id, source_domain
        client.table("job_listings").upsert(final_payload, on_conflict="external_id, source_domain").execute()
        print(f"✅ Saved job to 'job_listings': {final_payload['external_id']}")
    except Exception as e:
        print(f"❌ Failed to save job: {e}")
        print("Ensure you have run the 'create_job_listings.sql' script in Supabase!")

if __name__ == "__main__":
    client = test_connection()
    if client:
        test_schema_insert(client)
