"""Data fetcher, HBDS algorithm scoring engine, and ntfy notification sender."""

import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

from db import (
    DB_PATH,
    get_connection,
    get_headers,
    get_lowest_price_by_bucket,
    init_db,
    save_price_history,
)

logger = logging.getLogger(__name__)

MARKET_API_URL = "https://thesyndicate.games/api/v3/market/listings"


def get_notified_deals(db_path: Path | str = DB_PATH) -> set[str]:
    """Retrieve set of already notified listing IDs."""
    init_notification_table(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT listing_id FROM notified_deals")
        return {row["listing_id"] for row in cursor.fetchall()}


def init_notification_table(db_path: Path | str = DB_PATH) -> None:
    """Ensure notified_deals table exists."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notified_deals (
                listing_id TEXT PRIMARY KEY,
                notified_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


def save_notified_deal(listing_id: str, db_path: Path | str = DB_PATH) -> None:
    """Record that a listing has been notified."""
    init_notification_table(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO notified_deals (listing_id, notified_at)
            VALUES (?, ?)
            """,
            (listing_id, now),
        )
        conn.commit()


def get_setting(key: str, default: Optional[str] = None, db_path: Path | str = DB_PATH) -> Optional[str]:
    """Retrieve a setting from settings table."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            );
            """
        )
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return row["value"]
    return default


def save_setting(key: str, value: str, db_path: Path | str = DB_PATH) -> None:
    """Save a setting."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            );
            """
        )
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, now),
        )
        conn.commit()


def calculate_hbds_scores(
    listings: List[Dict[str, Any]],
    floors: Dict[str, Dict[str, Any]],
    db_path: Path | str = DB_PATH,
    fetch_timestamp: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Calculate HBDS (Hedonic-Bayesian Deal Scoring) scores for all listings purely from active snapshot.
    
    Returns:
        (scored_listings, aggregates_for_db)
    """
    if not listings:
        return [], []

    if not fetch_timestamp:
        fetch_timestamp = datetime.now(timezone.utc).isoformat()

    # Ensure DB is initialized so queries won't fail if db_path tables don't exist yet
    init_db(db_path)

    processed = []
    rarity_stats: Dict[str, List[float]] = {}
    rarity_prices: Dict[str, List[float]] = {}
    rarity_vals: Dict[str, List[float]] = {}

    for item in listings:
        capo = item.get("capo", {})
        rarity = capo.get("rarity", "rare").lower()
        muscle = capo.get("stat_muscle", 0) or 0
        brains = capo.get("stat_brains", 0) or 0
        hustle = capo.get("stat_hustle", 0) or 0
        grit = capo.get("stat_grit", 0) or 0
        rep = capo.get("stat_rep", 0) or 0
        total_stat = muscle + brains + hustle + grit + rep

        stat_bucket = (total_stat // 10) * 10

        try:
            price_lamports = float(item.get("priceLamports", "0") or 0)
        except (ValueError, TypeError):
            price_lamports = 0.0

        try:
            all_in_lamports = float(item.get("allInLamports", "0") or item.get("gateLamports", "0") or 0)
        except (ValueError, TypeError):
            all_in_lamports = 0.0

        effective_lamports = all_in_lamports if all_in_lamports > 0 else price_lamports

        try:
            price_usd = float(item.get("priceUsd", "0.0") or 0.0)
        except (ValueError, TypeError):
            price_usd = 0.0

        try:
            all_in_usd = float(item.get("allInUsd", "0.0") or 0.0)
        except (ValueError, TypeError):
            all_in_usd = 0.0
        if all_in_usd <= 0:
            all_in_usd = price_usd

        item["priceUsd"] = price_usd
        item["allInUsd"] = all_in_usd
        if all_in_lamports > 0:
            item["allInLamports"] = all_in_lamports

        item["_total_stat"] = total_stat
        item["_stat_bucket"] = stat_bucket
        item["_price_lamports"] = effective_lamports
        item["_price_usd"] = all_in_usd
        item["_rarity"] = rarity

        if price_lamports > 0:
            rarity_stats.setdefault(rarity, []).append(float(total_stat))
            rarity_prices.setdefault(rarity, []).append(price_lamports)
            val_score = total_stat / price_lamports if price_lamports > 0 else 0.0
            rarity_vals.setdefault(rarity, []).append(val_score)

        processed.append(item)

    rarity_median_val: Dict[str, float] = {}
    rarity_median_stat: Dict[str, float] = {}
    for r, v_list in rarity_vals.items():
        if v_list:
            sorted_v = sorted(v_list)
            rarity_median_val[r] = sorted_v[len(sorted_v) // 2]
        else:
            rarity_median_val[r] = 1.0

    for r, s_list in rarity_stats.items():
        if s_list:
            sorted_s = sorted(s_list)
            rarity_median_stat[r] = sorted_s[len(sorted_s) // 2]
        else:
            rarity_median_stat[r] = 50.0

    # Step 1: OLS Regression per rarity
    ols_params: Dict[str, Tuple[float, float]] = {}
    for r, stats in rarity_stats.items():
        prices = rarity_prices[r]
        n = len(stats)
        floor_lamps = float(floors.get(r, {}).get("lamports", 0) or 0)

        if n > 1:
            mean_s = sum(stats) / n
            mean_p = sum(prices) / n
            var_s = sum((s - mean_s) ** 2 for s in stats)
            cov_sp = sum((stats[i] - mean_s) * (prices[i] - mean_p) for i in range(n))
            slope = max(0.0, cov_sp / var_s if var_s > 0 else 0.0)
            intercept = max(floor_lamps, mean_p - slope * mean_s)
        else:
            slope = 0.0
            intercept = floor_lamps if floor_lamps > 0 else (prices[0] if prices else 1000.0)

        ols_params[r] = (intercept, slope)

    bucket_batch_aggregates: Dict[Tuple[str, int], List[float]] = {}
    for item in processed:
        r = item["_rarity"]
        b = item["_stat_bucket"]
        p = item["_price_lamports"]
        if p > 0:
            bucket_batch_aggregates.setdefault((r, b), []).append(p)

    bucket_avg_lamports: Dict[Tuple[str, int], float] = {}
    aggregates_for_db = []
    for (r, b), prices in bucket_batch_aggregates.items():
        min_p = min(prices)
        avg_p = sum(prices) / len(prices)
        bucket_avg_lamports[(r, b)] = avg_p
        aggregates_for_db.append(
            {
                "rarity": r,
                "stat_bucket": b,
                "min_price": min_p,
                "avg_price": avg_p,
                "count": len(prices),
            }
        )

    scored_listings = []
    for item in processed:
        r = item["_rarity"]
        b = item["_stat_bucket"]
        s = item["_total_stat"]
        p = item["_price_lamports"]

        floor_lamps = float(floors.get(r, {}).get("lamports", 0) or 0)
        intercept, slope = ols_params.get(r, (floor_lamps, 0.0))
        fair_price = intercept + slope * s
        if fair_price <= 0:
            fair_price = floor_lamps if floor_lamps > 0 else 1000.0

        benchmark = bucket_avg_lamports.get((r, b), fair_price)
        if benchmark <= 0:
            benchmark = fair_price

        disc_fair = max(0.0, (fair_price - p) / fair_price) if fair_price > 0 else 0.0
        disc_bucket = max(0.0, (benchmark - p) / benchmark) if benchmark > 0 else 0.0

        median_val = rarity_median_val.get(r, 1.0)
        val_score = (s / p) if p > 0 else 0.0
        val_ratio = (val_score / median_val) if median_val > 0 else 1.0

        median_stat = rarity_median_stat.get(r, 50.0)
        if floor_lamps > 0 and p <= floor_lamps * 1.15 and s > median_stat:
            floor_bonus = min(1.0, (s - median_stat) / median_stat) if median_stat > 0 else 0.0
        else:
            floor_bonus = 0.0

        base_score = (
            min(40.0, disc_fair * 60.0) +
            min(35.0, disc_bucket * 50.0) +
            min(25.0, max(0.0, (val_ratio - 1.0) * 15.0))
        )
        if floor_bonus > 0:
            base_score = max(base_score, 50.0 + floor_bonus * 40.0)

        if disc_fair >= 0.99 or (floor_lamps > 0 and p <= floor_lamps * 0.1):
            base_score = max(base_score, 85.0)

        deal_score = round(min(100.0, max(0.0, base_score)), 1)

        if deal_score >= 80:
            badge = "Steal"
            badge_icon = "🔥"
        elif deal_score >= 65:
            badge = "Great Deal"
            badge_icon = "⚡"
        elif deal_score >= 50:
            badge = "Good Value"
            badge_icon = "✍️"
        else:
            badge = "Normal"
            badge_icon = "○"

        disc_fair_pct = round(disc_fair * 100, 1)
        disc_bucket_pct = round(disc_bucket * 100, 1)
        val_ratio_rnd = round(val_ratio, 1)

        explain = (
            f"{badge_icon} Deal Score: {deal_score} | "
            f"{disc_fair_pct}% below fair value | "
            f"{disc_bucket_pct}% below bucket avg | "
            f"{val_ratio_rnd}x stats-per-SOL vs peers"
        )

        item_copy = dict(item)
        item_copy["fair_price_lamports"] = round(fair_price, 2)
        item_copy["benchmark_lamports"] = round(benchmark, 2)
        item_copy["deal_score"] = deal_score
        item_copy["badge"] = badge
        item_copy["explain"] = explain
        item_copy["total_stat"] = s
        item_copy["stat_bucket"] = b

        scored_listings.append(item_copy)

    scored_listings.sort(key=lambda x: x["deal_score"], reverse=True)
    return scored_listings, aggregates_for_db


def send_ntfy_notification(topic: str, title: str, message: str, click_url: str = "https://thesyndicate.games/market") -> bool:
    """Send push notification via ntfy.sh."""
    if not topic:
        return False
    url = f"https://ntfy.sh/{topic.strip()}"
    try:
        payload = {
            "title": title,
            "message": message,
            "tags": ["fire", "money_bag"],
            "click": click_url,
            "priority": 4,  # high
        }
        response = httpx.post(url, json=payload, timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send ntfy notification to {topic}: {e}")
        return False


def fetch_and_process_market(db_path: Path | str = DB_PATH) -> Dict[str, Any]:
    """Fetch market data from API, save successful fetch to latest_market_data.json, fallback to latest_market_data.json, compute HBDS, save history, and trigger ntfy alerts."""
    init_db(db_path)
    headers_dict = get_headers(db_path)
    fetched_at = datetime.now(timezone.utc).isoformat()

    raw_data: Optional[Dict[str, Any]] = None
    fetch_success = False

    if headers_dict:
        try:
            with httpx.Client(headers=headers_dict, timeout=2.0) as client:
                resp = client.get(MARKET_API_URL)
                if resp.status_code == 200:
                    raw_data = resp.json()
                    fetch_success = True
                    if "PYTEST_CURRENT_TEST" not in os.environ:
                        try:
                            snapshot_path = Path(__file__).resolve().parent / "latest_market_data.json"
                            with open(snapshot_path, "w", encoding="utf-8") as f:
                                json.dump(raw_data, f, indent=2)
                            logger.info("Saved successful market data fetch to latest_market_data.json")
                        except Exception as e:
                            logger.warning(f"Failed to save latest_market_data.json snapshot: {e}")
                else:
                    logger.warning(f"Market API returned status code {resp.status_code}, falling back to snapshot data.")
        except Exception as e:
            logger.warning(f"Market API request failed: {e}, falling back to snapshot data.")

    if not fetch_success or not raw_data:
        snapshot_path = Path(__file__).resolve().parent / "latest_market_data.json"
        if snapshot_path.exists():
            sample_path = snapshot_path
        else:
            sample_path = Path(__file__).resolve().parent / "data2.json"
            if not sample_path.exists():
                sample_path = Path(__file__).resolve().parent / "data.json"
        
        if sample_path.exists():
            try:
                with open(sample_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                logger.info(f"Loaded market data from fallback file: {sample_path.name}")
            except Exception as e:
                logger.error(f"Failed to load fallback data file: {e}")
                return {"status": "error", "message": f"Failed to fetch market data and fallback load failed: {e}"}
        else:
            return {"status": "error", "message": "No API headers configured and no fallback snapshot/sample data file found."}

    listings = raw_data.get("listings", [])
    floors = raw_data.get("floors", {})
    sol_usd = raw_data.get("solUsd", 0.0)
    api_at = raw_data.get("at", fetched_at)

    scored_listings, aggregates = calculate_hbds_scores(listings, floors, db_path=db_path, fetch_timestamp=api_at)
    save_price_history(api_at, aggregates, db_path=db_path)

    valid_badges = {"steal", "great deal", "good value"}
    filtered_listings = [
        item for item in scored_listings
        if item.get("badge", "").strip().lower() in valid_badges
    ]

    if fetch_success and "PYTEST_CURRENT_TEST" not in os.environ:
        try:
            snapshot_path = Path(__file__).resolve().parent / "latest_market_data.json"
            snapshot_data = dict(raw_data)
            snapshot_data["listings"] = filtered_listings
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(snapshot_data, f, indent=2)
            logger.info("Saved successful market data fetch to latest_market_data.json")
        except Exception as e:
            logger.warning(f"Failed to save latest_market_data.json snapshot: {e}")

    ntfy_topic = get_setting("ntfy_topic", db_path=db_path)
    notified_deals = get_notified_deals(db_path)

    new_steals_count = 0
    if ntfy_topic:
        for item in scored_listings:
            if item["deal_score"] >= 80:
                listing_id = item.get("id")
                if listing_id and listing_id not in notified_deals:
                    capo = item.get("capo", {})
                    name = capo.get("name", "Unknown Capo")
                    rarity = capo.get("rarity", "rare")
                    tier = capo.get("tier", "recruit")
                    total_stat = item.get("total_stat", 0)
                    price_usd = item.get("allInUsd", item.get("priceUsd", 0.0))
                    score = item.get("deal_score", 0)

                    title = f"🔥 Steal Detected: {name}"
                    msg = (
                        f"Score {score} | {rarity.capitalize()} {tier.capitalize()} | "
                        f"Stat {total_stat} | ${price_usd:.2f} USD"
                    )
                    success = send_ntfy_notification(ntfy_topic, title, msg)
                    if success:
                        save_notified_deal(listing_id, db_path=db_path)
                        new_steals_count += 1

    return {
        "status": "success",
        "fetched_at": api_at,
        "total_listings": len(filtered_listings),
        "steals_detected": sum(1 for x in filtered_listings if x["deal_score"] >= 80),
        "notifications_sent": new_steals_count,
        "listings": filtered_listings,
        "floors": floors,
        "sol_usd": sol_usd,
    }
