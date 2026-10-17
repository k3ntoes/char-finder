"""FastAPI application for Character Finder (Capo Finder).

Provides web routes for dashboard, filtering, settings, sample data loading, and API refresh.
"""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from db import get_headers, init_db, save_headers
from fetcher import fetch_and_process_market, get_setting, save_setting
from scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# In-memory cache for market listings and metrics
_market_cache: Dict[str, Any] = {
    "status": "idle",
    "listings": [],
    "floors": {},
    "sol_usd": 0.0,
    "fetched_at": "Never",
}


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: initialize DB, start background scheduler, and perform initial fetch."""
    logger.info("Initializing database and starting scheduler...")
    init_db()
    start_scheduler(interval_minutes=5)

    # Perform initial market fetch/load on startup
    try:
        result = fetch_and_process_market()
        if result.get("status") == "success":
            _market_cache.clear()
            _market_cache.update(result)
            logger.info(f"Startup market data loaded: {len(result.get('listings', []))} listings.")
    except Exception as e:
        logger.warning(f"Startup market fetch failed (will use fallback/empty cache): {e}")

    yield

    logger.info("Shutting down scheduler...")
    stop_scheduler()


app = FastAPI(
    title="Capo Finder",
    description="HBDS Deal Scoring & Market Monitor for The Syndicate",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse)
async def index_get(
    request: Request,
    rarity: Optional[str] = None,
    badge: Optional[str] = None,
    sort_by: Optional[str] = "deal_score",
    order: Optional[str] = "desc",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    """Render main dashboard with filtering and sorting."""
    listings = _market_cache.get("listings", [])
    if not listings:
        # If cache is empty, attempt to fetch/load
        try:
            result = fetch_and_process_market()
            if result.get("status") == "success":
                _market_cache.clear()
                _market_cache.update(result)
                listings = _market_cache.get("listings", [])
        except Exception as e:
            logger.error(f"Failed to fetch market data on index load: {e}")

    # Filter listings
    filtered = []
    for item in listings:
        capo = item.get("capo", {})
        item_rarity = capo.get("rarity", "").lower()
        item_badge = item.get("badge", "Normal")
        item_price_usd = item.get("_price_usd", item.get("allInUsd", item.get("priceUsd", 0.0)))

        if rarity and rarity.strip() and item_rarity != rarity.strip().lower():
            continue
        if badge and badge.strip() and item_badge != badge.strip():
            continue
        if min_price is not None and item_price_usd < min_price:
            continue
        if max_price is not None and item_price_usd > max_price:
            continue
        filtered.append(item)

    # Sort listings
    reverse_sort = order.lower() == "desc"
    if sort_by == "_price_lamports":
        filtered.sort(key=lambda x: x.get("_price_lamports", 0.0), reverse=reverse_sort)
    elif sort_by == "total_stat":
        filtered.sort(key=lambda x: x.get("total_stat", 0), reverse=reverse_sort)
    elif sort_by in ("_price_usd", "price", "allInUsd"):
        filtered.sort(key=lambda x: x.get("_price_usd", x.get("allInUsd", x.get("priceUsd", 0.0))), reverse=reverse_sort)
    else:  # default deal_score
        filtered.sort(key=lambda x: x.get("deal_score", 0.0), reverse=reverse_sort)

    total_listings = len(listings)
    steals_detected = sum(1 for x in listings if x.get("deal_score", 0) >= 80)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "total_listings": total_listings,
            "steals_detected": steals_detected,
            "sol_usd": _market_cache.get("sol_usd", 0.0),
            "floors": _market_cache.get("floors", {}),
            "fetched_at": _market_cache.get("fetched_at", "Never"),
            "listings": filtered,
            "selected_rarity": rarity or "",
            "selected_badge": badge or "",
            "sort_by": sort_by,
            "order": order,
            "min_price": min_price,
            "max_price": max_price,
        },
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request, message: Optional[str] = None):
    """Render settings page."""
    headers_dict = get_headers()
    headers_text = "\n".join(f"{k}: {v}" for k, v in headers_dict.items())
    ntfy_topic = get_setting("ntfy_topic") or ""

    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "headers_text": headers_text,
            "ntfy_topic": ntfy_topic,
            "message": message,
        },
    )


@app.post("/settings", response_class=HTMLResponse)
async def settings_post(
    request: Request,
    ntfy_topic: str = Form(""),
    headers_text: str = Form(""),
):
    """Save user settings (auth headers and ntfy topic)."""
    save_setting("ntfy_topic", ntfy_topic.strip())

    # Parse raw headers text (Line format: Header-Name: value)
    parsed_headers = {}
    for line in headers_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            parsed_headers[k.strip()] = v.strip()

    if parsed_headers:
        save_headers(parsed_headers, overwrite_all=True)

    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "headers_text": headers_text,
            "ntfy_topic": ntfy_topic.strip(),
            "message": "✅ Settings saved successfully!",
        },
    )


@app.post("/settings/load-sample")
@app.get("/settings/load-sample")
async def load_sample_data():
    """Load sample data (data2.json) into cache and database."""
    try:
        result = fetch_and_process_market()
        if result.get("status") == "success":
            _market_cache.clear()
            _market_cache.update(result)
            logger.info("Sample market data loaded successfully via /settings/load-sample.")
    except Exception as e:
        logger.error(f"Failed to load sample data: {e}")

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/refresh")
async def api_refresh():
    """Manual trigger to refresh market data from API or sample fallback, then redirect back to dashboard."""
    try:
        result = fetch_and_process_market()
        if result.get("status") == "success":
            _market_cache.clear()
            _market_cache.update(result)
            logger.info("Market data refreshed successfully via POST /refresh.")
    except Exception as e:
        logger.error(f"Error during manual market refresh: {e}")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/api/refresh")
@app.get("/api/refresh")
async def api_refresh_json():
    """API endpoint to trigger refresh and return JSON result."""
    try:
        result = fetch_and_process_market()
        if result.get("status") == "success":
            _market_cache.clear()
            _market_cache.update(result)
            logger.info("Market data refreshed successfully via /api/refresh.")
        return result
    except Exception as e:
        logger.error(f"Error during API market refresh: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
