import streamlit as st
import pandas as pd

st.set_page_config(page_title="Putaway Dashboard", layout="wide")
st.title("📦 Putaway Darkstore Dashboard")

# ---- CONFIGURE THIS ----
GITHUB_USER = "aditya-fk-minutes"
GITHUB_REPO = "Putaway-Dashboard"
# ------------------------

BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main"

@st.cache_data(ttl=3600)
def load(filename):
    df = pd.read_csv(f"{BASE}/{filename}")
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
        df = df.dropna(subset=['date'])
    return df

try:
    summary    = load("putaway_summary.csv")
    by_person  = load("by_person.csv")
    by_bin     = load("by_bin.csv")
    missing_df = load("missing_data.csv")
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
min_date, max_date = summary['date'].min(), summary['date'].max()
date_from = st.sidebar.date_input("From date", value=min_date, min_value=min_date, max_value=max_date)
date_to   = st.sidebar.date_input("To date",   value=max_date, min_value=min_date, max_value=max_date)

warehouses   = sorted(summary['destination_warehouse'].dropna().unique())
selected_wh  = st.sidebar.multiselect("Warehouse", warehouses, placeholder="All")

# --- Filter helper ---
def apply_filters(df, date_col='date'):
    out = df[(df[date_col] >= date_from) & (df[date_col] <= date_to)]
    if selected_wh:
        out = out[out['destination_warehouse'].isin(selected_wh)]
    return out

filtered_summary = apply_filters(summary)

# --- Overview Metrics ---
st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rows",                       f"{filtered_summary['total_rows'].sum():,}")
col2.metric("Empty grn_created_by",             f"{int(filtered_summary['empty_grn_created_by'].sum()):,}")
col3.metric("Empty grn_created_at",             f"{int(filtered_summary['empty_grn_created_at'].sum()):,}")
col4.metric("Empty inv_storage_location_label", f"{int(filtered_summary['empty_inv_storage_location_label'].sum()):,}")

st.divider()

# --- Putaway by Person ---
st.subheader("Putaway Count by Person")
filtered_person = apply_filters(by_person)
person_agg = filtered_person.groupby('grn_created_by')['items_putaway'].sum().sort_values(ascending=False).reset_index()
person_agg.columns = ['Person (grn_created_by)', 'Items Putaway']
st.dataframe(person_agg, use_container_width=True, hide_index=True)

st.divider()

# --- Putaway by Bin ---
st.subheader("Putaway Count by Bin (Storage Location)")
filtered_bin = apply_filters(by_bin)
bin_agg = filtered_bin.groupby('inv_storage_location_label')['items_putaway'].sum().sort_values(ascending=False).reset_index()
bin_agg.columns = ['Bin (inv_storage_location_label)', 'Items Putaway']
st.dataframe(bin_agg, use_container_width=True, hide_index=True)

st.divider()

# --- Missing Data Rows ---
st.subheader("Rows with Missing Data")
missing_df['grn_created_at'] = pd.to_datetime(missing_df['grn_created_at'], errors='coerce').dt.date
filtered_missing = missing_df[(missing_df['grn_created_at'] >= date_from) & (missing_df['grn_created_at'] <= date_to)]
if selected_wh:
    filtered_missing = filtered_missing[filtered_missing['destination_warehouse'].isin(selected_wh)]
st.write(f"**{len(filtered_missing):,} rows** with empty grn_created_by or inv_storage_location_label")
st.dataframe(filtered_missing, use_container_width=True, hide_index=True)
csv = filtered_missing.to_csv(index=False).encode('utf-8')
st.download_button("⬇️ Download Missing Rows", csv, "missing_data.csv", "text/csv")
