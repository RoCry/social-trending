import trafilatura
from bs4 import BeautifulSoup
import requests
from typing import Optional, Tuple
from utils import logger


class BaseCrawler:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _fetch_with_trafilatura(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text_result = trafilatura.extract(downloaded, include_comments=False)
            html_result = trafilatura.extract(
                downloaded, include_comments=False, output_format="html"
            )
            if text_result:
                logger.debug(
                    f"Trafilatura fetched {url}:\n{text_result.splitlines()[:3]}\n..."
                )
                # Extract content from HTML if it's a full HTML document
                if html_result and ("<html" in html_result or "<body" in html_result):
                    soup = BeautifulSoup(html_result, "html.parser")
                    body = soup.find("body")
                    if body:
                        html_result = "".join(str(tag) for tag in body.children)
                    else:
                        html_result = "".join(str(tag) for tag in soup.children)
                return text_result, html_result
        return None, None

    def _fetch_with_bs4(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract main content
        for tag in ["article", "main", "div.content"]:
            element = soup.find(tag)
            if element:
                return element.get_text(), str(element)
        return None, None

    def _fetch_with_jina(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=self.timeout)
        response.raise_for_status()
        return response.text, None  # Jina only returns text format

    def fetch_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch content from URL and return as (text, html) tuple"""
        # Try trafilatura first
        try:
            logger.debug(f"Fetching {url} with trafilatura")
            text_result, html_result = self._fetch_with_trafilatura(url)
            if text_result:
                return text_result, html_result
        except Exception as e:
            logger.warning(f"Trafilatura failed for {url}: {str(e)}")

        # Fallback to BeautifulSoup
        try:
            logger.debug(f"Fetching {url} with BeautifulSoup")
            text_result, html_result = self._fetch_with_bs4(url)
            if text_result:
                return text_result, html_result
        except Exception as e:
            logger.warning(f"BeautifulSoup failed for {url}: {str(e)}")

        # Fallback to Jina.ai
        try:
            logger.debug(f"Fetching {url} with Jina.ai")
            return self._fetch_with_jina(url)
        except Exception as e:
            logger.warning(f"Jina.ai failed for {url}: {str(e)}")
            return None, None
