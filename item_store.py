from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite
from loguru import logger
from models import Item

ITEM_TABLE_NAME = "item"

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {ITEM_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    payload TEXT NOT NULL
)
"""


class ItemStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as database:
            await database.execute(CREATE_TABLE_SQL)
            await database.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{ITEM_TABLE_NAME}_updated_at ON {ITEM_TABLE_NAME}(updated_at)"
            )
            await database.commit()
        logger.info("ItemStore initialized at {}", self.path)

    async def reconcile(self, now: datetime, fetched: list[Item]) -> list[Item]:
        reconciled: list[Item] = []
        for fresh_item in fetched:
            cached_item = await self._get(fresh_item.id)
            if cached_item is None:
                reconciled.append(fresh_item)
                continue
            reconciled.append(cached_item.model_copy(update={"comments": fresh_item.comments, "updated_at": now}))
        return reconciled

    async def save(self, item: Item) -> None:
        async with aiosqlite.connect(self.path) as database:
            await database.execute(
                f"""
                INSERT INTO {ITEM_TABLE_NAME} (id, created_at, updated_at, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    payload = excluded.payload
                """,
                (
                    item.id,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                    item.model_dump_json(),
                ),
            )
            await database.commit()

    async def cleanup(self, before_days: int = 180) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=before_days)
        async with aiosqlite.connect(self.path) as database:
            cursor = await database.execute(
                f"DELETE FROM {ITEM_TABLE_NAME} WHERE updated_at < ?",
                (cutoff.isoformat(),),
            )
            await database.commit()
            deleted_count = cursor.rowcount
        logger.info("Cleaned up {} Items older than {} days", deleted_count, before_days)
        return deleted_count

    async def _get(self, item_id: str) -> Item | None:
        async with aiosqlite.connect(self.path) as database:
            cursor = await database.execute(f"SELECT payload FROM {ITEM_TABLE_NAME} WHERE id = ?", (item_id,))
            row = await cursor.fetchone()
        return Item.model_validate_json(row[0]) if row else None
