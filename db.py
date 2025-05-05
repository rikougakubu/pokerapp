# db.py
import aiosqlite
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

DB_PATH = Path("hand.db")

class HandRecord(BaseModel):
    hand: str                 # AsKs
    preflop: str              # RAISE / 3BET ...
    position: str             # IP / OOP
    flop_action: str
    flop_value: str | None
    turn_action: str
    turn_value: str | None
    river_action: str
    river_value: str | None
    created_at: datetime = datetime.utcnow()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS hands (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hand TEXT,
  preflop TEXT,
  position TEXT,
  flop_action TEXT,
  flop_value TEXT,
  turn_action TEXT,
  turn_value TEXT,
  river_action TEXT,
  river_value TEXT,
  created_at TEXT
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(SCHEMA_SQL)
        await db.commit()

async def insert_record(rec: HandRecord):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO hands VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
            rec.model_dump().values()
        )
        await db.commit()

async def fetch_all(where: str = "", params: tuple = ()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(f"SELECT * FROM hands {where}", params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
