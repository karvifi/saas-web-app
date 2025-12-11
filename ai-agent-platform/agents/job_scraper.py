import scrapy
from scrapy.crawler import CrawlerProcess
from typing import List, Dict, Any
import json
import os

class JobItem(scrapy.Item):
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    salary = scrapy.Field()
    tags = scrapy.Field()

class RemoteOKSpider(scrapy.Spider):
    name = 'remoteok'
    start_urls = ['https://remoteok.com/api']

    def parse(self, response):
        try:
            jobs = json.loads(response.text)
            for job in jobs:
                if isinstance(job, dict) and 'position' in job:
                    yield JobItem(
                        title=job.get('position', ''),
                        company=job.get('company', ''),
                        location=job.get('location', ''),
                        description=job.get('description', ''),
                        url=job.get('url', ''),
                        salary=job.get('salary', ''),
                        tags=job.get('tags', [])
                    )
        except json.JSONDecodeError:
            self.logger.error("Failed to parse JSON from RemoteOK")

class WeWorkRemotelySpider(scrapy.Spider):
    name = 'weworkremotely'
    start_urls = ['https://weworkremotely.com/remote-jobs.rss']

    def parse(self, response):
        # Parse RSS feed
        for item in response.xpath('//item'):
            yield JobItem(
                title=item.xpath('title/text()').get(),
                company=item.xpath('company/text()').get() or 'Unknown',
                location='Remote',
                description=item.xpath('description/text()').get(),
                url=item.xpath('link/text()').get(),
                salary='',
                tags=[]
            )

class JobScraperAgent:
    def __init__(self):
        self.spiders = {
            'remoteok': RemoteOKSpider,
            'weworkremotely': WeWorkRemotelySpider
        }

    def scrape_jobs(self, platforms: List[str] = None, keywords: str = None) -> List[Dict[str, Any]]:
        """
        Scrape jobs from specified platforms
        """
        if platforms is None:
            platforms = ['remoteok', 'weworkremotely']

        all_jobs = []

        for platform in platforms:
            if platform in self.spiders:
                jobs = self._scrape_platform(platform, keywords)
                all_jobs.extend(jobs)

        return all_jobs

    def _scrape_platform(self, platform: str, keywords: str = None) -> List[Dict[str, Any]]:
        """
        Scrape jobs from a specific platform
        """
        jobs = []

        # For now, return mock data since we can't run scrapy in this context
        # In production, this would use CrawlerProcess

        if platform == 'remoteok':
            jobs = [
                {
                    'title': 'Senior Python Developer',
                    'company': 'Tech Corp',
                    'location': 'Remote',
                    'description': 'Looking for experienced Python developer...',
                    'url': 'https://remoteok.com/remote-jobs/123',
                    'salary': '-',
                    'tags': ['python', 'django', 'remote']
                }
            ]
        elif platform == 'weworkremotely':
            jobs = [
                {
                    'title': 'Full Stack Developer',
                    'company': 'Startup Inc',
                    'location': 'Remote',
                    'description': 'Join our team building amazing products...',
                    'url': 'https://weworkremotely.com/remote-jobs/456',
                    'salary': '-',
                    'tags': ['react', 'node.js', 'remote']
                }
            ]

        # Filter by keywords if provided
        if keywords:
            keywords_lower = keywords.lower()
            jobs = [job for job in jobs if
                   keywords_lower in job['title'].lower() or
                   keywords_lower in job['description'].lower() or
                   any(keywords_lower in tag.lower() for tag in job['tags'])]

        return jobs

    def run_scraper(self, platform: str, output_file: str = None):
        """
        Run the scraper for a specific platform and save results
        """
        if platform not in self.spiders:
            raise ValueError(f"Unknown platform: {platform}")

        # In production, this would use CrawlerProcess
        # For now, just return the mock data
        jobs = self._scrape_platform(platform)

        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(jobs, f, indent=2)

        return jobs
