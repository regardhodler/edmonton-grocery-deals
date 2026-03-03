"""Edmonton Grocery Deals Finder — Edmonton, St. Albert & Leduc."""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from services.flipp_client import fetch_deals, STORE_FLYER_LINKS
from data.stores import STORES
from utils.categories import categorize_item

st.set_page_config(
    page_title="Edmonton Grocery Deals",
    page_icon="\U0001f6d2",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Mobile-friendly CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
/* Tighter padding on mobile */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.5rem !important; }
    h1 { font-size: 1.5rem !important; }
    /* Stack columns vertically on small screens */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0 !important;
    }
}
/* Deal card styling */
.deal-card {
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}
/* Smaller images */
[data-testid="stImage"] img {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Click-outside-to-close expanders (runs JS via iframe) ─────────────────
import streamlit.components.v1 as components
components.html("""
<script>
const doc = window.parent.document;
doc.addEventListener('click', function(e) {
    doc.querySelectorAll('details[open]').forEach(function(d) {
        if (!d.contains(e.target)) {
            d.removeAttribute('open');
        }
    });
});
</script>
""", height=0)

st.title("\U0001f6d2 Edmonton Grocery Deals")
st.caption("Edmonton \u2022 St. Albert \u2022 Leduc \u2022 updated hourly")

# ── Fetch data ──────────────────────────────────────────────────────────────
df = fetch_deals()

if df.empty:
    st.warning("No deals loaded. The Flipp API may be temporarily unavailable.")
    st.subheader("Browse flyers directly")
    for store, url in STORE_FLYER_LINKS.items():
        st.markdown(f"- [{store}]({url})")
    st.stop()

# Add categories
df["category"] = df["name"].apply(categorize_item)

# ── Search bar + sort pills ────────────────────────────────────────────────
search_col, sort_col = st.columns([3, 1])
with search_col:
    search_query = st.text_input(
        "\U0001f50d Search items",
        placeholder="e.g. chicken, bread, eggs",
        label_visibility="collapsed",
    )
with sort_col:
    sort_options = ["Name (A-Z)", "Price: Low-High", "Price: High-Low", "Store"]
    sort_option = st.pills("Sort by", sort_options, default="Name (A-Z)")

# ── Filters popover ───────────────────────────────────────────────────────
available_merchants = sorted(df["merchant"].unique())
available_categories = sorted(df["category"].unique())

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
    st.caption("Edmonton, St. Albert & Leduc")
    if not df.empty:
        valid_from = df["valid_from"].dropna().min()
        valid_to = df["valid_to"].dropna().max()
        if valid_from and valid_to:
            st.caption(f"Flyers valid: {valid_from[:10]} to {valid_to[:10]}")

# ── Apply filters ───────────────────────────────────────────────────────────
filtered = df[
    df["merchant"].isin(selected_stores) & df["category"].isin(selected_categories)
]

if search_query:
    query_lower = search_query.lower()
    filtered = filtered[
        filtered["name"].str.lower().str.contains(query_lower, na=False)
    ]

# ── Sort ────────────────────────────────────────────────────────────────────
if sort_option == "Price: Low-High":
    filtered = filtered.sort_values("sort_price", ascending=True, na_position="last")
elif sort_option == "Price: High-Low":
    filtered = filtered.sort_values("sort_price", ascending=False, na_position="last")
elif sort_option == "Store":
    filtered = filtered.sort_values("merchant", ascending=True)
else:
    filtered = filtered.sort_values("name", ascending=True)

st.markdown(f"**{len(filtered)}** deals found")

# ── Tabs ────────────────────────────────────────────────────────────────────
tab_list, tab_map = st.tabs(["\U0001f4cb Deals", "\U0001f5fa\ufe0f Map"])

# ── List View ───────────────────────────────────────────────────────────────
with tab_list:
    if filtered.empty:
        st.info("No deals match your filters. Try broadening your search.")
    else:
        for merchant, group in filtered.groupby("merchant", sort=True):
            with st.expander(f"**{merchant}** ({len(group)} deals)", expanded=False):
                for _, row in group.iterrows():
                    cols = st.columns([1, 3])
                    with cols[0]:
                        if row["image_url"]:
                            st.image(row["image_url"], width=80)
                    with cols[1]:
                        price_display = row["price"] or ""
                        pre_price_display = row["pre_price"] or ""
                        if pre_price_display and price_display:
                            st.markdown(
                                f"**{row['name']}**  \n"
                                f"~~{pre_price_display}~~ \u2192 **{price_display}**"
                            )
                        elif price_display:
                            st.markdown(f"**{row['name']}**  \n**{price_display}**")
                        else:
                            st.markdown(f"**{row['name']}**")
                        if row["sale_story"]:
                            st.caption(row["sale_story"])
                    st.divider()

# ── Map View ────────────────────────────────────────────────────────────────
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
