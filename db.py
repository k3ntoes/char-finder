"""SQLite database handler for Character Finder.

Provides schema creation, header storage, and price history tracking.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "DB_PATH",
    "get_connection",
    "init_db",
    "save_headers",
    "get_headers",
    "save_price_history",
    "get_avg_price_by_rarity",
    "get_lowest_price_by_bucket",
    "cleanup_old_history",
]

DB_PATH: Path = Path(__file__).resolve().parent / "char_finder.db"


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Create and return a SQLite database connection with row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Initialize database tables and indexes."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS headers (
              key TEXT PRIMARY KEY,
              value TEXT,
              updated_at TEXT
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              fetched_at TEXT NOT NULL,
              rarity TEXT NOT NULL,
              stat_bucket INTEGER NOT NULL,
              min_price REAL NOT NULL,
              avg_price REAL NOT NULL,
              count INTEGER NOT NULL
            );
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ph_rarity_bucket
            ON price_history(rarity, stat_bucket);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ph_fetched_at
            ON price_history(fetched_at);
            """
        )
        conn.commit()


def save_headers(
    headers_dict: dict[str, str],
    overwrite_all: bool = True,
    db_path: Path | str = DB_PATH,
) -> None:
    """Save or update API headers.
    
    If overwrite_all is True, removes previous headers and stores the new set.
    """
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if overwrite_all:
            cursor.execute("DELETE FROM headers")
        for key, value in headers_dict.items():
            cursor.execute(
                """
                INSERT INTO headers (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                  value = excluded.value,
                  updated_at = excluded.updated_at
                """,
                (key.strip(), value.strip(), now),
            )
        conn.commit()


def get_headers(db_path: Path | str = DB_PATH) -> dict[str, str]:
    """Retrieve all saved headers as a key-value dictionary."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM headers ORDER BY key ASC")
        rows = cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}


def save_price_history(
    fetched_at: str,
    aggregates: list[dict[str, Any]],
    db_path: Path | str = DB_PATH,
) -> None:
    """Save aggregated price data for a fetch cycle.
    
    Each aggregate dict must contain:
    - rarity (str)
    - stat_bucket (int)
    - min_price (float)
    - avg_price (float)
    - count (int)
    """
    if not aggregates:
        return

    records = [
        (
            fetched_at,
            str(agg["rarity"]),
            int(agg["stat_bucket"]),
            float(agg["min_price"]),
            float(agg["avg_price"]),
            int(agg["count"]),
        )
        for agg in aggregates
    ]

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO price_history (
                fetched_at,
                rarity,
                stat_bucket,
                min_price,
                avg_price,
                count
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            records,
        )
        conn.commit()


def get_avg_price_by_rarity(
    rarity: str,
    last_n: int = 24,
    exclude_fetched_at: str | None = None,
    db_path: Path | str = DB_PATH,
) -> float | None:
    """Compute average of avg_price from last N fetch cycles for this rarity.
    
    If exclude_fetched_at is specified, excludes that fetch cycle from the query.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if exclude_fetched_at:
            cursor.execute(
                """
                SELECT AVG(avg_price) FROM price_history
                WHERE rarity = ? AND fetched_at != ?
                AND fetched_at IN (
                    SELECT DISTINCT fetched_at FROM price_history
                    WHERE rarity = ? AND fetched_at != ?
                    ORDER BY fetched_at DESC
                    LIMIT ?
                )
                """,
                (rarity, exclude_fetched_at, rarity, exclude_fetched_at, last_n),
            )
        else:
            cursor.execute(
                """
                SELECT AVG(avg_price) FROM price_history
                WHERE rarity = ?
                AND fetched_at IN (
                    SELECT DISTINCT fetched_at FROM price_history
                    WHERE rarity = ?
                    ORDER BY fetched_at DESC
                    LIMIT ?
                )
                """,
                (rarity, rarity, last_n),
            )
        row = cursor.fetchone()
        if row and row[0] is not None:
            return float(row[0])
        return None


def get_lowest_price_by_bucket(
    rarity: str,
    stat_bucket: int,
    last_n: int = 24,
    exclude_fetched_at: str | None = None,
    db_path: Path | str = DB_PATH,
) -> float | None:
    """Retrieve minimum of min_price from last N fetch cycles for rarity+bucket.
    
    If exclude_fetched_at is specified, excludes that fetch cycle from the query.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if exclude_fetched_at:
            cursor.execute(
                """
                SELECT MIN(min_price) FROM (
                    SELECT min_price FROM price_history
                    WHERE rarity = ? AND stat_bucket = ? AND fetched_at != ?
                    ORDER BY fetched_at DESC
                    LIMIT ?
                )
                """,
                (rarity, stat_bucket, exclude_fetched_at, last_n),
            )
        else:
            cursor.execute(
                """
                SELECT MIN(min_price) FROM (
                    SELECT min_price FROM price_history
                    WHERE rarity = ? AND stat_bucket = ?
                    ORDER BY fetched_at DESC
                    LIMIT ?
                )
                """,
                (rarity, stat_bucket, last_n),
            )
        row = cursor.fetchone()
        if row and row[0] is not None:
            return float(row[0])
        return None


def cleanup_old_history(
    keep_last_n: int = 100,
    db_path: Path | str = DB_PATH,
) -> None:
    """Delete oldest price_history rows beyond keep_last_n per (rarity, stat_bucket)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM price_history
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY rarity, stat_bucket
                        ORDER BY fetched_at DESC, id DESC
                    ) AS rn
                    FROM price_history
                )
                WHERE rn > ?
            )
            """,
            (keep_last_n,),
        )
        conn.commit()
