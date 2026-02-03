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
    
    def process_item(self, item):
        """Enrich item data"""
        
        # Parse location
        if item.get('location'):
            item['location_parsed'] = self._parse_location(item['location'])
        
        # Normalize salary
        if item.get('salary'):
            item['salary_normalized'] = self._normalize_salary(item['salary'])
        
        # Extract skills
        if item.get('description'):
            item['skills'] = self._extract_skills(item['description'])
        
        return item
    
    def _parse_location(self, location: str) -> dict:
        """Split location into components"""
        parts = [p.strip() for p in location.split(',')]
        
        parsed = {
            'raw': location,
            'city': None,
            'state': None,
            'country': None
        }
        
        if len(parts) >= 1:
            parsed['city'] = parts[0]
        if len(parts) >= 2:
            parsed['state'] = parts[1]
        if len(parts) >= 3:
            parsed['country'] = parts[2]
        else:
            # Default to USA if no country specified
            parsed['country'] = 'United States'
        
        return parsed
    
    def _normalize_salary(self, salary: str) -> dict:
        """Parse salary into structured format"""
        if not salary:
            return None
        
        normalized = {
            'raw': salary,
            'min': None,
            'max': None,
            'currency': 'USD',
            'period': 'year'
        }
        
        # Remove common prefixes/suffixes
        salary_clean = salary.replace('$', '').replace(',', '').lower()
        
        # Detect period
        if 'hour' in salary_clean or '/hr' in salary_clean:
            normalized['period'] = 'hour'
        elif 'month' in salary_clean or '/mo' in salary_clean:
            normalized['period'] = 'month'
        
        # Extract numbers
        numbers = re.findall(r'\d+(?:\.\d+)?', salary_clean)
        
        if len(numbers) == 1:
            # Single value (e.g., "$50,000")
            normalized['min'] = normalized['max'] = float(numbers[0])
        elif len(numbers) >= 2:
            # Range (e.g., "$50,000 - $70,000")
            normalized['min'] = float(numbers[0])
            normalized['max'] = float(numbers[1])
        
        # Convert to annual if hourly
        if normalized['period'] == 'hour' and normalized['min']:
            normalized['min'] = normalized['min'] * 40 * 52  # 40 hrs/week, 52 weeks/year
            if normalized['max']:
                normalized['max'] = normalized['max'] * 40 * 52
            normalized['period'] = 'year'
        
        return normalized
    
    def _extract_skills(self, description: str) -> list:
        """Extract technical skills from description"""
        if not description:
            return []
        
        description_lower = description.lower()
        
        found_skills = []
        for skill in self.SKILLS_KEYWORDS:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, description_lower):
                found_skills.append(skill)
        
        return found_skills
