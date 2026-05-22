"""Pinterest API v5 — pin-level analytics fetcher.

The Pinterest /pins/{id}/analytics endpoint returns daily breakdowns. We sum
across the requested window to get lifetime totals (or the last N days).
"""

from datetime import date, timedelta
from typing import Iterable

from agents.pinterest.api import API_BASE, _api_call, get_access_token

# Pinterest caps each analytics call to a 90-day window.
MAX_WINDOW_DAYS = 90

METRIC_TYPES = ["IMPRESSION", "SAVE", "OUTBOUND_CLICK", "PIN_CLICK"]


def fetch_pin_analytics(pin_id: str, days: int = 90) -> dict:
    """Fetch cumulative analytics for a single pin over the last `days` days.

    Returns a dict with keys: impressions, saves, outbound_clicks, pin_clicks.
    Missing/zero data returns zeros — never raises for the empty case.
    """
    days = min(days, MAX_WINDOW_DAYS)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    token = get_access_token()
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "metric_types": ",".join(METRIC_TYPES),
    }
    r = _api_call(
        "GET", f"{API_BASE}/pins/{pin_id}/analytics", token,
        params=params, timeout=30,
    )

    if r.status_code == 404:
        # Pin was deleted on Pinterest, or analytics not yet available.
        return {"impressions": 0, "saves": 0, "outbound_clicks": 0, "pin_clicks": 0, "missing": True}
    r.raise_for_status()

    return _sum_daily_metrics(r.json())


def _sum_daily_metrics(payload: dict) -> dict:
    """Sum a Pinterest analytics response into a single totals dict."""
    totals = {"impressions": 0, "saves": 0, "outbound_clicks": 0, "pin_clicks": 0}

    # Response shape: { "<METRIC_NAME>": { "summary_metrics": {...}, "daily_metrics": [...] } }
    metric_map = {
        "IMPRESSION": "impressions",
        "SAVE": "saves",
        "OUTBOUND_CLICK": "outbound_clicks",
        "PIN_CLICK": "pin_clicks",
    }

    for api_key, our_key in metric_map.items():
        block = payload.get(api_key) or payload.get("all", {}).get(api_key) or {}
        summary = block.get("summary_metrics") or {}
        # Some Pinterest responses put the total under a different key; check both.
        value = summary.get("LIFETIME") or summary.get(api_key) or 0
        if not value and "daily_metrics" in block:
            value = sum(d.get("data_status") != "PROCESSING" and d.get("value", 0) or 0
                        for d in block["daily_metrics"])
        totals[our_key] = int(value or 0)

    return totals


def fetch_pin_analytics_bulk(pin_ids: Iterable[str], days: int = 90) -> dict[str, dict]:
    """Fetch analytics for many pins. Returns {pin_id: metrics_dict}.

    Pin-by-pin (Pinterest has no batch endpoint for pin analytics). Errors on
    individual pins are recorded as a zero-row with `error` set, so the caller
    can persist what it got.
    """
    results: dict[str, dict] = {}
    for pid in pin_ids:
        try:
            results[pid] = fetch_pin_analytics(pid, days=days)
        except Exception as e:
            results[pid] = {
                "impressions": 0, "saves": 0, "outbound_clicks": 0, "pin_clicks": 0,
                "error": str(e),
            }
    return results
