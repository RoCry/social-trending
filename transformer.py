from loguru import logger
from models import Item
from perspective_generator import (
    MIN_COMMENTS_FOR_PERSPECTIVE,
    PerspectiveGenerationError,
    PerspectiveGenerator,
    needs_refresh,
)


class Transformer:
    def __init__(self, perspective_generator: PerspectiveGenerator) -> None:
        self._perspective_generator = perspective_generator

    async def transform(self, items: list[Item]) -> list[Item]:
        for item in items:
            await self._transform_item(item)
        return items

    async def _transform_item(self, item: Item) -> None:
        refreshing = item.ai_perspective is not None and needs_refresh(item)
        if refreshing:
            logger.info(
                "Comments changed from {} to {}; refreshing Perspective for {!r}",
                item.generated_at_comment_count,
                len(item.comments),
                item.title,
            )

        if item.ai_perspective is not None and not refreshing:
            return

        if len(item.comments) < MIN_COMMENTS_FOR_PERSPECTIVE:
            logger.info(
                "Skipping Perspective for {!r}: {} comments is below minimum {}",
                item.title,
                len(item.comments),
                MIN_COMMENTS_FOR_PERSPECTIVE,
            )
            return

        try:
            perspective = await self._perspective_generator.generate(title=item.title, comments=item.comments)
        except PerspectiveGenerationError:
            logger.exception("Skipping Perspective for {!r}: generation failed", item.title)
            return
        item.ai_perspective = perspective
        item.generated_at_comment_count = len(item.comments)
