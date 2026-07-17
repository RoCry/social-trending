import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from crawlers.hn import HackerNewsCrawler


class FakeContentFetcher:
    def __init__(self) -> None:
        self.urls: list[str] = []

    async def fetch(self, url: str) -> tuple[str | None, str | None]:
        self.urls.append(url)
        return "offline article", "<article>offline article</article>"


class FakeHackerNewsClient:
    def __init__(self, stories: list[SimpleNamespace]) -> None:
        self._stories = stories

    async def __aenter__(self) -> "FakeHackerNewsClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def fetch_top_stories(self, *, top_n: int, fetch_comment_levels_count: int) -> SimpleNamespace:
        assert top_n == 1
        assert fetch_comment_levels_count == 1
        return SimpleNamespace(stories=self._stories)


def test_hn_crawler_builds_items_offline_with_a_fake_content_fetcher() -> None:
    now = datetime(2026, 7, 17, 10, 0, tzinfo=UTC)
    story = SimpleNamespace(
        id=42,
        title="Composable crawler",
        url="https://example.test/article",
        time=datetime(2026, 7, 16, 9, 0, tzinfo=UTC),
        comments=[SimpleNamespace(by="alice", text="Good boundary")],
    )
    source_client = FakeHackerNewsClient([story])
    content_fetcher = FakeContentFetcher()

    def client_factory(*, cache_db_path: str) -> FakeHackerNewsClient:
        assert cache_db_path == "cache.sqlite"
        return source_client

    crawler = HackerNewsCrawler(
        content_fetcher=content_fetcher,
        client_factory=client_factory,
        clock=lambda: now,
    )

    items = asyncio.run(crawler.fetch_top_stories("cache.sqlite", count=1))

    assert content_fetcher.urls == ["https://example.test/article"]
    assert len(items) == 1
    assert items[0].model_dump() == {
        "title": "Composable crawler",
        "url": "https://news.ycombinator.com/item?id=42",
        "original_url": "https://example.test/article",
        "content": "offline article",
        "content_html": "<article>offline article</article>",
        "comments": [{"content": "Good boundary", "author": "alice"}],
        "published_at": datetime(2026, 7, 16, 9, 0, tzinfo=UTC),
        "id": "42",
        "created_at": now,
        "updated_at": now,
        "generated_at_comment_count": None,
        "ai_perspective": None,
    }
