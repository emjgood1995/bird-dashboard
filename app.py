import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

# ---- Nature UI styling (soft, not kitsch) ----
st.markdown(
    """
    <style>
      .stApp {
        background: radial-gradient(1200px 600px at 10% 0%,
          rgba(178, 223, 180, 0.35) 0%,
          rgba(248, 246, 239, 1) 45%,
          rgba(240, 246, 250, 1) 100%);
        color: #1f2937;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
      }

      .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
      }

      section[data-testid="stSidebar"] > div {
        background: rgba(255, 255, 255, 0.72);
        border-right: 1px solid rgba(31, 41, 55, 0.08);
        backdrop-filter: blur(10px);
      }

      h1, h2, h3 { letter-spacing: -0.02em; }

      /* Softer tabs */
      button[role="tab"] {
        border-radius: 999px !important;
        padding: 8px 14px !important;
        margin-right: 6px !important;
      }

      /* KPI cards */
      div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.75);
        border: 1px solid rgba(31, 41, 55, 0.10);
        border-radius: 16px;
        padding: 14px 14px;
        box-shadow: 0 8px 30px rgba(31, 41, 55, 0.08);
      }

      /* Plotly modebar less shouty */
      .js-plotly-plot .plotly .modebar { opacity: 0.25; }
      .js-plotly-plot:hover .plotly .modebar { opacity: 0.9; }
    </style>
    """,
    unsafe_allow_html=True
)

def style_fig(fig):
    """Make Plotly feel calm + nature-friendly."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(255,255,255,0.0)",
        plot_bgcolor="rgba(255,255,255,0.0)",
        font=dict(color="#1f2937"),
        title=dict(font=dict(size=20)),
        legend=dict(
            bgcolor="rgba(255,255,255,0.65)",
            bordercolor="rgba(31,41,55,0.12)",
            borderwidth=1
        ),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(31,41,55,0.08)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(31,41,55,0.08)")
    return fig

# ---- Shared natural palette ----
NATURE_PALETTE = [
    "#2E7D32", "#66BB6A", "#1B5E20", "#81C784",
    "#4E342E", "#6D4C41", "#8D6E63", "#1565C0",
    "#42A5F5", "#5C6BC0", "#9CCC65", "#A1887F",
    "#FFB74D", "#8E24AA", "#00897B", "#689F38",
    "#546E7A", "#F9A825", "#7CB342", "#3949AB",
]

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
st.caption("A calm view of detections across time, seasons, and community composition.")

# ---- Sidebar filters ----
st.sidebar.header("Explore")
st.sidebar.caption("Refine detections, then browse the tabs for patterns.")

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

# Date range filter
st.sidebar.subheader("Date Range")
filtered_ts = filtered.dropna(subset=["timestamp"]).copy()
min_date = filtered_ts["timestamp"].min().date()
max_date = filtered_ts["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    (min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range
    end_date = date_range

filtered = filtered[
    (filtered["timestamp"].dt.date >= start_date) &
    (filtered["timestamp"].dt.date <= end_date)
].copy()

# Checkbox: exclude Review Recording rows from charts
exclude_review = st.sidebar.checkbox("Exclude 'Review Recording' from graphs", value=True)

# Keep a copy for Tab 9 (review stats), regardless of checkbox
review_df = filtered[filtered["UK_Status"] == "Review Recording"].copy()

# Apply the checkbox filter to the main dataframe used everywhere else
if exclude_review:
    filtered = filtered[filtered["UK_Status"] != "Review Recording"].copy()

# KPI cards
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
    st.plotly_chart(style_fig(fig), use_container_width=True)

with tab2:
    hourly = filtered.groupby("hour").size().reset_index(name="Count")
    fig = px.line(hourly, x="hour", y="Count", title="Activity by Hour of Day")
    fig.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(style_fig(fig), use_container_width=True)

with tab3:
    weekly = filtered.groupby("week").size().reset_index(name="Count")
    fig = px.line(weekly, x="week", y="Count", title="Weekly Detection Trends")
    st.plotly_chart(style_fig(fig), use_container_width=True)

with tab4:
    monthly = filtered.groupby("month").size().reset_index(name="Count")
    fig = px.line(monthly, x="month", y="Count", title="Monthly Detection Trends")
    fig.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(style_fig(fig), use_container_width=True)

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
    st.plotly_chart(style_fig(fig), use_container_width=True)

with tab6:
    st.subheader("Community Composition by Hour (Top 20 species, %)")

    comp_df = filtered.dropna(subset=["timestamp"]).copy()
    comp_df["year"] = comp_df["timestamp"].dt.year.astype(int)
    comp_df["month_num"] = comp_df["timestamp"].dt.month.astype(int)
    comp_df["hour"] = comp_df["timestamp"].dt.hour.astype(int)

    MONTHS = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December"),
    ]
    month_num_by_name = {n: m for m, n in MONTHS}

    def season_from_month(m: int) -> str:
        if m in (3, 4, 5): return "Spring"
        if m in (6, 7, 8): return "Summer"
        if m in (9, 10, 11): return "Autumn"
        return "Winter"

    comp_df["season"] = comp_df["month_num"].apply(season_from_month)

    c1, c2, c3, c4 = st.columns([1.2, 1.0, 1.2, 1.0], gap="large")

    years_all = sorted(comp_df["year"].unique())
    month_names = [name for _, name in MONTHS]

    with c1:
        year_mode = st.selectbox("Years", ["All years", "Select years"], index=0)
        selected_years = []
        if year_mode == "Select years":
            selected_years = st.multiselect(" ", years_all, default=years_all[-1:] if years_all else [])

    with c2:
        selected_season = st.selectbox("Season", ["All", "Spring", "Summer", "Autumn", "Winter"], index=0)

    with c3:
        month_mode = st.selectbox("Months", ["All months", "Choose month"], index=0)
        chosen_month = None
        if month_mode == "Choose month":
            chosen_month = st.selectbox(" ", month_names, index=5)  # default June

    with c4:
        compare_mode = st.checkbox("Compare two months", value=False)

    view_df = comp_df.copy()

    if year_mode == "Select years" and selected_years:
        view_df = view_df[view_df["year"].isin(selected_years)].copy()

    if selected_season != "All":
        view_df = view_df[view_df["season"] == selected_season].copy()

    if month_mode == "Choose month" and chosen_month:
        view_df = view_df[view_df["month_num"] == month_num_by_name[chosen_month]].copy()

    if len(view_df) == 0:
        st.info("No data available for the selected filters.")
    else:
        def composition_plot(df_in: pd.DataFrame, title: str):
            if len(df_in) == 0:
                st.warning("No data for this selection.")
                return

            top_species = df_in["Com_Name"].value_counts().head(20).index.tolist()
            df_in = df_in[df_in["Com_Name"].isin(top_species)].copy()

            comp_hour = (
                df_in.groupby(["hour", "Com_Name"])
                .size()
                .reset_index(name="Count")
            )

            comp_hour["Percent"] = (
                comp_hour.groupby("hour")["Count"]
                .transform(lambda x: (x / x.sum()) * 100)
            )

            palette = NATURE_PALETTE
            color_map = {sp: palette[i % len(palette)] for i, sp in enumerate(top_species)}

            fig = px.bar(
                comp_hour,
                x="hour",
                y="Percent",
                color="Com_Name",
                title=title,
                labels={"hour": "Hour of day", "Percent": "% of detections"},
                category_orders={"Com_Name": top_species},
                color_discrete_map=color_map
            )
            fig.update_layout(barmode="stack", xaxis=dict(dtick=1))
            st.plotly_chart(style_fig(fig), use_container_width=True)

        if compare_mode:
            left, right = st.columns(2, gap="large")
            with left:
                month_a = st.selectbox("Month A", month_names, index=5, key="cc_month_a")  # June
            with right:
                month_b = st.selectbox("Month B", month_names, index=6, key="cc_month_b")  # July

            df_a = view_df[view_df["month_num"] == month_num_by_name[month_a]].copy()
            df_b = view_df[view_df["month_num"] == month_num_by_name[month_b]].copy()

            years_label = "All years" if year_mode == "All years" else ", ".join(map(str, selected_years))
            season_label = "All seasons" if selected_season == "All" else selected_season

            l, r = st.columns(2, gap="large")
            with l:
                composition_plot(df_a, f"{month_a} • {years_label} • {season_label}")
            with r:
                composition_plot(df_b, f"{month_b} • {years_label} • {season_label}")

        else:
            years_label = "All years" if year_mode == "All years" else ", ".join(map(str, selected_years))
            season_label = "All seasons" if selected_season == "All" else selected_season
            month_label = "All months" if month_mode == "All months" else chosen_month
            composition_plot(view_df, f"{month_label} • {years_label} • {season_label}")

with tab7:
    st.subheader("Status Composition Over Time (Monthly %)")

    tmp = filtered.dropna(subset=["timestamp"]).copy()
    tmp["month_period"] = tmp["timestamp"].dt.to_period("M").astype(str)

    status_month = (
        tmp.groupby(["month_period", "UK_Status"])
        .size()
        .reset_index(name="Count")
    )

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
    st.plotly_chart(style_fig(fig), use_container_width=True)

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
    st.plotly_chart(style_fig(fig), use_container_width=True)

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
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.subheader("Review Recording: Top Species to Check")

    review = review_df

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
        st.plotly_chart(style_fig(fig), use_container_width=True)

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
        st.plotly_chart(style_fig(fig), use_container_width=True)
