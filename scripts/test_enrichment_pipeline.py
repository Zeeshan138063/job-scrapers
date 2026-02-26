import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.pipelines.enrichment_pipeline import EnrichmentPipeline
from scrapers.items import JobItem

def test_parsing():
    pipeline = EnrichmentPipeline()
    
    # Sample data from user
    raw_data = {
        "canonical": {
            "company_name": "Stripe",
            "location": {"city": "United States", "country": "US", "region": ""},
            "raw_json_ld": {
                "jobLocation": {
                    "address": {
                        "addressCountry": "US",
                        "addressLocality": "United States",
                        "addressRegion": ""
                    }
                },
                "baseSalary": {
                    "currency": "USD",
                    "value": {"maxValue": 177000, "minValue": 117000}
                }
            },
            "employment_type": "FULL_TIME"
        },
        "details": {
            "salaryMin": 117000,
            "salaryMax": 177000,
            "currency": "USD",
            "isRemote": "hybrid",
            "contractType": ["full_time"],
            "education": [
                {"text": "Abgeschlossene Ausbildung im Bereich der Elektrotechnik oder Versorgungswirtschaft", "selected": False}
            ],
            "skills": [
                {"text": "Python", "selected": True},
                {"text": "Scrapy", "selected": False}
            ]
        }
    }
    
    item = JobItem(
        title="Program Manager",
        location="United States",
        salary="USD 117,000 - 177,000",
        raw_data=raw_data
    )
    
    enriched = pipeline.process_item(item, None)
    
    print("\n--- Parsed Results ---")
    print(f"Location Parsed: {json.dumps(enriched.get('location_parsed'), indent=2)}")
    print(f"Salary Min: {enriched.get('salary_min')}")
    print(f"Salary Max: {enriched.get('salary_max')}")
    print(f"Currency: {enriched.get('salary_currency')}")
    print(f"Employment Type: {enriched.get('employment_type')}")
    print(f"Remote Modality: {enriched.get('remote_modality')}")
    print(f"Company: {enriched.get('company_name')}")
    print(f"Education: {json.dumps(enriched.get('education'), indent=2)}")
    print(f"Skills: {json.dumps(enriched.get('skills'), indent=2)}")

if __name__ == "__main__":
    test_parsing()
