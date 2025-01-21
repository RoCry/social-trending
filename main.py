import asyncio
from datetime import datetime, UTC
from crawlers.hn import HackerNewsCrawler
from transformer import transform_items, items_to_md
from db import Database
from utils import logger
from models import Item
import dotenv
import os

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


async def main():
    # Initialize database
    db_path = "cache/social.sqlite"
    db = Database(db_path)
    await db.init()

    # Clean up old items (keep last 30 days)
    await db.cleanup()

    now = datetime.now(tz=UTC)

    # Fetch stories
    logger.info("Fetching stories from Hacker News...")
    crawler = HackerNewsCrawler()
    items = await crawler.fetch_top_stories(db_path, count=5)

    # Merge with cache
    logger.info("Merging with cached items...")
    items = await merge_with_cache(db, now, items)

    # 2. Transform and enhance with AI
    logger.info("Transforming stories with AI analysis...")
    items = await transform_items(items)

    # 3. Save to database
    for item in items:
        await db.upsert_item(item)
    logger.info(f"Saved {len(items)} stories to database")

    # 4. Generate markdown file
    logger.info("Generating markdown file...")
    md_content = items_to_md("HackerNews Top Stories", now, items)
    os.makedirs("cache", exist_ok=True)
    with open("cache/hackernews.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info("Generated markdown file at cache/hackernews.md")


if __name__ == "__main__":
    asyncio.run(main())
