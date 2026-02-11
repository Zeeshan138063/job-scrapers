import unittest
from unittest.mock import MagicMock, patch
from scrapers.utils.config_loader import ConfigLoader
from scrapers.spiders.job_leads_v2 import JobLeadsSpiderV2

class TestDynamicConfig(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            "filters": {
                "country": {
                    "key": "country",
                    "type": "select",
                    "is_nested": False,
                    "options": [{"label": "USA", "value": "USA"}]
                },
                "daysReleased": {
                    "key": "daysReleased",
                    "type": "select",
                    "is_nested": True,
                    "options": [{"label": "Last 7 days", "value": "7"}]
                }
            }
        }

    @patch('scrapers.utils.config_loader.ConfigLoader.get_spider_config')
    @patch('scrapers.utils.config_loader.create_engine')
    def test_payload_construction(self, mock_engine, mock_get_config):
        mock_get_config.return_value = self.mock_config
        
        spider = JobLeadsSpiderV2(
            search_queries='["python"]',
            locations='["USA"]',
            filters='{"daysReleased": "7", "customFilter": "extra"}'
        )
        
        # Manually trigger payload construction logic
        # We'll call fetch_search_page and inspect the Request body
        requests = list(spider.fetch_search_page(0, "python", "USA"))
        payload = eval(requests[0].body.decode('utf-8')) # use eval for simple dict string
        
        # Verify nested vs non-nested injection
        self.assertEqual(payload["country"], "USA")
        self.assertEqual(payload["filters"]["daysReleased"], "7")
        # Verify fallback for unregistered filters
        self.assertEqual(payload["filters"]["customFilter"], "extra")
        
        print("Success: Payload construction verified.")

if __name__ == "__main__":
    unittest.main()
