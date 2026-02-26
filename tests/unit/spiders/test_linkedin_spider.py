import unittest
from scrapy.http import HtmlResponse, Request
from scrapers.spiders.linkedin_spider import LinkedInJobsSpider
from scrapers.items import JobItem

class TestLinkedInSpider(unittest.TestCase):
    def setUp(self):
        self.spider = LinkedInJobsSpider()

    def test_parse_job_card(self):
        html = """
        <div class="base-card">
            <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/123456"></a>
            <h3 class="base-search-card__title">Python Dev</h3>
            <h4 class="base-search-card__subtitle">
                <a>Tech Corp</a>
            </h4>
            <span class="job-search-card__location">Remote</span>
        </div>
        """
        response = HtmlResponse(
            url="https://www.linkedin.com/jobs/search",
            body=html.encode('utf-8')
        )
        
        # We need to manually simulate the loop or call the parse method directly if exposed
        # Since parse_job_card is a method we can call:
        from scrapy.selector import Selector
        card = Selector(text=html).css('.base-card')[0]
        
        result = self.spider.parse_job_card(card, response)
        
        self.assertEqual(result['external_id'], '123456')
        self.assertEqual(result['title'], 'Python Dev')
        self.assertEqual(result['company'], 'Tech Corp')
        self.assertEqual(result['location'], 'Remote')

    def test_parse_detail_page(self):
        html = """
        <html>
            <div class="description__text">We need a strong python coder.</div>
            <span class="salary">$100k</span>
            <span class="posted-time-ago__text">2 days ago</span>
        </html>
        """
        response = HtmlResponse(
            url="https://www.linkedin.com/jobs/view/123",
            body=html.encode('utf-8')
        )
        
        result = self.spider.parse_job_detail(response)
        
        self.assertIn('python coder', result['description'])
        self.assertEqual(result['salary'], '$100k')
        self.assertIsNotNone(result['posted_at'])

if __name__ == '__main__':
    unittest.main()
