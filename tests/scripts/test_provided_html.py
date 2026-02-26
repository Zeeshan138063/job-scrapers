import json
from bs4 import BeautifulSoup
import logging

# --- Mocking the Extraction Logic from job_leads_v1.py ---
# (We replicate it here to test isolating the HTML content issue)

def extract_jobposting_jsonld(html_text: str) -> dict:
    soup = BeautifulSoup(html_text, "lxml")
    # 1. Try standard ID
    script = soup.find("script", {"type": "application/ld+json", "id": "jobPostingLdjson"})
    
    # 2. Fallback: Search all ld+json for @type="JobPosting"
    if not script or not script.string:
        print("   ⚠️  Direct ID 'jobPostingLdjson' not found. Searching all LD+JSON scripts...")
        scripts = soup.find_all("script", {"type": "application/ld+json"})
        for s in scripts:
            if s.string:
                try:
                    data = json.loads(s.string.strip())
                    if data.get("@type") == "JobPosting":
                        return data
                except:
                    continue
        raise ValueError("JobPosting JSON-LD not found in HTML")
        
    return json.loads(script.string.strip())

def normalize_jobposting(data: dict) -> dict:
    desc_html = data.get("description")
    return {
        "job_id": (data.get("identifier") or {}).get("value"),
        "title": data.get("title"),
        "company": (data.get("hiringOrganization") or {}).get("name"),
        "location": {
            "country": (((data.get("jobLocation") or {}).get("address") or {}).get("addressCountry")),
        },
    }

# --- User Provided HTML Snippet (Pasted) ---
# Note: This is potentially truncated as per the user message.
PROVIDED_HTML = """
<!DOCTYPE html><html  translate="no" lang="es-AR" data-theme="aurora"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>Shopify SEO Specialist (Agency) | Argentina | JobLeads.com</title>
""" 
# ... (Simulating the rest of the file being missing or just style tags) ...

def test_provided_html():
    print("--- Testing Provided HTML Snippet ---")
    try:
        data = extract_jobposting_jsonld(PROVIDED_HTML)
        print("✅ JSON-LD Parsed Successfully!")
        print(json.dumps(data, indent=2))
        
        normalized = normalize_jobposting(data)
        print("✅ Normalized Data:")
        print(normalized)
        
    except ValueError as e:
        print(f"❌ Extraction Failed: {e}")
        print("   Reason: The provided HTML snippet likely doesn't contain the <script> tag with JSON-LD.")
        print("   It appears truncated in the chat (ended with 'truncated bytes').")
        print("   If you have the full HTML file, please save it to 'full_page.html' and run the test against that.")

if __name__ == "__main__":
    test_provided_html()
