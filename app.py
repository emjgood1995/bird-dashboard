import sqlite3
import base64
import hashlib
import pathlib
import pandas as pd
import streamlit as st
import plotly.express as px
import requests
import numpy as np
import openpyxl

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


@st.cache_data(ttl=86400)
def fetch_wiki_summary(title: str):
    """Fetch a Wikipedia summary for the given page title."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    headers = {"User-Agent": "GardenBirdDashboard/1.0 (https://github.com/emjgood1995/bird-dashboard)"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "extract": data.get("extract", ""),
            "thumbnail_url": data.get("thumbnail", {}).get("source"),
            "page_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "title": data.get("title", title),
        }
    except Exception:
        return None


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
        "Trends",
        "Heatmap",
        "Community Composition",
        "Status Over Time",
        "Status by Hour",
        "Review / Richness",
        "Phenology",
        "Ecology",
        "Data Quality & Records",
        "Species Explorer",
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

    def tod_chart(data: pd.DataFrame, title: str, by_species: bool):
        """Render one Activity by Hour chart."""
        if len(data) == 0:
            st.warning("No data for this selection.")
            return
        if by_species:
            top_sp = data["Com_Name"].value_counts().head(20).index.tolist()
            tod_df = data[data["Com_Name"].isin(top_sp)].copy()
            sp_hour = tod_df.groupby(["hour", "Com_Name"]).size().reset_index(name="Count")
            sp_color_map = {
                sp: NATURE_PALETTE[i % len(NATURE_PALETTE)]
                for i, sp in enumerate(top_sp)
            }
            fig = px.area(
                sp_hour, x="hour", y="Count",
                color="Com_Name",
                title=title,
                labels={"hour": "Hour of day", "Count": "Detections", "Com_Name": "Species"},
                category_orders={"Com_Name": top_sp},
                color_discrete_map=sp_color_map,
            )
            fig.update_layout(xaxis=dict(dtick=1))
            fig.update_traces(marker_line_width=0)
            hourly = data.groupby("hour").size().reset_index(name="Count")
            fig.add_scatter(
                x=hourly["hour"], y=hourly["Count"],
                mode="lines+markers",
                line=dict(color="#1a2416", width=2.5, dash="dot"),
                marker=dict(size=5, color="#1a2416"),
                name="Total", showlegend=True,
            )
        else:
            hourly = data.groupby("hour").size().reset_index(name="Count")
            fig = px.area(
                hourly, x="hour", y="Count",
                title=title,
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

    # Controls row
    def _tod_on_months():
        if st.session_state.get("tod_cmp_months"):
            st.session_state["tod_cmp_seasons"] = False

    def _tod_on_seasons():
        if st.session_state.get("tod_cmp_seasons"):
            st.session_state["tod_cmp_months"] = False

    tc1, tc2, tc3 = st.columns(3, gap="large")
    with tc1:
        show_by_species = st.checkbox("Show by species", value=False, key="tod_by_species")
    with tc2:
        tod_cmp_months = st.checkbox("Compare two months", value=False, key="tod_cmp_months", on_change=_tod_on_months)
    with tc3:
        tod_cmp_seasons = st.checkbox("Compare two seasons", value=False, key="tod_cmp_seasons", on_change=_tod_on_seasons)

    # Pre-filter base for compare overrides
    _tod_base = _filtered_pre_season_month.dropna(subset=["timestamp"]).copy()
    if exclude_review:
        _tod_base = _tod_base[_tod_base["UK_Status"] != "Review Recording"].copy()

    years_label  = "All years" if year_mode == "All years" else ", ".join(map(str, selected_years))
    season_label = "All seasons" if selected_season == "All" else selected_season
    month_label  = "All months" if month_mode == "All months" else chosen_month

    if tod_cmp_months:
        left, right = st.columns(2, gap="large")
        with left:
            tod_ma = st.selectbox("Month A", month_names_list, index=5, key="tod_month_a")
        with right:
            tod_mb = st.selectbox("Month B", month_names_list, index=6, key="tod_month_b")

        _cmp = _tod_base.copy()
        if selected_season != "All":
            _cmp = _cmp[_cmp["season"] == selected_season].copy()

        l, r = st.columns(2, gap="large")
        with l:
            tod_chart(_cmp[_cmp["month_num"] == month_num_by_name[tod_ma]],
                      f"{tod_ma} · {years_label} · {season_label}", show_by_species)
        with r:
            tod_chart(_cmp[_cmp["month_num"] == month_num_by_name[tod_mb]],
                      f"{tod_mb} · {years_label} · {season_label}", show_by_species)

    elif tod_cmp_seasons:
        seasons_opts = ["Spring", "Summer", "Autumn", "Winter"]
        left, right = st.columns(2, gap="large")
        with left:
            tod_sa = st.selectbox("Season A", seasons_opts, index=0, key="tod_season_a")
        with right:
            tod_sb = st.selectbox("Season B", seasons_opts, index=1, key="tod_season_b")

        _cmp = _tod_base.copy()
        if month_mode == "Choose month" and chosen_month:
            _cmp = _cmp[_cmp["month_num"] == month_num_by_name[chosen_month]].copy()

        l, r = st.columns(2, gap="large")
        with l:
            tod_chart(_cmp[_cmp["season"] == tod_sa],
                      f"{tod_sa} · {years_label} · {month_label}", show_by_species)
        with r:
            tod_chart(_cmp[_cmp["season"] == tod_sb],
                      f"{tod_sb} · {years_label} · {month_label}", show_by_species)

    else:
        tod_chart(filtered, f"Activity by Hour · {month_label} · {years_label} · {season_label}",
                  show_by_species)

# ── Trends (Yearly / Monthly / Weekly) ─────────────────────────────────────
elif page == "Trends":
    # Yearly
    yearly = filtered.dropna(subset=["timestamp"]).copy()
    yearly = yearly.groupby("year").size().reset_index(name="Count")
    yearly["year"] = yearly["year"].astype(int)
    fig = px.area(
        yearly, x="year", y="Count",
        title="Yearly Detection Trends",
        labels={"year": "Year", "Count": "Detections"},
    )
    fig.update_traces(
        line=dict(color=PRIMARY, width=2),
        fillcolor="rgba(61,107,68,0.14)",
        marker=dict(size=6, color=PRIMARY),
        mode="lines+markers",
    )
    fig.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(style_fig(fig), use_container_width=True)

    # Monthly
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

    # Weekly
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

# ── Heatmap ─────────────────────────────────────────────────────────────────
elif page == "Heatmap":
    heatmap_data = (
        filtered.groupby(["month", "hour"])
        .size()
        .reset_index(name="Count")
    )
    # Pivot to a full 12×24 grid so every month gets its own row
    heatmap_pivot = heatmap_data.pivot(index="month", columns="hour", values="Count").fillna(0)
    heatmap_pivot = heatmap_pivot.reindex(index=range(1, 13), columns=range(24), fill_value=0)

    fig = px.imshow(
        heatmap_pivot.values,
        x=list(range(24)),
        y=list(MONTH_LABELS.values()),
        title="Activity Heatmap · Hour vs Month",
        color_continuous_scale=HEATMAP_SCALE,
        labels={"x": "Hour of day", "y": "Month", "color": "Detections"},
        aspect="auto",
    )
    fig.update_layout(
        xaxis=dict(dtick=1),
        yaxis=dict(dtick=1),
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

    # Build colour map from the broadest dataset (pre-season/month filter)
    # so compare modes can look up any species that exists in the data.
    _comp_base_all = _filtered_pre_season_month.dropna(subset=["timestamp"]).copy()
    if exclude_review:
        _comp_base_all = _comp_base_all[_comp_base_all["UK_Status"] != "Review Recording"].copy()
    _species_ranked = _comp_base_all["Com_Name"].value_counts().index.tolist()
    species_color_map = {
        sp: NATURE_PALETTE[i % len(NATURE_PALETTE)]
        for i, sp in enumerate(_species_ranked)
    }

    seasons_list = ["Spring", "Summer", "Autumn", "Winter"]

    # Mutually exclusive checkboxes: toggling one clears the other via callbacks
    # that fire before the next render, avoiding Streamlit's "can't set widget
    # state after creation" error.
    def _on_months_change():
        if st.session_state.get("cc_cmp_months"):
            st.session_state["cc_cmp_seasons"] = False

    def _on_seasons_change():
        if st.session_state.get("cc_cmp_seasons"):
            st.session_state["cc_cmp_months"] = False

    c_cmp_m, c_cmp_s = st.columns(2, gap="large")
    with c_cmp_m:
        compare_months = st.checkbox(
            "Compare two months", value=False,
            key="cc_cmp_months", on_change=_on_months_change,
        )
    with c_cmp_s:
        compare_seasons = st.checkbox(
            "Compare two seasons", value=False,
            key="cc_cmp_seasons", on_change=_on_seasons_change,
        )

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

        color_map = {
            sp: species_color_map.get(sp, NATURE_PALETTE[i % len(NATURE_PALETTE)])
            for i, sp in enumerate(top_species)
        }

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

    # ---- Validate Review Recording species ----
    st.subheader("Validate a 'Review Recording' Species")

    has_token = False
    try:
        _gh_token = st.secrets["GITHUB_TOKEN"]
        has_token = bool(_gh_token)
    except (KeyError, FileNotFoundError):
        pass

    if not has_token:
        st.info(
            "To validate species from here, configure a `GITHUB_TOKEN` secret "
            "with Contents write permission on the repo."
        )
    elif len(review_df) == 0:
        st.success("No species currently need review!")
    else:
        review_species = (
            review_df[["Sci_Name", "Com_Name"]]
            .drop_duplicates()
            .sort_values("Sci_Name")
        )
        display_labels = (
            review_species["Sci_Name"] + "  (" + review_species["Com_Name"] + ")"
        ).tolist()

        VALID_STATUSES = [
            "Resident", "Summer visitor", "Winter visitor",
            "Passage migrant", "Scarce visitor", "Rare vagrant",
            "Introduced species", "Reintroduced", "Extinct", "False Positive", "Other",
        ]

        with st.form("validate_review_species"):
            chosen = st.selectbox("Species to validate", display_labels)
            new_status = st.selectbox("Assign status", VALID_STATUSES)
            submitted = st.form_submit_button("Save & push to GitHub")

        if submitted:
            idx = display_labels.index(chosen)
            sci_name = review_species.iloc[idx]["Sci_Name"]
            com_name = review_species.iloc[idx]["Com_Name"]

            EXCEL_PATH = "UK_Birds_Generalized_Status.xlsx"
            REPO = "emjgood1995/bird-dashboard"
            TOKEN = st.secrets["GITHUB_TOKEN"]

            # 1. Update the local Excel file
            wb = openpyxl.load_workbook(EXCEL_PATH)
            ws = wb.active
            ws.append([com_name, sci_name, new_status])
            wb.save(EXCEL_PATH)

            # 2. Push to GitHub via Contents API
            api_url = f"https://api.github.com/repos/{REPO}/contents/{EXCEL_PATH}"
            headers = {
                "Authorization": f"Bearer {TOKEN}",
                "Accept": "application/vnd.github+json",
            }

            # GET current SHA
            get_resp = requests.get(api_url, headers=headers, timeout=15)
            if get_resp.status_code != 200:
                st.error(f"GitHub GET failed ({get_resp.status_code}): {get_resp.text}")
            else:
                sha = get_resp.json()["sha"]
                file_bytes = pathlib.Path(EXCEL_PATH).read_bytes()
                encoded = base64.b64encode(file_bytes).decode()

                put_resp = requests.put(
                    api_url,
                    headers=headers,
                    json={
                        "message": f"Add species status: {sci_name} -> {new_status}",
                        "content": encoded,
                        "sha": sha,
                    },
                    timeout=30,
                )
                if put_resp.status_code in (200, 201):
                    st.cache_data.clear()
                    st.success(
                        f"Saved **{sci_name}** as *{new_status}* and pushed to GitHub."
                    )
                else:
                    st.error(
                        f"GitHub PUT failed ({put_resp.status_code}): {put_resp.text}"
                    )

# ── Phenology ──────────────────────────────────────────────────────────────
elif page == "Phenology":

    # ── Dawn Chorus Tracker ──
    st.subheader("Dawn Chorus Tracker")
    dc_topn = st.slider("Top N species", 5, 20, 12, key="dc_topn")

    dc_df = filtered.dropna(subset=["timestamp"]).copy()
    dc_df = dc_df[(dc_df["hour"] >= 3) & (dc_df["hour"] <= 10)]

    if len(dc_df) == 0:
        st.info("No detections in the dawn window (03:00-10:00) for current filters.")
    else:
        top_dawn = dc_df["Com_Name"].value_counts().head(dc_topn).index.tolist()
        dc_df = dc_df[dc_df["Com_Name"].isin(top_dawn)].copy()
        dc_df["decimal_hour"] = dc_df["timestamp"].dt.hour + dc_df["timestamp"].dt.minute / 60.0

        earliest = (
            dc_df.groupby(["month", "Com_Name"])["decimal_hour"]
            .min()
            .reset_index(name="Earliest_Hour")
        )
        earliest["Month_Label"] = earliest["month"].map(MONTH_LABELS)

        color_map = {
            sp: NATURE_PALETTE[i % len(NATURE_PALETTE)]
            for i, sp in enumerate(top_dawn)
        }
        fig = px.line(
            earliest, x="month", y="Earliest_Hour",
            color="Com_Name",
            title="Earliest Detection by Month (Dawn Window)",
            labels={"month": "Month", "Earliest_Hour": "Earliest hour", "Com_Name": "Species"},
            color_discrete_map=color_map,
            markers=True,
        )
        fig.update_layout(xaxis=dict(
            dtick=1,
            tickmode="array",
            tickvals=list(MONTH_LABELS.keys()),
            ticktext=list(MONTH_LABELS.values()),
        ))
        fig.update_traces(line=dict(width=2), marker=dict(size=5))
        st.plotly_chart(style_fig(fig), use_container_width=True)

    st.divider()

    # ── New Arrival Alerts ──
    st.subheader("New Arrival Alerts")

    na_df = filtered.dropna(subset=["timestamp"]).copy()
    na_df["year"] = na_df["timestamp"].dt.year

    available_years = sorted(na_df["year"].dropna().unique())
    if len(available_years) == 0:
        st.info("No data available for new arrival analysis.")
    else:
        na_years = st.multiselect(
            "Years to inspect", available_years,
            default=[available_years[-1]], key="na_years",
        )
        if not na_years:
            st.info("Select at least one year.")
        else:
            first_det = (
                na_df.groupby(["Com_Name", "year"])["timestamp"]
                .min()
                .reset_index(name="First_Seen")
            )
            first_det["First_Seen_Date"] = first_det["First_Seen"].dt.date

            # Compute the earliest year each species was ever seen
            ever_first = first_det.groupby("Com_Name")["year"].min().reset_index(name="First_Year_Ever")
            first_det = first_det.merge(ever_first, on="Com_Name", how="left")
            first_det["New_Species"] = first_det["year"] == first_det["First_Year_Ever"]

            display_df = first_det[first_det["year"].isin(na_years)].copy()
            display_df = display_df.sort_values("First_Seen_Date")

            cols = st.columns(len(na_years))
            for i, yr in enumerate(sorted(na_years)):
                yr_new = display_df[(display_df["year"] == yr) & (display_df["New_Species"])]
                cols[i].metric(f"New arrivals {yr}", len(yr_new))

            st.dataframe(
                display_df[["Com_Name", "year", "First_Seen_Date", "New_Species"]]
                .rename(columns={"Com_Name": "Species", "year": "Year",
                                 "First_Seen_Date": "First Seen", "New_Species": "New Species"}),
                hide_index=True,
            )

    st.divider()

    # ── Year List Progress ──
    st.subheader("Year List Progress")

    yl_df = filtered.dropna(subset=["timestamp"]).copy()
    yl_df["year"] = yl_df["timestamp"].dt.year
    yl_years_avail = sorted(yl_df["year"].dropna().unique())

    if len(yl_years_avail) < 1:
        st.info("No data available for year list progress.")
    else:
        default_yl = yl_years_avail[-2:] if len(yl_years_avail) >= 2 else yl_years_avail
        yl_years = st.multiselect(
            "Years to compare", yl_years_avail,
            default=default_yl, key="yl_years",
        )
        if not yl_years:
            st.info("Select at least one year.")
        else:
            yl_df = yl_df[yl_df["year"].isin(yl_years)].copy()
            yl_df["doy"] = yl_df["timestamp"].dt.dayofyear

            first_doy = yl_df.groupby(["year", "Com_Name"])["doy"].min().reset_index(name="First_DOY")

            cumul_rows = []
            for yr in sorted(yl_years):
                yr_data = first_doy[first_doy["year"] == yr].sort_values("First_DOY")
                for doy_val in range(1, 367):
                    count = (yr_data["First_DOY"] <= doy_val).sum()
                    cumul_rows.append({"Year": str(int(yr)), "Day_of_Year": doy_val, "Cumulative_Species": count})
            cumul_df = pd.DataFrame(cumul_rows)

            fig = px.line(
                cumul_df, x="Day_of_Year", y="Cumulative_Species",
                color="Year",
                title="Cumulative Species by Day of Year",
                labels={"Day_of_Year": "Day of year", "Cumulative_Species": "Cumulative species", "Year": "Year"},
                color_discrete_sequence=NATURE_PALETTE,
            )
            fig.update_traces(line=dict(width=2))
            st.plotly_chart(style_fig(fig), use_container_width=True)

# ── Ecology ────────────────────────────────────────────────────────────────
elif page == "Ecology":

    # ── Species Co-occurrence ──
    st.subheader("Species Co-occurrence")

    co_topn = st.slider("Top N species", 5, 20, 15, key="co_topn")
    co_unit = st.radio("Co-occurrence unit", ["Day", "Hour"], horizontal=True, key="co_unit")

    co_df = filtered.dropna(subset=["timestamp"]).copy()

    if len(co_df) == 0:
        st.info("No data available for co-occurrence analysis.")
    else:
        top_co = co_df["Com_Name"].value_counts().head(co_topn).index.tolist()
        co_df = co_df[co_df["Com_Name"].isin(top_co)].copy()

        if co_unit == "Day":
            co_df["unit"] = co_df["timestamp"].dt.date.astype(str)
        else:
            co_df["unit"] = co_df["timestamp"].dt.strftime("%Y-%m-%d-%H")

        presence = co_df.groupby(["unit", "Com_Name"]).size().unstack(fill_value=0)
        presence = (presence > 0).astype(int)
        # Ensure all top species are columns
        for sp in top_co:
            if sp not in presence.columns:
                presence[sp] = 0
        presence = presence[top_co]

        dot = presence.T.values @ presence.values  # species x species
        counts = presence.sum(axis=0).values
        min_counts = np.minimum(counts[:, None], counts[None, :])
        min_counts[min_counts == 0] = 1  # avoid division by zero
        norm_co = dot / min_counts
        np.fill_diagonal(norm_co, 0)

        fig = px.imshow(
            norm_co,
            x=top_co, y=top_co,
            title=f"Species Co-occurrence (normalised, by {co_unit.lower()})",
            color_continuous_scale=HEATMAP_SCALE,
            labels={"color": "Co-occurrence"},
            aspect="auto",
        )
        fig.update_layout(
            coloraxis_colorbar=dict(
                title="Co-occurrence",
                tickfont=dict(size=11, color="#4a5c44"),
                title_font=dict(size=12, color="#4a5c44"),
                thickness=14,
            ),
        )
        st.plotly_chart(style_fig(fig), use_container_width=True)

    st.divider()

    # ── Diversity Indices ──
    st.subheader("Diversity Indices")

    div_res = st.radio("Time resolution", ["Month", "Week"], horizontal=True, key="div_res")

    div_df = filtered.dropna(subset=["timestamp"]).copy()

    if len(div_df) == 0:
        st.info("No data available for diversity index computation.")
    else:
        if div_res == "Month":
            div_df["period"] = div_df["timestamp"].dt.to_period("M").astype(str)
        else:
            div_df["period"] = (
                div_df["timestamp"].dt.isocalendar().year.astype(str) + "-W"
                + div_df["timestamp"].dt.isocalendar().week.astype(str).str.zfill(2)
            )

        periods = sorted(div_df["period"].unique())
        div_rows = []
        for p in periods:
            p_df = div_df[div_df["period"] == p]
            counts = p_df["Com_Name"].value_counts().values
            total = counts.sum()
            richness = len(counts)
            if total > 0 and richness > 0:
                proportions = counts / total
                shannon = -np.sum(proportions * np.log(proportions))
                simpson = 1 - np.sum(proportions ** 2)
            else:
                shannon = 0.0
                simpson = 0.0
            div_rows.append({"Period": p, "Shannon_H": shannon, "Simpson_1D": simpson, "Richness": richness})
        div_result = pd.DataFrame(div_rows)

        fig_h = px.line(
            div_result, x="Period", y="Shannon_H",
            title="Shannon Diversity (H')",
            labels={"Period": div_res, "Shannon_H": "H'"},
            markers=True,
        )
        fig_h.update_traces(line=dict(color=PRIMARY, width=2), marker=dict(size=5, color=PRIMARY))
        st.plotly_chart(style_fig(fig_h), use_container_width=True)

        fig_s = px.line(
            div_result, x="Period", y="Simpson_1D",
            title="Simpson's Diversity (1-D)",
            labels={"Period": div_res, "Simpson_1D": "1-D"},
            markers=True,
        )
        fig_s.update_traces(line=dict(color=SECONDARY, width=2), marker=dict(size=5, color=SECONDARY))
        st.plotly_chart(style_fig(fig_s), use_container_width=True)

        fig_r = px.bar(
            div_result, x="Period", y="Richness",
            title="Species Richness",
            labels={"Period": div_res, "Richness": "Species count"},
        )
        fig_r.update_traces(marker_color=TERTIARY, marker_line_width=0)
        st.plotly_chart(style_fig(fig_r), use_container_width=True)

# ── Data Quality & Records ─────────────────────────────────────────────────
elif page == "Data Quality & Records":

    # ── Confidence Distribution ──
    st.subheader("Confidence Distribution")

    cd_topn = st.slider("Top N species", 5, 30, 20, key="cd_topn")
    cd_box = st.checkbox("Overlay box plot", value=True, key="cd_box")

    cd_df = filtered.dropna(subset=["Confidence"]).copy()

    if len(cd_df) == 0:
        st.info("No confidence data available.")
    else:
        # Sort species by median confidence
        medians = cd_df.groupby("Com_Name")["Confidence"].median().sort_values()
        top_cd = medians.tail(cd_topn).index.tolist()
        cd_df = cd_df[cd_df["Com_Name"].isin(top_cd)].copy()
        # Reorder by median
        species_order = medians.loc[medians.index.isin(top_cd)].index.tolist()

        color_map = {
            sp: NATURE_PALETTE[i % len(NATURE_PALETTE)]
            for i, sp in enumerate(species_order)
        }

        fig = px.violin(
            cd_df, x="Confidence", y="Com_Name",
            orientation="h",
            title="Confidence Distribution by Species",
            labels={"Confidence": "Confidence", "Com_Name": "Species"},
            color="Com_Name",
            color_discrete_map=color_map,
            category_orders={"Com_Name": species_order},
        )
        if cd_box:
            fig.update_traces(box_visible=True)
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    st.divider()

    # ── False Positive Candidates ──
    st.subheader("False Positive Candidates")

    fp_thresh = st.slider("Confidence threshold", 0.0, 1.0, 0.7, key="fp_thresh")
    all_statuses = sorted(filtered["UK_Status"].dropna().unique())
    fp_default = [s for s in ["Rare vagrant", "Scarce visitor"] if s in all_statuses]
    fp_statuses = st.multiselect(
        "UK statuses to flag", all_statuses,
        default=fp_default, key="fp_statuses",
    )

    fp_df = filtered[filtered["Confidence"] <= fp_thresh].copy()
    if fp_statuses:
        fp_df = fp_df[fp_df["UK_Status"].isin(fp_statuses)].copy()

    if len(fp_df) == 0:
        st.info("No false positive candidates for current filters.")
    else:
        fp_left, fp_right = st.columns(2, gap="large")

        with fp_left:
            cmap = status_color_map(fp_df["UK_Status"].unique())
            fig = px.scatter(
                fp_df, x="Confidence", y="Com_Name",
                color="UK_Status",
                title="Low-Confidence Detections",
                labels={"Confidence": "Confidence", "Com_Name": "Species", "UK_Status": "UK Status"},
                color_discrete_map=cmap,
            )
            fig.update_traces(marker=dict(size=6, opacity=0.7))
            st.plotly_chart(style_fig(fig), use_container_width=True)

        with fp_right:
            summary = (
                fp_df.groupby(["Com_Name", "UK_Status"])
                .agg(Count=("Confidence", "size"), Avg_Confidence=("Confidence", "mean"))
                .reset_index()
                .sort_values("Avg_Confidence")
                .rename(columns={"Com_Name": "Species", "UK_Status": "Status",
                                 "Avg_Confidence": "Avg Confidence"})
            )
            summary["Avg Confidence"] = summary["Avg Confidence"].round(3)
            st.dataframe(summary, hide_index=True)

    st.divider()

    # ── Personal Records ──
    st.subheader("Personal Records")

    pr_df = filtered.dropna(subset=["timestamp"]).copy()
    pr_df["year"] = pr_df["timestamp"].dt.year

    pr_years_avail = sorted(pr_df["year"].dropna().unique())
    pr_years = st.multiselect(
        "Filter to years", pr_years_avail,
        default=pr_years_avail, key="pr_years",
    )
    pr_rarest_n = st.slider("N rarest species", 5, 30, 15, key="pr_rarest_n")

    if pr_years:
        pr_df = pr_df[pr_df["year"].isin(pr_years)].copy()

    if len(pr_df) == 0:
        st.info("No data available for personal records.")
    else:
        # Earliest / latest detection
        det_range = pr_df.groupby("Com_Name")["timestamp"].agg(["min", "max"]).reset_index()
        det_range.columns = ["Species", "Earliest_Detection", "Latest_Detection"]
        det_range["Earliest"] = det_range["Earliest_Detection"].dt.strftime("%m-%d")
        det_range["Latest"] = det_range["Latest_Detection"].dt.strftime("%m-%d")

        pr_k1, pr_k2 = st.columns(2)
        pr_k1.metric("Total species recorded", det_range["Species"].nunique())
        pr_k2.metric("Date range", f"{pr_df['timestamp'].min().strftime('%Y-%m-%d')} to {pr_df['timestamp'].max().strftime('%Y-%m-%d')}")

        st.dataframe(
            det_range[["Species", "Earliest", "Latest"]].sort_values("Earliest"),
            hide_index=True,
        )

        st.divider()

        # Rarest visitors
        st.subheader("Rarest Visitors")
        rarest = (
            pr_df["Com_Name"].value_counts()
            .tail(pr_rarest_n)
            .reset_index()
        )
        rarest.columns = ["Species", "Count"]
        rarest = rarest.sort_values("Count", ascending=True)

        fig = px.bar(
            rarest, x="Count", y="Species", orientation="h",
            title=f"Top {pr_rarest_n} Rarest Species (fewest detections)",
            labels={"Count": "Detections", "Species": ""},
            color="Count",
            color_continuous_scale=[[0, "#a3c47a"], [1, "#2d5233"]],
        )
        fig.update_coloraxes(showscale=False)
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(style_fig(fig), use_container_width=True)

        st.divider()

        # Longest streak
        st.subheader("Longest Detection Streak")

        def longest_streak(dates):
            """Compute longest run of consecutive days."""
            if len(dates) == 0:
                return 0
            unique_days = sorted(set(dates))
            best = 1
            current = 1
            for i in range(1, len(unique_days)):
                if (unique_days[i] - unique_days[i - 1]).days == 1:
                    current += 1
                    best = max(best, current)
                else:
                    current = 1
            return best

        pr_df["det_date"] = pr_df["timestamp"].dt.date
        streak_data = (
            pr_df.groupby("Com_Name")["det_date"]
            .apply(lambda x: longest_streak(x.tolist()))
            .reset_index(name="Longest_Streak")
            .sort_values("Longest_Streak", ascending=False)
        )

        st.metric("Top streak", f"{streak_data['Longest_Streak'].max()} days" if len(streak_data) else "—")
        st.dataframe(
            streak_data.rename(columns={"Com_Name": "Species", "Longest_Streak": "Longest Streak (days)"}),
            hide_index=True,
        )

# ── Species Explorer ──────────────────────────────────────────────────────
elif page == "Species Explorer":
    st.subheader("Species Explorer")

    se_species_pairs = (
        filtered[["Com_Name", "Sci_Name"]]
        .dropna()
        .drop_duplicates()
        .sort_values("Com_Name")
        .reset_index(drop=True)
    )

    if len(se_species_pairs) == 0:
        st.info("No species available for the current filters.")
    else:
        se_labels = (se_species_pairs["Com_Name"] + "  (" + se_species_pairs["Sci_Name"] + ")").tolist()
        today_str = str(pd.Timestamp.now().date())
        bird_of_day_idx = int(hashlib.md5(today_str.encode()).hexdigest(), 16) % len(se_labels)

        chosen_label = st.selectbox("Choose a species", se_labels, index=bird_of_day_idx, key="se_species")
        chosen_idx = se_labels.index(chosen_label)
        se_com = se_species_pairs.iloc[chosen_idx]["Com_Name"]
        se_sci = se_species_pairs.iloc[chosen_idx]["Sci_Name"]

        # Fetch Wikipedia info — try scientific name first, fall back to common name
        wiki = fetch_wiki_summary(se_sci)
        if wiki is None:
            wiki = fetch_wiki_summary(se_com)

        if wiki is not None:
            img_col, text_col = st.columns([1, 2], gap="large")
            with img_col:
                if wiki["thumbnail_url"]:
                    st.image(wiki["thumbnail_url"], use_container_width=True)
                else:
                    st.info("No image available.")
            with text_col:
                st.markdown(f"### {se_com}")
                st.markdown(f"*{se_sci}*")
                st.markdown(wiki["extract"])
                if wiki["page_url"]:
                    st.markdown(f"[Read more on Wikipedia]({wiki['page_url']})")

            if chosen_idx == bird_of_day_idx:
                st.caption("Bird of the day — changes daily, seeded by today's date.")

            first_sentence = wiki["extract"].split(". ")[0]
            if first_sentence:
                st.info(f"Fun fact: {first_sentence}.")
        else:
            st.warning("Could not fetch information from Wikipedia.")

        # Detection summary for selected species
        st.divider()
        st.markdown(f"#### Detection Summary: {se_com}")
        sp_df = filtered[filtered["Com_Name"] == se_com].copy()

        if len(sp_df) == 0:
            st.info("No detections for this species in the current filters.")
        else:
            sk1, sk2, sk3, sk4 = st.columns(4)
            sk1.metric("Total Detections", f"{len(sp_df):,}")
            sp_ts = sp_df.dropna(subset=["timestamp"])
            if len(sp_ts) > 0:
                sk2.metric("Last Seen", sp_ts['timestamp'].max().strftime('%Y-%m-%d'))
                peak_hour = sp_ts["hour"].value_counts().idxmax()
                sk3.metric("Peak Hour", f"{peak_hour}:00")
                peak_month = sp_ts["month"].value_counts().idxmax()
                sk4.metric("Peak Month", MONTH_LABELS.get(peak_month, str(peak_month)))
