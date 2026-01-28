import unittest
from scrapy.exceptions import DropItem
from scrapers.pipelines.validation_pipeline import ValidationPipeline
from scrapers.pipelines.enrichment_pipeline import EnrichmentPipeline

class TestValidationPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = ValidationPipeline()
        self.spider = None # Mock spider if needed

    def test_valid_item(self):
        item = {
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'url': 'http://example.com/job/1',
            'source': 'test'
        }
        processed = self.pipeline.process_item(item, self.spider)
        self.assertEqual(processed['title'], 'Software Engineer')
        self.assertTrue(item.get('external_id')) # Should be auto-generated

    def test_missing_field(self):
        item = {
            'company': 'Tech Corp',
            # Missing title
            'url': 'http://example.com/job/1',
            'source': 'test'
        }
        with self.assertRaises(DropItem):
            self.pipeline.process_item(item, self.spider)

    def test_invalid_url(self):
        item = {
            'title': 'Job',
            'company': 'Co',
            'url': 'javascript:void(0)',
            'source': 'test'
        }
        with self.assertRaises(DropItem):
            self.pipeline.process_item(item, self.spider)

class TestEnrichmentPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = EnrichmentPipeline()
        self.spider = None

    def test_salary_parsing(self):
        item = {'salary': '$100,000 - $120,000 a year'}
        processed = self.pipeline.process_item(item, self.spider)
        normalized = processed['salary_normalized']
        
        self.assertEqual(normalized['min'], 100000)
        self.assertEqual(normalized['max'], 120000)
        self.assertEqual(normalized['period'], 'year')

    def test_hourly_salary(self):
        item = {'salary': '$50 - $60 an hour'}
        processed = self.pipeline.process_item(item, self.spider)
        normalized = processed['salary_normalized']
        
        # 50 * 40 * 52 = 104000
        self.assertEqual(normalized['min'], 104000)
        self.assertEqual(normalized['period'], 'year')

    def test_location_parsing(self):
        item = {'location': 'New York, NY, USA'}
        processed = self.pipeline.process_item(item, self.spider)
        parsed = processed['location_parsed']
        
        self.assertEqual(parsed['city'], 'New York')
        self.assertEqual(parsed['state'], 'NY')
        self.assertEqual(parsed['country'], 'USA')

    def test_skill_extraction(self):
        item = {'description': 'We need Python and React experts using AWS.'}
        processed = self.pipeline.process_item(item, self.spider)
        
        self.assertIn('python', processed['skills'])
        self.assertIn('react', processed['skills'])
        self.assertIn('aws', processed['skills'])

if __name__ == '__main__':
    unittest.main()
