import sys
from bs4 import BeautifulSoup
import json

def inspect_html(file_path):
    print(f"🔍 Inspecting: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    soup = BeautifulSoup(html, "lxml")
    
    # 1. Search for specific ID
    print("\n--- 1. Searching for ID='jobPostingLdjson' ---")
    script_id = soup.find("script", id="jobPostingLdjson")
    if script_id:
        print("✅ Found script with ID 'jobPostingLdjson'")
        print(f"   Content length: {len(script_id.string) if script_id.string else 0} chars")
    else:
        print("❌ ID 'jobPostingLdjson' NOT FOUND")

    # 2. Search for all JSON-LD
    print("\n--- 2. Searching for all application/ld+json scripts ---")
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    print(f"Found {len(scripts)} scripts.")
    
    for i, s in enumerate(scripts):
        print(f"\n[Script #{i+1}]")
        if s.get("id"):
            print(f"   ID: {s.get('id')}")
            
        if not s.string:
            print("   (Empty content)")
            continue
            
        try:
            data = json.loads(s.string)
            type_val = data.get("@type")
            print(f"   @type: {type_val}")
            
            if type_val == "JobPosting":
                print("   🎯 PARTIAL MATCH FOUND (@type=JobPosting)")
        except json.JSONDecodeError:
            print("   ⚠️ Invalid JSON content")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_jsonld.py <html_file>")
        sys.exit(1)
    
    inspect_html(sys.argv[1])
