"""Tests for main.py (FastAPI app, routes, dashboard, settings, and refresh endpoints)."""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from main import app, _market_cache


@pytest.fixture
def client():
    """Create a FastAPI TestClient instance."""
    with TestClient(app) as c:
        yield c


@patch("main.fetch_and_process_market")
def test_index_route(mock_fetch, client):
    """Test GET / dashboard route with populated market cache."""
    mock_fetch.return_value = {
        "status": "success",
        "fetched_at": "2026-10-16T12:00:00+00:00",
        "total_listings": 2,
        "steals_detected": 1,
        "notifications_sent": 0,
        "sol_usd": 150.0,
        "floors": {"rare": {"lamports": "1000000000", "usd": 10.0}},
        "listings": [
            {
                "id": "list_1",
                "capo": {"name": "Test Boss", "rarity": "legendary", "tier": "boss"},
                "total_stat": 90,
                "stat_bucket": 90,
                "_price_lamports": 5000000000,
                "_price_usd": 75.0,
                "fair_price_lamports": 10000000000,
                "benchmark_lamports": 9000000000,
                "deal_score": 85.0,
                "badge": "Steal",
                "explain": "🔥 Deal Score: 85.0",
            },
            {
                "id": "list_2",
                "capo": {"name": "Test Soldier", "rarity": "rare", "tier": "soldato"},
                "total_stat": 50,
                "stat_bucket": 50,
                "_price_lamports": 2000000000,
                "_price_usd": 30.0,
                "fair_price_lamports": 2000000000,
                "benchmark_lamports": 2000000000,
                "deal_score": 45.0,
                "badge": "Normal",
                "explain": "○ Deal Score: 45.0",
            },
        ],
    }

    # Populate cache
    _market_cache.update(mock_fetch.return_value)

    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Pawn Shop" in html
    assert "Test Boss" in html
    assert "Test Soldier" in html
    assert "🔥 Steal" in html


@patch("main.fetch_and_process_market")
def test_index_filtering(mock_fetch, client):
    """Test GET / with rarity and badge filter query parameters."""
    mock_fetch.return_value = {
        "status": "success",
        "fetched_at": "2026-10-16T12:00:00+00:00",
        "total_listings": 2,
        "steals_detected": 1,
        "sol_usd": 150.0,
        "listings": [
            {
                "id": "list_1",
                "capo": {"name": "Test Boss", "rarity": "legendary", "tier": "boss"},
                "total_stat": 90,
                "stat_bucket": 90,
                "_price_lamports": 5000000000,
                "_price_usd": 75.0,
                "deal_score": 85.0,
                "badge": "Steal",
                "explain": "🔥 Steal",
            },
            {
                "id": "list_2",
                "capo": {"name": "Test Soldier", "rarity": "rare", "tier": "soldato"},
                "total_stat": 50,
                "stat_bucket": 50,
                "_price_lamports": 2000000000,
                "_price_usd": 30.0,
                "deal_score": 45.0,
                "badge": "Normal",
                "explain": "Normal",
            },
        ],
    }
    _market_cache.update(mock_fetch.return_value)

    # Filter by legendary rarity
    resp = client.get("/?rarity=legendary")
    assert resp.status_code == 200
    assert "Test Boss" in resp.text
    assert "Test Soldier" not in resp.text

    # Filter by Steal badge
    resp2 = client.get("/?badge=Steal")
    assert resp2.status_code == 200
    assert "Test Boss" in resp2.text
    assert "Test Soldier" not in resp2.text


def test_settings_get(client):
    """Test GET /settings route."""
    response = client.get("/settings")
    assert response.status_code == 200
    assert "Application Settings" in response.text
    assert "ntfy_topic" in response.text


def test_settings_post(client):
    """Test POST /settings route for updating ntfy topic and headers."""
    response = client.post(
        "/settings",
        data={
            "ntfy_topic": "my-test-steals-topic",
            "headers_text": "Cookie: session=xyz\nAuthorization: Bearer token123",
        },
    )
    assert response.status_code == 200
    assert "Settings saved successfully" in response.text
    assert "my-test-steals-topic" in response.text


@patch("main.fetch_and_process_market")
def test_load_sample_endpoint(mock_fetch, client):
    """Test GET /settings/load-sample endpoint."""
    mock_fetch.return_value = {
        "status": "success",
        "fetched_at": "2026-10-16T12:00:00+00:00",
        "total_listings": 1,
        "steals_detected": 1,
        "sol_usd": 100.0,
        "listings": [],
    }
    response = client.get("/settings/load-sample", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    mock_fetch.assert_called_once()


@patch("main.fetch_and_process_market")
def test_api_refresh_endpoint(mock_fetch, client):
    """Test GET /api/refresh endpoint."""
    mock_fetch.return_value = {
        "status": "success",
        "fetched_at": "2026-10-16T12:30:00+00:00",
        "total_listings": 10,
        "steals_detected": 2,
        "notifications_sent": 1,
        "sol_usd": 120.0,
        "listings": [],
    }
    response = client.get("/api/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_listings"] == 10
    assert data["steals_detected"] == 2


@patch("main.fetch_and_process_market")
def test_index_price_filtering_and_sorting(mock_fetch, client):
    """Test GET / with min_price/max_price filtering and _price_usd sorting."""
    mock_fetch.return_value = {
        "status": "success",
        "fetched_at": "2026-10-16T12:00:00+00:00",
        "total_listings": 2,
        "steals_detected": 0,
        "sol_usd": 150.0,
        "listings": [
            {
                "id": "list_cheap",
                "capo": {"name": "Cheap Capo", "rarity": "rare", "tier": "recruit"},
                "total_stat": 40,
                "stat_bucket": 40,
                "_price_lamports": 1000000000,
                "priceUsd": 1.0,
                "allInUsd": 1.2,
                "_price_usd": 1.2,
                "deal_score": 50.0,
                "badge": "Normal",
                "explain": "Normal",
            },
            {
                "id": "list_expensive",
                "capo": {"name": "Expensive Capo", "rarity": "legendary", "tier": "boss"},
                "total_stat": 90,
                "stat_bucket": 90,
                "_price_lamports": 10000000000,
                "priceUsd": 10.0,
                "allInUsd": 12.0,
                "_price_usd": 12.0,
                "deal_score": 60.0,
                "badge": "Normal",
                "explain": "Normal",
            },
        ],
    }
    _market_cache.update(mock_fetch.return_value)

    # Test min_price filter
    resp = client.get("/?min_price=5.0")
    assert resp.status_code == 200
    assert "Expensive Capo" in resp.text
    assert "Cheap Capo" not in resp.text

    # Test max_price filter
    resp2 = client.get("/?max_price=5.0")
    assert resp2.status_code == 200
    assert "Cheap Capo" in resp2.text
    assert "Expensive Capo" not in resp2.text

