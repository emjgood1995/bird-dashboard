import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

# ---- Load data ----
@st.cache_data
def load_data():
    # --- load detections ---
    conn = sqlite3.connect("birds.db")
    df = pd.read_sql_query("SELECT * FROM detections", conn)
    conn.close()

    # Combine Date + Time into timestamp
    df["timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors="coerce")

    # Time features
    df["hour"] = df["timestamp"].dt.hour
    df["week"] = df["timestamp"].dt.isocalendar().week.astype(int)
    df["month"] = df["timestamp"].dt.month.astype(int)

    # --- load metadata (UK statuses) ---
    meta = pd.read_excel("UK_Birds_Generalized_Status.xlsx")

    # Normalize / rename to match DB column
    meta = meta.rename(columns={
        "Latin Name": "Sci_Name",
        "Common Name": "UK_Common_Name",
        "Status": "UK_Status"
    })

    # Keep only what we need (avoid duplicate column names)
    meta = meta[["Sci_Name", "UK_Common_Name", "UK_Status"]].drop_duplicates()

    # --- merge ---
    df = df.merge(meta, on="Sci_Name", how="left")

    # Flag missing metadata
    df["UK_Status"] = df["UK_Status"].fillna("Review Recording")

    return df

df = load_data()

st.title("🦜 Bird Detection Dashboard")

# ---- Sidebar filters ----
st.sidebar.header("Filters")

# Confidence filter
min_conf = st.sidebar.slider(
    "Minimum Confidence",
    float(df["Confidence"].min()),
    float(df["Confidence"].max()),
    float(df["Confidence"].min())
)

filtered = df[df["Confidence"] >= min_conf].copy()

# Species filter
species_list = st.sidebar.multiselect(
    "Select Species",
    sorted(filtered["Com_Name"].dropna().unique())
)
if species_list:
    filtered = filtered[filtered["Com_Name"].isin(species_list)]

status_list = st.sidebar.multiselect(
    "UK Status",
    sorted(filtered["UK_Status"].dropna().unique())
)
if status_list:
    filtered = filtered[filtered["UK_Status"].isin(status_list)]

# ✅ Update 1: Date range filter
st.sidebar.subheader("Date Range")

# Guard against missing timestamps
filtered_ts = filtered.dropna(subset=["timestamp"]).copy()
min_date = filtered_ts["timestamp"].min().date()
max_date = filtered_ts["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    (min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# date_input can return a single date if user clicks oddly; normalize it
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range
    end_date = date_range

filtered = filtered[
    (filtered["timestamp"].dt.date >= start_date) &
    (filtered["timestamp"].dt.date <= end_date)
].copy()

# ✅ Update 2: KPI cards (PowerBI-style summary)
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Detections", f"{len(filtered):,}")
kpi2.metric("Unique Species", f"{filtered['Com_Name'].nunique():,}")
kpi3.metric("Average Confidence", f"{filtered['Confidence'].mean():.2f}" if len(filtered) else "—")

st.divider()

# ---- Tabs ----
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Most Common Species",
    "Time of Day",
    "Weekly Trends",
    "Monthly Trends",
    "Heatmap",
    "Community Composition",
    "Status Over Time",
    "Status by Hour",
    "Review / Richness"
])


with tab1:
    top = filtered["Com_Name"].value_counts().head(20).reset_index()
    top.columns = ["Species", "Count"]
    fig = px.bar(top, x="Count", y="Species", orientation="h",
                 title="Top 20 Most Common Species")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    hourly = filtered.groupby("hour").size().reset_index(name="Count")
    fig = px.line(hourly, x="hour", y="Count", title="Activity by Hour of Day")
    fig.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    weekly = filtered.groupby("week").size().reset_index(name="Count")
    fig = px.line(weekly, x="week", y="Count", title="Weekly Detection Trends")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    monthly = filtered.groupby("month").size().reset_index(name="Count")
    fig = px.line(monthly, x="month", y="Count", title="Monthly Detection Trends")
    fig.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig, use_container_width=True)

# ✅ Update 3: Heatmap (Hour × Month)
with tab5:
    heatmap = (
        filtered.groupby(["month", "hour"])
        .size()
        .reset_index(name="Count")
    )

    fig = px.density_heatmap(
        heatmap,
        x="hour",
        y="month",
        z="Count",
        title="Activity Heatmap (Hour vs Month)",
    )
    fig.update_layout(xaxis=dict(dtick=1), yaxis=dict(dtick=1))
    st.plotly_chart(fig, use_container_width=True)

with tab6:
    st.subheader("Community Composition by Hour (Top 20 species, %)")

    top_species = (
        filtered["Com_Name"]
        .value_counts()
        .head(20)
        .index
    )

    comp = filtered[filtered["Com_Name"].isin(top_species)].copy()

    comp_hour = (
        comp.groupby(["hour", "Com_Name"])
        .size()
        .reset_index(name="Count")
    )

    # Convert to % per hour
    comp_hour["Percent"] = (
        comp_hour.groupby("hour")["Count"]
        .transform(lambda x: (x / x.sum()) * 100)
    )

    # Make hours appear even if empty
    comp_hour = comp_hour.sort_values(["hour", "Percent"], ascending=[True, False])

    fig = px.bar(
        comp_hour,
        x="hour",
        y="Percent",
        color="Com_Name",
        title="Community composition by hour (%)",
        labels={"hour": "Hour of day", "Percent": "% of detections"}
    )
    fig.update_layout(barmode="stack", xaxis=dict(dtick=1))
    st.plotly_chart(fig, use_container_width=True)

with tab7:
    st.subheader("Status Composition Over Time (Monthly %)")

    # Month as YYYY-MM for clean x-axis
    tmp = filtered.dropna(subset=["timestamp"]).copy()
    tmp["month_period"] = tmp["timestamp"].dt.to_period("M").astype(str)

    status_month = (
        tmp.groupby(["month_period", "UK_Status"])
        .size()
        .reset_index(name="Count")
    )

    # Convert to % per month
    status_month["Percent"] = (
        status_month.groupby("month_period")["Count"]
        .transform(lambda x: (x / x.sum()) * 100)
    )

    fig = px.area(
        status_month,
        x="month_period",
        y="Percent",
        color="UK_Status",
        title="Monthly status composition (%)",
        labels={"month_period": "Month", "Percent": "% of detections"}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab8:
    st.subheader("Activity by Hour, split by Status")

    status_hour = (
        filtered.groupby(["hour", "UK_Status"])
        .size()
        .reset_index(name="Count")
    )

    fig = px.line(
        status_hour,
        x="hour",
        y="Count",
        color="UK_Status",
        markers=True,
        title="Detections by hour (by status)",
        labels={"hour": "Hour of day", "Count": "Detections"}
    )
    fig.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig, use_container_width=True)

with tab9:
    st.subheader("Species Richness Over Time (Unique species)")

    tmp = filtered.dropna(subset=["timestamp"]).copy()
    tmp["month_period"] = tmp["timestamp"].dt.to_period("M").astype(str)

    richness_month = (
        tmp.groupby("month_period")["Com_Name"]
        .nunique()
        .reset_index(name="Unique_Species")
    )

    fig = px.line(
        richness_month,
        x="month_period",
        y="Unique_Species",
        markers=True,
        title="Unique species per month",
        labels={"month_period": "Month", "Unique_Species": "Unique species"}
    )
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Review Recording: Top Species to Check")

    review = filtered[filtered["UK_Status"] == "Review Recording"].copy()

    if len(review) == 0:
        st.info("No 'Review Recording' rows in the current filter.")
    else:
        top_review = (
            review["Sci_Name"]
            .value_counts()
            .head(20)
            .reset_index()
        )
        top_review.columns = ["Sci_Name", "Count"]

        fig = px.bar(
            top_review,
            x="Count",
            y="Sci_Name",
            orientation="h",
            title="Top 20 Latin names needing review"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Review Recording: Confidence by Hour")

        conf_hour = (
            review.groupby("hour")["Confidence"]
            .mean()
            .reset_index(name="Avg_Confidence")
        )

        fig = px.line(
            conf_hour,
            x="hour",
            y="Avg_Confidence",
            markers=True,
            title="Average confidence by hour (Review Recording only)",
            labels={"hour": "Hour of day", "Avg_Confidence": "Avg confidence"}
        )
        fig.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig, use_container_width=True)

