from datetime import UTC, datetime

from exporter import (
    FeedIdentity,
    items_to_json_feed,
    items_to_markdown,
    items_to_raw_json,
)
from models import Comment, Item, Perspective, Viewpoint


def fixture_items() -> list[Item]:
    created_at = datetime(2026, 7, 17, 8, 0, tzinfo=UTC)
    updated_at = datetime(2026, 7, 17, 9, 0, tzinfo=UTC)
    return [
        Item(
            id="1",
            title="With perspective",
            url="https://example.test/discussions/1",
            original_url="https://example.test/articles/1",
            content="Article text",
            content_html="<article>Article HTML</article>",
            comments=[Comment(author="alice", content="Useful discussion")],
            published_at=created_at,
            created_at=created_at,
            updated_at=updated_at,
            generated_at_comment_count=1,
            ai_perspective=Perspective(
                title="A shared theme",
                summary="Readers broadly agree.",
                sentiment="positive",
                viewpoints=[Viewpoint(statement="The change is useful", support_percentage=60)],
            ),
        ),
        Item(
            id="2",
            title="Without perspective",
            url="https://example.test/discussions/2",
            comments=[Comment(author="bob", content="Still discussing")],
            created_at=created_at,
            updated_at=updated_at,
        ),
    ]


def test_json_feed_uses_the_supplied_feed_identity() -> None:
    now = datetime(2026, 7, 17, 8, 0, tzinfo=UTC)
    item = Item(
        id="reddit-1",
        title="A portable renderer",
        url="https://reddit.example/posts/1",
        comments=[Comment(author="alice", content="ship it")],
        created_at=now,
        updated_at=now,
    )
    identity = FeedIdentity(
        source_name="Reddit",
        feed_title="Social Trending - Reddit",
        home_page_url="https://reddit.example/",
        feed_url="https://feeds.example/reddit.json",
        tags=("reddit", "social"),
    )

    feed = items_to_json_feed([item], identity=identity)

    assert feed["title"] == "Social Trending - Reddit"
    assert feed["home_page_url"] == "https://reddit.example/"
    assert feed["feed_url"] == "https://feeds.example/reddit.json"
    assert feed["description"] == "Top stories from Reddit with AI-powered analysis"
    assert feed["items"][0]["tags"] == ["reddit", "social"]


def test_markdown_snapshot_includes_items_with_and_without_perspectives() -> None:
    assert items_to_markdown(fixture_items()) == (
        "## [With perspective](https://example.test/discussions/1)\n\n\n"
        "### AI Perspective: A shared theme\n\n"
        "<details><summary>Perspective Summary</summary>\n"
        "Readers broadly agree.\n"
        "</details>\n\n"
        "### 1 Key Viewpoints (1 comments)\n"
        "> **Overall Sentiment**: positive\n\n"
        "- The change is useful _(~60%)_\n"
        "---\n\n"
        "## [Without perspective](https://example.test/discussions/2)\n\n\n"
        "---\n"
    )


def test_json_feed_snapshot_pins_skip_none_perspective_behavior() -> None:
    identity = FeedIdentity(
        source_name="Example",
        feed_title="Example feed",
        home_page_url="https://example.test/",
        feed_url="https://example.test/feed.json",
        tags=("example",),
    )

    complete_feed = items_to_json_feed(fixture_items(), identity=identity)
    perspective_feed = items_to_json_feed(fixture_items(), identity=identity, skip_none_perspective=True)

    assert [item["id"] for item in complete_feed["items"]] == ["1", "2"]
    assert perspective_feed == {
        **complete_feed,
        "items": [complete_feed["items"][0]],
    }


def test_raw_json_snapshot() -> None:
    raw_items = items_to_raw_json(fixture_items())

    assert raw_items[0] == {
        "title": "With perspective",
        "url": "https://example.test/discussions/1",
        "original_url": "https://example.test/articles/1",
        "content": "Article text",
        "content_html": "<article>Article HTML</article>",
        "comments": [{"content": "Useful discussion", "author": "alice"}],
        "published_at": "2026-07-17T08:00:00Z",
        "id": "1",
        "created_at": "2026-07-17T08:00:00Z",
        "updated_at": "2026-07-17T09:00:00Z",
        "generated_at_comment_count": 1,
        "ai_perspective": {
            "title": "A shared theme",
            "summary": "Readers broadly agree.",
            "sentiment": "positive",
            "viewpoints": [
                {
                    "statement": "The change is useful",
                    "support_percentage": 60.0,
                }
            ],
        },
    }
    assert raw_items[1]["ai_perspective"] is None
