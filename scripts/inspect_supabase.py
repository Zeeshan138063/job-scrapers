import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('scrapers/.env')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

if not url or not key:
    print("Supabase credentials missing.")
    exit(1)

supabase = create_client(url, key)

try:
    # Query one row to see columns
    res = supabase.table('job_listings').select('*').limit(1).execute()
    if res.data:
        print("Columns found in job_listings:")
        for key in res.data[0].keys():
            print(f"- {key}")
    else:
        print("No data found in job_listings to inspect columns.")
except Exception as e:
    print(f"Error: {e}")
