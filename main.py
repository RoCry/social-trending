import asyncio
from datetime import datetime, timedelta, UTC
from crawlers.hn import HackerNewsCrawler
from transformer import transform_items
from db import Database
from utils import logger
import dotenv

dotenv.load_dotenv()
import os
print(os.getenv("DEEPSEEK_API_KEY"))

async def merge_with_cache(db: Database, now: datetime, new_items: list[dict]) -> list[dict]:
    merged = []
    for new_item in new_items:
        exist_item = await db.get_item(new_item["id"])
        if not exist_item:
            # no cache, just add it
            merged.append(new_item)
            continue

        # we assume only the comments will change
        exist_item["comments"] = new_item["comments"]
        exist_item["updated_at"] = now.isoformat()
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
    items = await crawler.fetch_top_stories(db_path, count=1)

    # Merge with cache
    logger.info("Merging with cached items...")
    items = await merge_with_cache(db, now, items)

    # 2. Transform and enhance with AI
    logger.info("Transforming stories with AI analysis...")
    transformed = await transform_items(items)

    # 3. Save to database
    for story in transformed:
        await db.upsert_item(story)
    logger.info(f"Saved {len(transformed)} stories to database")


if __name__ == "__main__":
    asyncio.run(main())
