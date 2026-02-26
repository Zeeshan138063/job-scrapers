import re
import logging

logger = logging.getLogger(__name__)


class EnrichmentPipeline:
    """
    Pipeline 3: Enrich job data
    - Parse location into components
    - Normalize salary
    - Extract skills
    """
    
    SKILLS_KEYWORDS = [
        'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'php', 'go', 'rust',
        'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch',
        'git', 'ci/cd', 'agile', 'scrum', 'rest api', 'graphql'
    ]
    
    def process_item(self, item, spider):
        """Enrich item data using structured raw_data where available"""
        
        raw_data = item.get('raw_data', {})
        canonical = raw_data.get('canonical', {})
        details = raw_data.get('details', {})
        json_ld = canonical.get('raw_json_ld', {})

        # 1. Parse location
        item['location_parsed'] = self._parse_location_enriched(item, canonical, details, json_ld)
        
        # Sync top-level location fields if parsed
        if item['location_parsed']:
            if item['location_parsed'].get('country'):
                item['location_country'] = item['location_parsed']['country']
                item['country_code'] = item['location_parsed']['country'] # Keep for backward compat
            if item['location_parsed'].get('city'):
                item['location_city'] = item['location_parsed']['city']
            if item['location_parsed'].get('state'):
                item['location_state'] = item['location_parsed']['state']

        # 2. Normalize salary
        salary_data = self._normalize_salary_enriched(item, canonical, details, json_ld)
        if salary_data:
            item['salary_min'] = salary_data.get('min')
            item['salary_max'] = salary_data.get('max')
            item['salary_currency'] = salary_data.get('currency')
            item['salary_period'] = salary_data.get('period')
            item['salary_raw'] = salary_data.get('raw')

        # 3. Extract other fields from structured data if missing
        if not item.get('employment_type'):
            item['employment_type'] = details.get('contractType', [None])[0] if isinstance(details.get('contractType'), list) else canonical.get('employment_type')
        
        if not item.get('remote_modality'):
            item['remote_modality'] = details.get('isRemote')

        if not item.get('company_name'):
            item['company_name'] = canonical.get('company_name') or json_ld.get('hiringOrganization', {}).get('name')

        # 4. Populate structured lists from details if missing
        for field in ['benefits', 'qualifications', 'responsibilities', 'education', 'tools', 'skills']:
            val = item.get(field) or details.get(field)
            if val:
                item[field] = self._unravel_structured_list(val)

        # 5. Extract skills (fallback to description parsing)
        desc = item.get('description') or item.get('description_text') or details.get('jobSummary')
        if desc:
            extracted_skills = self._extract_skills(desc)
            # Merge with existing skills if any
            existing_skills = item.get('skills') or []
            item['skills'] = list(set(existing_skills + extracted_skills))

        # 6. Ensure country_name is never empty (prioritize scraped, fallback to Credential-provided)
        scraped_country = item.get('location_parsed', {}).get('country')
        
        # If we scraped a full name (longer than code), prioritize it
        if scraped_country and len(scraped_country) > 3:
            item['country_name'] = scraped_country
            
        if not item.get('country_name'):
            # Fallback 1: Derive from code
            if scraped_country and len(scraped_country) > 0:
                # If it's a code (2-3 chars), we could map it, but for now just use it if name is missing
                item['country_name'] = scraped_country
            
            # Fallback 2: Sync from country_code if it's already a full name
            elif item.get('country_code') and len(item.get('country_code', '')) > 2:
                item['country_name'] = item['country_code']

        return item

    def _parse_location_enriched(self, item, canonical, details, json_ld) -> dict:
        """Smarter location parsing using structured data sources"""
        parsed = {
            'city': None,
            'state': None,
            'country': None,
            'raw': item.get('location')
        }

        # Try JSON-LD first (Highest fidelity)
        address = json_ld.get('jobLocation', {}).get('address', {})
        if isinstance(address, dict):
            parsed['country'] = address.get('addressCountry')
            parsed['city'] = address.get('addressLocality')
            parsed['state'] = address.get('addressRegion')

        # Fallback to canonical location object
        can_loc = canonical.get('location', {})
        if isinstance(can_loc, dict):
            parsed['country'] = parsed['country'] or can_loc.get('country')
            parsed['city'] = parsed['city'] or can_loc.get('city')
            parsed['state'] = parsed['state'] or can_loc.get('region')

        # Final fallback to string parsing if we still lack data
        if not parsed['city'] and item.get('location'):
            legacy = self._parse_location(item['location'])
            parsed['city'] = legacy['city']
            parsed['state'] = legacy['state']
            parsed['country'] = parsed['country'] or legacy['country']

        return parsed

    def _normalize_salary_enriched(self, item, canonical, details, json_ld) -> dict:
        """Smarter salary normalization using structured data sources"""
        
        # 1. Try details (often has explicit min/max)
        if details.get('salaryMin') or details.get('salaryMax'):
            return {
                'min': details.get('salaryMin'),
                'max': details.get('salaryMax'),
                'currency': details.get('currency', 'USD'),
                'period': 'year', # JobLeads usually annual
                'raw': details.get('salary')
            }

        # 2. Try JSON-LD
        base_salary = json_ld.get('baseSalary', {})
        if isinstance(base_salary, dict):
            val = base_salary.get('value', {})
            if isinstance(val, dict):
                return {
                    'min': val.get('minValue'),
                    'max': val.get('maxValue'),
                    'currency': base_salary.get('currency') or json_ld.get('salaryCurrency'),
                    'period': (val.get('unitText') or 'year').lower(),
                    'raw': item.get('salary')
                }

        # 3. Fallback to regex parsing of the raw string
        raw_salary = item.get('salary') or item.get('salary_raw')
        if raw_salary:
            return self._normalize_salary(raw_salary)

        return None

    def _parse_location(self, location: str) -> dict:
        """Split location into components (Legacy/Fallback)"""
        if not location:
            return {'city': None, 'state': None, 'country': None}
            
        parts = [p.strip() for p in location.split(',')]
        parsed = {'city': None, 'state': None, 'country': None}
        
        if len(parts) >= 1:
            parsed['city'] = parts[0]
        if len(parts) >= 2:
            parsed['state'] = parts[1]
        if len(parts) >= 3:
            parsed['country'] = parts[2]
        
        return parsed
    
    def _normalize_salary(self, salary: str) -> dict:
        """Parse salary into structured format using regex (Fallback)"""
        normalized = {
            'min': None,
            'max': None,
            'currency': 'USD',
            'period': 'year',
            'raw': salary
        }
        
        # Basic currency detection
        if '€' in salary or 'eur' in salary.lower():
            normalized['currency'] = 'EUR'
        elif '£' in salary or 'gbp' in salary.lower():
            normalized['currency'] = 'GBP'

        # Remove common prefixes/suffixes
        salary_clean = salary.replace('$', '').replace('€', '').replace('£', '').replace(',', '').lower()
        
        # Detect period
        if 'hour' in salary_clean or '/hr' in salary_clean:
            normalized['period'] = 'hour'
        elif 'month' in salary_clean or '/mo' in salary_clean:
            normalized['period'] = 'month'
        
        # Extract numbers
        numbers = re.findall(r'\d+(?:\.\d+)?', salary_clean)
        
        if len(numbers) == 1:
            normalized['min'] = normalized['max'] = float(numbers[0])
        elif len(numbers) >= 2:
            normalized['min'] = float(numbers[0])
            normalized['max'] = float(numbers[1])
        
        # Handle "k" notation
        if 'k' in salary_clean:
            if normalized['min'] and normalized['min'] < 1000: normalized['min'] *= 1000
            if normalized['max'] and normalized['max'] < 1000: normalized['max'] *= 1000

        # Convert to annual if hourly
        if normalized['period'] == 'hour' and normalized['min']:
            normalized['min'] = normalized['min'] * 40 * 52 
            if normalized['max']:
                normalized['max'] = normalized['max'] * 40 * 52
            normalized['period'] = 'year'
        
        return normalized
    
    def _unravel_structured_list(self, items: list) -> list:
        """
        Converts lists of dicts like [{"text": "val", "selected": false}] 
        into simple string lists ["val"].
        """
        if not isinstance(items, list):
            return items
            
        unraveled = []
        for it in items:
            if isinstance(it, dict) and 'text' in it:
                unraveled.append(it['text'])
            elif isinstance(it, str):
                unraveled.append(it)
            else:
                # Keep original if it doesn't match the pattern
                unraveled.append(it)
        return unraveled

    def _extract_skills(self, description: str) -> list:
        """Extract technical skills from description"""
        if not description:
            return []
        
        description_lower = description.lower()
        found_skills = []
        for skill in self.SKILLS_KEYWORDS:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, description_lower):
                found_skills.append(skill)
        
        return found_skills
