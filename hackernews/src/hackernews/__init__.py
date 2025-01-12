import asyncio
from .client import HackerNewsClient

async def fetch_top_stories(top_n: int = 10):
    async with HackerNewsClient() as client:
        return await client.fetch_top_stories(top_n)

def main() -> None:
    response = asyncio.run(fetch_top_stories(5))
    for story in response.stories:
        print(f"\n{story.title} by {story.by}")
        print(f"Score: {story.score}, Comments: {story.descendants}")
        if story.url:
            print(f"URL: {story.url}")
        
        print("\nTop comments:")
        for comment in story.comments[:3]:  # Show first 3 comments
            print(f"- {comment.by}: {comment.text[:100]}...")
