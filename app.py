"""Edmonton Grocery Deals Finder — Edmonton, St. Albert & Leduc."""

import html as html_mod
import json as json_mod
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

/* Store filter chips */
.store-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    padding: 0.4rem 0;
}
.store-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.3rem 0.7rem;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    border: 1.5px solid rgba(128,128,128,0.3);
    background: transparent;
    color: #ccc;
    transition: all 0.15s;
}
.store-chip.active {
    border-color: var(--chip-color);
    background: color-mix(in srgb, var(--chip-color) 15%, transparent);
    color: #fff;
}
.store-chip .chip-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.store-chip .chip-count {
    font-size: 0.7rem;
    opacity: 0.7;
    margin-left: 0.1rem;
}

/* Bag controls on deal cards */
.deal-card { position: relative; }
.bag-controls {
    position: absolute;
    top: 0.6rem;
    right: 0.4rem;
    display: flex;
    align-items: center;
    gap: 0;
    z-index: 2;
}
.bag-ctrl-btn {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 1.5px solid rgba(128,128,128,0.35);
    background: rgba(30,30,30,0.85);
    color: #ccc;
    font-size: 1.1rem;
    line-height: 1;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    padding: 0;
}
.bag-ctrl-btn.bag-plus:hover {
    border-color: #4CAF50;
    color: #4CAF50;
    background: rgba(76,175,80,0.1);
}
.bag-ctrl-btn.bag-minus {
    border-color: #E53935;
    color: #E53935;
    display: none;
}
.bag-ctrl-btn.bag-minus:hover {
    background: rgba(229,57,53,0.15);
}
.bag-qty {
    min-width: 22px;
    text-align: center;
    font-size: 0.8rem;
    font-weight: 700;
    color: #fff;
    display: none;
    user-select: none;
}

/* Floating bag FAB */
.bag-fab {
    position: fixed;
    bottom: 2rem;
    left: 2rem;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: rgba(76,175,80,0.9);
    color: #fff;
    font-size: 1.4rem;
    display: none;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 1001;
    border: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    transition: background 0.2s, transform 0.15s;
}
.bag-fab:hover { background: rgba(76,175,80,1); transform: scale(1.05); }
.bag-fab .bag-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: #E53935;
    color: #fff;
    font-size: 0.65rem;
    font-weight: 700;
    min-width: 18px;
    height: 18px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
}

/* Bag panel */
.bag-panel {
    position: fixed;
    bottom: 8.5rem;
    left: 2rem;
    width: 340px;
    max-height: 60vh;
    background: #1a1a2e;
    border: 1px solid rgba(128,128,128,0.3);
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    z-index: 1002;
    display: none;
    flex-direction: column;
    overflow: hidden;
}
.bag-panel.open { display: flex; }
.bag-panel-header {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgba(128,128,128,0.2);
    font-weight: 600;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.bag-panel-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.25rem 0;
}
.bag-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-bottom: 1px solid rgba(128,128,128,0.1);
    font-size: 0.85rem;
}
.bag-item:last-child { border-bottom: none; }
.bag-item img {
    width: 36px;
    height: 36px;
    object-fit: contain;
    border-radius: 6px;
    flex-shrink: 0;
}
.bag-item-info { flex: 1; min-width: 0; }
.bag-item-name {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.bag-item-detail {
    font-size: 0.75rem;
    color: #999;
}
.bag-item-remove {
    background: none;
    border: none;
    color: #999;
    font-size: 1.1rem;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 4px;
    transition: color 0.15s, background 0.15s;
    flex-shrink: 0;
}
.bag-item-remove:hover { color: #E53935; background: rgba(229,57,53,0.1); }
.bag-panel-footer {
    padding: 0.5rem 1rem;
    border-top: 1px solid rgba(128,128,128,0.2);
    display: flex;
    justify-content: center;
}
.bag-clear-btn {
    background: none;
    border: 1px solid rgba(229,57,53,0.4);
    color: #E53935;
    font-size: 0.8rem;
    padding: 0.3rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s;
}
.bag-clear-btn:hover { background: rgba(229,57,53,0.1); }

/* Bag panel empty state */
.bag-empty {
    padding: 2rem 1rem;
    text-align: center;
    color: #888;
    font-size: 0.85rem;
}

/* Mobile bag */
@media (max-width: 768px) {
    .bag-panel {
        left: 0.5rem;
        right: 0.5rem;
        width: auto;
        max-height: 50vh;
    }
    .bag-fab { left: 1rem; bottom: 1.5rem; }
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
// ── Grocery Bag ──────────────────────────────────────────────────
(function() {
    const STORAGE_KEY = 'grocery_bag';
    function getBag() {
        try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
        catch { return []; }
    }
    function saveBag(bag) { localStorage.setItem(STORAGE_KEY, JSON.stringify(bag)); }
    function itemKey(item) { return item.name + '||' + item.merchant; }

    // Remove duplicates from Streamlit reruns
    doc.querySelectorAll('.bag-fab').forEach(function(el) { el.remove(); });
    doc.querySelectorAll('.bag-panel').forEach(function(el) { el.remove(); });

    // Create FAB
    var container = doc.querySelector('.stApp') || doc.body;
    const fab = doc.createElement('button');
    fab.className = 'bag-fab';
    fab.title = 'Grocery Bag';
    fab.innerHTML = '&#x1F6D2;<span class="bag-badge">0</span>';
    container.appendChild(fab);

    // Create Panel
    const panel = doc.createElement('div');
    panel.className = 'bag-panel';
    panel.innerHTML =
        '<div class="bag-panel-header"><span>&#x1F6D2; Grocery Bag</span><span class="bag-panel-count"></span></div>' +
        '<div class="bag-panel-list"></div>' +
        '<div class="bag-panel-footer"><button class="bag-clear-btn">Clear all</button></div>';
    container.appendChild(panel);

    const badge = fab.querySelector('.bag-badge');
    const listEl = panel.querySelector('.bag-panel-list');
    const countEl = panel.querySelector('.bag-panel-count');
    const clearBtn = panel.querySelector('.bag-clear-btn');

    function totalQty(bag) {
        return bag.reduce(function(s, item) { return s + (item.qty || 1); }, 0);
    }

    function updateBadge() {
        const bag = getBag();
        const n = totalQty(bag);
        badge.textContent = n;
        fab.style.display = n > 0 ? 'flex' : 'none';
        if (n === 0) panel.classList.remove('open');
    }

    function renderPanel() {
        const bag = getBag();
        const total = totalQty(bag);
        countEl.textContent = total + ' item' + (total !== 1 ? 's' : '');
        if (bag.length === 0) {
            listEl.innerHTML = '<div class="bag-empty">Your bag is empty</div>';
            clearBtn.style.display = 'none';
            return;
        }
        clearBtn.style.display = '';
        listEl.innerHTML = bag.map(function(item, i) {
            const imgHtml = item.image_url
                ? '<img src="' + item.image_url.replace(/"/g, '&quot;') + '" alt="">'
                : '';
            const name = item.name.replace(/</g, '&lt;');
            const qty = item.qty || 1;
            const qtyLabel = qty > 1 ? ' \u00D7' + qty : '';
            const detail = (item.price ? item.price.replace(/</g, '&lt;') + ' \u2022 ' : '') + item.merchant.replace(/</g, '&lt;');
            return '<div class="bag-item" data-idx="' + i + '">' +
                imgHtml +
                '<div class="bag-item-info"><div class="bag-item-name">' + name + qtyLabel + '</div>' +
                '<div class="bag-item-detail">' + detail + '</div></div>' +
                '<button class="bag-item-remove" title="Remove">\u00D7</button></div>';
        }).join('');
    }

    // FAB click toggles panel
    fab.addEventListener('click', function() {
        const isOpen = panel.classList.toggle('open');
        if (isOpen) renderPanel();
    });

    // Clear all
    clearBtn.addEventListener('click', function() {
        saveBag([]);
        updateBadge();
        renderPanel();
        syncAllCards();
    });

    // Remove item from panel
    panel.addEventListener('click', function(e) {
        const removeBtn = e.target.closest('.bag-item-remove');
        if (!removeBtn) return;
        const bagItem = removeBtn.closest('.bag-item');
        const idx = parseInt(bagItem.dataset.idx, 10);
        const bag = getBag();
        bag.splice(idx, 1);
        saveBag(bag);
        updateBadge();
        renderPanel();
        syncAllCards();
    });

    // Update a single card's controls to reflect current bag qty
    function syncCard(card) {
        try {
            const d = JSON.parse(card.getAttribute('data-item'));
            const bag = getBag();
            const key = itemKey(d);
            const entry = bag.find(function(b) { return itemKey(b) === key; });
            const qty = entry ? (entry.qty || 1) : 0;
            const minusBtn = card.querySelector('.bag-minus');
            const qtyEl = card.querySelector('.bag-qty');
            if (qty > 0) {
                minusBtn.style.display = 'flex';
                qtyEl.style.display = 'block';
                qtyEl.textContent = qty;
            } else {
                minusBtn.style.display = 'none';
                qtyEl.style.display = 'none';
                qtyEl.textContent = '';
            }
        } catch {}
    }

    function syncAllCards() {
        doc.querySelectorAll('.deal-card[data-item]').forEach(syncCard);
    }

    // Plus button — add / increment
    doc.addEventListener('click', function(e) {
        const btn = e.target.closest('.bag-plus');
        if (!btn) return;
        const card = btn.closest('.deal-card[data-item]');
        if (!card) return;
        e.stopPropagation();
        try {
            const item = JSON.parse(card.getAttribute('data-item'));
            var bag = getBag();
            const key = itemKey(item);
            const entry = bag.find(function(b) { return itemKey(b) === key; });
            if (entry) {
                entry.qty = (entry.qty || 1) + 1;
            } else {
                item.qty = 1;
                bag.push(item);
            }
            saveBag(bag);
            updateBadge();
            syncCard(card);
            if (panel.classList.contains('open')) renderPanel();
        } catch {}
    });

    // Minus button — decrement / remove
    doc.addEventListener('click', function(e) {
        const btn = e.target.closest('.bag-minus');
        if (!btn) return;
        const card = btn.closest('.deal-card[data-item]');
        if (!card) return;
        e.stopPropagation();
        try {
            const item = JSON.parse(card.getAttribute('data-item'));
            var bag = getBag();
            const key = itemKey(item);
            const idx = bag.findIndex(function(b) { return itemKey(b) === key; });
            if (idx === -1) return;
            var entry = bag[idx];
            var qty = entry.qty || 1;
            if (qty <= 1) {
                bag.splice(idx, 1);
            } else {
                entry.qty = qty - 1;
            }
            saveBag(bag);
            updateBadge();
            syncCard(card);
            if (panel.classList.contains('open')) renderPanel();
        } catch {}
    });

    // Sync all card controls on load
    setTimeout(syncAllCards, 500);
    setTimeout(syncAllCards, 1500);

    updateBadge();
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

# ── Store chip selector (shown when "Store" sort is active) ───────────────────
store_sort_order = "Name (A-Z)"
if sort_option == "Store":
    all_merchants = sorted(df["merchant"].unique())
    # Init session state for selected store chips
    if "store_chips" not in st.session_state:
        st.session_state.store_chips = set(all_merchants)

    # Count deals per merchant
    merchant_counts = df["merchant"].value_counts().to_dict()

    # Render chips as Streamlit pills for each store
    store_chip_picks = st.pills(
        "Filter stores",
        options=all_merchants,
        default=list(st.session_state.store_chips),
        selection_mode="multi",
        label_visibility="collapsed",
    )
    st.session_state.store_chips = set(store_chip_picks) if store_chip_picks else set()

    # Sub-sort within stores
    store_sort_order = st.pills(
        "Sort within store",
        ["Name (A-Z)", "Price: Low-High", "Price: High-Low", "Best Deals"],
        default="Name (A-Z)",
        label_visibility="collapsed",
    )

    # Show deal counts per selected store
    if st.session_state.store_chips:
        counts_parts = []
        for m in sorted(st.session_state.store_chips):
            color = MERCHANT_COLORS.get(m, "#888")
            count = merchant_counts.get(m, 0)
            dot = f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};margin-right:3px"></span>'
            counts_parts.append(f'{dot}{m} ({count})')
        st.markdown(
            '<div style="font-size:0.8rem;color:#aaa;display:flex;flex-wrap:wrap;gap:0.6rem;">'
            + "".join(counts_parts) + '</div>',
            unsafe_allow_html=True,
        )

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
# When "Store" sort is active, intersect with store chip selection
active_stores = selected_stores
if sort_option == "Store" and hasattr(st.session_state, "store_chips"):
    active_stores = [s for s in selected_stores if s in st.session_state.store_chips]

filtered = df[
    df["merchant"].isin(active_stores) & df["category"].isin(selected_categories)
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
    if store_sort_order == "Price: Low-High":
        filtered = filtered.sort_values(
            ["merchant", "sort_price"], ascending=[True, True], na_position="last"
        )
    elif store_sort_order == "Price: High-Low":
        filtered = filtered.sort_values(
            ["merchant", "sort_price"], ascending=[True, False], na_position="last"
        )
    elif store_sort_order == "Best Deals":
        filtered = filtered.sort_values(
            ["merchant", "discount_pct"], ascending=[True, False], na_position="last"
        )
    else:
        filtered = filtered.sort_values(
            ["merchant", "name"], ascending=[True, True]
        )
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

            # Bag data attribute
            item_data = json_mod.dumps({
                "name": row["name"],
                "merchant": row["merchant"],
                "price": row["price"] or "",
                "image_url": row["image_url"] or "",
            })
            item_data_escaped = html_mod.escape(item_data)

            cards_html += f'<div class="{card_class}" data-item="{item_data_escaped}">'

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
            cards_html += (
                '<div class="bag-controls">'
                '<button class="bag-ctrl-btn bag-minus" title="Remove one">\u2212</button>'
                '<span class="bag-qty"></span>'
                '<button class="bag-ctrl-btn bag-plus" title="Add to bag">+</button>'
                '</div>'
            )
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

# ── Back to top button (rendered natively in Streamlit DOM) ──────────────────
st.markdown("""
<a href="#" id="back-to-top-anchor" style="
    position: fixed;
    bottom: 5rem;
    right: 2rem;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: rgba(128,128,128,0.25);
    color: #fff;
    font-size: 1.3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 99999;
    backdrop-filter: blur(8px);
    border: none;
    text-decoration: none;
" onclick="
    var selectors = [
        '[data-testid=stAppViewContainer] > section',
        '[data-testid=stAppViewContainer] > .main',
        '[data-testid=stAppViewContainer]',
        'section.main',
        '.stApp'
    ];
    selectors.forEach(function(s) {
        var el = document.querySelector(s);
        if (el) { el.scrollTop = 0; }
    });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    window.scrollTo(0, 0);
    var h = document.querySelector('h1');
    if (h) h.scrollIntoView({behavior: 'smooth'});
    return false;
" title="Back to top">\u2191</a>
""", unsafe_allow_html=True)
