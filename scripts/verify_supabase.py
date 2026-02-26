import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load .env from scrapers directory
load_dotenv('scrapers/.env')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in environment.")
    sys.exit(1)

try:
    supabase = create_client(url, key)
    
    # Check total count
    response = supabase.table('job_listings').select('id', count='exact').limit(1).execute()
    print(f"Total jobs in Supabase: {response.count}")
    
    # Check non-null companies
    non_null = supabase.table('job_listings').select('id', count='exact').not_.is_('company_name', 'null').execute()
    print(f"Jobs with company_name: {non_null.count}")
    
    # Check most recent non-null
    recent = supabase.table('job_listings').select('title, company_name, created_at').not_.is_('company_name', 'null').order('created_at', desc=True).limit(5).execute()
    if recent.data:
        print("\nMost recent jobs with company names:")
        for job in recent.data:
            print(f"- {job['title']} at {job['company_name']} (Created: {job['created_at']})")
    else:
        print("\nNo jobs found in 'job_listings' table.")
        
except Exception as e:
    print(f"Error connecting to Supabase or querying table: {e}")
