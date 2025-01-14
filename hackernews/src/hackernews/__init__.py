import asyncio
from .client import HackerNewsClient


async def fetch_top_stories(top_n: int = 10, max_comment_depth: int = 2):
    async with HackerNewsClient(max_comment_depth=max_comment_depth) as client:
        return await client.fetch_top_stories(top_n)


def main() -> None:
    response = asyncio.run(fetch_top_stories(2))
    for story in response.stories:
        print(f"\n{story.title} by {story.by}")
        print(f"Score: {story.score}, Comments: {story.descendants}")
        if story.url:
            print(f"URL: {story.url}")

        print("\nComments:")
        # Print L0 comments
        for comment in story.comments[:3]:
            text = comment.text[:140].replace("\n", "\n│  ├─ ")
            print(f"├─ {comment.by}: {text}...")
            # Print L1 comments
            for reply in comment.replies[:2]:
                reply_text = reply.text[:140].replace("\n", "\n│     └─ ")
                print(f"│  └─ {reply.by}: {reply_text}...")
