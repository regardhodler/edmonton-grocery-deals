"""Weekly price snapshots — save, load, and trend calculation."""

import json
import os
from datetime import datetime, timedelta

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "price_history.json")
MAX_WEEKS = 8


def _load() -> dict:
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save(data: dict):
    with open(HISTORY_PATH, "w") as f:
        json.dump(data, f, indent=1)


def save_snapshot(df):
    """Record current prices keyed by merchant::item_name, deduplicated by week."""
    if df.empty:
        return
    week_key = datetime.now().strftime("%Y-W%W")
    cutoff = (datetime.now() - timedelta(weeks=MAX_WEEKS)).strftime("%Y-W%W")
    data = _load()

    for _, row in df.iterrows():
        price = row.get("current_price")
        if price is None:
            continue
        key = f"{row['merchant']}::{row['name']}"
        entry = data.setdefault(key, {})
        entry[week_key] = round(float(price), 2)
        # Prune old entries
        for wk in list(entry):
            if wk < cutoff:
                del entry[wk]

    # Drop keys with no remaining entries
    data = {k: v for k, v in data.items() if v}
    _save(data)


def get_price_trend(merchant: str, name: str) -> dict | None:
    """Return trend info or None if fewer than 2 data points.

    Returns: {prev_price, trend: up/down/same, symbol: ↑↓→, label}
    """
    data = _load()
    key = f"{merchant}::{name}"
    entry = data.get(key, {})
    if len(entry) < 2:
        return None

    weeks = sorted(entry.keys())
    prev_price = entry[weeks[-2]]
    curr_price = entry[weeks[-1]]

    if curr_price < prev_price:
        trend, symbol, label = "down", "↓", f"Down from ${prev_price:.2f}"
    elif curr_price > prev_price:
        trend, symbol, label = "up", "↑", f"Up from ${prev_price:.2f}"
    else:
        trend, symbol, label = "same", "→", "Unchanged"

    return {
        "prev_price": prev_price,
        "trend": trend,
        "symbol": symbol,
        "label": label,
    }
