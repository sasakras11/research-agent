import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
from typing import Optional, Dict, List
from urllib.parse import urlparse
from aiohttp import ClientTimeout

class WebScraper:
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self.timeout = ClientTimeout(total=10)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def get_pages_content(self, urls: List[str]) -> Dict[str, Optional[str]]:
        """Fetch multiple pages concurrently"""
        async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
            tasks = [self._fetch_page(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return {url: result for url, result in zip(urls, results) if not isinstance(result, Exception)}

    async def get_page_content(self, url: str) -> Optional[str]:
        """Backwards compatibility method for single page fetch"""
        results = await self.get_pages_content([url])
        return results.get(url)

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch and parse a single page"""
        try:
            if url in self._cache:
                return self._cache[url]

            parsed = urlparse(url)
            if not parsed.scheme.startswith('http'):
                return None

            async with session.get(url) as response:
                if response.status != 200:
                    return None
                html = await response.text()
                
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            
            content = ' '.join([p.get_text().strip() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'li'])])
            content = ' '.join(content.split())
            
            self._cache[url] = content
            return content

        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
            return None
