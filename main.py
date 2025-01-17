import asyncio

from hackernews_crawler import fetch_top_stories
from transformer import transform_stories
from db import Database
from utils import logger
import dotenv

dotenv.load_dotenv()

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

    # 2. Transform and enhance with AI
    logger.info("Transforming stories with AI analysis...")
    transformed = await transform_stories(stories)

    # 3. Save to database
    for story in transformed:
        await db.upsert_item(story)
    logger.info(f"Saved {len(transformed)} stories to database")


if __name__ == "__main__":
    asyncio.run(main())
