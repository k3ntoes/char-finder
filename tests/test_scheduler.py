"""Tests for scheduler.py (APScheduler background job and ntfy alerting)."""

from unittest.mock import MagicMock, patch

import pytest

from scheduler import (
    get_scheduler_status,
    run_scheduled_poll,
    send_ntfy_alert,
    start_scheduler,
    stop_scheduler,
)


def test_send_ntfy_alert_success():
    """Test successful ntfy push notification sending with proper headers and payload."""
    with patch("httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        success = send_ntfy_alert(
            topic="my-test-topic",
            title="🔥 Steal Alert",
            message="Capo priced 40% below fair value",
            tags="fire,money_bag",
            priority="high",
            click_url="https://thesyndicate.games/market",
        )

        assert success is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://ntfy.sh/my-test-topic"
        payload = kwargs["json"]
        assert payload["title"] == "🔥 Steal Alert"
        assert payload["message"] == "Capo priced 40% below fair value"
        assert payload["tags"] == ["fire", "money_bag"]
        assert payload["priority"] == 4
        assert payload["click"] == "https://thesyndicate.games/market"


def test_send_ntfy_alert_empty_topic():
    """Test that empty topic returns False without sending."""
    success = send_ntfy_alert(topic="", title="Title", message="Msg")
    assert success is False

    success_whitespace = send_ntfy_alert(topic="   ", title="Title", message="Msg")
    assert success_whitespace is False


def test_send_ntfy_alert_network_failure():
    """Test resilience against network errors when calling ntfy.sh."""
    with patch("httpx.post", side_effect=Exception("Connection refused")):
        success = send_ntfy_alert(topic="my-test-topic", title="Title", message="Msg")
        assert success is False


def test_scheduler_lifecycle():
    """Test starting, stopping, and status reporting of the APScheduler background manager."""
    stop_scheduler()  # Ensure clean initial state
    status_stopped = get_scheduler_status()
    assert status_stopped["running"] is False

    sched = start_scheduler(interval_minutes=15)
    assert sched.running is True

    status_running = get_scheduler_status()
    assert status_running["running"] is True
    job_ids = [j["id"] for j in status_running["jobs"]]
    assert "market_poll_job" in job_ids

    stop_scheduler()
    status_after_stop = get_scheduler_status()
    assert status_after_stop["running"] is False


@patch("scheduler.fetch_and_process_market")
def test_run_scheduled_poll_success(mock_fetch):
    """Test running scheduled poll wrapper successfully."""
    mock_fetch.return_value = {
        "status": "success",
        "steals_detected": 1,
        "notifications_sent": 1,
    }
    result = run_scheduled_poll()
    assert result["status"] == "success"
    assert result["steals_detected"] == 1
    mock_fetch.assert_called_once()


@patch("scheduler.fetch_and_process_market", side_effect=Exception("Database locked"))
def test_run_scheduled_poll_exception_handling(mock_fetch):
    """Test error handling inside scheduled poll wrapper when fetcher fails."""
    result = run_scheduled_poll()
    assert result["status"] == "error"
    assert "Database locked" in result["message"]
