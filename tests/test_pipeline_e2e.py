import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from crawlers.hn import HackerNewsCrawler
from exporter import (
    FeedIdentity,
    items_to_json_feed,
    items_to_markdown,
    items_to_raw_json,
)
from item_store import ItemStore
from models import Comment, Perspective, Viewpoint
from transformer import Transformer


class FakeContentFetcher:
    async def fetch(self, url: str) -> tuple[str, str]:
        return f"Offline text for {url}", f"<article>Offline HTML for {url}</article>"


class FakeSourceClient:
    def __init__(self, stories: list[SimpleNamespace]) -> None:
        self._stories = stories

    async def __aenter__(self) -> "FakeSourceClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def fetch_top_stories(self, **_: object) -> SimpleNamespace:
        return SimpleNamespace(stories=self._stories)


class FakePerspectiveGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    async def generate(self, title: str, comments: list[Comment]) -> Perspective:
        self.calls.append((title, len(comments)))
        return Perspective(
            title=f"Perspective at {len(comments)} comments",
            summary=f"Offline analysis for {title}",
            sentiment="mixed",
            viewpoints=[Viewpoint(statement="Composed entirely from fakes", support_percentage=75)],
        )


def stories(stable_count: int, growing_count: int) -> list[SimpleNamespace]:
    published_at = datetime(2026, 7, 16, tzinfo=UTC)

    def story(item_id: int, title: str, comment_count: int) -> SimpleNamespace:
        return SimpleNamespace(
            id=item_id,
            title=title,
            url=f"https://example.test/articles/{item_id}",
            time=published_at,
            comments=[SimpleNamespace(by=f"reader-{index}", text=f"comment-{index}") for index in range(comment_count)],
        )

    return [
        story(1, "Stable discussion", stable_count),
        story(2, "Growing discussion", growing_count),
    ]


def test_two_run_offline_pipeline_proves_reconcile_refresh_and_all_artifacts(
    tmp_path,
) -> None:
    async def scenario() -> None:
        store = ItemStore(tmp_path / "pipeline.sqlite")
        await store.init()
        generator = FakePerspectiveGenerator()
        transformer = Transformer(generator)
        identity = FeedIdentity(
            source_name="Fixture Source",
            feed_title="Fixture feed",
            home_page_url="https://example.test/",
            feed_url="https://example.test/feed.json",
            tags=("fixture",),
        )

        async def run(
            *, now: datetime, source_stories: list[SimpleNamespace]
        ) -> tuple[list, str, dict[str, object], list[dict[str, object]]]:
            crawler = HackerNewsCrawler(
                FakeContentFetcher(),
                client_factory=lambda **_: FakeSourceClient(source_stories),
                clock=lambda: now,
            )
            fetched = await crawler.fetch_top_stories("offline.sqlite", count=2)
            reconciled = await store.reconcile(now, fetched)
            transformed = await transformer.transform(reconciled)
            for transformed_item in transformed:
                await store.save(transformed_item)
            return (
                reconciled,
                items_to_markdown(transformed),
                items_to_json_feed(transformed, identity=identity),
                items_to_raw_json(transformed),
            )

        first_now = datetime(2026, 7, 17, 8, 0, tzinfo=UTC)
        first_items, _, _, _ = await run(now=first_now, source_stories=stories(15, 15))
        first_perspectives = [item.ai_perspective for item in first_items]
        assert generator.calls == [
            ("Stable discussion", 15),
            ("Growing discussion", 15),
        ]

        second_now = datetime(2026, 7, 17, 20, 0, tzinfo=UTC)
        second_items, markdown, json_feed, raw_json = await run(now=second_now, source_stories=stories(16, 26))

        assert second_items[0].ai_perspective == first_perspectives[0]
        assert second_items[1].ai_perspective != first_perspectives[1]
        assert second_items[0].ai_perspective.title == "Perspective at 15 comments"
        assert second_items[1].ai_perspective.title == "Perspective at 26 comments"
        assert generator.calls == [
            ("Stable discussion", 15),
            ("Growing discussion", 15),
            ("Growing discussion", 26),
        ]

        assert "Perspective at 15 comments" in markdown
        assert "Perspective at 26 comments" in markdown
        assert [item["summary"] for item in json_feed["items"]] == [
            "Perspective at 15 comments",
            "Perspective at 26 comments",
        ]
        assert [item["ai_perspective"]["title"] for item in raw_json] == [
            "Perspective at 15 comments",
            "Perspective at 26 comments",
        ]
        assert raw_json[0]["content"].startswith("Offline text")

    asyncio.run(scenario())
