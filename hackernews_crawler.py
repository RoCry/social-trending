from typing import List
from datetime import datetime

from hackernews.client import HackerNewsClient
from crawler import url_to_markdown


async def fetch_top_stories(count: int = 3) -> List[dict]:
    """Fetch top stories from HN with their comments."""
    stories = []
    async with HackerNewsClient() as client:
        # Get top story IDs
        top_ids = await client.top_stories()
        top_ids = top_ids[:count]  # Limit to specified count

        # Fetch each story with comments
        for story_id in top_ids:
            story = await client.fetch_story(
                story_id=story_id,
                fetch_comment_levels_count=1,  # Only fetch root comments for now
            )

            # Extract content if URL exists
            content = None
            if story.url:
                content = url_to_markdown(story.url)

            # Transform comments to list
            comments = [{"content": c.text, "author": c.by} for c in story.comments]

            now = datetime.utcnow().isoformat() + "Z"
            # Build story data
            story_data = {
                "title": story.title,
                "url": f"https://news.ycombinator.com/item?id={story.id}",
                "source_url": story.url,  # original url
                "content": content,
                "comments": comments,
                "published": story.time.isoformat() + "Z",
                "id": str(story.id),
                "created": now,
                "updated": now,
            }
            stories.append(story_data)

    return stories


if __name__ == "__main__":
    import json
    from pathlib import Path

    async def test():
        stories = await fetch_top_stories(3)

        # Create cache directory if not exists
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)

        # Save to cache file
        date = datetime.now().strftime("%Y%m%d")
        cache_file = cache_dir / f"{date}_hackernews.json"
        with open(cache_file, "w") as f:
            json.dump(stories, f, indent=2)
        print(f"Fetched {len(stories)} stories and saved to {cache_file}")
