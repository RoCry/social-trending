from typing import List
from datetime import datetime, UTC

from hackernews.client import HackerNewsClient
from .base import BaseCrawler


class HackerNewsCrawler(BaseCrawler):
    async def fetch_top_stories(self, cache_db_path: str, count: int = 3) -> List[dict]:
        """Fetch top stories from HN with their comments."""
        stories = []
        async with HackerNewsClient(cache_path=cache_db_path) as client:
            # Get top story IDs
            resp = await client.fetch_top_stories(top_n=count, fetch_comment_levels_count=1)

            # Fetch each story with comments
            for story in resp.stories:
                # Extract content if URL exists
                content = None
                if story.url:
                    content = self.fetch_url(story.url)

                # Transform comments to list
                comments = [{"content": c.text, "author": c.by} for c in story.comments]

                now = datetime.now(UTC)
                # Build story data
                story_data = {
                    "title": story.title,
                    "url": f"https://news.ycombinator.com/item?id={story.id}",
                    "content": content,
                    "comments": comments,
                    "published_at": story.time.isoformat(),
                    "id": str(story.id),
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
                stories.append(story_data)

        return stories 