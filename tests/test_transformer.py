import asyncio
from datetime import UTC, datetime

import pytest
from models import Comment, Item, Perspective, Viewpoint
from perspective_generator import PerspectiveGenerationError
from transformer import Transformer


class FakePerspectiveGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[Comment]]] = []

    async def generate(self, title: str, comments: list[Comment]) -> Perspective:
        self.calls.append((title, comments))
        return Perspective(
            title="Offline result",
            summary="Generated without a network.",
            sentiment="mixed",
            viewpoints=[Viewpoint(statement="A fixture viewpoint", support_percentage=70)],
        )


class SelectivePerspectiveGenerator(FakePerspectiveGenerator):
    async def generate(self, title: str, comments: list[Comment]) -> Perspective:
        if title == "Generation fails":
            raise PerspectiveGenerationError("provider unavailable")
        return await super().generate(title=title, comments=comments)


class BrokenPerspectiveGenerator:
    async def generate(self, title: str, comments: list[Comment]) -> Perspective:
        raise AssertionError("unexpected implementation defect")


def test_transformer_generates_perspective_through_one_fakeable_seam() -> None:
    now = datetime(2026, 7, 17, tzinfo=UTC)
    comments = [Comment(author=f"reader-{index}", content=f"comment-{index}") for index in range(15)]
    item = Item(
        id="1",
        title="Testable transformation",
        url="https://example.test/1",
        comments=comments,
        created_at=now,
        updated_at=now,
    )
    generator = FakePerspectiveGenerator()

    transformed = asyncio.run(Transformer(perspective_generator=generator).transform(items=[item]))

    assert generator.calls == [("Testable transformation", comments)]
    assert transformed == [item]
    assert transformed[0].ai_perspective is not None
    assert transformed[0].ai_perspective.title == "Offline result"
    assert transformed[0].generated_at_comment_count == 15


def test_transformer_skips_failed_perspective_and_continues() -> None:
    now = datetime(2026, 7, 21, tzinfo=UTC)
    comments = [Comment(author=f"reader-{index}", content=f"comment-{index}") for index in range(15)]
    failed_item = Item(
        id="1",
        title="Generation fails",
        url="https://example.test/1",
        comments=comments,
        created_at=now,
        updated_at=now,
    )
    successful_item = Item(
        id="2",
        title="Generation succeeds",
        url="https://example.test/2",
        comments=comments,
        created_at=now,
        updated_at=now,
    )

    transformed = asyncio.run(
        Transformer(perspective_generator=SelectivePerspectiveGenerator()).transform(
            items=[failed_item, successful_item]
        )
    )

    assert transformed[0].ai_perspective is None
    assert transformed[0].generated_at_comment_count is None
    assert transformed[1].ai_perspective is not None
    assert transformed[1].ai_perspective.title == "Offline result"


def test_transformer_preserves_cached_perspective_when_refresh_fails() -> None:
    now = datetime(2026, 7, 21, tzinfo=UTC)
    cached_perspective = Perspective(
        title="Cached result",
        summary="Keep this when refresh fails.",
        sentiment="mixed",
        viewpoints=[Viewpoint(statement="A cached viewpoint", support_percentage=60)],
    )
    item = Item(
        id="1",
        title="Generation fails",
        url="https://example.test/1",
        comments=[Comment(author=f"reader-{index}", content=f"comment-{index}") for index in range(30)],
        created_at=now,
        updated_at=now,
        ai_perspective=cached_perspective,
        generated_at_comment_count=15,
    )

    transformed = asyncio.run(
        Transformer(perspective_generator=SelectivePerspectiveGenerator()).transform(items=[item])
    )

    assert transformed[0].ai_perspective == cached_perspective
    assert transformed[0].generated_at_comment_count == 15


def test_transformer_fails_fast_on_unexpected_generator_error() -> None:
    now = datetime(2026, 7, 21, tzinfo=UTC)
    item = Item(
        id="1",
        title="Broken generator",
        url="https://example.test/1",
        comments=[Comment(author=f"reader-{index}", content=f"comment-{index}") for index in range(15)],
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(AssertionError, match="unexpected implementation defect"):
        asyncio.run(Transformer(perspective_generator=BrokenPerspectiveGenerator()).transform(items=[item]))
