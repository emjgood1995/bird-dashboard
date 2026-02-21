import json
import sqlite3
import base64
import hashlib
import pathlib
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import numpy as np
import openpyxl
from scipy.spatial.distance import pdist, squareform
from sklearn.manifold import MDS
from zoneinfo import ZoneInfo

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

DIET_COLORS = {
    "Insectivore":  "#6a90b0",
    "Granivore":    "#d4ac60",
    "Omnivore":     "#5c8c5c",
    "Frugivore":    "#c47a5a",
    "Carnivore":    "#8b4c4c",
    "Piscivore":    "#4a7090",
    "Herbivore":    "#a3c47a",
    "Unclassified": "#8c9c8c",
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

TIME_BUCKET_COLORS = {
    "Dawn (5–8)":       "#d4ac60",
    "Morning (8–12)":   "#5c8c5c",
    "Afternoon (12–17)":"#b89040",
    "Dusk (17–20)":     "#8c5a70",
    "Night (20–5)":     "#4a5c70",
}

SEASON_COLORS = {
    "Spring": "#7aaa6a",
    "Summer": "#d4ac60",
    "Autumn": "#c47a5a",
    "Winter": "#4a7090",
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


def assign_time_bucket(hour):
    if 5 <= hour < 8:
        return "Dawn (5–8)"
    elif 8 <= hour < 12:
        return "Morning (8–12)"
    elif 12 <= hour < 17:
        return "Afternoon (12–17)"
    elif 17 <= hour < 20:
        return "Dusk (17–20)"
    else:
        return "Night (20–5)"


@st.cache_data
def compute_nmds(feature_matrix, species_list):
    dist = squareform(pdist(feature_matrix, metric="braycurtis"))
    mds = MDS(
        n_components=2,
        metric=False,
        dissimilarity="precomputed",
        n_init=10,
        max_iter=500,
        random_state=42,
    )
    coords = mds.fit_transform(dist)
    stress = mds.stress_
    return coords, stress


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


def load_diet_map():
    try:
        with open("species_diet.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

_diet_map = load_diet_map()
df["Diet"] = df["Sci_Name"].map(_diet_map).fillna("Unclassified")


@st.cache_data(ttl=86400)
def fetch_weather(lat: float, lon: float, start_date: str, end_date: str):
    """Fetch historical hourly weather from Open-Meteo and return a DataFrame."""
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&hourly=temperature_2m,precipitation,wind_speed_10m,cloud_cover,pressure_msl"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,sunrise,sunset"
        f"&timezone=Europe%2FLondon"
    )
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return None, None
        data = resp.json()

        hourly = pd.DataFrame({
            "datetime": pd.to_datetime(data["hourly"]["time"]),
            "temperature": data["hourly"]["temperature_2m"],
            "precipitation": data["hourly"]["precipitation"],
            "wind_speed": data["hourly"]["wind_speed_10m"],
            "cloud_cover": data["hourly"]["cloud_cover"],
            "pressure": data["hourly"]["pressure_msl"],
        })
        hourly["date"] = hourly["datetime"].dt.date
        hourly["hour"] = hourly["datetime"].dt.hour

        # Parse sunrise/sunset as Europe/London aware, then convert to UTC
        _tz_london = ZoneInfo("Europe/London")
        _tz_utc = ZoneInfo("UTC")
        sunrise_local = pd.to_datetime(data["daily"]["sunrise"])
        sunset_local = pd.to_datetime(data["daily"]["sunset"])
        sunrise_utc = sunrise_local.map(lambda t: t.replace(tzinfo=_tz_london).astimezone(_tz_utc).replace(tzinfo=None))
        sunset_utc = sunset_local.map(lambda t: t.replace(tzinfo=_tz_london).astimezone(_tz_utc).replace(tzinfo=None))

        daily = pd.DataFrame({
            "date": pd.to_datetime(data["daily"]["time"]).date,
            "temp_max": data["daily"]["temperature_2m_max"],
            "temp_min": data["daily"]["temperature_2m_min"],
            "precip_sum": data["daily"]["precipitation_sum"],
            "wind_max": data["daily"]["wind_speed_10m_max"],
            "sunrise": sunrise_local,
            "sunset": sunset_local,
            "sunrise_utc": sunrise_utc,
            "sunset_utc": sunset_utc,
        })
        return hourly, daily
    except Exception:
        return None, None


_TZ_LONDON = ZoneInfo("Europe/London")
_TZ_UTC = ZoneInfo("UTC")


def to_utc_hour(ts: pd.Series) -> pd.Series:
    """Convert naive local (Europe/London) detection timestamps to UTC decimal hours."""
    utc_ts = ts.apply(lambda t: t.replace(tzinfo=_TZ_LONDON).astimezone(_TZ_UTC) if pd.notna(t) else t)
    return utc_ts.dt.hour + utc_ts.dt.minute / 60.0


st.title("🐦 Garden Bird Dashboard")
st.caption("Detections across time, seasons, and community composition.")

# ---- Sidebar filters ----
st.sidebar.header("Explore")

page = st.sidebar.radio(
    "View",
    [
        "Overview",
        "Community",
        "NMDS",
        "Dawn Chorus Overview",
        "Weather & Activity",
        "Data Quality",
        "Records",
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

exclude_review = st.sidebar.checkbox("Exclude 'Review Recording' & 'False Positive'", value=True)
review_df = filtered[filtered["UK_Status"] == "Review Recording"].copy()
if exclude_review:
    filtered = filtered[~filtered["UK_Status"].isin(["Review Recording", "False Positive"])].copy()

# ---- KPI cards ----
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Detections",  f"{len(filtered):,}")
kpi2.metric("Unique Species",    f"{filtered['Com_Name'].nunique():,}")
kpi3.metric("Average Confidence",
            f"{filtered['Confidence'].mean():.2f}" if len(filtered) else "—")

st.divider()

# ── Overview ────────────────────────────────────────────────────────────────
if page == "Overview":
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

    st.divider()

    # ── Detection Trends (Yearly / Monthly / Weekly) ──
    st.subheader("Detection Trends")

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

    # Monthly & Weekly — with optional year comparison
    trends_df = filtered.dropna(subset=["timestamp"]).copy()
    trends_df["year"] = trends_df["timestamp"].dt.year.astype(int)
    trends_years_avail = sorted(trends_df["year"].dropna().unique())

    trends_cmp = st.checkbox("Compare years", value=False, key="trends_cmp_years")

    if trends_cmp and len(trends_years_avail) >= 2:
        default_trends_yrs = trends_years_avail[-2:] if len(trends_years_avail) >= 2 else trends_years_avail
        trends_years = st.multiselect(
            "Years to compare", trends_years_avail,
            default=default_trends_yrs, key="trends_years",
        )
        if not trends_years:
            st.info("Select at least one year.")
        else:
            t_df = trends_df[trends_df["year"].isin(trends_years)].copy()

            # Monthly by year
            monthly_yr = t_df.groupby(["year", "month"]).size().reset_index(name="Count")
            monthly_yr["Year"] = monthly_yr["year"].astype(str)
            fig = px.line(
                monthly_yr, x="month", y="Count", color="Year",
                title="Monthly Detection Trends by Year",
                labels={"month": "Month", "Count": "Detections", "Year": "Year"},
                color_discrete_sequence=NATURE_PALETTE,
                markers=True,
            )
            fig.update_traces(line=dict(width=2), marker=dict(size=5))
            fig.update_layout(xaxis=dict(
                dtick=1,
                tickmode="array",
                tickvals=list(MONTH_LABELS.keys()),
                ticktext=list(MONTH_LABELS.values()),
            ))
            st.plotly_chart(style_fig(fig), use_container_width=True)

            # Weekly by year
            weekly_yr = t_df.groupby(["year", "week"]).size().reset_index(name="Count")
            weekly_yr["Year"] = weekly_yr["year"].astype(str)
            fig = px.line(
                weekly_yr, x="week", y="Count", color="Year",
                title="Weekly Detection Trends by Year",
                labels={"week": "Week of year", "Count": "Detections", "Year": "Year"},
                color_discrete_sequence=NATURE_PALETTE,
                markers=True,
            )
            fig.update_traces(line=dict(width=2), marker=dict(size=4))
            st.plotly_chart(style_fig(fig), use_container_width=True)
    else:
        # Monthly — aggregated
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

        # Weekly — aggregated
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

# ── Community ──────────────────────────────────────────────────────
elif page == "Community":

    def tod_chart(data: pd.DataFrame, title: str, by_species: bool, by_status: bool):
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
        elif by_status:
            status_hour = (
                data.groupby(["hour", "UK_Status"])
                .size()
                .reset_index(name="Count")
            )
            cmap = status_color_map(status_hour["UK_Status"].unique())
            fig = px.line(
                status_hour,
                x="hour", y="Count",
                color="UK_Status",
                markers=True,
                title=title,
                labels={"hour": "Hour of day", "Count": "Detections", "UK_Status": "UK Status"},
                color_discrete_map=cmap,
            )
            fig.update_layout(xaxis=dict(dtick=1))
            fig.update_traces(line=dict(width=2), marker=dict(size=5))
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

    def _tod_on_species():
        if st.session_state.get("tod_by_species"):
            st.session_state["tod_by_status"] = False

    def _tod_on_status():
        if st.session_state.get("tod_by_status"):
            st.session_state["tod_by_species"] = False

    tc1, tc2, tc3, tc4 = st.columns(4, gap="large")
    with tc1:
        show_by_species = st.checkbox("Show by species", value=False, key="tod_by_species", on_change=_tod_on_species)
    with tc2:
        show_by_status = st.checkbox("Show by status", value=False, key="tod_by_status", on_change=_tod_on_status)
    with tc3:
        tod_cmp_months = st.checkbox("Compare two months", value=False, key="tod_cmp_months", on_change=_tod_on_months)
    with tc4:
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
                      f"{tod_ma} · {years_label} · {season_label}", show_by_species, show_by_status)
        with r:
            tod_chart(_cmp[_cmp["month_num"] == month_num_by_name[tod_mb]],
                      f"{tod_mb} · {years_label} · {season_label}", show_by_species, show_by_status)

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
                      f"{tod_sa} · {years_label} · {month_label}", show_by_species, show_by_status)
        with r:
            tod_chart(_cmp[_cmp["season"] == tod_sb],
                      f"{tod_sb} · {years_label} · {month_label}", show_by_species, show_by_status)

    else:
        tod_chart(filtered, f"Activity by Hour · {month_label} · {years_label} · {season_label}",
                  show_by_species, show_by_status)

    st.divider()

    # ── Heatmap ──
    st.subheader("Activity Heatmap")

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

    st.divider()

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

    st.divider()

    # ── Status / Diet Over Time ──
    st.subheader("Composition Over Time")

    comp_mode = st.radio("Breakdown by", ["UK Status", "Diet"], horizontal=True, key="comp_over_time")

    tmp = filtered.dropna(subset=["timestamp"]).copy()

    if comp_mode == "UK Status":
        comp_col = "UK_Status"
        comp_label = "UK Status"
        comp_month = (
            tmp.groupby(["month", comp_col])
            .size()
            .reset_index(name="Count")
        )
        comp_month["Percent"] = (
            comp_month.groupby("month")["Count"]
            .transform(lambda x: (x / x.sum()) * 100)
        )
        cmap = status_color_map(comp_month[comp_col].unique())
        fig = px.area(
            comp_month,
            x="month", y="Percent",
            color=comp_col,
            title="Monthly Status Composition",
            labels={"month": "Month", "Percent": "% of detections", comp_col: comp_label},
            color_discrete_map=cmap,
        )
    else:
        comp_col = "Diet"
        comp_label = "Diet"
        comp_month = (
            tmp.groupby(["month", comp_col])
            .size()
            .reset_index(name="Count")
        )
        comp_month["Percent"] = (
            comp_month.groupby("month")["Count"]
            .transform(lambda x: (x / x.sum()) * 100)
        )
        fig = px.area(
            comp_month,
            x="month", y="Percent",
            color=comp_col,
            title="Monthly Diet Composition",
            labels={"month": "Month", "Percent": "% of detections", comp_col: comp_label},
            color_discrete_map=DIET_COLORS,
        )

    fig.update_layout(xaxis=dict(
        dtick=1,
        tickmode="array",
        tickvals=list(MONTH_LABELS.keys()),
        ticktext=list(MONTH_LABELS.values()),
    ))
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.divider()

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

    div_df = filtered.dropna(subset=["timestamp"]).copy()
    div_df["year"] = div_df["timestamp"].dt.year.astype(int)
    div_years_avail = sorted(div_df["year"].dropna().unique())

    div_cmp = st.checkbox("Compare years", value=False, key="div_cmp_years")

    if len(div_df) == 0:
        st.info("No data available for diversity index computation.")
    elif div_cmp and len(div_years_avail) >= 2:
        default_div_yrs = div_years_avail[-2:] if len(div_years_avail) >= 2 else div_years_avail
        div_years = st.multiselect(
            "Years to compare", div_years_avail,
            default=default_div_yrs, key="div_years",
        )
        if not div_years:
            st.info("Select at least one year.")
        else:
            d_df = div_df[div_df["year"].isin(div_years)].copy()

            # Compute indices per year × month
            div_rows = []
            for yr in sorted(div_years):
                for m in range(1, 13):
                    p_df = d_df[(d_df["year"] == yr) & (d_df["month"] == m)]
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
                    div_rows.append({"Year": str(yr), "month": m, "Shannon_H": shannon,
                                     "Simpson_1D": simpson, "Unique_Species": richness})
            div_result = pd.DataFrame(div_rows)

            _month_tick = dict(dtick=1, tickmode="array",
                               tickvals=list(MONTH_LABELS.keys()),
                               ticktext=list(MONTH_LABELS.values()))

            fig_h = px.line(
                div_result, x="month", y="Shannon_H", color="Year",
                title="Shannon Diversity (H') by Year",
                labels={"month": "Month", "Shannon_H": "H'", "Year": "Year"},
                color_discrete_sequence=NATURE_PALETTE,
                markers=True,
            )
            fig_h.update_traces(line=dict(width=2), marker=dict(size=5))
            fig_h.update_layout(xaxis=_month_tick)
            st.plotly_chart(style_fig(fig_h), use_container_width=True)

            fig_s = px.line(
                div_result, x="month", y="Simpson_1D", color="Year",
                title="Simpson's Diversity (1-D) by Year",
                labels={"month": "Month", "Simpson_1D": "1-D", "Year": "Year"},
                color_discrete_sequence=NATURE_PALETTE,
                markers=True,
            )
            fig_s.update_traces(line=dict(width=2), marker=dict(size=5))
            fig_s.update_layout(xaxis=_month_tick)
            st.plotly_chart(style_fig(fig_s), use_container_width=True)

            fig_r = px.line(
                div_result, x="month", y="Unique_Species", color="Year",
                title="Unique Species per Month by Year",
                labels={"month": "Month", "Unique_Species": "Unique species", "Year": "Year"},
                color_discrete_sequence=NATURE_PALETTE,
                markers=True,
            )
            fig_r.update_traces(line=dict(width=2), marker=dict(size=5))
            fig_r.update_layout(xaxis=_month_tick)
            st.plotly_chart(style_fig(fig_r), use_container_width=True)
    else:
        div_res = st.radio("Time resolution", ["Month", "Week"], horizontal=True, key="div_res")

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
            div_rows.append({"Period": p, "Shannon_H": shannon, "Simpson_1D": simpson, "Unique_Species": richness})
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

        fig_r = px.line(
            div_result, x="Period", y="Unique_Species",
            title="Unique Species per Month",
            labels={"Period": div_res, "Unique_Species": "Unique species"},
            markers=True,
        )
        fig_r.update_traces(line=dict(color=TERTIARY, width=2), marker=dict(size=5, color=TERTIARY))
        st.plotly_chart(style_fig(fig_r), use_container_width=True)

# ── NMDS ──────────────────────────────────────────────────────────────────
elif page == "NMDS":
    st.subheader("NMDS Ordination")

    nmds_c1, nmds_c2, nmds_c3 = st.columns(3)
    with nmds_c1:
        nmds_matrix = st.selectbox(
            "Feature matrix",
            ["Species × Diet", "Species × UK Status", "Species × Time Bucket", "Species × Season"],
            key="nmds_matrix",
        )
    with nmds_c2:
        nmds_colour = st.selectbox(
            "Colour by",
            ["Diet", "UK Status", "Dominant Time Bucket", "Peak Season"],
            key="nmds_colour",
        )
    with nmds_c3:
        nmds_min_det = st.slider(
            "Minimum detections per species", 1, 100, 5, key="nmds_min_det",
        )

    # Filter to species with enough detections
    nmds_det_counts = filtered["Com_Name"].value_counts()
    nmds_valid_species = nmds_det_counts[nmds_det_counts >= nmds_min_det].index.tolist()
    nmds_df = filtered[filtered["Com_Name"].isin(nmds_valid_species)].copy()

    if len(nmds_valid_species) < 5:
        st.warning(
            f"Only {len(nmds_valid_species)} species meet the minimum detection threshold. "
            "At least 5 are needed for NMDS. Try lowering the threshold or broadening filters."
        )
    else:
        nmds_ts = nmds_df.dropna(subset=["timestamp"]).copy()

        # Build pivot table based on chosen matrix
        _season_map = {1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
                       6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn",
                       11: "Autumn", 12: "Winter"}
        if nmds_matrix == "Species × Diet":
            nmds_ts["_unit"] = nmds_ts["Diet"]
            all_cols = sorted(nmds_ts["Diet"].dropna().unique())
        elif nmds_matrix == "Species × UK Status":
            nmds_ts["_unit"] = nmds_ts["UK_Status"]
            all_cols = sorted(nmds_ts["UK_Status"].dropna().unique())
        elif nmds_matrix == "Species × Time Bucket":
            nmds_ts["_unit"] = nmds_ts["hour"].apply(assign_time_bucket)
            all_cols = list(TIME_BUCKET_COLORS.keys())
        else:  # Species × Season
            nmds_ts["_unit"] = nmds_ts["month"].map(_season_map)
            all_cols = list(SEASON_COLORS.keys())

        nmds_pivot = nmds_ts.pivot_table(
            index="Com_Name", columns="_unit", values="timestamp",
            aggfunc="count", fill_value=0,
        )
        # Ensure all columns present
        for c in all_cols:
            if c not in nmds_pivot.columns:
                nmds_pivot[c] = 0
        nmds_pivot = nmds_pivot[all_cols]

        # Normalise rows to proportions
        row_sums = nmds_pivot.sum(axis=1).replace(0, 1)
        nmds_norm = nmds_pivot.div(row_sums, axis=0)

        species_list = nmds_norm.index.tolist()
        coords, stress = compute_nmds(nmds_norm.values, tuple(species_list))

        # Build result DataFrame with metadata
        nmds_result = pd.DataFrame({
            "Species": species_list,
            "NMDS1": coords[:, 0],
            "NMDS2": coords[:, 1],
        })

        # Add metadata per species
        sp_meta = nmds_df.groupby("Com_Name").agg(
            Diet=("Diet", lambda x: x.mode().iloc[0] if len(x.mode()) else "Unclassified"),
            UK_Status=("UK_Status", lambda x: x.mode().iloc[0] if len(x.mode()) else "Unknown"),
            Detections=("Com_Name", "count"),
        ).reset_index().rename(columns={"Com_Name": "Species"})

        # Dominant time bucket
        nmds_ts["_tb"] = nmds_ts["hour"].apply(assign_time_bucket)
        tb_counts = nmds_ts.groupby(["Com_Name", "_tb"]).size().reset_index(name="n")
        dom_tb = tb_counts.loc[tb_counts.groupby("Com_Name")["n"].idxmax()][["Com_Name", "_tb"]]
        dom_tb.columns = ["Species", "Dominant_Time_Bucket"]

        # Peak season
        nmds_ts["_season"] = nmds_ts["month"].map(_season_map)
        season_counts = nmds_ts.groupby(["Com_Name", "_season"]).size().reset_index(name="n")
        peak_season = season_counts.loc[season_counts.groupby("Com_Name")["n"].idxmax()][["Com_Name", "_season"]]
        peak_season.columns = ["Species", "Peak_Season"]

        nmds_result = nmds_result.merge(sp_meta, on="Species", how="left")
        nmds_result = nmds_result.merge(dom_tb, on="Species", how="left")
        nmds_result = nmds_result.merge(peak_season, on="Species", how="left")

        # Select colour column and colour map
        if nmds_colour == "Diet":
            color_col = "Diet"
            color_map = DIET_COLORS
        elif nmds_colour == "UK Status":
            color_col = "UK_Status"
            color_map = STATUS_COLORS
        elif nmds_colour == "Dominant Time Bucket":
            color_col = "Dominant_Time_Bucket"
            color_map = TIME_BUCKET_COLORS
        else:  # Peak Season
            color_col = "Peak_Season"
            color_map = SEASON_COLORS

        fig_nmds = px.scatter(
            nmds_result,
            x="NMDS1", y="NMDS2",
            color=color_col,
            color_discrete_map=color_map,
            hover_name="Species",
            hover_data={
                "Diet": True,
                "UK_Status": True,
                "Dominant_Time_Bucket": True,
                "Peak_Season": True,
                "Detections": True,
                "NMDS1": ":.3f",
                "NMDS2": ":.3f",
            },
            title="NMDS — Species Similarity Ordination",
        )
        fig_nmds.update_traces(marker=dict(size=10, line=dict(width=1, color="rgba(26,36,22,0.3)")))
        st.plotly_chart(style_fig(fig_nmds), use_container_width=True)

        # Metrics row
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Stress", f"{stress:.4f}")
        mc2.metric("Species", len(species_list))
        if stress < 0.05:
            quality = "Excellent"
        elif stress < 0.1:
            quality = "Good"
        elif stress < 0.2:
            quality = "Fair"
        else:
            quality = "Poor"
        mc3.metric("Stress Quality", quality)
        st.caption(
            "Stress measures how well the 2D layout preserves the original dissimilarities. "
            "Excellent < 0.05, Good < 0.1, Fair < 0.2, Poor ≥ 0.2."
        )

# ── Dawn Chorus Overview ──────────────────────────────────────────────────
elif page == "Dawn Chorus Overview":

    # ── Dawn Chorus Tracker ──
    st.subheader("Dawn Chorus Tracker")
    dc_c1, dc_c2 = st.columns(2, gap="large")
    with dc_c1:
        dc_topn = st.slider("Top N species", 5, 20, 12, key="dc_topn")
    with dc_c2:
        dc_time_mode = st.radio("Time format", ["Local (GMT/BST)", "UTC"], horizontal=True, key="dc_time_mode")

    dc_df = filtered.dropna(subset=["timestamp"]).copy()
    dc_df = dc_df[(dc_df["hour"] >= 3) & (dc_df["hour"] <= 10)]

    if len(dc_df) == 0:
        st.info("No detections in the dawn window (03:00-10:00) for current filters.")
    else:
        top_dawn = dc_df["Com_Name"].value_counts().head(dc_topn).index.tolist()
        dc_df = dc_df[dc_df["Com_Name"].isin(top_dawn)].copy()
        dc_df["date"] = dc_df["timestamp"].dt.date

        # Open-Meteo sunrise is in GMT (smooth). Detections are in local time.
        # In UTC mode: convert detections local→UTC so both align with sunrise.
        # In local mode: use raw detection hours; shift sunrise by +1 during BST.
        use_utc = dc_time_mode == "UTC"
        if use_utc:
            dc_df["decimal_hour"] = to_utc_hour(dc_df["timestamp"])
            hour_label = "Hour (UTC)"
        else:
            dc_df["decimal_hour"] = dc_df["timestamp"].dt.hour + dc_df["timestamp"].dt.minute / 60.0
            hour_label = "Hour (local)"

        earliest = (
            dc_df.groupby(["date", "Com_Name"])["decimal_hour"]
            .min()
            .reset_index(name="Earliest_Hour")
        )

        color_map = {
            sp: NATURE_PALETTE[i % len(NATURE_PALETTE)]
            for i, sp in enumerate(top_dawn)
        }
        fig = px.scatter(
            earliest, x="date", y="Earliest_Hour",
            color="Com_Name",
            title="Earliest Detection by Day (Dawn Window)",
            labels={"date": "Date", "Earliest_Hour": hour_label, "Com_Name": "Species"},
            color_discrete_map=color_map,
        )
        fig.update_traces(marker=dict(size=5, opacity=0.7))

        # Always show sunrise
        w_lat = float(dc_df["Lat"].mode().iloc[0])
        w_lon = float(dc_df["Lon"].mode().iloc[0])
        w_start = dc_df["timestamp"].min().strftime("%Y-%m-%d")
        w_end = dc_df["timestamp"].max().strftime("%Y-%m-%d")
        _, sunrise_daily = fetch_weather(w_lat, w_lon, w_start, w_end)
        if sunrise_daily is not None and "sunrise" in sunrise_daily.columns:
            sunrise_daily = sunrise_daily.copy()
            if use_utc:
                # Sunrise from Open-Meteo is already GMT/UTC
                sunrise_daily["sunrise_hour"] = (
                    sunrise_daily["sunrise"].dt.hour + sunrise_daily["sunrise"].dt.minute / 60.0
                )
            else:
                # Convert GMT sunrise to local time (add 1 hour during BST)
                sunrise_daily["sunrise_hour"] = sunrise_daily["sunrise"].apply(
                    lambda t: t.replace(tzinfo=_TZ_UTC).astimezone(_TZ_LONDON)
                ).dt.hour + sunrise_daily["sunrise"].apply(
                    lambda t: t.replace(tzinfo=_TZ_UTC).astimezone(_TZ_LONDON)
                ).dt.minute / 60.0
            fig.add_scatter(
                x=sunrise_daily["date"], y=sunrise_daily["sunrise_hour"],
                mode="lines", line=dict(color="#c47a5a", width=2.5, dash="dash"),
                name="Sunrise", showlegend=True,
            )

        st.plotly_chart(style_fig(fig), use_container_width=True)

    st.divider()

    # ── First Detection vs Sunrise ──
    st.subheader("First Detection vs Sunrise")

    fds_df = filtered.dropna(subset=["timestamp"]).copy()
    fds_df = fds_df[(fds_df["hour"] >= 3) & (fds_df["hour"] <= 10)].copy()

    if len(fds_df) == 0:
        st.info("No dawn detections (03:00-10:00) in the current filters.")
    else:
        fds_df["date"] = fds_df["timestamp"].dt.date

        # Reuse the same time mode from the dawn chorus tracker
        fds_utc = dc_time_mode == "UTC"

        # Earliest detection per day
        fds_earliest = (
            fds_df.groupby("date")["timestamp"]
            .min()
            .reset_index(name="earliest_detection")
        )
        if fds_utc:
            fds_earliest["earliest_hour"] = to_utc_hour(fds_earliest["earliest_detection"])
        else:
            fds_earliest["earliest_hour"] = (
                fds_earliest["earliest_detection"].dt.hour
                + fds_earliest["earliest_detection"].dt.minute / 60.0
            )

        # Fetch weather for sunrise data
        fds_lat = float(fds_df["Lat"].mode().iloc[0])
        fds_lon = float(fds_df["Lon"].mode().iloc[0])
        fds_start = fds_df["timestamp"].min().strftime("%Y-%m-%d")
        fds_end = fds_df["timestamp"].max().strftime("%Y-%m-%d")
        fds_weather_hourly, fds_weather_daily = fetch_weather(fds_lat, fds_lon, fds_start, fds_end)

        if fds_weather_daily is not None and "sunrise" in fds_weather_daily.columns:
            sunrise_df = fds_weather_daily[["date", "sunrise"]].copy()
            if fds_utc:
                sunrise_df["sunrise_hour"] = (
                    sunrise_df["sunrise"].dt.hour + sunrise_df["sunrise"].dt.minute / 60.0
                )
            else:
                _sr_local = sunrise_df["sunrise"].apply(
                    lambda t: t.replace(tzinfo=_TZ_UTC).astimezone(_TZ_LONDON)
                )
                sunrise_df["sunrise_hour"] = _sr_local.dt.hour + _sr_local.dt.minute / 60.0

            # Temperature at sunrise hour
            sunrise_temps = []
            for _, row in sunrise_df.iterrows():
                sr_row = fds_weather_daily[fds_weather_daily["date"] == row["date"]]
                if len(sr_row):
                    sr_hour = int(sr_row.iloc[0]["sunrise"].hour)
                else:
                    sr_hour = 6
                match = fds_weather_hourly[
                    (fds_weather_hourly["date"] == row["date"]) & (fds_weather_hourly["hour"] == sr_hour)
                ] if fds_weather_hourly is not None else pd.DataFrame()
                temp = match["temperature"].iloc[0] if len(match) > 0 else None
                sunrise_temps.append({"date": row["date"], "sunrise_hour": row["sunrise_hour"],
                                      "sunrise_temp": temp})
            sunrise_temp_df = pd.DataFrame(sunrise_temps)

            fds_merged = fds_earliest.merge(sunrise_temp_df, on="date", how="inner")
            fds_merged = fds_merged.dropna(subset=["sunrise_temp"])

            hour_suffix = "UTC" if fds_utc else "local"

            if len(fds_merged) == 0:
                st.info("No matching weather data for dawn detections.")
            else:
                d_l2, d_r2 = st.columns(2, gap="large")
                with d_l2:
                    fig = px.scatter(
                        fds_merged, x="sunrise_temp", y="earliest_hour",
                        title="First Detection vs Sunrise Temperature",
                        labels={"sunrise_temp": "Temperature at sunrise (°C)",
                                "earliest_hour": f"Earliest detection ({hour_suffix})"},
                        hover_data={"date": True},
                    )
                    fig.update_traces(marker=dict(size=8, color=PRIMARY, opacity=0.7))
                    if len(fds_merged) > 2:
                        z = np.polyfit(fds_merged["sunrise_temp"], fds_merged["earliest_hour"], 1)
                        x_range = np.linspace(fds_merged["sunrise_temp"].min(),
                                              fds_merged["sunrise_temp"].max(), 50)
                        fig.add_scatter(x=x_range, y=np.polyval(z, x_range),
                                        mode="lines", line=dict(color=TERTIARY, width=2, dash="dash"),
                                        name="Trend", showlegend=True)
                    st.plotly_chart(style_fig(fig), use_container_width=True)

                with d_r2:
                    fig = px.scatter(
                        fds_merged, x="sunrise_hour", y="earliest_hour",
                        title="First Detection vs Sunrise Time",
                        labels={"sunrise_hour": f"Sunrise ({hour_suffix})",
                                "earliest_hour": f"Earliest detection ({hour_suffix})"},
                        hover_data={"date": True},
                    )
                    fig.update_traces(marker=dict(size=8, color=SECONDARY, opacity=0.7))
                    # Add y=x reference line
                    xy_range = [min(fds_merged["sunrise_hour"].min(), fds_merged["earliest_hour"].min()),
                                max(fds_merged["sunrise_hour"].max(), fds_merged["earliest_hour"].max())]
                    fig.add_scatter(x=xy_range, y=xy_range,
                                    mode="lines", line=dict(color="#1a2416", width=1, dash="dot"),
                                    name="Sunrise = Detection", showlegend=True)
                    st.plotly_chart(style_fig(fig), use_container_width=True)
        else:
            st.info("Could not fetch sunrise data.")

# ── Weather & Activity ──────────────────────────────────────────────────────
elif page == "Weather & Activity":

    w_df = filtered.dropna(subset=["timestamp"]).copy()

    if len(w_df) == 0:
        st.info("No detection data available for weather analysis.")
    else:
        # Get location and date range from the data
        w_lat = float(w_df["Lat"].mode().iloc[0])
        w_lon = float(w_df["Lon"].mode().iloc[0])
        w_start = w_df["timestamp"].min().strftime("%Y-%m-%d")
        w_end = w_df["timestamp"].max().strftime("%Y-%m-%d")

        weather_hourly, weather_daily = fetch_weather(w_lat, w_lon, w_start, w_end)

        if weather_hourly is None or weather_daily is None:
            st.error("Could not fetch weather data from Open-Meteo.")
        else:
            # ── Prepare merged datasets ──
            w_df["date"] = w_df["timestamp"].dt.date
            w_df["hour"] = w_df["timestamp"].dt.hour

            # Daily detection counts
            daily_det = w_df.groupby("date").agg(
                det_count=("Com_Name", "size"),
                species_count=("Com_Name", "nunique"),
            ).reset_index()
            daily_merged = daily_det.merge(weather_daily, on="date", how="inner")

            # Hourly detection counts
            hourly_det = w_df.groupby(["date", "hour"]).size().reset_index(name="det_count")
            hourly_merged = hourly_det.merge(weather_hourly, on=["date", "hour"], how="inner")

            # ── 1. Detections vs Temperature ──
            st.subheader("Detections vs Temperature")

            fig = px.scatter(
                daily_merged, x="temp_max", y="det_count",
                color="precip_sum",
                color_continuous_scale=[[0, "#f5f3ee"], [0.5, "#6a90b0"], [1, "#4a5c70"]],
                title="Daily Detections vs Max Temperature",
                labels={"temp_max": "Max temperature (°C)", "det_count": "Detections",
                        "precip_sum": "Rainfall (mm)"},
                hover_data={"date": True},
            )
            fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="#1a2416")))
            # Add trendline manually
            if len(daily_merged) > 2:
                z = np.polyfit(daily_merged["temp_max"].dropna(), daily_merged.loc[daily_merged["temp_max"].notna(), "det_count"], 1)
                x_range = np.linspace(daily_merged["temp_max"].min(), daily_merged["temp_max"].max(), 50)
                fig.add_scatter(x=x_range, y=np.polyval(z, x_range),
                                mode="lines", line=dict(color=PRIMARY, width=2, dash="dash"),
                                name="Trend", showlegend=True)
            st.plotly_chart(style_fig(fig), use_container_width=True)

            st.divider()

            # ── 2. Rainy vs Dry Days ──
            st.subheader("Rainy vs Dry Days")

            # Merge hourly weather with hourly detections for activity profile
            rain_thresh = st.slider("Rain threshold (mm/day)", 0.0, 10.0, 1.0, key="w_rain_thresh")

            rain_days = set(weather_daily[weather_daily["precip_sum"] >= rain_thresh]["date"].tolist())
            w_df["day_type"] = w_df["date"].apply(lambda d: "Rainy" if d in rain_days else "Dry")

            rain_profile = w_df.groupby(["hour", "day_type"]).size().reset_index(name="Count")
            # Normalise by number of days of each type
            n_rain = max(len(rain_days & set(w_df["date"].unique())), 1)
            n_dry = max(len(set(w_df["date"].unique()) - rain_days), 1)
            rain_profile["Avg_Detections"] = rain_profile.apply(
                lambda r: r["Count"] / n_rain if r["day_type"] == "Rainy" else r["Count"] / n_dry,
                axis=1,
            )

            fig = px.line(
                rain_profile, x="hour", y="Avg_Detections", color="day_type",
                title=f"Average Hourly Activity: Rainy vs Dry Days (threshold: {rain_thresh}mm)",
                labels={"hour": "Hour of day", "Avg_Detections": "Avg detections per day",
                        "day_type": "Day type"},
                color_discrete_map={"Rainy": SECONDARY, "Dry": TERTIARY},
                markers=True,
            )
            fig.update_traces(line=dict(width=2), marker=dict(size=5))
            fig.update_layout(xaxis=dict(dtick=1))

            # Add KPI cards
            r_k1, r_k2, r_k3 = st.columns(3)
            r_k1.metric("Rainy days", f"{n_rain}")
            r_k2.metric("Dry days", f"{n_dry}")
            avg_rain_det = daily_merged[daily_merged["date"].isin(rain_days)]["det_count"].mean()
            avg_dry_det = daily_merged[~daily_merged["date"].isin(rain_days)]["det_count"].mean()
            r_k3.metric("Avg detections",
                        f"Rainy: {avg_rain_det:.0f}" if pd.notna(avg_rain_det) else "—",
                        f"Dry: {avg_dry_det:.0f}" if pd.notna(avg_dry_det) else None)

            st.plotly_chart(style_fig(fig), use_container_width=True)

            st.divider()

            # ── 3. Wind Speed Impact ──
            st.subheader("Wind Speed Impact")

            wind_bins = [0, 10, 20, 30, 100]
            wind_labels = ["Calm (0-10)", "Light (10-20)", "Moderate (20-30)", "Strong (30+)"]
            daily_merged["wind_bracket"] = pd.cut(
                daily_merged["wind_max"], bins=wind_bins, labels=wind_labels, right=False,
            )

            wind_agg = daily_merged.groupby("wind_bracket", observed=True).agg(
                avg_det=("det_count", "mean"),
                avg_species=("species_count", "mean"),
                day_count=("date", "count"),
            ).reset_index()

            w_l, w_r = st.columns(2, gap="large")
            with w_l:
                fig = px.bar(
                    wind_agg, x="wind_bracket", y="avg_det",
                    title="Avg Daily Detections by Wind Speed",
                    labels={"wind_bracket": "Wind speed (km/h)", "avg_det": "Avg detections"},
                    text="day_count",
                )
                fig.update_traces(marker_color=PRIMARY, marker_line_width=0,
                                  texttemplate="%{text} days", textposition="outside")
                st.plotly_chart(style_fig(fig), use_container_width=True)

            with w_r:
                fig = px.bar(
                    wind_agg, x="wind_bracket", y="avg_species",
                    title="Avg Species Richness by Wind Speed",
                    labels={"wind_bracket": "Wind speed (km/h)", "avg_species": "Avg unique species"},
                    text="day_count",
                )
                fig.update_traces(marker_color=SECONDARY, marker_line_width=0,
                                  texttemplate="%{text} days", textposition="outside")
                st.plotly_chart(style_fig(fig), use_container_width=True)

            st.divider()

            # ── 4. Weather Overlay on Monthly Trends ──
            st.subheader("Monthly Trends with Weather")

            daily_merged["month"] = pd.to_datetime(daily_merged["date"]).dt.month
            monthly_weather = daily_merged.groupby("month").agg(
                total_det=("det_count", "sum"),
                avg_temp=("temp_max", "mean"),
                total_rain=("precip_sum", "sum"),
            ).reset_index()

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Bar(x=monthly_weather["month"], y=monthly_weather["total_det"],
                       name="Detections", marker_color=PRIMARY, opacity=0.7),
                secondary_y=False,
            )
            fig.add_trace(
                go.Scatter(x=monthly_weather["month"], y=monthly_weather["avg_temp"],
                           name="Avg max temp (°C)", mode="lines+markers",
                           line=dict(color="#c47a5a", width=2.5),
                           marker=dict(size=7, color="#c47a5a")),
                secondary_y=True,
            )
            fig.update_layout(
                title="Monthly Detections & Temperature",
                xaxis=dict(dtick=1, tickmode="array",
                           tickvals=list(MONTH_LABELS.keys()),
                           ticktext=list(MONTH_LABELS.values())),
                legend=dict(x=0.01, y=0.99),
            )
            fig.update_yaxes(title_text="Detections", secondary_y=False)
            fig.update_yaxes(title_text="Temperature (°C)", secondary_y=True)
            st.plotly_chart(style_fig(fig), use_container_width=True)

            # Rainfall overlay
            fig2 = make_subplots(specs=[[{"secondary_y": True}]])
            fig2.add_trace(
                go.Bar(x=monthly_weather["month"], y=monthly_weather["total_det"],
                       name="Detections", marker_color=PRIMARY, opacity=0.7,
                       offsetgroup=0),
                secondary_y=False,
            )
            fig2.add_trace(
                go.Bar(x=monthly_weather["month"], y=monthly_weather["total_rain"],
                       name="Total rainfall (mm)", marker_color=SECONDARY, opacity=0.7,
                       offsetgroup=1),
                secondary_y=True,
            )
            fig2.update_layout(
                title="Monthly Detections & Rainfall",
                xaxis=dict(dtick=1, tickmode="array",
                           tickvals=list(MONTH_LABELS.keys()),
                           ticktext=list(MONTH_LABELS.values())),
                barmode="group",
                legend=dict(x=0.01, y=0.99),
            )
            fig2.update_yaxes(title_text="Detections", secondary_y=False)
            fig2.update_yaxes(title_text="Rainfall (mm)", secondary_y=True)
            st.plotly_chart(style_fig(fig2), use_container_width=True)

            st.divider()

            # ── 5. Species Diversity vs Conditions ──
            st.subheader("Species Diversity vs Conditions")

            d_l, d_r = st.columns(2, gap="large")
            with d_l:
                fig = px.scatter(
                    daily_merged, x="temp_max", y="species_count",
                    title="Unique Species vs Temperature",
                    labels={"temp_max": "Max temperature (°C)", "species_count": "Unique species"},
                    color="precip_sum",
                    color_continuous_scale=[[0, "#f5f3ee"], [0.5, "#6a90b0"], [1, "#4a5c70"]],
                )
                fig.update_traces(marker=dict(size=8, opacity=0.7))
                if len(daily_merged) > 2:
                    mask = daily_merged["temp_max"].notna()
                    z = np.polyfit(daily_merged.loc[mask, "temp_max"], daily_merged.loc[mask, "species_count"], 1)
                    x_range = np.linspace(daily_merged["temp_max"].min(), daily_merged["temp_max"].max(), 50)
                    fig.add_scatter(x=x_range, y=np.polyval(z, x_range),
                                    mode="lines", line=dict(color=PRIMARY, width=2, dash="dash"),
                                    name="Trend", showlegend=True)
                st.plotly_chart(style_fig(fig), use_container_width=True)

            with d_r:
                fig = px.scatter(
                    daily_merged, x="wind_max", y="species_count",
                    title="Unique Species vs Wind Speed",
                    labels={"wind_max": "Max wind speed (km/h)", "species_count": "Unique species"},
                    color="precip_sum",
                    color_continuous_scale=[[0, "#f5f3ee"], [0.5, "#6a90b0"], [1, "#4a5c70"]],
                )
                fig.update_traces(marker=dict(size=8, opacity=0.7))
                if len(daily_merged) > 2:
                    mask = daily_merged["wind_max"].notna()
                    z = np.polyfit(daily_merged.loc[mask, "wind_max"], daily_merged.loc[mask, "species_count"], 1)
                    x_range = np.linspace(daily_merged["wind_max"].min(), daily_merged["wind_max"].max(), 50)
                    fig.add_scatter(x=x_range, y=np.polyval(z, x_range),
                                    mode="lines", line=dict(color=PRIMARY, width=2, dash="dash"),
                                    name="Trend", showlegend=True)
                st.plotly_chart(style_fig(fig), use_container_width=True)


# ── Data Quality ─────────────────────────────────────────────────
elif page == "Data Quality":

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

    # ── Review Recording: Top Species to Check + Confidence by Hour ──
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

    st.divider()

    # ── Validate Review Recording species ──
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

            # Check if species already exists (match on Latin Name in column B)
            existing_row = None
            for row in ws.iter_rows(min_row=2):
                if row[1].value == sci_name:
                    existing_row = row
                    break

            if existing_row is not None:
                existing_row[0].value = com_name
                existing_row[2].value = new_status
            else:
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

                action = "Update" if existing_row is not None else "Add"
                put_resp = requests.put(
                    api_url,
                    headers=headers,
                    json={
                        "message": f"{action} species status: {sci_name} -> {new_status}",
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

# ── Records ───────────────────────────────────────────────────────────────
elif page == "Records":

    # ── First & Last Detection per Species ──
    st.subheader("First & Last Detection per Species")
    st.caption("Earliest and most recent date each species was recorded.")

    pr_df = filtered.dropna(subset=["timestamp"]).copy()
    pr_df["year"] = pr_df["timestamp"].dt.year

    pr_years_avail = sorted(pr_df["year"].dropna().unique())
    pr_years = st.multiselect(
        "Filter to years", pr_years_avail,
        default=pr_years_avail, key="pr_years",
    )

    if pr_years:
        pr_df = pr_df[pr_df["year"].isin(pr_years)].copy()

    if len(pr_df) == 0:
        st.info("No data available.")
    else:
        det_range = pr_df.groupby("Com_Name")["timestamp"].agg(["min", "max"]).reset_index()
        det_range.columns = ["Species", "Earliest_Detection", "Latest_Detection"]
        det_range["First Detected"] = det_range["Earliest_Detection"].dt.strftime("%Y-%m-%d")
        det_range["Last Detected"] = det_range["Latest_Detection"].dt.strftime("%Y-%m-%d")
        det_counts = pr_df["Com_Name"].value_counts().rename("Total Detections")
        det_range = det_range.merge(det_counts, left_on="Species", right_index=True)

        pr_k1, pr_k2 = st.columns(2)
        pr_k1.metric("Total species recorded", det_range["Species"].nunique())
        pr_k2.metric("Date range", f"{pr_df['timestamp'].min().strftime('%Y-%m-%d')} to {pr_df['timestamp'].max().strftime('%Y-%m-%d')}")

        st.dataframe(
            det_range[["Species", "First Detected", "Last Detected", "Total Detections"]]
            .sort_values("First Detected"),
            hide_index=True,
        )

    st.divider()

    # ── Rarest Visitors ──
    st.subheader("Rarest Visitors")
    st.caption("Species with the fewest total detections — when they appeared and at what confidence.")
    pr_rarest_n = st.slider("N rarest species", 5, 30, 15, key="pr_rarest_n")

    if len(pr_df) == 0:
        st.info("No data available.")
    else:
        # Identify the N rarest species
        species_counts = pr_df["Com_Name"].value_counts()
        rare_species = species_counts.tail(pr_rarest_n).index.tolist()
        rare_df = pr_df[pr_df["Com_Name"].isin(rare_species)].copy()
        rare_df["date"] = rare_df["timestamp"].dt.date

        # Timeline scatter — coloured by UK status
        cmap = status_color_map(rare_df["UK_Status"].dropna().unique())
        # Order species by detection count (fewest at top)
        species_order = species_counts.loc[rare_species].sort_values().index.tolist()

        fig = px.scatter(
            rare_df, x="date", y="Com_Name",
            color="UK_Status",
            size="Confidence",
            size_max=12,
            title=f"Rarest {pr_rarest_n} Species — Detection Timeline",
            labels={"date": "Date", "Com_Name": "Species", "UK_Status": "UK Status",
                    "Confidence": "Confidence"},
            color_discrete_map=cmap,
            category_orders={"Com_Name": species_order},
            hover_data={"Confidence": ":.2f", "date": True},
        )
        fig.update_traces(marker=dict(opacity=0.8, line=dict(width=0.5, color="#1a2416")))
        st.plotly_chart(style_fig(fig), use_container_width=True)

        # Detail table
        rare_table = (
            rare_df.groupby("Com_Name")
            .agg(
                Detections=("Com_Name", "size"),
                Avg_Confidence=("Confidence", "mean"),
                First_Seen=("timestamp", "min"),
                Last_Seen=("timestamp", "max"),
                UK_Status=("UK_Status", "first"),
            )
            .reset_index()
        )
        rare_table["First Seen"] = rare_table["First_Seen"].dt.strftime("%Y-%m-%d")
        rare_table["Last Seen"] = rare_table["Last_Seen"].dt.strftime("%Y-%m-%d")
        rare_table["Avg Confidence"] = rare_table["Avg_Confidence"].round(3)
        rare_table = rare_table.sort_values("Detections")

        st.dataframe(
            rare_table[["Com_Name", "Detections", "Avg Confidence", "First Seen", "Last Seen", "UK_Status"]]
            .rename(columns={"Com_Name": "Species", "UK_Status": "UK Status"}),
            hide_index=True,
        )

    st.divider()

    # ── Longest Detection Streak ──
    st.subheader("Longest Detection Streak")

    if len(pr_df) == 0:
        st.info("No data available.")
    else:
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

    # ── Classify Unclassified Species ──
    st.divider()
    st.subheader("Classify Unclassified Species")
    st.caption("Species not yet assigned a diet category.")

    unclassified = df[df["Diet"] == "Unclassified"][["Sci_Name", "Com_Name"]].drop_duplicates().sort_values("Sci_Name")

    if len(unclassified) == 0:
        st.success("All species have been classified!")
    else:
        st.warning(f"{len(unclassified)} species need diet classification.")
        labels = (unclassified["Sci_Name"] + "  (" + unclassified["Com_Name"] + ")").tolist()

        DIET_CATEGORIES = ["Insectivore", "Granivore", "Omnivore", "Frugivore",
                           "Carnivore", "Piscivore", "Herbivore"]

        with st.form("classify_diet"):
            chosen = st.selectbox("Species", labels)
            diet = st.selectbox("Diet category", DIET_CATEGORIES)
            submitted = st.form_submit_button("Save classification")

        if submitted:
            idx = labels.index(chosen)
            sci_name = unclassified.iloc[idx]["Sci_Name"]

            diet_data = load_diet_map()
            diet_data[sci_name] = diet
            with open("species_diet.json", "w") as f:
                json.dump(diet_data, f, indent=2, sort_keys=True)

            st.cache_data.clear()
            st.success(f"Classified {sci_name} as {diet}.")
            st.rerun()

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

                _se_status = filtered.loc[filtered["Sci_Name"] == se_sci, "UK_Status"].mode()
                _se_diet = filtered.loc[filtered["Sci_Name"] == se_sci, "Diet"].mode()
                _se_status_val = _se_status.iloc[0] if len(_se_status) else "Unknown"
                _se_diet_val = _se_diet.iloc[0] if len(_se_diet) else "Unclassified"
                _stat_color = STATUS_COLORS.get(_se_status_val, "#8c9c8c")
                _diet_color = DIET_COLORS.get(_se_diet_val, "#8c9c8c")
                st.markdown(
                    f'<span style="background:{_stat_color};color:#fff;padding:3px 10px;border-radius:8px;font-size:0.85rem;font-weight:600;margin-right:8px">{_se_status_val}</span>'
                    f'<span style="background:{_diet_color};color:#fff;padding:3px 10px;border-radius:8px;font-size:0.85rem;font-weight:600">{_se_diet_val}</span>',
                    unsafe_allow_html=True,
                )

                st.markdown(wiki["extract"])
                if wiki["page_url"]:
                    st.markdown(f"[Read more on Wikipedia]({wiki['page_url']})")

            if chosen_idx == bird_of_day_idx:
                st.caption("Bird of the day — changes daily, seeded by today's date.")

            first_sentence = wiki["extract"].split(". ")[0]
            if first_sentence:
                st.info(f"Fun fact: {first_sentence}.")
        else:
            st.markdown(f"### {se_com}")
            st.markdown(f"*{se_sci}*")
            _se_status = filtered.loc[filtered["Sci_Name"] == se_sci, "UK_Status"].mode()
            _se_diet = filtered.loc[filtered["Sci_Name"] == se_sci, "Diet"].mode()
            _se_status_val = _se_status.iloc[0] if len(_se_status) else "Unknown"
            _se_diet_val = _se_diet.iloc[0] if len(_se_diet) else "Unclassified"
            _stat_color = STATUS_COLORS.get(_se_status_val, "#8c9c8c")
            _diet_color = DIET_COLORS.get(_se_diet_val, "#8c9c8c")
            st.markdown(
                f'<span style="background:{_stat_color};color:#fff;padding:3px 10px;border-radius:8px;font-size:0.85rem;font-weight:600;margin-right:8px">{_se_status_val}</span>'
                f'<span style="background:{_diet_color};color:#fff;padding:3px 10px;border-radius:8px;font-size:0.85rem;font-weight:600">{_se_diet_val}</span>',
                unsafe_allow_html=True,
            )
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

        # Update species status & diet form
        st.divider()
        current_status = sp_df["UK_Status"].mode().iloc[0] if len(sp_df) > 0 else "Unknown"
        current_diet = sp_df["Diet"].mode().iloc[0] if len(sp_df) > 0 else "Unclassified"
        st.markdown(f"#### Update Status & Diet for {se_com}")
        st.caption(f"Current status: **{current_status}** · Current diet: **{current_diet}**")

        has_token = False
        try:
            _gh_token = st.secrets["GITHUB_TOKEN"]
            has_token = bool(_gh_token)
        except (KeyError, FileNotFoundError):
            pass

        if not has_token:
            st.info(
                "To update species status, configure a `GITHUB_TOKEN` secret "
                "with Contents write permission on the repo."
            )
        else:
            SE_STATUSES = [
                "Resident", "Summer visitor", "Winter visitor",
                "Passage migrant", "Scarce visitor", "Rare vagrant",
                "Introduced species", "Reintroduced", "Extinct", "False Positive", "Other",
            ]
            SE_DIETS = ["Insectivore", "Granivore", "Omnivore", "Frugivore",
                        "Carnivore", "Piscivore", "Herbivore"]
            default_status_idx = SE_STATUSES.index(current_status) if current_status in SE_STATUSES else 0
            default_diet_idx = SE_DIETS.index(current_diet) if current_diet in SE_DIETS else 0

            with st.form("se_update_status"):
                se_new_status = st.selectbox("Assign status", SE_STATUSES, index=default_status_idx, key="se_new_status")
                se_new_diet = st.selectbox("Assign diet", SE_DIETS, index=default_diet_idx, key="se_new_diet")
                se_submitted = st.form_submit_button("Save & push to GitHub")

            if se_submitted:
                # ── Save diet to local JSON ──
                diet_changed = se_new_diet != current_diet
                if diet_changed:
                    diet_data = load_diet_map()
                    diet_data[se_sci] = se_new_diet
                    with open("species_diet.json", "w") as f:
                        json.dump(diet_data, f, indent=2, sort_keys=True)

                # ── Save status to Excel & push to GitHub ──
                EXCEL_PATH = "UK_Birds_Generalized_Status.xlsx"
                REPO = "emjgood1995/bird-dashboard"
                TOKEN = st.secrets["GITHUB_TOKEN"]

                wb = openpyxl.load_workbook(EXCEL_PATH)
                ws = wb.active

                # Check if species already exists (match on Latin Name in column B)
                existing_row = None
                for row in ws.iter_rows(min_row=2):
                    if row[1].value == se_sci:
                        existing_row = row
                        break

                if existing_row is not None:
                    existing_row[0].value = se_com
                    existing_row[2].value = se_new_status
                else:
                    ws.append([se_com, se_sci, se_new_status])
                wb.save(EXCEL_PATH)

                api_url = f"https://api.github.com/repos/{REPO}/contents/{EXCEL_PATH}"
                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Accept": "application/vnd.github+json",
                }

                get_resp = requests.get(api_url, headers=headers, timeout=15)
                if get_resp.status_code != 200:
                    st.error(f"GitHub GET failed ({get_resp.status_code}): {get_resp.text}")
                else:
                    sha = get_resp.json()["sha"]
                    file_bytes = pathlib.Path(EXCEL_PATH).read_bytes()
                    encoded = base64.b64encode(file_bytes).decode()

                    action = "Update" if existing_row is not None else "Add"
                    put_resp = requests.put(
                        api_url,
                        headers=headers,
                        json={
                            "message": f"{action} species status: {se_sci} -> {se_new_status}",
                            "content": encoded,
                            "sha": sha,
                        },
                        timeout=30,
                    )
                    if put_resp.status_code in (200, 201):
                        st.cache_data.clear()
                        parts = [f"Status: *{se_new_status}*"]
                        if diet_changed:
                            parts.append(f"Diet: *{se_new_diet}*")
                        st.success(f"Saved **{se_sci}** — {', '.join(parts)}. Pushed to GitHub.")
                    else:
                        st.error(f"GitHub PUT failed ({put_resp.status_code}): {put_resp.text}")
