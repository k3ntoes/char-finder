"""Tests for db.py database schema and storage handler."""

from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from db import (
    init_db,
    get_connection,
    save_headers,
    get_headers,
    save_price_history,
    get_avg_price_by_rarity,
    get_lowest_price_by_bucket,
    cleanup_old_history,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_file = tmp_path / "test_char_finder.db"
    init_db(db_file)
    return db_file


def test_init_db(temp_db: Path) -> None:
    """Test database initialization creates expected tables and indexes."""
    conn = get_connection(temp_db)
    cursor = conn.cursor()
    
    # Check tables exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('headers', 'price_history')"
    )
    tables = {row["name"] for row in cursor.fetchall()}
    assert tables == {"headers", "price_history"}
    
    # Check indexes exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='price_history'"
    )
    indexes = {row["name"] for row in cursor.fetchall()}
    assert "idx_ph_rarity_bucket" in indexes
    assert "idx_ph_fetched_at" in indexes
    
    conn.close()


def test_headers_crud(temp_db: Path) -> None:
    """Test saving and retrieving headers, including overwrite behavior."""
    headers1 = {"User-Agent": "Mozilla/5.0", "Cookie": "session=123"}
    save_headers(headers1, overwrite_all=True, db_path=temp_db)
    
    retrieved = get_headers(temp_db)
    assert retrieved == {"Cookie": "session=123", "User-Agent": "Mozilla/5.0"}
    
    # Test update/overwrite with new headers
    headers2 = {"Authorization": "Bearer token456"}
    save_headers(headers2, overwrite_all=True, db_path=temp_db)
    retrieved2 = get_headers(temp_db)
    assert retrieved2 == {"Authorization": "Bearer token456"}


def test_price_history_operations(temp_db: Path) -> None:
    """Test saving price history and querying averages and lowest prices."""
    aggregates1 = [
        {"rarity": "Epic", "stat_bucket": 10, "min_price": 100.0, "avg_price": 150.0, "count": 5},
        {"rarity": "Legendary", "stat_bucket": 20, "min_price": 500.0, "avg_price": 600.0, "count": 2},
    ]
    save_price_history("2026-10-16T10:00:00Z", aggregates1, db_path=temp_db)
    
    aggregates2 = [
        {"rarity": "Epic", "stat_bucket": 10, "min_price": 80.0, "avg_price": 120.0, "count": 4},
        {"rarity": "Legendary", "stat_bucket": 20, "min_price": 450.0, "avg_price": 550.0, "count": 3},
    ]
    save_price_history("2026-10-16T11:00:00Z", aggregates2, db_path=temp_db)

    # Test get_avg_price_by_rarity
    avg_epic = get_avg_price_by_rarity("Epic", last_n=24, db_path=temp_db)
    # Average of 150.0 and 120.0 = 135.0
    assert avg_epic == pytest.approx(135.0)

    # Test exclude_fetched_at
    avg_epic_excluded = get_avg_price_by_rarity("Epic", last_n=24, exclude_fetched_at="2026-10-16T11:00:00Z", db_path=temp_db)
    assert avg_epic_excluded == pytest.approx(150.0)

    # Test get_lowest_price_by_bucket
    min_leg = get_lowest_price_by_bucket("Legendary", 20, last_n=24, db_path=temp_db)
    # Min of 500.0 and 450.0 = 450.0
    assert min_leg == pytest.approx(450.0)


def test_edge_cases(temp_db: Path) -> None:
    """Test edge cases: empty aggregates, missing records, null/empty queries."""
    # Empty aggregates list should not fail
    save_price_history("2026-10-16T12:00:00Z", [], db_path=temp_db)

    # Querying non-existent rarity/bucket should return None
    assert get_avg_price_by_rarity("NonExistent", db_path=temp_db) is None
    assert get_lowest_price_by_bucket("Epic", 999, db_path=temp_db) is None

    # Empty headers query
    conn = get_connection(temp_db)
    conn.execute("DELETE FROM headers")
    conn.commit()
    conn.close()
    assert get_headers(temp_db) == {}


def test_cleanup_old_history(temp_db: Path) -> None:
    """Test cleanup of old price history beyond keep_last_n."""
    # Insert multiple history records for same rarity/bucket
    for i in range(10):
        aggregates = [{"rarity": "Rare", "stat_bucket": 5, "min_price": float(10 + i), "avg_price": float(20 + i), "count": 1}]
        save_price_history(f"2026-10-16T10:0{i}:00Z", aggregates, db_path=temp_db)

    # Cleanup keeping only last 3
    cleanup_old_history(keep_last_n=3, db_path=temp_db)

    # Verify count in db
    conn = get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM price_history WHERE rarity = 'Rare'")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 3
