from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from typing import Any, Protocol

from content_fetcher import ContentFetcher
from hackernews.client import HackerNewsClient
from models import Comment, Item


class FetchesContent(Protocol):
    async def fetch(self, url: str) -> tuple[str | None, str | None]: ...


class HackerNewsCrawler:
    def __init__(
        self,
        content_fetcher: ContentFetcher | FetchesContent,
        *,
        client_factory: Callable[..., AbstractAsyncContextManager[Any]] = HackerNewsClient,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._content_fetcher = content_fetcher
        self._client_factory = client_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    async def fetch_top_stories(self, cache_db_path: str, count: int = 3) -> list[Item]:
        items: list[Item] = []
        async with self._client_factory(cache_db_path=cache_db_path) as client:
            response = await client.fetch_top_stories(top_n=count, fetch_comment_levels_count=1)
            for story in response.stories:
                content = None
                content_html = None
                if story.url:
                    content, content_html = await self._content_fetcher.fetch(story.url)

                now = self._clock()
                items.append(
                    Item(
                        title=story.title,
                        url=f"https://news.ycombinator.com/item?id={story.id}",
                        original_url=story.url,
                        content=content,
                        content_html=content_html,
                        comments=[Comment(content=comment.text, author=comment.by) for comment in story.comments],
                        published_at=story.time,
                        id=str(story.id),
                        created_at=now,
                        updated_at=now,
                    )
                )
        return items
