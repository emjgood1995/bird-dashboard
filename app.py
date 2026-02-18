import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

# Connect to DB
conn = sqlite3.connect("birds.db")
df = pd.read_sql_query("SELECT * FROM detections", conn)

# Combine datetime
df["timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors="coerce")
df["hour"] = df["timestamp"].dt.hour
df["week"] = df["timestamp"].dt.isocalendar().week
df["month"] = df["timestamp"].dt.month

st.title("🦜 Bird Detection Dashboard")

# Sidebar filters
st.sidebar.header("Filters")

min_conf = st.sidebar.slider(
    "Minimum Confidence",
    float(df["Confidence"].min()),
    float(df["Confidence"].max()),
    float(df["Confidence"].min())
)

df = df[df["Confidence"] >= min_conf]

species_list = st.sidebar.multiselect(
    "Select Species",
    df["Com_Name"].unique()
)

if species_list:
    df = df[df["Com_Name"].isin(species_list)]

# Tabs like PowerBI
tab1, tab2, tab3, tab4 = st.tabs([
    "Most Common Species",
    "Time of Day",
    "Weekly Trends",
    "Monthly Trends"
])

with tab1:
    top = (
        df["Com_Name"]
        .value_counts()
        .head(20)
        .reset_index()
    )
    top.columns = ["Species", "Count"]
    fig = px.bar(top, x="Count", y="Species", orientation="h")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    hourly = df.groupby("hour").size().reset_index(name="Count")
    fig = px.line(hourly, x="hour", y="Count")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    weekly = df.groupby("week").size().reset_index(name="Count")
    fig = px.line(weekly, x="week", y="Count")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    monthly = df.groupby("month").size().reset_index(name="Count")
    fig = px.line(monthly, x="month", y="Count")
    st.plotly_chart(fig, use_container_width=True)
