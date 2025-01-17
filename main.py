import asyncio
from datetime import datetime, timedelta, UTC
from hackernews_crawler import fetch_top_stories
from transformer import transform_stories
from db import Database
from utils import logger
import dotenv

dotenv.load_dotenv()


async def merge_with_cache(db: Database, new_stories: list[dict]) -> list[dict]:
    """Merge new stories with cached versions, keeping AI fields if they exist."""
    merged = []
    for new in new_stories:
        old = await db.get_item(new["id"])
        # only the comments will change, so we use new.comments with old
        if not old:
            merged.append(new)
            continue
        old["comments"] = new["comments"]
        merged.append(old)
    return merged


async def main():
    # Initialize database
    db_path = "cache/social.sqlite3"
    db = Database(db_path)
    await db.init()

    # Clean up old items (keep last 30 days)
    await db.cleanup()

    # 1. Fetch stories
    logger.info("Fetching stories from Hacker News...")
    stories = await fetch_top_stories(db_path, count=1)  # Start with 3 for testing

    # 1.5 Merge with cache
    logger.info("Merging with cached items...")
    stories = await merge_with_cache(db, stories)

    # 2. Transform and enhance with AI
    logger.info("Transforming stories with AI analysis...")
    transformed = await transform_stories(stories)

    # 3. Save to database
    for story in transformed:
        await db.upsert_item(story)
    logger.info(f"Saved {len(transformed)} stories to database")


if __name__ == "__main__":
    asyncio.run(main())
