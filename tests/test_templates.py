"""Unit tests for Jinja2 templates (templates/base.html and templates/index.html)."""

from pathlib import Path
import pytest
from jinja2 import Environment, FileSystemLoader


@pytest.fixture
def jinja_env():
    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    return Environment(loader=FileSystemLoader(str(templates_dir)))


def test_index_template_empty_state(jinja_env):
    template = jinja_env.get_template("index.html")
    html = template.render(
        total_listings=0,
        steals_detected=0,
        sol_usd=150.0,
        fetched_at="2026-10-16T12:00:00+00:00",
        listings=[],
        selected_rarity="",
        selected_badge="",
    )

    assert "Pawn Shop" in html
    assert "No Capo Listings Found" in html
    assert "🔄 Refresh" in html
    assert "sol_usd" in html or "$150.00" in html


def test_index_template_populated_state(jinja_env):
    template = jinja_env.get_template("index.html")
    mock_listings = [
        {
            "id": "listing_001_long_uuid_string",
            "capo": {
                "name": "Don Corleone",
                "rarity": "legendary",
                "tier": "boss",
            },
            "total_stat": 95,
            "stat_bucket": 90,
            "_price_lamports": 5000000000,  # 5 SOL
            "_price_usd": 750.0,
            "fair_price_lamports": 10000000000,  # 10 SOL
            "benchmark_lamports": 9000000000,
            "deal_score": 92.5,
            "badge": "Steal",
            "explain": "🔥 Deal Score: 92.5 | 50.0% below fair value",
        },
        {
            "id": "listing_002_uuid",
            "capo": {
                "name": "Paulie Walnuts",
                "rarity": "rare",
                "tier": "soldato",
            },
            "total_stat": 65,
            "stat_bucket": 60,
            "_price_lamports": 3000000000,
            "_price_usd": 450.0,
            "fair_price_lamports": 3500000000,
            "benchmark_lamports": 3400000000,
            "deal_score": 70.0,
            "badge": "Great Deal",
            "explain": "⚡ Deal Score: 70.0 | 14.3% below fair value",
        },
        {
            "id": "listing_003_uuid",
            "capo": {
                "name": "Silvio Dante",
                "rarity": "common",
                "tier": "recruit",
            },
            "total_stat": 40,
            "stat_bucket": 40,
            "_price_lamports": 1000000000,
            "_price_usd": 150.0,
            "fair_price_lamports": 1050000000,
            "benchmark_lamports": 1020000000,
            "deal_score": 45.0,
            "badge": "Normal",
            "explain": "○ Deal Score: 45.0 | Normal value",
        },
    ]

    html = template.render(
        total_listings=3,
        steals_detected=1,
        sol_usd=150.0,
        fetched_at="2026-10-16T12:00:00+00:00",
        listings=mock_listings,
        selected_rarity="legendary",
        selected_badge="Steal",
    )

    assert "Don Corleone" in html
    assert "Paulie Walnuts" in html
    assert "Silvio Dante" in html
    assert "🔥 Steal" in html
    assert "⚡ Great Deal" in html
    assert "Normal" in html
    assert "5.000 SOL" in html
    assert "92.5" in html
    assert "list-view" in html
