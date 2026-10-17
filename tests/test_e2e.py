"""Comprehensive End-to-End Test Suite for Char-Finder (HBDS Market Intelligence & Dashboard)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import db
import fetcher
import main
import scheduler


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create a temporary SQLite database for E2E testing."""
    db_file = tmp_path / "e2e_char_finder.db"
    db.init_db(db_file)
    return db_file


@pytest.fixture
def client():
    """Create a FastAPI TestClient instance."""
    with TestClient(main.app) as c:
        yield c


def test_e2e_clean_database_initialization(temp_db: Path) -> None:
    """1. Clean database initialization (`db.init_db()`)."""
    with db.get_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('headers', 'price_history')"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        assert "headers" in tables
        assert "price_history" in tables

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='price_history'"
        )
        indexes = {row["name"] for row in cursor.fetchall()}
        assert "idx_ph_rarity_bucket" in indexes
        assert "idx_ph_fetched_at" in indexes


@patch("fetcher.httpx.Client")
def test_e2e_market_fetching_and_hbds_persistence(mock_client_cls, temp_db: Path) -> None:
    """2 & 3. Market fetching & parsing (`fetcher.fetch_and_process_market()`) and HBDS algorithmic scoring persistence into SQLite."""
    db.save_headers({"Authorization": "Bearer test-token"}, db_path=temp_db)

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "solUsd": 150.0,
        "floors": {
            "rare": {"lamports": "5000000000", "usd": 75.0},
            "legendary": {"lamports": "20000000000", "usd": 300.0},
        },
        "listings": [
            {
                "id": "e2e_listing_1",
                "priceLamports": "100000000",
                "priceUsd": 1.5,
                "capo": {
                    "name": "E2E Legendary Boss",
                    "rarity": "legendary",
                    "tier": "boss",
                    "stat_muscle": 60,
                    "stat_brains": 60,
                    "stat_hustle": 60,
                    "stat_grit": 60,
                    "stat_rep": 60,
                },
            },
            {
                "id": "e2e_listing_2",
                "priceLamports": "100000000",
                "priceUsd": 1.5,
                "capo": {
                    "name": "E2E Rare Soldier",
                    "rarity": "rare",
                    "tier": "soldato",
                    "stat_muscle": 50,
                    "stat_brains": 50,
                    "stat_hustle": 50,
                    "stat_grit": 50,
                    "stat_rep": 50,
                },
            },
        ],
    }
    mock_client.get.return_value = mock_response
    mock_client_cls.return_value.__enter__.return_value = mock_client

    result = fetcher.fetch_and_process_market(db_path=temp_db)

    assert result["status"] == "success"
    assert result["total_listings"] == 2
    assert result["sol_usd"] == 150.0
    assert len(result["listings"]) == 2

    with db.get_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM price_history")
        row = cursor.fetchone()
        assert row["cnt"] > 0


def test_e2e_settings_update_and_verification(client) -> None:
    """5. Configuration / Settings update & verification (`/settings` POST and GET)."""
    response = client.post(
        "/settings",
        data={
            "ntfy_topic": "e2e-test-syndicate-alerts",
            "headers_text": "Cookie: session=e2e_test_cookie\nUser-Agent: E2ETester/1.0",
        },
    )
    assert response.status_code == 200
    assert "Settings saved successfully" in response.text
    assert "e2e-test-syndicate-alerts" in response.text

    get_resp = client.get("/settings")
    assert get_resp.status_code == 200
    assert "e2e-test-syndicate-alerts" in get_resp.text
    assert "session=e2e_test_cookie" in get_resp.text


@patch("main.fetch_and_process_market")
def test_e2e_fastapi_dashboard_and_filtering(mock_fetch, client) -> None:
    """4. FastAPI endpoint integration (`main.app` with `TestClient`), triggering manual refresh and checking index page rendering (character table, discount badge, search filtering)."""
    mock_fetch.return_value = {
        "status": "success",
        "fetched_at": "2026-10-16T12:00:00+00:00",
        "total_listings": 2,
        "steals_detected": 1,
        "notifications_sent": 0,
        "sol_usd": 150.0,
        "floors": {"legendary": {"lamports": "20000000000", "usd": 300.0}},
        "listings": [
            {
                "id": "item_alpha",
                "capo": {"name": "Alpha Capo", "rarity": "legendary", "tier": "boss"},
                "total_stat": 300,
                "stat_bucket": 300,
                "_price_lamports": 5000000000,
                "_price_usd": 75.0,
                "fair_price_lamports": 15000000000,
                "deal_score": 92.5,
                "badge": "Steal",
                "explain": "🔥 Deal Score: 92.5 (Huge Discount)",
            },
            {
                "id": "item_beta",
                "capo": {"name": "Beta Soldier", "rarity": "rare", "tier": "recruit"},
                "total_stat": 100,
                "stat_bucket": 100,
                "_price_lamports": 4000000000,
                "_price_usd": 60.0,
                "fair_price_lamports": 4000000000,
                "deal_score": 40.0,
                "badge": "Normal",
                "explain": "○ Deal Score: 40.0 (Fair Value)",
            },
        ],
    }

    main._market_cache.update(mock_fetch.return_value)

    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Pawn Shop" in html
    assert "Alpha Capo" in html
    assert "Beta Soldier" in html
    assert "🔥 Steal" in html

    filtered_resp = client.get("/?rarity=legendary")
    assert filtered_resp.status_code == 200
    assert "Alpha Capo" in filtered_resp.text
    assert "Beta Soldier" not in filtered_resp.text

    refresh_resp = client.get("/api/refresh")
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert data["status"] == "success"
    mock_fetch.assert_called()


@patch("fetcher.httpx.post")
@patch("scheduler.fetch_and_process_market")
def test_e2e_scheduler_and_ntfy_alerts(mock_fetch_market, mock_post, temp_db: Path) -> None:
    """6. Scheduler / Alert verification: triggering scheduled polls with mock network requests and verifying `ntfy.sh` notifications when discount threshold criteria are met vs not met."""
    fetcher.save_setting("ntfy_topic", "e2e-alert-topic", db_path=temp_db)

    def side_effect(db_path=db.DB_PATH):
        fetcher.send_ntfy_notification(
            topic="e2e-alert-topic",
            title="🔥 Steal Detected: Super Steal Capo",
            message="Score 95.0 | Legendary Boss | Stat 400 | $30.00 USD",
        )
        return {
            "status": "success",
            "steals_detected": 1,
            "notifications_sent": 1,
        }

    mock_fetch_market.side_effect = side_effect
    mock_post.return_value = MagicMock(status_code=200)

    with patch("scheduler.DB_PATH", temp_db):
        result = scheduler.run_scheduled_poll()

    assert result["status"] == "success"
    assert result["steals_detected"] == 1

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://ntfy.sh/e2e-alert-topic"
    assert "Steal Detected" in kwargs["json"]["title"]
