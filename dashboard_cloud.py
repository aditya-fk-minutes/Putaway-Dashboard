import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Putaway Dashboard", layout="wide")

# ---- CONFIGURE THIS ----
GITHUB_USER = "aditya-fk-minutes"
GITHUB_REPO = "Putaway-Dashboard"
# ------------------------

BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main"
URL = f"{BASE}/putaway_detail.csv"
API_BASE = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}"

@st.cache_data(ttl=3600)
def get_last_updated():
    try:
        r = requests.get(f"{API_BASE}/commits?path=putaway_detail.csv.manifest&per_page=1")
        if r.status_code != 200:
            r = requests.get(f"{API_BASE}/commits?path=putaway_detail.csv&per_page=1")
        commits = r.json()
        if commits:
            ts = commits[0]['commit']['committer']['date']  # e.g. "2024-09-26T08:32:11Z"
            from datetime import timezone
            import datetime
            dt = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            # Convert to IST (UTC+5:30)
            ist = dt + datetime.timedelta(hours=5, minutes=30)
            return ist.strftime("%d %b %Y, %I:%M %p IST")
    except Exception:
        pass
    return "Unknown"

@st.cache_data(ttl=3600)
def load():
    import io
    # Check if file was split into parts
    manifest_url = f"{BASE}/putaway_detail.csv.manifest"
    r = requests.get(manifest_url)
    if r.status_code == 200:
        parts = r.text.strip().split("\n")
        chunks = [requests.get(f"{BASE}/{p}").content for p in parts]
        content = b"".join(chunks)
        df = pd.read_csv(io.BytesIO(content))
    else:
        df = pd.read_csv(URL)
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    return df.dropna(subset=['date', 'person', 'bin'])

try:
    df = load()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

# --- Title + Last Updated ---
col_title, col_updated = st.columns([3, 1])
with col_title:
    st.title("📦 Putaway Darkstore Dashboard")
with col_updated:
    last_updated = get_last_updated()
    st.markdown(f"<div style='text-align:right; padding-top:18px; color:gray; font-size:13px;'>🕐 Last updated: <b>{last_updated}</b></div>", unsafe_allow_html=True)

st.info("ℹ️ This dashboard will be updated every day by 10AM with D-1 Data.")

# --- Sidebar Filters ---
st.sidebar.header("Filters")
from datetime import date, timedelta
min_date, max_date = df['date'].min(), df['date'].max()
yesterday = max_date  # most recent date in data = D-1
date_from = st.sidebar.date_input("From date", value=yesterday, min_value=min_date, max_value=max_date)
date_to   = st.sidebar.date_input("To date",   value=yesterday, min_value=min_date, max_value=max_date)

warehouses  = sorted(df['warehouse'].dropna().unique())
selected_wh = st.sidebar.multiselect("Warehouse", warehouses, placeholder="All")

persons = sorted(df['person'].dropna().unique())
selected_person = st.sidebar.multiselect("LDAP ID", persons, placeholder="All")

bins = sorted(df['bin'].dropna().unique())
selected_bin = st.sidebar.multiselect("Storage Bin Label", bins, placeholder="All")

# --- Apply Filters ---
filtered = df[(df['date'] >= date_from) & (df['date'] <= date_to)]
if selected_wh:
    filtered = filtered[filtered['warehouse'].isin(selected_wh)]
if selected_person:
    filtered = filtered[filtered['person'].isin(selected_person)]
if selected_bin:
    filtered = filtered[filtered['bin'].isin(selected_bin)]

# --- Table ---
display = filtered[['date', 'warehouse', 'person', 'bin', 'items_putaway']].copy()
display.columns = ['Date', 'Warehouse', 'LDAP ID', 'Storage Bin Label', 'Items Putaway']

st.subheader(f"Putaway Activity — {len(display):,} records")
st.dataframe(display.sort_values(['Date', 'Warehouse', 'LDAP ID']), use_container_width=True, hide_index=True)

csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button("⬇️ Download", csv, "putaway_activity.csv", "text/csv")
