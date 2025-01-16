import trafilatura
from bs4 import BeautifulSoup
import requests
from typing import Optional
from utils import logger


class Crawler:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _fetch_with_trafilatura(self, url: str) -> Optional[str]:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = trafilatura.extract(downloaded, include_comments=False)
            if result:
                return result
        return None

    def _fetch_with_bs4(self, url: str) -> Optional[str]:
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract main content
        for tag in ["article", "main", "div.content"]:
            element = soup.find(tag)
            if element:
                return element.get_text()
        return None

    def _fetch_with_jina(self, url: str) -> Optional[str]:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from URL and return as markdown/text"""
        # Try trafilatura first
        try:
            logger.debug(f"Fetching {url} with trafilatura")
            result = self._fetch_with_trafilatura(url)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Trafilatura failed for {url}: {str(e)}")

        # Fallback to BeautifulSoup
        try:
            logger.debug(f"Fetching {url} with BeautifulSoup")
            result = self._fetch_with_bs4(url)
            if result:
                return result
        except Exception as e:
            logger.warning(f"BeautifulSoup failed for {url}: {str(e)}")

        # Fallback to Jina.ai
        try:
            logger.debug(f"Fetching {url} with Jina.ai")
            return self._fetch_with_jina(url)
        except Exception as e:
            logger.warning(f"Jina.ai failed for {url}: {str(e)}")
            return None


def url_to_markdown(url: str) -> Optional[str]:
    """Convert URL to markdown/text"""
    crawler = Crawler()
    return crawler.fetch_url(url)
