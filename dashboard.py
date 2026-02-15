import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import timedelta

# --- Configuration ---
DB_PATH = "/home/dantzler/python_workspace/weather_data.db"  # Path to your downloaded DB
TIMEZONE_LOCAL = "America/Los_Angeles"  # Target Timezone

st.set_page_config(page_title="Sensor Dashboard", layout="wide")

# --- 1. Load Data ---
@st.cache_data(ttl=60)  # Cache data for 60 seconds to avoid constant DB reads
def load_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Read entire table (efficient for local DBs up to ~1M rows)
    # If DB grows huge, write a SQL query with WHERE clauses based on inputs instead
    query = "SELECT * FROM readings ORDER BY timestamp DESC"
    df = pd.read_sql(query, conn)
    conn.close()

    # --- Timezone Handling ---
    # 1. Convert string timestamp to datetime objects (assumes UTC stored)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # 2. Convert to Local Time
    df['timestamp'] = df['timestamp'].dt.tz_convert(TIMEZONE_LOCAL)
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading database: {e}")
    st.stop()

# --- 2. Sidebar Controls ---
st.sidebar.header("Filter Data")

# Filter: Location
locations = df['location'].unique()
selected_location = st.sidebar.selectbox("Select Location", locations)

# Filter: Date Range
min_date = df['timestamp'].min().date()
max_date = df['timestamp'].max().date()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(max_date - timedelta(days=1), max_date), # Default to last 7 days
    min_value=min_date,
    max_value=max_date
)

# Filter: Sensors (Columns to plot)
# Exclude non-sensor columns
non_sensor_cols = ['id', 'timestamp', 'mac_address', 'location']
sensor_options = [col for col in df.columns if col not in non_sensor_cols]
selected_sensors = st.sidebar.multiselect(
    "Select Sensors to Plot", 
    options=sensor_options,
    default=['temp_bmp', 'humidity'] # Default selection
)

# --- 3. Apply Filters ---
mask = (
    (df['location'] == selected_location) &
    (df['timestamp'].dt.date >= date_range[0]) &
    (df['timestamp'].dt.date <= date_range[1])
)
filtered_df = df.loc[mask]

# --- 4. Main Dashboard ---
st.title(f"Weather Data: {selected_location}")
st.write(f"Showing {len(filtered_df)} readings from {date_range[0]} to {date_range[1]}")

if not filtered_df.empty and selected_sensors:
    # Plotly Line Chart
    fig = px.line(
        filtered_df, 
        x='timestamp', 
        y=selected_sensors,
        title=f"Sensor Readings over Time ({selected_location})",
        labels={"value": "Reading", "variable": "Sensor"},
        height=600
    )
    
    # Improve chart readability
    fig.update_xaxes(title_text="Time (Pacific)")
    fig.update_layout(hovermode="x unified") # Show all values on hover
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Optional: Show raw data
    with st.expander("View Raw Data"):
        st.dataframe(filtered_df)
else:
    st.warning("No data available for the selected filters.")
