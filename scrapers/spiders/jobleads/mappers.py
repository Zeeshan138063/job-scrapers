import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def map_listing_response(job_data: dict) -> dict:
    """Ported from original scraper."""
    meta = {
        "is_featured": job_data.get("isFeatured"),
        "is_promoted": job_data.get("isPromoted"),
        "is_deactivated": job_data.get("isDeactivated"),
        "source_type": job_data.get("source"),
        "contract_type_raw": job_data.get("contractType"),
    }

    ctype = job_data.get("contractType")
    employment_type = None
    if isinstance(ctype, list) and len(ctype) > 0:
        employment_type = ctype[0]
    elif isinstance(ctype, str):
        employment_type = ctype

    location_raw = job_data.get("location")
    location_parsed = {}
    if location_raw and isinstance(location_raw, str):
        parts = location_raw.split(",")
        if len(parts) > 0:
            location_parsed["city"] = parts[0].strip()
        if len(parts) > 1:
            location_parsed["country"] = parts[-1].strip()

    res = {
        "source": "jobleads",
        "external_id": job_data.get("id"),
        "source_domain": "jobleads.com",
        "scraped_source": "job_leads_spider",
        "title": job_data.get("title"),
        "company": "JobLeads (Aggregator)",
        "company_name": "JobLeads (Aggregator)",
        "location": location_raw,
        "location_raw": location_raw,
        "location_parsed": location_parsed,
        "url": f"https://www.jobleads.com/job/{job_data.get('id')}",
        "salary_raw": str(job_data.get("salary")) if job_data.get("salary") else None,
        "employment_type": employment_type,
        "remote_modality": job_data.get("isRemote"),
        "meta_flags": meta,
        "_raw_listing": job_data
    }
    return res


def map_details_response(api_response: dict) -> dict:
    """Ported from original scraper."""
    if not api_response:
        return {}
    content = api_response.get("payload", {}).get("content", {})
    url_slug = content.get("canonicalUrl", "")
    full_url = f"https://www.jobleads.com/{url_slug.lstrip('/')}" if url_slug else None
    company = content.get("hiringOrganization", {}).get("name")

    res = {
        "salary_currency": content.get("currency"),
        "salary_min": content.get("salaryMin"),
        "salary_max": content.get("salaryMax"),
        "region": content.get("locationRegion"),
        "hostname_origin": content.get("hostname"),
        "url": full_url,
        "description_short": content.get("jobSummary"),
        "benefits": content.get("benefits"),
        "qualifications": content.get("qualifications"),
        "responsibilities": content.get("responsibilities"),
        "skills": content.get("skills"),
        "education": content.get("education"),
        "tools": content.get("tools"),
        "meta_flags": {
            "is_accessible": content.get("isAccessible"),
            "is_deactivated": content.get("isDeactivated"),
            "posted_since": content.get("releasedSince"),
        },
        "posted_at": content.get("postedAt"),
        "expires_at": content.get("validThrough"),
        "_raw_details": content
    }
    if company:
        res["company"] = company
        res["company_name"] = company
    return res


def map_canonical_response(normalized_data: dict) -> dict:
    """Ported from original scraper."""
    if not normalized_data:
        return {}
    salary = normalized_data.get("salary") or {}
    location_data = normalized_data.get("location") or {}
    location_parsed = {}
    if isinstance(location_data, dict):
        location_parsed["city"] = location_data.get("city")
        location_parsed["country"] = location_data.get("country")
        location_parsed["state"] = location_data.get("region")
    res = {
        "salary_currency": normalized_data.get("salaryCurrency") or (normalized_data.get("salary") or {}).get(
            "currency"),
        "salary_min": (normalized_data.get("salary") or {}).get("min"),
        "salary_max": (normalized_data.get("salary") or {}).get("max"),
        "description": normalized_data.get("description_html"),
        "description_html": normalized_data.get("description_html"),
        "description_text": normalized_data.get("description_text"),
        "salary_period": salary.get("unit"),
        "country_code": location_data.get("country"),
        "location_parsed": location_parsed,
        "source_url": normalized_data.get("source_url"),
        "_raw_canonical": normalized_data
    }
    company = normalized_data.get("company_name") or normalized_data.get("company")
    if company:
        res["company"] = company
        res["company_name"] = company
    return res


def yield_final_item(listing: Dict[str, Any], details: Dict[str, Any],
                     canonical: Dict[str, Any], country_name: Optional[str] = None) -> Dict[str, Any]:
    """Ported from original scraper's _yield_final_item."""
    # Merge
    item_dict = {**listing, **details, **canonical}

    # Unified company name
    final_company = item_dict.get('company_name') or item_dict.get('company')
    item_dict['company_name'] = final_company
    item_dict['company'] = final_company

    if canonical.get('location_parsed'):
        item_dict['location_parsed'] = canonical.get('location_parsed')

    # Additional fields for JobItem compatibility
    item_dict['scraped_at'] = datetime.now(timezone.utc).isoformat()
    item_dict['scraped_source'] = "job_leads_spider"
    item_dict['source'] = "jobleads"
    item_dict['source_domain'] = "jobleads.com"

    item_dict['raw_data'] = {
        "listing": item_dict.pop("_raw_listing", {}),
        "details": item_dict.pop("_raw_details", {}),
        "canonical": item_dict.pop("_raw_canonical", {})
    }

    if 'description' not in item_dict and 'description_html' in item_dict:
        item_dict['description'] = item_dict['description_html']

    item_dict['country_name'] = country_name
    return item_dict
