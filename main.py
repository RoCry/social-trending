import asyncio
import json
import os
from datetime import UTC, datetime

import dotenv
from content_fetcher import ContentFetcher
from crawlers.hn import HackerNewsCrawler
from exporter import (
    FeedIdentity,
    items_to_json_feed,
    items_to_markdown,
    items_to_raw_json,
)
from item_store import ItemStore
from perspective_generator import SmolLLMPerspectiveGenerator
from transformer import Transformer
from utils import logger

dotenv.load_dotenv()
logger.info("Using SMOLLLM_MODEL: %s", os.getenv("SMOLLLM_MODEL"))

HACKER_NEWS_FEED = FeedIdentity(
    source_name="Hacker News",
    feed_title="Social Trending - Hacker News",
    home_page_url="https://news.ycombinator.com/",
    feed_url="https://github.com/RoCry/social-trending/releases/download/latest/hackernews.rss.json",
    tags=("hackernews",),
)


async def main():
    perspective_generator = SmolLLMPerspectiveGenerator.from_env()

    # Initialize ItemStore
    db_path = "cache/social.sqlite"
    store = ItemStore(db_path)
    await store.init()

    # Clean up old items
    await store.cleanup()

    now = datetime.now(tz=UTC)

    # Fetch stories
    logger.info("Fetching stories from Hacker News...")
    crawler = HackerNewsCrawler(ContentFetcher())
    top_n = os.getenv("HN_COUNT", 30)
    fetched = await crawler.fetch_top_stories(db_path, count=int(top_n))

    # Reconcile with cached Items
    logger.info("Reconciling with cached Items...")
    items = await store.reconcile(now, fetched)

    # Transform and enhance with AI perspective
    logger.info("Analyzing discussions with AI...")
    items = await Transformer(perspective_generator).transform(items)
    for item in items:
        await store.save(item)
    logger.info(f"Completed analyzing {len(items)} discussions")

    # Generate output files
    logger.info("Generating output files...")
    os.makedirs("cache", exist_ok=True)

    # Generate JSON Feed file
    json_feed = items_to_json_feed(items, identity=HACKER_NEWS_FEED, skip_none_perspective=True)
    with open("cache/hackernews.rss.json", "w", encoding="utf-8") as f:
        json.dump(json_feed, f, indent=2, ensure_ascii=False)
    logger.info("Generated JSON Feed file at cache/hackernews.rss.json")

    # Generate markdown file
    md_content = items_to_markdown(items)
    with open("cache/hackernews.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info("Generated markdown file at cache/hackernews.md")

    # Generate JSON file
    json_content = items_to_raw_json(items)
    with open("cache/hackernews.json", "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2, ensure_ascii=False)
    logger.info("Generated JSON file at cache/hackernews.json")


if __name__ == "__main__":
    asyncio.run(main())
