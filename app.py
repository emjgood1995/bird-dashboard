import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide", page_title="Garden Bird Dashboard", page_icon="🐦")

# ---- Styling ----
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cabin:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

  :root {
    --bg:     #f5f3ee;
    --panel:  #ffffff;
    --text:   #1a2416;
    --muted:  #4a5c44;
    --border: rgba(26,36,22,0.11);
    --shadow: 0 4px 20px rgba(26,36,22,0.07);
    --radius: 14px;
    --accent: #3d6b44;
  }

  .stApp {
    background: var(--bg);
    font-family: 'Cabin', ui-sans-serif, system-ui, sans-serif !important;
  }
  /* Apply Cabin to text-bearing elements — NOT * (which broke icon fonts) */
  .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
  .stApp p, .stApp label, .stApp div, .stApp a, .stApp li,
  .stApp td, .stApp th,
  .stApp input, .stApp textarea, .stApp select,
  .stApp .stRadio label {
    font-family: 'Cabin', ui-sans-serif, system-ui, sans-serif !important;
  }

  .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1280px;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] > div {
    background: #edeae0 !important;
    border-right: 1px solid var(--border) !important;
  }
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] p,
  section[data-testid="stSidebar"] span {
    color: var(--muted) !important;
    font-size: 0.88rem;
    font-weight: 500;
  }

  /* Headings */
  h1 {
    color: var(--text) !important;
    letter-spacing: -0.03em;
    font-weight: 700;
  }
  h2, h3 {
    color: var(--text) !important;
    letter-spacing: -0.02em;
  }

  /* Sidebar navigation radio buttons */
  section[data-testid="stSidebar"] .stRadio > div {
    gap: 2px !important;
  }
  section[data-testid="stSidebar"] .stRadio label {
    padding: 8px 12px !important;
    border-radius: 10px !important;
    cursor: pointer !important;
    transition: background 0.15s ease !important;
  }
  section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(61,107,68,0.08) !important;
  }
  section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
  section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
    background: rgba(61,107,68,0.12) !important;
    color: var(--accent) !important;
    font-weight: 600 !important;
  }

  /* KPI metric cards */
  div[data-testid="stMetric"] {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 18px 22px !important;
    box-shadow: var(--shadow) !important;
  }
  div[data-testid="stMetric"] label {
    color: var(--muted) !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-weight: 700 !important;
  }

  /* Inputs */
  div[data-baseweb="select"] * ,
  div[data-baseweb="input"] * ,
  div[data-baseweb="textarea"] * {
    color: var(--text) !important;
  }
  div[data-baseweb="select"] > div,
  div[data-baseweb="input"] > div,
  div[data-baseweb="textarea"] > div {
    background: #ffffff !important;
    border-radius: 10px !important;
    border-color: var(--border) !important;
  }

  /* Plotly modebar */
  .js-plotly-plot .plotly .modebar { opacity: 0.2; }
  .js-plotly-plot:hover .plotly .modebar { opacity: 0.85; }

  hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

  /* Header: transparent so it takes no visual space but keeps sidebar toggle in the DOM */
  header[data-testid="stHeader"] {
    background: var(--bg) !important;
    box-shadow: none !important;
  }
  /* Hide only the menu button inside the toolbar — NOT the toolbar container itself,
     which breaks the header flexbox layout and makes the expand button disappear */
  [data-testid="stMainMenu"] { display: none !important; }
  .stDecoration { display: none !important; }

  /* ── Sidebar toggle buttons — visual only, don't touch font/icons ──── */
  [data-testid="stSidebarCollapseButton"],
  [data-testid="stSidebarNavExpandButton"] {
    visibility: visible !important;
    opacity: 1 !important;
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(26,36,22,0.22) !important;
  }
  /* Force icon colour to white so it reads clearly against the green */
  [data-testid="stSidebarCollapseButton"] span,
  [data-testid="stSidebarCollapseButton"] svg {
    color: #ffffff !important;
    fill: #ffffff !important;
  }
  [data-testid="stSidebarCollapseButton"]:hover,
  [data-testid="stSidebarNavExpandButton"]:hover {
    background: #2d5233 !important;
  }
</style>
""", unsafe_allow_html=True)


# ---- Colour system ----
# A cohesive British-garden palette: foliage greens, earth tones, sky blues,
# harvest golds, mossy olives, hedgerow berries. Nothing electric or garish.
NATURE_PALETTE = [
    "#3d6b44",  # deep forest
    "#4a7090",  # lake blue
    "#b89040",  # harvest gold
    "#7a5c3d",  # dark bark
    "#6b7c4a",  # olive moss
    "#8c5a70",  # bramble berry
    "#5c8c5c",  # leaf green
    "#6a90b0",  # sky blue
    "#d4ac60",  # warm amber
    "#a07850",  # warm earth
    "#8c9c60",  # lichen
    "#4a5c70",  # dusk blue
    "#c47a5a",  # autumn terracotta
    "#7aaa6a",  # fresh growth
    "#8ab4c8",  # pale sky
    "#c4a07a",  # sandy loam
    "#a3c47a",  # spring sage
    "#607080",  # slate
    "#8c6b8c",  # heather
    "#90a890",  # soft sage
]

# Meaningful colours for UK conservation status
STATUS_COLORS = {
    "Green":            "#5c8c5c",
    "Amber":            "#d4ac60",
    "Red":              "#c47a5a",
    "Review Recording": "#8c9c8c",
    "Introduced":       "#4a7090",
    "Migrant":          "#6a90b0",
    "Scarce Migrant":   "#8ab4c8",
}

PRIMARY   = "#3d6b44"  # deep forest — main single-series colour
SECONDARY = "#4a7090"  # lake blue
TERTIARY  = "#b89040"  # harvest gold

# Green-to-forest colorscale for heatmap
HEATMAP_SCALE = [
    [0.00, "#f5f3ee"],
    [0.20, "#c8dfa0"],
    [0.50, "#7aaa6a"],
    [0.75, "#5c8c5c"],
    [1.00, "#2d5233"],
]

MONTH_LABELS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def status_color_map(statuses):
    """Build a color_discrete_map for a list of status strings."""
    cmap = {}
    fallback = [c for c in NATURE_PALETTE if c not in STATUS_COLORS.values()]
    fi = 0
    for s in statuses:
        if s in STATUS_COLORS:
            cmap[s] = STATUS_COLORS[s]
        else:
            cmap[s] = fallback[fi % len(fallback)]
            fi += 1
    return cmap


def style_fig(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#fafaf8",
        font=dict(
            family="Cabin, ui-sans-serif, system-ui, sans-serif",
            color="#1a2416",
            size=13,
        ),
        title=dict(
            font=dict(size=19, color="#1a2416"),
            x=0.01,
            xanchor="left",
        ),
        legend=dict(
            font=dict(size=12, color="#1a2416"),
            title=dict(font=dict(size=12, color="#4a5c44")),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="rgba(26,36,22,0.10)",
            borderwidth=1,
        ),
        margin=dict(l=10, r=10, t=58, b=10),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="rgba(26,36,22,0.15)",
            font=dict(size=13, color="#1a2416"),
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(26,36,22,0.06)",
        zeroline=False,
        linecolor="rgba(26,36,22,0.10)",
        title_font=dict(size=13, color="#4a5c44"),
        tickfont=dict(size=12, color="#4a5c44"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(26,36,22,0.06)",
        zeroline=False,
        linecolor="rgba(26,36,22,0.10)",
        title_font=dict(size=13, color="#4a5c44"),
        tickfont=dict(size=12, color="#4a5c44"),
    )
    return fig


# ---- Load data ----
@st.cache_data
def load_data():
    conn = sqlite3.connect("birds.db")
    df = pd.read_sql_query("SELECT * FROM detections", conn)
    conn.close()

    df["timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors="coerce")
    df["hour"]  = df["timestamp"].dt.hour
    df["week"]  = df["timestamp"].dt.isocalendar().week.astype(int)
    df["month"] = df["timestamp"].dt.month.astype(int)

    meta = pd.read_excel("UK_Birds_Generalized_Status.xlsx")
    meta = meta.rename(columns={
        "Latin Name":  "Sci_Name",
        "Common Name": "UK_Common_Name",
        "Status":      "UK_Status",
    })
    meta = meta[["Sci_Name", "UK_Common_Name", "UK_Status"]].drop_duplicates()

    df = df.merge(meta, on="Sci_Name", how="left")
    df["UK_Status"] = df["UK_Status"].fillna("Review Recording")
    return df

df = load_data()

st.title("🐦 Garden Bird Dashboard")
st.caption("Detections across time, seasons, and community composition.")

# ---- Sidebar filters ----
st.sidebar.header("Explore")

page = st.sidebar.radio(
    "View",
    [
        "Most Common Species",
        "Time of Day",
        "Weekly Trends",
        "Monthly Trends",
        "Heatmap",
        "Community Composition",
        "Status Over Time",
        "Status by Hour",
        "Review / Richness",
    ],
    label_visibility="collapsed",
)
st.sidebar.divider()

min_conf = st.sidebar.slider(
    "Minimum Confidence",
    float(df["Confidence"].min()),
    float(df["Confidence"].max()),
    float(df["Confidence"].min()),
)

filtered = df[df["Confidence"] >= min_conf].copy()

species_list = st.sidebar.multiselect(
    "Select Species",
    sorted(filtered["Com_Name"].dropna().unique()),
)
if species_list:
    filtered = filtered[filtered["Com_Name"].isin(species_list)]

status_list = st.sidebar.multiselect(
    "UK Status",
    sorted(filtered["UK_Status"].dropna().unique()),
)
if status_list:
    filtered = filtered[filtered["UK_Status"].isin(status_list)]

st.sidebar.subheader("Date Range")
filtered_ts = filtered.dropna(subset=["timestamp"]).copy()
min_date = filtered_ts["timestamp"].min().date()
max_date = filtered_ts["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    (min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

filtered = filtered[
    (filtered["timestamp"].dt.date >= start_date) &
    (filtered["timestamp"].dt.date <= end_date)
].copy()

def season_from_month(m: int) -> str:
    if m in (3, 4, 5):  return "Spring"
    if m in (6, 7, 8):  return "Summer"
    if m in (9, 10, 11): return "Autumn"
    return "Winter"

filtered["year"]      = filtered["timestamp"].dt.year.astype("Int64")
filtered["month_num"] = filtered["timestamp"].dt.month.astype("Int64")
filtered["season"]    = filtered["month_num"].apply(lambda m: season_from_month(m) if pd.notna(m) else None)

# ── Year / Season / Month sidebar filters ──
st.sidebar.subheader("Year / Season / Month")

_years_available = sorted(filtered["year"].dropna().unique())
year_mode = st.sidebar.selectbox("Years", ["All years", "Select years"], index=0)
selected_years = []
if year_mode == "Select years":
    selected_years = st.sidebar.multiselect(
        "Choose years", _years_available,
        default=_years_available[-1:] if _years_available else [],
    )
    if selected_years:
        filtered = filtered[filtered["year"].isin(selected_years)].copy()

selected_season = st.sidebar.selectbox("Season", ["All", "Spring", "Summer", "Autumn", "Winter"], index=0)

MONTHS_FULL = [
    (1, "January"), (2, "February"), (3, "March"), (4, "April"),
    (5, "May"), (6, "June"), (7, "July"), (8, "August"),
    (9, "September"), (10, "October"), (11, "November"), (12, "December"),
]
month_num_by_name = {n: m for m, n in MONTHS_FULL}
month_names_list  = [name for _, name in MONTHS_FULL]

month_mode = st.sidebar.selectbox("Months", ["All months", "Choose month"], index=0)
chosen_month = None
if month_mode == "Choose month":
    chosen_month = st.sidebar.selectbox("Choose month value", month_names_list, index=0)

# Keep a copy before season/month filters for compare-mode overrides
_filtered_pre_season_month = filtered.copy()

if selected_season != "All":
    filtered = filtered[filtered["season"] == selected_season].copy()
if month_mode == "Choose month" and chosen_month:
    filtered = filtered[filtered["month_num"] == month_num_by_name[chosen_month]].copy()

st.sidebar.divider()

exclude_review = st.sidebar.checkbox("Exclude 'Review Recording' from graphs", value=True)
review_df = filtered[filtered["UK_Status"] == "Review Recording"].copy()
if exclude_review:
    filtered = filtered[filtered["UK_Status"] != "Review Recording"].copy()

# ---- KPI cards ----
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Detections",  f"{len(filtered):,}")
kpi2.metric("Unique Species",    f"{filtered['Com_Name'].nunique():,}")
kpi3.metric("Average Confidence",
            f"{filtered['Confidence'].mean():.2f}" if len(filtered) else "—")

st.divider()

# ── Most Common Species ─────────────────────────────────────────────────────
if page == "Most Common Species":
    top = (
        filtered["Com_Name"].value_counts()
        .head(20)
        .reset_index()
    )
    top.columns = ["Species", "Count"]
    top = top.sort_values("Count", ascending=True)  # most common at top of chart

    fig = px.bar(
        top, x="Count", y="Species", orientation="h",
        title="Top 20 Most Common Species",
        color="Count",
        color_continuous_scale=[[0, "#a3c47a"], [1, "#2d5233"]],
        labels={"Count": "Detections", "Species": ""},
    )
    fig.update_coloraxes(showscale=False)
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ── Time of Day ─────────────────────────────────────────────────────────────
elif page == "Time of Day":
    hourly = filtered.groupby("hour").size().reset_index(name="Count")
    fig = px.area(
        hourly, x="hour", y="Count",
        title="Activity by Hour of Day",
        labels={"hour": "Hour of day", "Count": "Detections"},
    )
    fig.update_traces(
        line=dict(color=PRIMARY, width=2),
        fillcolor="rgba(61,107,68,0.14)",
        marker=dict(size=5, color=PRIMARY),
        mode="lines+markers",
    )
    fig.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ── Weekly Trends ───────────────────────────────────────────────────────────
elif page == "Weekly Trends":
    weekly = filtered.groupby("week").size().reset_index(name="Count")
    fig = px.area(
        weekly, x="week", y="Count",
        title="Weekly Detection Trends",
        labels={"week": "Week of year", "Count": "Detections"},
    )
    fig.update_traces(
        line=dict(color=SECONDARY, width=2),
        fillcolor="rgba(74,112,144,0.14)",
        marker=dict(size=5, color=SECONDARY),
        mode="lines+markers",
    )
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ── Monthly Trends ──────────────────────────────────────────────────────────
elif page == "Monthly Trends":
    monthly = filtered.groupby("month").size().reset_index(name="Count")
    fig = px.area(
        monthly, x="month", y="Count",
        title="Monthly Detection Trends",
        labels={"month": "Month", "Count": "Detections"},
    )
    fig.update_traces(
        line=dict(color=TERTIARY, width=2),
        fillcolor="rgba(184,144,64,0.14)",
        marker=dict(size=6, color=TERTIARY),
        mode="lines+markers",
    )
    fig.update_layout(xaxis=dict(
        dtick=1,
        tickmode="array",
        tickvals=list(MONTH_LABELS.keys()),
        ticktext=list(MONTH_LABELS.values()),
    ))
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ── Heatmap ─────────────────────────────────────────────────────────────────
elif page == "Heatmap":
    heatmap_data = (
        filtered.groupby(["month", "hour"])
        .size()
        .reset_index(name="Count")
    )
    fig = px.density_heatmap(
        heatmap_data, x="hour", y="month", z="Count",
        title="Activity Heatmap · Hour vs Month",
        color_continuous_scale=HEATMAP_SCALE,
        labels={"hour": "Hour of day", "month": "Month", "Count": "Detections"},
    )
    fig.update_layout(
        xaxis=dict(dtick=1),
        yaxis=dict(
            dtick=1,
            tickmode="array",
            tickvals=list(MONTH_LABELS.keys()),
            ticktext=list(MONTH_LABELS.values()),
        ),
        coloraxis_colorbar=dict(
            title="Detections",
            tickfont=dict(size=11, color="#4a5c44"),
            title_font=dict(size=12, color="#4a5c44"),
            thickness=14,
        ),
    )
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ── Community Composition ───────────────────────────────────────────────────
elif page == "Community Composition":
    st.subheader("Community Composition by Hour (Top 20 species, %)")

    comp_df = filtered.dropna(subset=["timestamp"]).copy()

    # Assign each species a colour once, ranked by overall frequency.
    # Both comparison plots share this map so species colours are consistent.
    _species_ranked = comp_df["Com_Name"].value_counts().index.tolist()
    species_color_map = {
        sp: NATURE_PALETTE[i % len(NATURE_PALETTE)]
        for i, sp in enumerate(_species_ranked)
    }

    seasons_list = ["Spring", "Summer", "Autumn", "Winter"]

    c_cmp_m, c_cmp_s = st.columns(2, gap="large")
    with c_cmp_m:
        compare_months = st.checkbox("Compare two months", value=False, key="cc_cmp_months")
    with c_cmp_s:
        compare_seasons = st.checkbox("Compare two seasons", value=False, key="cc_cmp_seasons")

    # Mutually exclusive: if both are checked, the most recently toggled wins.
    if compare_months and compare_seasons:
        # Both can't be true at once — keep the one that was just toggled.
        # Use session state to track which was last active.
        prev_months  = st.session_state.get("_cc_prev_cmp_months", False)
        prev_seasons = st.session_state.get("_cc_prev_cmp_seasons", False)
        if compare_months != prev_months:
            compare_seasons = False
            st.session_state["cc_cmp_seasons"] = False
        else:
            compare_months = False
            st.session_state["cc_cmp_months"] = False
    st.session_state["_cc_prev_cmp_months"]  = compare_months
    st.session_state["_cc_prev_cmp_seasons"] = compare_seasons

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

        color_map = {sp: species_color_map[sp] for sp in top_species}

        fig = px.bar(
            comp_hour,
            x="hour", y="Percent",
            color="Com_Name",
            title=title,
            labels={"hour": "Hour of day", "Percent": "% of detections", "Com_Name": "Species"},
            category_orders={"Com_Name": top_species},
            color_discrete_map=color_map,
        )
        fig.update_layout(barmode="stack", xaxis=dict(dtick=1))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    # Build label parts from global sidebar state
    years_label  = "All years" if year_mode == "All years" else ", ".join(map(str, selected_years))
    season_label = "All seasons" if selected_season == "All" else selected_season
    month_label  = "All months" if month_mode == "All months" else chosen_month

    # For compare modes, use pre-season/month filtered data so the compare
    # selectors override the global season/month filters for this page.
    _comp_base = _filtered_pre_season_month.dropna(subset=["timestamp"]).copy()
    if exclude_review:
        _comp_base = _comp_base[_comp_base["UK_Status"] != "Review Recording"].copy()

    if compare_months:
        left, right = st.columns(2, gap="large")
        with left:
            month_a = st.selectbox("Month A", month_names_list, index=5, key="cc_month_a")
        with right:
            month_b = st.selectbox("Month B", month_names_list, index=6, key="cc_month_b")

        # Apply global season filter but override month
        _cmp_df = _comp_base.copy()
        if selected_season != "All":
            _cmp_df = _cmp_df[_cmp_df["season"] == selected_season].copy()

        df_a = _cmp_df[_cmp_df["month_num"] == month_num_by_name[month_a]].copy()
        df_b = _cmp_df[_cmp_df["month_num"] == month_num_by_name[month_b]].copy()

        l, r = st.columns(2, gap="large")
        with l:
            composition_plot(df_a, f"{month_a} · {years_label} · {season_label}")
        with r:
            composition_plot(df_b, f"{month_b} · {years_label} · {season_label}")

    elif compare_seasons:
        left, right = st.columns(2, gap="large")
        with left:
            season_a = st.selectbox("Season A", seasons_list, index=0, key="cc_season_a")
        with right:
            season_b = st.selectbox("Season B", seasons_list, index=1, key="cc_season_b")

        # Apply global month filter but override season
        _cmp_df = _comp_base.copy()
        if month_mode == "Choose month" and chosen_month:
            _cmp_df = _cmp_df[_cmp_df["month_num"] == month_num_by_name[chosen_month]].copy()

        df_a = _cmp_df[_cmp_df["season"] == season_a].copy()
        df_b = _cmp_df[_cmp_df["season"] == season_b].copy()

        l, r = st.columns(2, gap="large")
        with l:
            composition_plot(df_a, f"{season_a} · {years_label} · {month_label}")
        with r:
            composition_plot(df_b, f"{season_b} · {years_label} · {month_label}")

    elif len(comp_df) == 0:
        st.info("No data available for the selected filters.")
    else:
        composition_plot(comp_df, f"{month_label} · {years_label} · {season_label}")

# ── Status Over Time ────────────────────────────────────────────────────────
elif page == "Status Over Time":
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

    cmap = status_color_map(status_month["UK_Status"].unique())
    fig = px.area(
        status_month,
        x="month_period", y="Percent",
        color="UK_Status",
        title="Monthly Status Composition",
        labels={"month_period": "Month", "Percent": "% of detections", "UK_Status": "UK Status"},
        color_discrete_map=cmap,
    )
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ── Status by Hour ──────────────────────────────────────────────────────────
elif page == "Status by Hour":
    status_hour = (
        filtered.groupby(["hour", "UK_Status"])
        .size()
        .reset_index(name="Count")
    )

    cmap = status_color_map(status_hour["UK_Status"].unique())
    fig = px.line(
        status_hour,
        x="hour", y="Count",
        color="UK_Status",
        markers=True,
        title="Activity by Hour · by Status",
        labels={"hour": "Hour of day", "Count": "Detections", "UK_Status": "UK Status"},
        color_discrete_map=cmap,
    )
    fig.update_layout(xaxis=dict(dtick=1))
    fig.update_traces(line=dict(width=2), marker=dict(size=5))
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ── Review / Richness ───────────────────────────────────────────────────────
elif page == "Review / Richness":
    st.subheader("Species Richness Over Time")

    tmp = filtered.dropna(subset=["timestamp"]).copy()
    tmp["month_period"] = tmp["timestamp"].dt.to_period("M").astype(str)

    richness_month = (
        tmp.groupby("month_period")["Com_Name"]
        .nunique()
        .reset_index(name="Unique_Species")
    )

    fig = px.area(
        richness_month,
        x="month_period", y="Unique_Species",
        title="Unique Species per Month",
        labels={"month_period": "Month", "Unique_Species": "Unique species"},
    )
    fig.update_traces(
        line=dict(color=PRIMARY, width=2),
        fillcolor="rgba(61,107,68,0.14)",
        marker=dict(size=5, color=PRIMARY),
        mode="lines+markers",
    )
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.subheader("Review Recording: Top Species to Check")

    if len(review_df) == 0:
        st.info("No 'Review Recording' rows in the current filter.")
    else:
        top_review = (
            review_df["Sci_Name"]
            .value_counts()
            .head(20)
            .reset_index()
        )
        top_review.columns = ["Sci_Name", "Count"]
        top_review = top_review.sort_values("Count", ascending=True)

        fig = px.bar(
            top_review,
            x="Count", y="Sci_Name", orientation="h",
            title="Top 20 Latin Names Needing Review",
            color="Count",
            color_continuous_scale=[[0, "#c4a07a"], [1, "#7a5c3d"]],
            labels={"Count": "Detections", "Sci_Name": ""},
        )
        fig.update_coloraxes(showscale=False)
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(style_fig(fig), use_container_width=True)

        st.subheader("Review Recording: Confidence by Hour")

        conf_hour = (
            review_df.groupby("hour")["Confidence"]
            .mean()
            .reset_index(name="Avg_Confidence")
        )
        fig = px.line(
            conf_hour,
            x="hour", y="Avg_Confidence",
            markers=True,
            title="Average Confidence by Hour (Review Recording only)",
            labels={"hour": "Hour of day", "Avg_Confidence": "Avg confidence"},
        )
        fig.update_traces(
            line=dict(color=TERTIARY, width=2),
            marker=dict(size=5, color=TERTIARY),
        )
        fig.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(style_fig(fig), use_container_width=True)
