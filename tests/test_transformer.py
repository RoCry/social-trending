import asyncio
from datetime import UTC, datetime

from models import Comment, Item, Perspective, Viewpoint
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

    transformed = asyncio.run(Transformer(generator).transform([item]))

    assert generator.calls == [("Testable transformation", comments)]
    assert transformed == [item]
    assert transformed[0].ai_perspective is not None
    assert transformed[0].ai_perspective.title == "Offline result"
    assert transformed[0].generated_at_comment_count == 15
