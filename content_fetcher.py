import asyncio
from collections.abc import Callable

import requests
import trafilatura
from bs4 import BeautifulSoup
from utils import logger

FetchResult = tuple[str | None, str | None]
Extractor = Callable[[str], FetchResult]
NamedExtractor = tuple[str, Extractor]


class ContentFetcher:
    def __init__(
        self,
        timeout: int = 10,
        *,
        extractors: tuple[NamedExtractor, ...] | None = None,
    ) -> None:
        self._timeout = timeout
        self._extractors = extractors or (
            ("trafilatura", self._fetch_with_trafilatura),
            ("BeautifulSoup", self._fetch_with_beautifulsoup),
            ("Jina.ai", self._fetch_with_jina),
        )

    async def fetch(self, url: str) -> FetchResult:
        return await asyncio.to_thread(self._fetch_sync, url)

    def _fetch_sync(self, url: str) -> FetchResult:
        for name, extract in self._extractors:
            try:
                logger.debug("Fetching %s with %s", url, name)
                text, html = extract(url)
                if text:
                    return text, html
            except Exception as error:
                logger.warning("%s failed for %s: %s", name, url, error)
        return None, None

    def _fetch_with_trafilatura(self, url: str) -> FetchResult:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None, None

        text = trafilatura.extract(downloaded, include_comments=False)
        if not text:
            return None, None

        html = trafilatura.extract(downloaded, include_comments=False, output_format="html")
        if html and ("<html" in html or "<body" in html):
            soup = BeautifulSoup(html, "html.parser")
            container = soup.find("body") or soup
            html = "".join(str(tag) for tag in container.children)
        return text, html

    def _fetch_with_beautifulsoup(self, url: str) -> FetchResult:
        response = requests.get(url, timeout=self._timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        if element := soup.select_one("article, main, div.content"):
            return element.get_text(), str(element)
        return None, None

    def _fetch_with_jina(self, url: str) -> FetchResult:
        response = requests.get(f"https://r.jina.ai/{url}", timeout=self._timeout)
        response.raise_for_status()
        return response.text, None
