from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Optional

import aiosqlite
from utils import logger
from models import Item

ITEM_TABLE_NAME = "item"

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {ITEM_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload TEXT NOT NULL
)
"""

CREATE_INDEXES_SQL = [
    f"CREATE INDEX IF NOT EXISTS idx_{ITEM_TABLE_NAME}_updated_at ON {ITEM_TABLE_NAME}(updated_at)",
]


class Database:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)

    async def init(self):
        """Initialize database and create tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_TABLE_SQL)
            for index_sql in CREATE_INDEXES_SQL:
                await db.execute(index_sql)
            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")

    async def upsert_item(self, item: Item) -> None:
        """Insert or update an item in the database."""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if item exists
            async with db.execute(
                f"SELECT created_at FROM {ITEM_TABLE_NAME} WHERE id = ?", (item.id,)
            ) as cursor:
                existing = await cursor.fetchone()

            if existing:
                # Update existing item
                await db.execute(
                    f"UPDATE {ITEM_TABLE_NAME} SET updated_at = CURRENT_TIMESTAMP, payload = ? WHERE id = ?",
                    (item.model_dump_json(), item.id),
                )
            else:
                # Insert new item
                await db.execute(
                    f"INSERT INTO {ITEM_TABLE_NAME} (id, payload) VALUES (?, ?)",
                    (item.id, item.model_dump_json()),
                )

            await db.commit()

    async def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                f"SELECT payload FROM {ITEM_TABLE_NAME} WHERE id = ?", (item_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Item.model_validate_json(row[0])
        return None

    async def cleanup(self, before_days: int = 30) -> int:
        """Delete items older than specified days. Returns number of items deleted."""
        cutoff_date = datetime.now(UTC) - timedelta(days=before_days)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                f"DELETE FROM {ITEM_TABLE_NAME} WHERE updated_at < ?",
                (cutoff_date.isoformat(),),
            ) as cursor:
                deleted_count = cursor.rowcount
                await db.commit()
                logger.info(
                    f"Cleaned up {deleted_count} items older than {before_days} days"
                )
                return deleted_count
