import asyncio

from hackernews_crawler import fetch_top_stories
from transformer import transform_stories
from db import Database
from utils import logger


async def main():
    # Initialize database
    db = Database("cache/social.db")
    await db.init()

    # Clean up old items (keep last 30 days)
    await db.cleanup()

    # 1. Fetch stories
    logger.info("Fetching stories from Hacker News...")
    stories = await fetch_top_stories(3)  # Start with 3 for testing

    # 2. Transform and enhance with AI
    logger.info("Transforming stories with AI analysis...")
    transformed = await transform_stories(stories)

    # 3. Save to database
    for story in transformed:
        await db.upsert_item(story)
    logger.info(f"Saved {len(transformed)} stories to database")


if __name__ == "__main__":
    asyncio.run(main())
