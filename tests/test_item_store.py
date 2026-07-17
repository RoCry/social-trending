import asyncio
from datetime import UTC, datetime, timedelta

from item_store import ItemStore
from models import Comment, Item, Perspective, Viewpoint


def item(
    item_id: str,
    *,
    updated_at: datetime,
    comments: list[Comment] | None = None,
    perspective_title: str | None = None,
) -> Item:
    perspective = (
        Perspective(
            title=perspective_title,
            summary="Cached summary",
            sentiment="positive",
            viewpoints=[Viewpoint(statement="Cached view", support_percentage=80)],
        )
        if perspective_title
        else None
    )
    return Item(
        id=item_id,
        title=f"Item {item_id}",
        url=f"https://example.test/{item_id}",
        comments=comments or [],
        created_at=updated_at - timedelta(days=1),
        updated_at=updated_at,
        generated_at_comment_count=15 if perspective else None,
        ai_perspective=perspective,
    )


def test_reconcile_returns_a_new_item_unchanged(tmp_path) -> None:
    async def scenario() -> None:
        store = ItemStore(tmp_path / "items.sqlite")
        await store.init()
        now = datetime(2026, 7, 17, tzinfo=UTC)
        fetched = item("new", updated_at=now)

        reconciled = await store.reconcile(now, [fetched])

        assert reconciled == [fetched]
        assert reconciled[0] is fetched

    asyncio.run(scenario())


def test_reconcile_keeps_cached_perspective_and_takes_fresh_comments(tmp_path) -> None:
    async def scenario() -> None:
        store = ItemStore(tmp_path / "items.sqlite")
        await store.init()
        cached_at = datetime(2026, 7, 16, tzinfo=UTC)
        cached = item(
            "cached",
            updated_at=cached_at,
            comments=[Comment(author="old", content="old comment")],
            perspective_title="Keep me",
        )
        await store.save(cached)
        now = datetime(2026, 7, 17, tzinfo=UTC)
        fresh_comments = [Comment(author="new", content="fresh comment")]
        fetched = item("cached", updated_at=now, comments=fresh_comments)
        fetched.title = "Fresh title is not part of the current merge policy"

        reconciled = await store.reconcile(now, [fetched])

        assert reconciled[0].title == "Item cached"
        assert reconciled[0].comments == fresh_comments
        assert reconciled[0].updated_at == now
        assert reconciled[0].ai_perspective == cached.ai_perspective
        assert reconciled[0].generated_at_comment_count == 15

    asyncio.run(scenario())


def test_cleanup_drops_old_items(tmp_path) -> None:
    async def scenario() -> None:
        store = ItemStore(tmp_path / "items.sqlite")
        await store.init()
        now = datetime.now(UTC)
        old = item(
            "old",
            updated_at=now - timedelta(days=181),
            perspective_title="Old cached Perspective",
        )
        recent = item(
            "recent",
            updated_at=now - timedelta(days=1),
            perspective_title="Recent cached Perspective",
        )
        await store.save(old)
        await store.save(recent)

        assert await store.cleanup(before_days=180) == 1

        fetched_old = item("old", updated_at=now)
        fetched_recent = item("recent", updated_at=now)
        reconciled = await store.reconcile(now, [fetched_old, fetched_recent])
        assert reconciled[0] is fetched_old
        assert reconciled[0].ai_perspective is None
        assert reconciled[1].ai_perspective == recent.ai_perspective

    asyncio.run(scenario())
