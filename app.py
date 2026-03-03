"""Edmonton Grocery Deals Finder — Edmonton, St. Albert & Leduc."""

import html as html_mod
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import folium
from streamlit_folium import st_folium

from services.flipp_client import fetch_deals, STORE_FLYER_LINKS
from services.notifications import send_telegram_alert
from data.stores import STORES, MERCHANT_COLORS
from data.price_history import save_snapshot, get_price_trend
from utils.categories import categorize_item

st.set_page_config(
    page_title="Edmonton Grocery Deals",
    page_icon="\U0001f6d2",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Mobile padding */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.5rem !important; }
    h1 { font-size: 1.5rem !important; }
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0 !important;
    }
    .deal-card { flex-direction: column !important; }
    .deal-card img { width: 60px !important; height: 60px !important; }
    .price-compare-row { gap: 0.5rem !important; }
    .pc-card { min-width: 100px !important; padding: 0.4rem !important; }
}

/* Deal cards */
.deals-container { max-width: 900px; }
.deal-card {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 0.5rem;
    border-bottom: 1px solid rgba(128,128,128,0.2);
}
.deal-card:hover { background: rgba(128,128,128,0.05); }
.deal-card img {
    width: 80px;
    height: 80px;
    object-fit: contain;
    border-radius: 8px;
    flex-shrink: 0;
}
.deal-card .deal-info { flex: 1; min-width: 0; }
.deal-card .deal-name {
    font-weight: 600;
    font-size: 0.95rem;
    margin: 0;
    line-height: 1.3;
}
.deal-card .deal-meta {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.2rem;
    flex-wrap: wrap;
}
.deal-card .deal-story {
    color: #888;
    font-size: 0.8rem;
    margin-top: 0.15rem;
}
.deal-card .deal-price {
    font-weight: 700;
    font-size: 0.95rem;
}
.deal-card .deal-orig-price {
    text-decoration: line-through;
    color: #999;
    font-size: 0.85rem;
}

/* Store dot */
.store-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.store-name-label {
    font-size: 0.78rem;
    color: #aaa;
}

/* Savings badge */
.savings-badge {
    display: inline-block;
    background: #2e7d32;
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 1px 7px;
    border-radius: 10px;
    white-space: nowrap;
}

/* Price trend */
.deal-history {
    font-size: 0.75rem;
    margin-top: 0.1rem;
}
.deal-history.trend-down { color: #43A047; }
.deal-history.trend-up { color: #E53935; }
.deal-history.trend-same { color: #888; }

/* Watched item */
.deal-card.watched {
    border-left: 3px solid #FFD600;
    padding-left: calc(0.5rem - 3px);
}

/* Price comparison row */
.price-compare-row {
    display: flex;
    overflow-x: auto;
    gap: 0.75rem;
    padding: 0.5rem 0 0.75rem 0;
    -webkit-overflow-scrolling: touch;
}
.pc-card {
    flex: 0 0 auto;
    min-width: 120px;
    background: rgba(128,128,128,0.08);
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
    text-align: center;
}
.pc-card .pc-price {
    font-weight: 700;
    font-size: 1.1rem;
}
.pc-card .pc-store {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
    font-size: 0.78rem;
    color: #aaa;
    margin-top: 0.2rem;
}
</style>
""", unsafe_allow_html=True)

# ── JS: click-outside-to-close expanders + sticky search ─────────────────────
components.html("""
<script>
const doc = window.parent.document;
// Click outside to close expanders / popovers
doc.addEventListener('click', function(e) {
    doc.querySelectorAll('details[open]').forEach(function(d) {
        if (!d.contains(e.target)) d.removeAttribute('open');
    });
});
// Sticky search bar
(function() {
    const trySticky = () => {
        const inputs = doc.querySelectorAll('[data-testid="stTextInput"]');
        if (!inputs.length) return setTimeout(trySticky, 300);
        const searchRow = inputs[0].closest('[data-testid="stHorizontalBlock"]');
        if (searchRow) {
            searchRow.style.position = 'sticky';
            searchRow.style.top = '0';
            searchRow.style.zIndex = '999';
            searchRow.style.background = 'var(--background-color, #0e1117)';
            searchRow.style.paddingTop = '0.5rem';
            searchRow.style.paddingBottom = '0.5rem';
        }
    };
    trySticky();
})();
</script>
""", height=0)

st.title("\U0001f6d2 Edmonton Grocery Deals")
st.caption("Edmonton \u2022 St. Albert \u2022 Leduc \u2022 updated hourly")

# ── Fetch data ────────────────────────────────────────────────────────────────
df = fetch_deals()

if df.empty:
    st.warning("No deals loaded. The Flipp API may be temporarily unavailable.")
    st.subheader("Browse flyers directly")
    for store, url in STORE_FLYER_LINKS.items():
        st.markdown(f"- [{store}]({url})")
    st.stop()

# Add categories
df["category"] = df["name"].apply(categorize_item)

# Save price snapshot for history tracking
save_snapshot(df)

# Compute discount percentage
df["discount_pct"] = 0.0
mask = df["original_price"].notna() & df["current_price"].notna() & (df["original_price"] > 0)
df.loc[mask, "discount_pct"] = (
    (df.loc[mask, "original_price"] - df.loc[mask, "current_price"])
    / df.loc[mask, "original_price"]
    * 100
).round(0)

# ── Watched items from URL params ─────────────────────────────────────────────
if "watched_keywords" not in st.session_state:
    watch_param = st.query_params.get("watch", "")
    st.session_state.watched_keywords = (
        [w.strip().lower() for w in watch_param.split(",") if w.strip()]
        if watch_param else []
    )

# ── Search bar + sort pills ──────────────────────────────────────────────────
search_col, sort_col = st.columns([3, 1])
with search_col:
    search_query = st.text_input(
        "\U0001f50d Search items",
        placeholder="e.g. chicken, bread, eggs",
        label_visibility="collapsed",
    )
with sort_col:
    sort_options = ["Name (A-Z)", "Price: Low-High", "Price: High-Low", "Store", "Best Deals"]
    sort_option = st.pills("Sort by", sort_options, default="Name (A-Z)")

# ── Filters + Settings popovers ──────────────────────────────────────────────
available_merchants = sorted(df["merchant"].unique())
available_categories = sorted(df["category"].unique())

filter_col, settings_col = st.columns([1, 1])

with filter_col:
    with st.popover("Filters", use_container_width=True):
        if st.button("\U0001f504 Refresh Deals"):
            fetch_deals.clear()
            st.rerun()

        selected_stores = st.multiselect(
            "Stores",
            options=available_merchants,
            default=available_merchants,
        )
        selected_categories = st.multiselect(
            "Categories",
            options=available_categories,
            default=available_categories,
        )

        st.divider()

        watch_input = st.text_input(
            "Watch Items (comma-separated)",
            placeholder="e.g. chicken, eggs, milk",
        )
        if watch_input:
            new_keywords = [w.strip().lower() for w in watch_input.split(",") if w.strip()]
            if new_keywords != st.session_state.watched_keywords:
                st.session_state.watched_keywords = new_keywords
                st.query_params["watch"] = ",".join(new_keywords)
                st.rerun()

        if st.session_state.watched_keywords:
            st.caption(f"Watching: {', '.join(st.session_state.watched_keywords)}")
            if st.button("Clear all watches"):
                st.session_state.watched_keywords = []
                if "watch" in st.query_params:
                    del st.query_params["watch"]
                st.rerun()

        st.divider()
        st.caption("Edmonton, St. Albert & Leduc")
        if not df.empty:
            valid_from = df["valid_from"].dropna().min()
            valid_to = df["valid_to"].dropna().max()
            if valid_from and valid_to:
                st.caption(f"Flyers valid: {valid_from[:10]} to {valid_to[:10]}")

with settings_col:
    with st.popover("Settings", use_container_width=True):
        tg_token = st.text_input("Telegram Bot Token", type="password")
        tg_chat = st.text_input("Telegram Chat ID")
        if st.button("Send Test Alert") and tg_token and tg_chat:
            test_items = [{"name": "Test Item", "merchant": "Test Store", "price": "$1.99", "sale_story": "Test alert from Edmonton Grocery Deals"}]
            ok = send_telegram_alert(tg_token, tg_chat, test_items)
            if ok:
                st.success("Test alert sent!")
            else:
                st.error("Failed to send. Check token and chat ID.")

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df[
    df["merchant"].isin(selected_stores) & df["category"].isin(selected_categories)
]

if search_query:
    query_lower = search_query.lower()
    filtered = filtered[
        filtered["name"].str.lower().str.contains(query_lower, na=False)
    ]

# ── Sort ──────────────────────────────────────────────────────────────────────
if sort_option == "Price: Low-High":
    filtered = filtered.sort_values("sort_price", ascending=True, na_position="last")
elif sort_option == "Price: High-Low":
    filtered = filtered.sort_values("sort_price", ascending=False, na_position="last")
elif sort_option == "Store":
    filtered = filtered.sort_values("merchant", ascending=True)
elif sort_option == "Best Deals":
    filtered = filtered.sort_values("discount_pct", ascending=False, na_position="last")
else:
    filtered = filtered.sort_values("name", ascending=True)

st.markdown(f"**{len(filtered)}** deals found")

# ── Auto-send Telegram alert for watched items on first load ──────────────────
if (
    st.session_state.watched_keywords
    and tg_token
    and tg_chat
    and "tg_alert_sent" not in st.session_state
):
    watched_df = filtered[
        filtered["name"].str.lower().apply(
            lambda n: any(kw in n for kw in st.session_state.watched_keywords)
        )
    ]
    if not watched_df.empty:
        items = watched_df[["name", "merchant", "price", "sale_story"]].to_dict("records")
        send_telegram_alert(tg_token, tg_chat, items)
        st.session_state.tg_alert_sent = True

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_list, tab_map = st.tabs(["\U0001f4cb Deals", "\U0001f5fa\ufe0f Map"])

# ── List View ─────────────────────────────────────────────────────────────────
with tab_list:
    if filtered.empty:
        st.info("No deals match your filters. Try broadening your search.")
    else:
        # ── Price comparison (shown when search is active) ────────────────
        if search_query and len(filtered) > 1:
            lowest_per_merchant = (
                filtered.dropna(subset=["sort_price"])
                .sort_values("sort_price")
                .drop_duplicates(subset=["merchant"], keep="first")
            )
            if len(lowest_per_merchant) > 1:
                st.markdown("**Price Comparison**")
                pc_html = '<div class="price-compare-row">'
                for _, row in lowest_per_merchant.iterrows():
                    color = MERCHANT_COLORS.get(row["merchant"], "#888")
                    price = html_mod.escape(row["price"] or "")
                    merchant = html_mod.escape(row["merchant"])
                    pc_html += (
                        f'<div class="pc-card">'
                        f'<div class="pc-price">{price}</div>'
                        f'<div class="pc-store">'
                        f'<span class="store-dot" style="background:{color}"></span>'
                        f'{merchant}</div></div>'
                    )
                pc_html += "</div>"
                st.markdown(pc_html, unsafe_allow_html=True)

        # ── Pagination state ──────────────────────────────────────────────
        PAGE_SIZE = 50
        if "show_count" not in st.session_state:
            st.session_state.show_count = PAGE_SIZE

        visible = filtered.head(st.session_state.show_count)

        # ── Build flat card HTML ──────────────────────────────────────────
        cards_html = '<div class="deals-container">'
        watched_kws = st.session_state.watched_keywords

        for _, row in visible.iterrows():
            name = html_mod.escape(row["name"])
            merchant = html_mod.escape(row["merchant"])
            color = MERCHANT_COLORS.get(row["merchant"], "#888")
            price = html_mod.escape(row["price"] or "")
            pre_price = html_mod.escape(row["pre_price"] or "")
            sale_story = html_mod.escape(row["sale_story"] or "")
            img_url = row["image_url"] or ""
            discount = row["discount_pct"]

            # Watched?
            is_watched = any(kw in row["name"].lower() for kw in watched_kws)
            card_class = "deal-card watched" if is_watched else "deal-card"

            cards_html += f'<div class="{card_class}">'

            # Image
            if img_url:
                img_escaped = html_mod.escape(img_url)
                cards_html += f'<img src="{img_escaped}" alt="" loading="lazy">'

            cards_html += '<div class="deal-info">'

            # Product name
            cards_html += f'<p class="deal-name">{name}</p>'

            # Meta row: store dot + name, price, savings badge
            cards_html += '<div class="deal-meta">'
            cards_html += f'<span class="store-dot" style="background:{color}"></span>'
            cards_html += f'<span class="store-name-label">{merchant}</span>'

            if pre_price and price:
                cards_html += f' <span class="deal-orig-price">{pre_price}</span>'
                cards_html += f' <span class="deal-price">{price}</span>'
            elif price:
                cards_html += f' <span class="deal-price">{price}</span>'

            if discount > 0:
                cards_html += f' <span class="savings-badge">Save {int(discount)}%</span>'

            cards_html += "</div>"  # deal-meta

            # Sale story
            if sale_story:
                cards_html += f'<div class="deal-story">{sale_story}</div>'

            # Price trend
            trend = get_price_trend(row["merchant"], row["name"])
            if trend:
                trend_class = f"trend-{trend['trend']}"
                label = html_mod.escape(trend["label"])
                cards_html += (
                    f'<div class="deal-history {trend_class}">'
                    f'{trend["symbol"]} {label}</div>'
                )

            cards_html += "</div>"  # deal-info
            cards_html += "</div>"  # deal-card

        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

        # Show more button
        if len(filtered) > st.session_state.show_count:
            remaining = len(filtered) - st.session_state.show_count
            if st.button(f"Show more ({remaining} remaining)"):
                st.session_state.show_count += PAGE_SIZE
                st.rerun()

# ── Map View ──────────────────────────────────────────────────────────────────
with tab_map:
    m = folium.Map(location=[53.48, -113.53], zoom_start=10, tiles="OpenStreetMap")

    for store in STORES:
        merchant = store["merchant"]
        merchant_deals = filtered[
            filtered["merchant"].str.lower() == merchant.lower()
        ]
        deal_count = len(merchant_deals)

        popup_lines = [
            f"<b>{store['name']}</b><br>"
            f"{store['address']}<br>"
            f"<b>{deal_count} deals</b><br><hr>"
        ]
        for _, row in merchant_deals.head(5).iterrows():
            price_text = row["price"] or ""
            popup_lines.append(f"{row['name']} \u2014 <b>{price_text}</b><br>")
        if deal_count > 5:
            popup_lines.append(f"<i>...and {deal_count - 5} more</i>")

        folium.Marker(
            location=[store["lat"], store["lon"]],
            popup=folium.Popup("".join(popup_lines), max_width=280),
            tooltip=f"{store['name']} ({deal_count})",
            icon=folium.Icon(
                color=store["color"], icon="shopping-cart", prefix="fa"
            ),
        ).add_to(m)

    st_folium(m, width=None, height=450, use_container_width=True)
