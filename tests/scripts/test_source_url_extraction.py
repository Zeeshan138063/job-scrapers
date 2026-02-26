import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scrapers.spiders.job_leads import JobExtractor

def test_source_url_extraction():
    # Path relative to project root or absolute path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    html_path = os.path.join(base_dir, "tests/data/job_detail.html")
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found.")
        return

    with open(html_path, "r") as f:
        html = f.read()

    extractor = JobExtractor()
    try:
        data = extractor.extract(html)
        print("Successfully extracted data:")
        print(f"Title: {data.get('title')}")
        print(f"Company: {data.get('company_name')}")
        
        source_url = data.get("source_url")
        expected_url = "https://pk.linkedin.com/jobs/view/lms-administrator-moodle-microsoft-teams-at-metapi-4363283090"
        
        if source_url == expected_url:
            print(f"✅ Success: source_url correctly extracted: {source_url}")
        else:
            print(f"❌ Failure: source_url mismatch.")
            print(f"   Expected: {expected_url}")
            print(f"   Got:      {source_url}")

        # Check for new rich fields
        if data.get("description_html") and "<div" in data.get("description_html"):
            print("✅ Success: description_html found.")
        else:
            print("❌ Failure: description_html missing or invalid.")

        # Test mapping in a mock way if needed, or just check extractor output
        print(f"Salary Min (Extracted): {data.get('salary', {}).get('min')}")
        print(f"Salary Max (Extracted): {data.get('salary', {}).get('max')}")
        
        # Test map_canonical_response
        from scrapers.spiders.job_leads import map_canonical_response
        mapped = map_canonical_response(data)
        if mapped.get("salary_min") == 2000000:
            print("✅ Success: map_canonical_response correctly mapped salary_min.")
        else:
            print(f"❌ Failure: map_canonical_response salary_min mismatch. Got: {mapped.get('salary_min')}")
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")

if __name__ == "__main__":
    test_source_url_extraction()
