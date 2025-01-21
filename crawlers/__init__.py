from .base import BaseCrawler
from .hn import HackerNewsCrawler


def url_to_markdown(url: str) -> str:
    """Helper function to quickly fetch and convert a URL to markdown"""
    crawler = BaseCrawler()
    return crawler.fetch_url(url)


__all__ = ["BaseCrawler", "HackerNewsCrawler", "url_to_markdown"]
