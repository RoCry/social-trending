import asyncio
from datetime import datetime, UTC
from crawlers.hn import HackerNewsCrawler
from transformer import transform_items, items_to_md
from db import Database
from utils import logger
from models import Item
import dotenv
import os
import json
from typing import List

dotenv.load_dotenv()


async def merge_with_cache(
    db: Database, now: datetime, new_items: list[Item]
) -> list[Item]:
    merged = []
    for new_item in new_items:
        exist_item = await db.get_item(new_item.id)
        if not exist_item:
            # no cache, just add it
            merged.append(new_item)
            continue

        # we assume only the comments will change
        exist_item.comments = new_item.comments
        exist_item.updated_at = now
        merged.append(exist_item)
    return merged


def items_to_json_feed(now: datetime, items: List[Item]) -> dict:
    """Convert items to JSON Feed v1.1 format."""

    # generate the content_text
    content_text = ""

    return {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "Social Trending - Hacker News",
        "home_page_url": "https://news.ycombinator.com/",
        "feed_url": "https://github.com/RoCry/social-trending/releases/download/latest/hackernews.rss.json",
        "description": "Top stories from Hacker News with AI-powered analysis",
        "authors": [
            {
                "name": "Social Trending Bot",
                "url": "https://github.com/RoCry/social-trending",
            }
        ],
        "language": "en-US",
        "items": [
            {
                "id": item.id,
                "url": item.url,
                "title": item.title,
                "content_text": content_text,
                "date_published": (
                    item.published_at.isoformat()
                    if item.published_at
                    else item.created_at.isoformat()
                ),
                "date_modified": item.updated_at.isoformat(),
                "authors": (
                    [{"name": comment.author} for comment in item.comments[:1]]
                    if item.comments
                    else None
                ),
                "tags": ["hackernews", "tech", "news"],
                # "_hn_comments": [
                #     {"text": comment.content, "author": comment.author}
                #     for comment in item.comments
                # ],
            }
            for item in items
        ],
    }


async def main():
    # Initialize database
    db_path = "cache/social.sqlite"
    db = Database(db_path)
    await db.init()

    # Clean up old items
    await db.cleanup()

    now = datetime.now(tz=UTC)

    # Fetch stories
    logger.info("Fetching stories from Hacker News...")
    crawler = HackerNewsCrawler()
    top_n = os.getenv("HN_COUNT", 30)
    items = await crawler.fetch_top_stories(db_path, count=int(top_n))

    # Merge with cache
    logger.info("Merging with cached items...")
    items = await merge_with_cache(db, now, items)

    # 2. Transform and enhance with AI, with progressive save
    logger.info("Transforming stories with AI analysis...")
    items = await transform_items(items, db=db)
    logger.info(f"Completed transforming {len(items)} stories")

    # 4. Generate markdown and JSON files
    logger.info("Generating output files...")
    os.makedirs("cache", exist_ok=True)

    # Generate JSON Feed file
    json_feed = items_to_json_feed(now, items)
    with open("cache/hackernews.rss.json", "w", encoding="utf-8") as f:
        json.dump(json_feed, f, indent=2, ensure_ascii=False)
    logger.info("Generated JSON Feed file at cache/hackernews.rss.json")

    # Generate markdown file
    md_content = items_to_md(now, items)
    with open("cache/hackernews.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info("Generated markdown file at cache/hackernews.md")

    # Generate JSON file
    json_content = [item.model_dump(mode="json") for item in items]
    with open("cache/hackernews.json", "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2, ensure_ascii=False)
    logger.info("Generated JSON file at cache/hackernews.json")


if __name__ == "__main__":
    asyncio.run(main())
