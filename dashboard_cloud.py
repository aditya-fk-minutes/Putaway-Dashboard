import streamlit as st
import pandas as pd

st.set_page_config(page_title="Putaway Dashboard", layout="wide")
st.title("📦 Putaway Darkstore Dashboard")

# ---- CONFIGURE THIS ----
GITHUB_USER = "aditya-fk-minutes"
GITHUB_REPO = "Putaway-Dashboard"
# ------------------------

URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/putaway_detail.csv"

@st.cache_data(ttl=3600)
def load():
    df = pd.read_csv(URL)
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    return df.dropna(subset=['date', 'person', 'bin'])

try:
    df = load()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
min_date, max_date = df['date'].min(), df['date'].max()
date_from = st.sidebar.date_input("From date", value=min_date, min_value=min_date, max_value=max_date)
date_to   = st.sidebar.date_input("To date",   value=max_date, min_value=min_date, max_value=max_date)

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
