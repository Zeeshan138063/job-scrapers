import json
from bs4 import BeautifulSoup
import logging

# Mock the client methods here to test logic in isolation
# (Copying relevant logic from job_leads_v1.py for standalone testing)

def extract_jobposting_jsonld(html_text: str) -> dict:
    soup = BeautifulSoup(html_text, "lxml")
    script = soup.find("script", {"type": "application/ld+json", "id": "jobPostingLdjson"})
    if not script or not script.string:
        raise ValueError("JobPosting JSON-LD not found")
    return json.loads(script.string.strip())

def normalize_jobposting(data: dict) -> dict:
    desc_html = data.get("description")
    return {
        "job_id": (data.get("identifier") or {}).get("value"),
        "title": data.get("title"),
        "company": (data.get("hiringOrganization") or {}).get("name"),
        "employment_type": data.get("employmentType"),
        "date_posted": data.get("datePosted"),
        "valid_through": data.get("validThrough"),
        "location": {
            "city": (((data.get("jobLocation") or {}).get("address") or {}).get("addressLocality")),
            "region": (((data.get("jobLocation") or {}).get("address") or {}).get("addressRegion")),
            "country": (((data.get("jobLocation") or {}).get("address") or {}).get("addressCountry")),
        },
        "salary": {
            "currency": data.get("salaryCurrency"),
            "min": (((data.get("baseSalary") or {}).get("value") or {}).get("minValue")),
            "max": (((data.get("baseSalary") or {}).get("value") or {}).get("maxValue")),
            "unit": (((data.get("baseSalary") or {}).get("value") or {}).get("unitText")),
        },
        "description_html": desc_html,
    }

def map_canonical_to_schema(normalized_data: dict) -> dict:
    salary = normalized_data.get("salary") or {}
    location = normalized_data.get("location") or {}
    return {
        "company_name": normalized_data.get("company"),
        "description_html": normalized_data.get("description_html"),
        "salary_period": salary.get("unit"),
        "country_code": location.get("country"),
        "_raw_canonical": normalized_data
    }

# Mock HTML based on typical JobLeads structure
MOCK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Job</title>
    <script type="application/ld+json" id="jobPostingLdjson">
    {
        "@context": "http://schema.org",
        "@type": "JobPosting",
        "title": "Shopify SEO Specialist",
        "description": "<p>We are looking for an SEO expert...</p>",
        "identifier": {
            "@type": "PropertyValue",
            "name": "JobLeads",
            "value": "123456"
        },
        "datePosted": "2026-02-14",
        "validThrough": "2026-03-14",
        "employmentType": "FULL_TIME",
        "hiringOrganization": {
            "@type": "Organization",
            "name": "E-Com Agency"
        },
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Buenos Aires",
                "addressRegion": "BA",
                "addressCountry": "AR"
            }
        },
        "baseSalary": {
            "@type": "MonetaryAmount",
            "currency": "USD",
            "value": {
                "@type": "QuantitativeValue",
                "minValue": 50000,
                "maxValue": 80000,
                "unitText": "YEAR"
            }
        }
    }
    </script>
</head>
<body></body>
</html>
"""

def test_html_extraction():
    print("--- Testing HTML Parsing & Schema Mapping ---")
    try:
        # 1. Extract
        print("1. Extracting JSON-LD...")
        json_data = extract_jobposting_jsonld(MOCK_HTML)
        print("   ✅ Extracted.")

        # 2. Normalize
        print("2. Normalizing Data...")
        normalized = normalize_jobposting(json_data)
        print("   ✅ Normalized.")

        # 3. Map to Schema
        print("3. Mapping to DB Schema...")
        mapped = map_canonical_to_schema(normalized)
        
        # Verify Keys
        expected_keys = ["company_name", "description_html", "salary_period", "country_code", "_raw_canonical"]
        missing = [k for k in expected_keys if k not in mapped]
        
        if missing:
            print(f"❌ Missing keys in mapped data: {missing}")
        else:
            print(f"✅ Schema Mapping Success!")
            print(f"   Company: {mapped['company_name']}")
            print(f"   Country: {mapped['country_code']}")
            print(f"   Salary Unit: {mapped['salary_period']}")
            print(f"   Description Length: {len(mapped['description_html'])}")

    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_html_extraction()
