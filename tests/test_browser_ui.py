"""Tests for browser UI / dashboard interactions using FastAPI TestClient."""

from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app


@patch("main.fetch_and_process_market")
def test_refresh_button_browser(mock_fetch):
    """Test dashboard rendering, table headers, and manual refresh action via TestClient."""
    mock_fetch.return_value = {
        "status": "success",
        "listings": [{
            "id": "1",
            "capo": {"name": "Test", "rarity": "rare", "tier": "boss"},
            "total_stat": 80,
            "_price_usd": 10.0,
            "badge": "Normal",
            "explain": "Test"
        }],
        "floors": {}
    }
    with TestClient(app) as client:
        # 1. Open dashboard root URL
        response = client.get("/")
        assert response.status_code == 200
        html = response.text
        assert "Pawn Shop" in html
        assert "listings" in html.lower()
        assert "status" in html.lower()  # Table column header check

        # 2. Simulate manual refresh action via API /api/refresh (returning JSON response { "status": "success" })
        response_refresh = client.get("/api/refresh")
        assert response_refresh.status_code == 200
        data = response_refresh.json()
        assert data.get("status") == "success"

        # 3. Verify that dashboard page displays UI correctly after refresh
        response_home = client.get("/")
        assert response_home.status_code == 200
        html_home = response_home.text
        assert "Pawn Shop" in html_home
        assert "listings" in html_home.lower()
        assert "status" in html_home.lower()
