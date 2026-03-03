"""Hardcoded west-end Edmonton store locations."""

STORES = [
    {
        "name": "Real Canadian Superstore (Mayfield)",
        "merchant": "Real Canadian Superstore",
        "address": "16940 109 Ave NW, Edmonton",
        "lat": 53.5561,
        "lon": -113.5878,
        "color": "red",
    },
    {
        "name": "Real Canadian Superstore (West End)",
        "merchant": "Real Canadian Superstore",
        "address": "17010 90 Ave NW, Edmonton",
        "lat": 53.5241,
        "lon": -113.5870,
        "color": "red",
    },
    {
        "name": "Walmart (WEM)",
        "merchant": "Walmart",
        "address": "8882 170 St NW, Edmonton",
        "lat": 53.5225,
        "lon": -113.6230,
        "color": "blue",
    },
    {
        "name": "Walmart (Mayfield Common)",
        "merchant": "Walmart",
        "address": "16930 109 Ave NW, Edmonton",
        "lat": 53.5563,
        "lon": -113.5885,
        "color": "blue",
    },
    {
        "name": "Save-On-Foods (Jasper Gates)",
        "merchant": "Save-On-Foods",
        "address": "14927 Stony Plain Rd NW, Edmonton",
        "lat": 53.5438,
        "lon": -113.5672,
        "color": "green",
    },
    {
        "name": "No Frills (West Edmonton)",
        "merchant": "No Frills",
        "address": "9511 149 St NW, Edmonton",
        "lat": 53.5195,
        "lon": -113.5618,
        "color": "orange",
    },
    {
        "name": "Safeway (Meadowlark)",
        "merchant": "Safeway",
        "address": "15710 87 Ave NW, Edmonton",
        "lat": 53.5183,
        "lon": -113.5765,
        "color": "purple",
    },
    {
        "name": "Safeway (Callingwood)",
        "merchant": "Safeway",
        "address": "6655 178 St NW, Edmonton",
        "lat": 53.4920,
        "lon": -113.6310,
        "color": "purple",
    },
    {
        "name": "Costco (West Edmonton)",
        "merchant": "Costco",
        "address": "10020 180 St NW, Edmonton",
        "lat": 53.5155,
        "lon": -113.6380,
        "color": "darkred",
    },
    {
        "name": "FreshCo (West Edmonton)",
        "merchant": "FreshCo",
        "address": "10706 107 Ave NW, Edmonton",
        "lat": 53.5455,
        "lon": -113.5250,
        "color": "cadetblue",
    },
]

# Quick lookup: merchant name → list of store dicts
STORES_BY_MERCHANT = {}
for _s in STORES:
    STORES_BY_MERCHANT.setdefault(_s["merchant"], []).append(_s)

MERCHANT_NAMES = sorted(STORES_BY_MERCHANT.keys())
