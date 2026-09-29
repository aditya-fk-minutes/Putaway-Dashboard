import streamlit as st
import pandas as pd

st.set_page_config(page_title="Putaway Dashboard", layout="wide")
st.title("📦 Putaway Darkstore Dashboard")

# ---- CONFIGURE THIS ----
GITHUB_USER = "aditya-fk-minutes"
GITHUB_REPO = "Putaway-Dashboard"   # e.g. "putaway-dashboard"
GITHUB_FILE = "putaway_summary.csv"
# ------------------------

RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{GITHUB_FILE}"

@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv(RAW_URL)
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")

min_date = df['date'].min()
max_date = df['date'].max()
date_from = st.sidebar.date_input("From date", value=min_date, min_value=min_date, max_value=max_date)
date_to = st.sidebar.date_input("To date", value=max_date, min_value=min_date, max_value=max_date)

warehouses = sorted(df['destination_warehouse'].dropna().unique())
selected_wh = st.sidebar.multiselect("Warehouse", warehouses, placeholder="All")

# --- Apply filters ---
filtered = df[(df['date'] >= date_from) & (df['date'] <= date_to)]
if selected_wh:
    filtered = filtered[filtered['destination_warehouse'].isin(selected_wh)]

# --- Metrics ---
st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rows", f"{filtered['total_rows'].sum():,}")
col2.metric("Empty grn_created_by", f"{int(filtered['empty_grn_created_by'].sum()):,}")
col3.metric("Empty grn_created_at", f"{int(filtered['empty_grn_created_at'].sum()):,}")
col4.metric("Empty inv_storage_location_label", f"{int(filtered['empty_inv_storage_location_label'].sum()):,}")

st.divider()

# --- Rows per Warehouse ---
st.subheader("Rows per Warehouse")
wh_summary = filtered.groupby('destination_warehouse')['total_rows'].sum().sort_values(ascending=False)
st.bar_chart(wh_summary)

st.divider()

# --- Daily Trend ---
st.subheader("Daily Trend")
daily = filtered.groupby('date')['total_rows'].sum()
st.line_chart(daily)

st.divider()

# --- Summary Table ---
st.subheader("Summary Table")
st.dataframe(filtered.sort_values(['date', 'destination_warehouse']), use_container_width=True)
