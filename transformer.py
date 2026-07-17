from loguru import logger
from models import Item
from perspective_generator import (
    MIN_COMMENTS_FOR_PERSPECTIVE,
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
        if item.ai_perspective and needs_refresh(item):
            logger.info(
                "Comments changed from {} to {}; refreshing Perspective for {!r}",
                item.generated_at_comment_count,
                len(item.comments),
                item.title,
            )
            item.ai_perspective = None

        if item.ai_perspective:
            return

        if len(item.comments) < MIN_COMMENTS_FOR_PERSPECTIVE:
            logger.info(
                "Skipping Perspective for {!r}: {} comments is below minimum {}",
                item.title,
                len(item.comments),
                MIN_COMMENTS_FOR_PERSPECTIVE,
            )
            return

        item.ai_perspective = await self._perspective_generator.generate(title=item.title, comments=item.comments)
        item.generated_at_comment_count = len(item.comments)
