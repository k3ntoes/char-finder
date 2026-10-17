"""Tests for fetcher.py and HBDS scoring algorithm."""

import tempfile
from pathlib import Path
import pytest

from db import init_db, save_headers, save_price_history
from fetcher import calculate_hbds_scores, fetch_and_process_market, send_ntfy_notification


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_char_finder.db"
        init_db(db_path)
        yield db_path


def test_calculate_hbds_scores_normal():
    listings = [
        {
            "id": "item-1",
            "priceLamports": "10000000",
            "priceUsd": 1.0,
            "capo": {
                "rarity": "rare",
                "tier": "recruit",
                "name": "Test Capo 1",
                "stat_muscle": 20,
                "stat_brains": 20,
                "stat_hustle": 20,
                "stat_grit": 20,
                "stat_rep": 20,
            },
        },
        {
            "id": "item-2",
            "priceLamports": "2000000",
            "priceUsd": 0.2,
            "capo": {
                "rarity": "rare",
                "tier": "recruit",
                "name": "Test Capo 2",
                "stat_muscle": 50,
                "stat_brains": 50,
                "stat_hustle": 50,
                "stat_grit": 50,
                "stat_rep": 50,
            },
        },
    ]
    floors = {"rare": {"lamports": "4000000", "usd": 0.4}}

    scored, aggregates = calculate_hbds_scores(listings, floors)
    assert len(scored) == 2
    assert scored[0]["id"] == "item-2"
    assert scored[0]["deal_score"] > scored[1]["deal_score"]
    assert len(aggregates) > 0


def test_calculate_hbds_scores_edge_cases(temp_db):
    listings = [
        {
            "id": "item-extreme",
            "priceLamports": "1",
            "priceUsd": 0.0001,
            "capo": {
                "rarity": "epic",
                "tier": "boss",
                "name": "Extreme Deal",
                "stat_muscle": 50,
                "stat_brains": 50,
                "stat_hustle": 50,
                "stat_grit": 50,
                "stat_rep": 50,
            },
        },
        {
            "id": "item-zero",
            "priceLamports": "0",
            "priceUsd": 0.0,
            "capo": {
                "rarity": "rare",
                "tier": "recruit",
                "name": "Zero Price",
                "stat_muscle": 10,
                "stat_brains": 10,
                "stat_hustle": 10,
                "stat_grit": 10,
                "stat_rep": 10,
            },
        },
    ]
    floors = {"epic": {"lamports": "50000000", "usd": 5.0}, "rare": {"lamports": "5000000", "usd": 0.5}}

    scored, aggregates = calculate_hbds_scores(listings, floors, db_path=temp_db)
    assert len(scored) == 2
    steal_item = next(x for x in scored if x["id"] == "item-extreme")
    assert steal_item["deal_score"] >= 75.0
    assert steal_item["badge"] in ("Great Deal", "Steal")


def test_fetch_and_process_market_fallback(temp_db):
    result = fetch_and_process_market(db_path=temp_db)
    assert result["status"] == "success"
    assert result["total_listings"] > 0
    assert "listings" in result
    assert "floors" in result


def test_calculate_hbds_scores_all_in_usd():
    listings = [
        {
            "id": "item-allin",
            "priceLamports": "5000000",
            "priceUsd": 0.5,
            "allInUsd": 0.75,
            "allInLamports": "7500000",
            "capo": {
                "rarity": "rare",
                "tier": "recruit",
                "name": "AllIn Capo",
                "stat_muscle": 20,
                "stat_brains": 20,
                "stat_hustle": 20,
                "stat_grit": 20,
                "stat_rep": 20,
            },
        }
    ]
    floors = {"rare": {"lamports": "4000000", "usd": 0.4}}
    scored, _ = calculate_hbds_scores(listings, floors)
    assert len(scored) == 1
    assert scored[0]["allInUsd"] == 0.75
    assert scored[0]["_price_usd"] == 0.75
    assert scored[0]["allInLamports"] == 7500000.0
    assert scored[0]["_price_lamports"] == 7500000.0


def test_fetch_and_process_market_filters_normal(temp_db):
    result = fetch_and_process_market(db_path=temp_db)
    assert result["status"] == "success"
    for item in result["listings"]:
        assert item["badge"] in ("Steal", "Great Deal", "Good Value")

