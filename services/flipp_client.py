"""Flipp API client — pulls current flyer items via backflipp search endpoint."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pandas as pd
import streamlit as st

SEARCH_URL = "https://backflipp.wishabi.com/flipp/items/search"

HEADERS = {"User-Agent": "Mozilla/5.0"}

TARGET_MERCHANTS = {
    "Real Canadian Superstore",
    "Walmart",
    "Save-On-Foods",
    "No Frills",
    "Safeway",
    "Costco",
    "FreshCo",
}

# Postal codes covering Edmonton, St. Albert, and Leduc
POSTAL_CODES = [
    "T5P1A1",  # West Edmonton
    "T5J0K1",  # Central Edmonton
    "T8N0A1",  # St. Albert
    "T9E0A1",  # Leduc
]

# Multiple queries to get broad coverage across all merchants
SEARCH_QUERIES = [
    "", "meat", "chicken", "produce", "fruit", "dairy", "milk", "cheese",
    "bread", "snack", "frozen", "drink", "juice", "cereal", "rice", "pasta",
    "vegetable", "fish", "pork", "beef", "egg", "butter", "yogurt", "coffee",
    "soap", "paper", "baby", "chocolate", "pizza", "chip", "water", "sauce",
]

# Fallback links if API fails
STORE_FLYER_LINKS = {
    "Real Canadian Superstore": "https://www.realcanadiansuperstore.ca/print-flyer",
    "Walmart": "https://www.walmart.ca/flyer",
    "Save-On-Foods": "https://www.saveonfoods.com/flyer/",
    "No Frills": "https://www.nofrills.ca/print-flyer",
    "Safeway": "https://www.safeway.ca/flyer",
    "Costco": "https://www.costco.ca/warehouse-savings.html",
    "FreshCo": "https://www.freshco.com/flyer/",
}


def _search_items(postal_code: str, query: str) -> list[dict]:
    """Run a single search query and return items."""
    resp = requests.get(
        SEARCH_URL,
        params={"locale": "en-ca", "postal_code": postal_code, "q": query},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


@st.cache_data(ttl=3600, show_spinner="Loading flyer deals...")
def fetch_deals() -> pd.DataFrame:
    """Fetch current deals from target stores across all postal codes."""
    # Build all (postal_code, query) pairs and fetch in parallel
    pairs = [
        (postal_code, query)
        for postal_code in POSTAL_CODES
        for query in SEARCH_QUERIES
    ]

    raw_results: list[list[dict]] = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(_search_items, pc, q): (pc, q)
            for pc, q in pairs
        }
        for future in as_completed(futures):
            try:
                raw_results.append(future.result())
            except Exception:
                continue

    # Deduplicate and filter
    seen_ids = set()
    all_items = []
    for items in raw_results:
        for item in items:
            item_id = item.get("id")
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            merchant = item.get("merchant_name", "")
            if merchant not in TARGET_MERCHANTS:
                continue

            name = item.get("name", "").strip()
            if not name:
                continue

            current_price = item.get("current_price")
            original_price = item.get("original_price")
            pre_price = item.get("pre_price_text", "") or ""
            sale_story = item.get("sale_story", "") or ""
            image_url = (
                item.get("clean_image_url")
                or item.get("clipping_image_url", "")
            )

            if current_price is not None:
                price_text = f"${current_price:.2f}"
            else:
                price_text = sale_story

            all_items.append({
                "merchant": merchant,
                "name": name,
                "price": price_text,
                "pre_price": (
                    f"${original_price:.2f}" if original_price else pre_price
                ),
                "current_price": current_price,
                "original_price": original_price,
                "sale_story": sale_story,
                "valid_from": item.get("valid_from", ""),
                "valid_to": item.get("valid_to", ""),
                "image_url": image_url,
            })

    df = pd.DataFrame(all_items)
    if df.empty:
        return df

    df["sort_price"] = pd.to_numeric(df["current_price"], errors="coerce")
    return df
