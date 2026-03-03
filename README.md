# Edmonton Grocery Deals Finder

Browse current flyer deals from west-end Edmonton grocery stores. Pulls data from Flipp's public API.

## Stores Tracked
- Real Canadian Superstore (Mayfield, West End)
- Walmart (WEM, Mayfield Common)
- Save-On-Foods (Jasper Gates)
- No Frills (West Edmonton)
- Safeway (Meadowlark, Callingwood)
- Costco (West Edmonton)
- FreshCo (West Edmonton)

## Features
- Search deals by keyword
- Filter by store and category
- Sort by price, name, or store
- Map view with store locations and top deals
- Auto-refreshes every hour

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud
1. Push to GitHub
2. Connect repo on [share.streamlit.io](https://share.streamlit.io)
3. No secrets needed — Flipp API is public
