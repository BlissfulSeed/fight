import os
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "votes.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character TEXT NOT NULL CHECK(character IN ('left', 'right')),
    tx_hash TEXT UNIQUE,
    amount REAL DEFAULT 0,
    verified INTEGER DEFAULT 0,
    is_phantom INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_votes_character ON votes(character);
CREATE INDEX IF NOT EXISTS idx_votes_tx_hash ON votes(tx_hash);
"""


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA busy_timeout=5000")
    return db


async def init_db():
    db = await get_db()
    await db.executescript(SCHEMA)
    await db.close()


async def get_vote_counts():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT character, COUNT(*) as count FROM votes "
            "WHERE verified = 1 OR is_phantom = 1 GROUP BY character"
        )
        rows = await cursor.fetchall()
        return {row["character"]: row["count"] for row in rows}
    finally:
        await db.close()
