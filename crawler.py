import trafilatura
from bs4 import BeautifulSoup
import requests
from typing import Optional


class Crawler:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from URL and return as markdown/text"""
        try:
            # Try trafilatura first
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded, include_comments=False)
                if result:
                    return result

            # Fallback to BeautifulSoup
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract main content
            for tag in ["article", "main", "div.content"]:
                element = soup.find(tag)
                if element:
                    return element.get_text()

            # Fallback to Jina.ai
            jina_url = f"https://r.jina.ai/{url}"
            response = requests.get(jina_url, timeout=self.timeout)
            response.raise_for_status()
            return response.text

        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None


def url_to_markdown(url: str) -> Optional[str]:
    """Convert URL to markdown/text"""
    crawler = Crawler()
    return crawler.fetch_url(url)
