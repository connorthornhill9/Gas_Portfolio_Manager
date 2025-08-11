# Natural Gas Portfolio Manager
# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
from datetime import date, timedelta
import os
import base64

st.set_page_config(layout="wide", page_title="Natural Gas Portfolio Manager")

# ========== Helpers ==========

# Mapping for Forecast columns
FORECAST_COL_MAP = {
    "date": "Date",
    "year": "Year",
    "month": "Month",
    "day": "Day",
    "forecast_consumption": "Forecast Consumption"
}
FORECAST_REVERSE_COL_MAP = {v: k for k, v in FORECAST_COL_MAP.items()}

# Mapping for Deals columns
DEALS_COL_MAP = {
    "start_date": "Start Date",
    "end_date": "End Date",
    "deal_type": "Deal Type",
    "volume_gj_per_day": "Volume (GJ/day)",
    "price": "Price ($/GJ)",
    "supplier": "Supplier",
    "delivery_point": "Delivery Point",
    "date": "Date"
}
DEALS_REVERSE_COL_MAP = {v: k for k, v in DEALS_COL_MAP.items()}

def load_forecast():
    try:
        if os.path.exists(FORECAST_PATH):
            df = pd.read_csv(FORECAST_PATH)
            df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed").dt.date
            df = df.dropna(subset=["date"])
            df = df.rename(columns=FORECAST_COL_MAP)
            return df
    except Exception as e:
        st.warning(f"⚠️ Could not load forecast file: {e}")
    return pd.DataFrame(columns=list(FORECAST_COL_MAP.values()))


def save_forecast(df):
    try:
        df = df.rename(columns=FORECAST_REVERSE_COL_MAP)
        df.to_csv(FORECAST_PATH, index=False)
    except Exception:
        st.info("🔒 Forecast not saved (read-only environment).")


def load_deals():
    try:
        if os.path.exists(DEALS_PATH):
            df = pd.read_csv(DEALS_PATH)
            df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce").dt.date
            df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce").dt.date
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
            df = df.rename(columns=DEALS_COL_MAP)
            return df
    except Exception as e:
        st.warning(f"⚠️ Could not load deals file: {e}")
    return pd.DataFrame(columns=list(DEALS_COL_MAP.values()))


def save_deals(df):
    try:
        df = df.rename(columns=DEALS_REVERSE_COL_MAP)
        df.to_csv(DEALS_PATH, index=False)
    except Exception:
        st.info("🔒 Deals not saved (read-only environment).")

def right_aligned_help(label: str, content_md: str):
    c1, c2 = st.columns([1, 0.14])
    with c2:
        try:
            with st.popover(label, use_container_width=True):
                st.markdown(content_md)
        except Exception:
            with st.expander(label, expanded=False):
                st.markdown(content_md)

def _set_viz_range(new_start, new_end):
    """Ensure the chart's date picker (key='viz_range') includes [new_start, new_end]."""
    s, e = st.session_state.get("viz_range", (new_start, new_end))
    if new_start < s:
        s = new_start
    if new_end > e:
        e = new_end
    st.session_state["viz_range"] = (s, e)

def include_dates_and_rerun(new_start, new_end):
    """Expand the visible window to include the new dates and rerun the app."""
    _set_viz_range(new_start, new_end)
    st.rerun()

# ========== Constants ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FORECAST_PATH = os.path.join(DATA_DIR, "forecast.csv")
DEALS_PATH = os.path.join(DATA_DIR, "deals.csv")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
GJ_TO_M3 = 26.853  # hardcoded conversion factor
os.makedirs(DATA_DIR, exist_ok=True)
logo_path = os.path.join(ASSETS_DIR, "Gasflame2.png")

# Encode logo as base64
try:
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
except Exception as e:
    st.warning(f"Logo not found at {logo_path}: {e}")
    logo_base64 = ""

# Demo/persistent toggle (set ALLOW_WRITE=1 in your Streamlit secrets or env if you want to persist)
ALLOW_WRITE = os.environ.get("ALLOW_WRITE", "0") == "1"

# Initialize in-memory working copies from CSVs (first run only)
if "forecast_df" not in st.session_state:
    st.session_state["forecast_df"] = load_forecast()

if "deals_df" not in st.session_state:
    st.session_state["deals_df"] = load_deals()

def get_forecast():
    # Always read from in-memory working copy
    return st.session_state["forecast_df"].copy()

def get_deals():
    return st.session_state["deals_df"].copy()

def set_forecast(df):
    st.session_state["forecast_df"] = df.copy()
    if ALLOW_WRITE:
        save_forecast(df)

def set_deals(df):
    st.session_state["deals_df"] = df.copy()
    if ALLOW_WRITE:
        save_deals(df)

# GitHub and LinkedIn icon URLs (white icons)
github_url = "https://github.com/connorthornhill9"
github_icon = "https://img.icons8.com/ios-glyphs/30/ffffff/github.png"
linkedin_url = "https://www.linkedin.com/in/connor-thornhill-16378316/"
linkedin_icon = "https://img.icons8.com/ios-filled/30/ffffff/linkedin.png"

# Header with centered social icons
st.markdown(f"""
    <style>
        .header-container {{
            background-color: #0e1117;
            padding: 2rem;
            border-radius: 12px;
            border-left: 4px solid #00BFFF;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .header-left {{
            display: flex;
            align-items: center;
        }}
        .header-left img {{
            width: 160px;
            height: 160px;
            margin-right: 1.5rem;
        }}
        .header-left h1 {{
            margin: 0;
            font-size: 3rem;
            color: white;
        }}
        .social-icons {{
            display: flex;
            align-items: center;
            gap: 1.2rem;
        }}
        .social-icons img {{
            transition: transform 0.2s ease, opacity 0.2s ease;
        }}
        .social-icons img:hover {{
            transform: scale(1.15);
            opacity: 0.8;
        }}
    </style>

    <div class="header-container">
        <div class="header-left">
            <img src="data:image/png;base64,{logo_base64}" />
            <h1>Natural Gas Portfolio Manager</h1>
        </div>
        <div class="social-icons">
            <a href="{github_url}" target="_blank"><img src="{github_icon}" width="30" height="30" alt="GitHub" /></a>
            <a href="{linkedin_url}" target="_blank"><img src="{linkedin_icon}" width="30" height="30" alt="LinkedIn" /></a>
        </div>
    </div>
""", unsafe_allow_html=True)

# ================== APP HEADER ==================
with st.container():
    st.markdown(
        """
        <div style="background-color: rgba(255,255,255,0.03); padding: 0.5rem 1rem; border-radius: 8px; margin-top: -10px;">
        """,
        unsafe_allow_html=True
    )

    with st.expander("ℹ️ **How to use this app**", expanded=False):
        st.markdown("""
        **What this app does**
        - Helps Portfolio Managers track positions in their natural gas book.
        - Supports procurement teams in making informed daily nomination decisions.
        
        **Key features**
        - Track daily **Forecasted Consumption** and record **Executed Deals** (Fixed/Index).
        - Visualize coverage vs. forecast and see per-day Buy/Sell guidance.
        - Export forecast data for reporting or further analysis.

        **Quick start**
        1. **Enter/Upload Forecast** – add daily consumption values.
        2. **Enter Deal** – add fixed/index volumes for a date range.
        3. **Chart** – compare forecast vs. executed; filter by date range.
        4. **Weekly Plan** – see per-day Buy/Sell suggestions.

        **Notes**
        - Re-uploading the same dates overwrites values.
        - Deals expand to all days in Start–End range.
        - The app is currently only able to write data when run locally.
                    
        Thank you for checking out the app! Feedback and suggestions are welcome.
        """)
    st.markdown("</div>", unsafe_allow_html=True)


# === THEME: unified font + colors for dark mode ===

# Palette (tweak if you want)
BG        = "#0E1117"  # page bg
PANEL     = "#111827"  # cards/expanders
BORDER    = "#1F2937"
TEXT      = "#E5E7EB"
MUTED     = "#9CA3AF"
ACCENT    = "#22D3EE"  # teal (primary)
ACCENT_2  = "#F97316"  # orange (secondary)
SUCCESS   = "#10B981"
WARN      = "#F59E0B"
DANGER    = "#EF4444"

st.markdown(f"""
<style>
/* ---------- Font ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="st-"], [data-testid="stAppViewContainer"] {{
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif !important;
  color: {TEXT};
}}
.stApp {{
  background: {BG};
}}
/* tighten default margins a hair */
.block-container {{
  padding-top: 0.75rem;
}}

/* ---------- Expanders / Panels ---------- */
div[data-testid="stExpander"] {{
  background: {PANEL};
  border: 1px solid {BORDER};
  border-radius: 12px;
}}
div[data-testid="stExpander"] details {{
  padding: .35rem .6rem 1rem .6rem;
}}
div[data-testid="stExpander"] summary p {{
  font-weight: 600;
  color: {TEXT};
}}

/* ---------- Inputs ---------- */
.stTextInput>div>div>input,
.stNumberInput input,
.stDateInput input,
.stSelectbox > div > div > div,
.stFileUploader > div {{
  background: {BG} !important;
  color: {TEXT} !important;
  border: 1px solid {BORDER} !important;
  border-radius: 10px !important;
}}
/* radio/checkbox labels */
.stRadio label, .stCheckbox label {{
  color: {TEXT} !important;
}}
/* focus ring */
.stTextInput>div>div>input:focus,
.stNumberInput input:focus,
.stDateInput input:focus {{
  outline: 2px solid {ACCENT};
  border-color: {ACCENT} !important;
}}

/* ---------- Buttons ---------- */
.stButton>button {{
  background: {ACCENT};
  color: #061018;
  border: none;
  border-radius: 10px;
  padding: 0.5rem 0.9rem;
  font-weight: 600;
}}
.stButton>button:hover {{
  background: #1BCFE3;
}}
/* Download button variant uses secondary accent */
.stDownloadButton>button {{
  background: {ACCENT_2};
  color: #0B0F14;
  border: none;
  border-radius: 10px;
  padding: 0.5rem 0.9rem;
  font-weight: 600;
}}
.stDownloadButton>button:hover {{
  filter: brightness(1.1);
}}

/* ---------- Metrics ---------- */
[data-testid="stMetricValue"] {{
  color: {TEXT};
  font-weight: 700;
}}
[data-testid="stMetricDelta"] {{
  font-weight: 600;
}}
/* color helpers if you show ups/downs */
.metric-up    {{ color: {SUCCESS} !important; }}
.metric-down  {{ color: {DANGER} !important; }}

/* ---------- Tables / DataFrames ---------- */
.stDataFrame, .stTable {{
  border-radius: 10px;
  overflow: hidden;
}}
.stDataFrame [data-testid="stTable"] thead th {{
  background: {BG} !important;
  color: {MUTED} !important;
  border-bottom: 1px solid {BORDER} !important;
}}
.stDataFrame [data-testid="stTable"] tbody td {{
  color: {TEXT} !important;
  border-color: {BORDER} !important;
}}
/* dataframe toolbar */
[data-testid="stElementToolbar"] button {{
  background: {PANEL};
  color: {TEXT};
}}

/* ---------- Headers inside your custom header ---------- */
.header-container {{
  background-color: {PANEL};
  border-left: 4px solid {ACCENT};
}}
.header-title h1 {{
  color: {TEXT};
}}
/* subtle muted helper text if you show tips */
.muted {{
  color: {MUTED};
}}

/* ---------- Plotly tweaks ---------- */
/* Legend text & axes */
.js-plotly-plot .legendtext, 
.js-plotly-plot .xtick text, 
.js-plotly-plot .ytick text {{
  fill: {TEXT} !important;
}}
</style>
""", unsafe_allow_html=True)

# ========== SECTION 1: Visualization ==========

# Title + inline help
title_col, help_col = st.columns([1, 0.08])
with title_col:
    st.markdown("## Forecast vs. Executed Deals")
with help_col:
    # Small inline tip for this section
    try:
        # Streamlit >= 1.33 has st.popover
        with st.popover("ℹ️", use_container_width=True):
            st.markdown("""
**What you’re seeing**
- **Bars**: daily executed volume (**Fixed + Index**, stacked)
- **Line**: daily **Forecasted Consumption**
- Soft halo color hints **Long / Short / Balanced** per day

**How to use**
- Pick a **date range** to focus the analysis (defaults to the current gas week).
- Tiles show period totals and % difference.
""")
    except Exception:
        # Fallback if popover isn't available
        with st.expander("ℹ️ About this chart", expanded=False):
            st.markdown("""
**Bars**: Fixed + Index (stacked) • **Line**: Forecast  
Soft halos: Long / Short / Balanced by day  
Use the date range to focus the view; tiles sum the selected period.
""")

# ---- Load data ----
fc = get_forecast()
dl = get_deals()

if fc.empty:
    st.info("No forecast data yet.")
else:
    fc["Date"] = pd.to_datetime(fc["Date"]).dt.date
    fc = fc.set_index("Date").sort_index()

    if not dl.empty:
        dl["Date"] = pd.to_datetime(dl["Date"]).dt.date

    # ---- Default date window: Aug 2 → Aug 8 (7 days) ----
    seeded_start = date(2025, 8, 2)
    seeded_end   = seeded_start + timedelta(days=6)

    min_date = fc.index.min()
    max_date = fc.index.max()

    # The picker bounds must at least cover both the data span and the seeded week
    start_bound = min(min_date, seeded_start)
    end_bound   = max(max_date, seeded_end)

    # Initialize or clamp the stored range
    start0, end0 = st.session_state.get("viz_range", (seeded_start, seeded_end))
    start0 = max(start_bound, min(start0, end_bound))
    end0   = max(start0, min(end0, end_bound))  # ensure start0 <= end0 and within bounds
    st.session_state["viz_range"] = (start0, end0)

    # Date picker is bound to session state; helpers can update this and call st.rerun()
    st.date_input(
        "Select Date Range",
        value=st.session_state["viz_range"],
        min_value=start_bound,
        max_value=end_bound,
        format="YYYY/MM/DD",
        key="viz_range",
    )
    start_date, end_date = st.session_state["viz_range"]
    
    # ---- Build daily pivot for deals and align with forecast ----
    if not dl.empty:
        pivot = dl.pivot_table(
            index="Date",
            columns="Deal Type",
            values="Volume (GJ/day)",
            aggfunc="sum"
        ).fillna(0).sort_index()
        pivot["Total"] = pivot.sum(axis=1)
    else:
        # No deals yet; still show forecast line
        pivot = pd.DataFrame(index=fc.index.copy())
        pivot["Fixed"] = 0
        pivot["Index"] = 0
        pivot["Total"] = 0

    combined_index = fc.index.union(pivot.index)
    fc_aligned = fc.reindex(combined_index).fillna(0)
    pv = pivot.reindex(combined_index).fillna(0)

    pv["Forecast"] = fc_aligned["Forecast Consumption"]
    pv["Long/Short"] = pv["Total"] - pv["Forecast"]

    # Filter to selected window
    mask = (pv.index >= start_date) & (pv.index <= end_date)
    pv = pv.loc[mask]

    # ---- Summary metrics ----
    total_forecast = float(pv["Forecast"].sum())
    total_executed = float(pv["Total"].sum())
    pct_diff = (total_executed - total_forecast) / total_forecast * 100 if total_forecast else 0.0

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Forecasted", f"{total_forecast:,.0f} GJ")
    col_b.metric("Total Executed", f"{total_executed:,.0f} GJ")
    col_c.metric("% Difference", f"{pct_diff:,.1f}%")

    # ---- Dark mode palette ----
    COLOR_FIXED   = "#3B82F6"   # blue-500 (muted)
    COLOR_INDEX   = "#F97316"   # orange-400 (muted)
    COLOR_LINE    = "#FFFFFF"   # forecast line
    COLOR_GRID    = "rgba(255,255,255,0.08)"
    COLOR_BG      = "rgba(0,0,0,0)"

    # Status glow colors (softer)
    GLOW_LONG     = "rgba(77,182,172,0.18)"   # soft teal
    GLOW_SHORT    = "rgba(229,115,115,0.20)"  # soft coral
    GLOW_BAL      = "rgba(144,164,174,0.15)"  # blue-grey

    # ---- Precompute arrays ----
    idx_dates     = pv.index
    fixed_vals    = pv.get("Fixed", pd.Series(index=pv.index, data=0)).to_numpy()
    index_vals    = pv.get("Index", pd.Series(index=pv.index, data=0)).to_numpy()
    forecast_vals = pv["Forecast"].to_numpy()

    def status_label(v):
        if v < -1e-2: return "Short"
        if v >  1e-2: return "Long"
        return "Balanced"

    status = pv["Long/Short"].apply(status_label).tolist()
    customdata = np.stack([status, forecast_vals, fixed_vals, index_vals], axis=-1)

    # ---- Plotly figure ----
    fig = go.Figure()

    # Bars (stacked): add a subtle border to increase separation on dark bg
    fig.add_trace(go.Bar(
        name="Fixed", x=idx_dates, y=fixed_vals,
        marker=dict(color=COLOR_FIXED, line=dict(width=0.5, color="rgba(255,255,255,0.2)"))
    ))
    fig.add_trace(go.Bar(
        name="Index", x=idx_dates, y=index_vals,
        marker=dict(color=COLOR_INDEX, line=dict(width=0.5, color="rgba(255,255,255,0.2)"))
    ))

    # Soft “glow” markers behind the forecast line to hint long/short/balanced
    for d, y, s in zip(idx_dates, forecast_vals, status):
        glow = GLOW_LONG if s == "Long" else GLOW_SHORT if s == "Short" else GLOW_BAL
        fig.add_trace(go.Scatter(
            x=[d], y=[y], mode="markers",
            marker=dict(size=18, color=glow, symbol="circle"),
            hoverinfo="skip", showlegend=False
        ))

    # Forecast line
    fig.add_trace(go.Scatter(
        name="Forecasted Consumption",
        x=idx_dates, y=forecast_vals,
        mode="lines+markers",
        line=dict(color=COLOR_LINE, width=2),
        marker=dict(size=6, line=dict(width=1, color="rgba(255,255,255,0.6)")),
        customdata=customdata,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Position: %{customdata[0]}<br>"
            "Forecast: %{customdata[1]:,.0f} GJ<br>"
            "Fixed: %{customdata[2]:,.0f} GJ<br>"
            "Index: %{customdata[3]:,.0f} GJ<br>"
            "<extra></extra>"
        )
    ))

    # Layout: dark-mode friendly grid, spacing, legend
    fig.update_layout(
        barmode="stack",
        xaxis_title="Date",
        yaxis_title="GJ",
        plot_bgcolor=COLOR_BG,
        paper_bgcolor=COLOR_BG,
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=10, b=30),
    )
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_GRID, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLOR_GRID, zeroline=False)

    st.plotly_chart(fig, use_container_width=True)

# ========== SECTION 2: Forecast Entry ==========

with st.expander("1. Enter or Upload Daily Forecast"):
    # ---- Inline Help ----
    right_aligned_help(
        "ℹ️ Help",
        """
**Purpose**
- Add or upload daily **Forecast Consumption (GJ)**.

**Manual Entry**
- Pick a *Forecast Date* and enter GJ.
- Adding the same date **replaces** the previous forecast for that date.

**Upload**
- CSV must contain columns: **`Date`**, **`Forecast Consumption`**.
- Dates are parsed leniently; invalid rows are skipped.
- If a date already exists, the uploaded row **overwrites** it.

**Tip**
- You can re-upload a file as you iterate—data for the same dates will be updated, not duplicated.
        """
    )

    forecast_tab, upload_tab = st.tabs(["Manual Entry", "Upload File"])

    # --- Manual Entry Tab ---
    with forecast_tab:
        with st.form("forecast_form"):
            forecast_date = st.date_input("Forecast Date")
            forecast_consumption = st.number_input("Forecast Consumption (GJ)", min_value=0.0)
            submit_forecast = st.form_submit_button("Add Forecast")

        if submit_forecast:
            forecast_df = get_forecast()  # read from session state

            new_row = pd.DataFrame({
                "Date": [forecast_date],
                "Year": [forecast_date.year],
                "Month": [forecast_date.month],
                "Day": [forecast_date.day],
                "Forecast Consumption": [forecast_consumption]
            })

            # overwrite same-date rows, then append
            forecast_df = forecast_df[forecast_df["Date"] != forecast_date]
            forecast_df = pd.concat([forecast_df, new_row], ignore_index=True)

            set_forecast(forecast_df)  # updates session (+ saves locally if ALLOW_WRITE=1)
            st.success("✅ Forecast added.")
            st.dataframe(new_row)
            include_dates_and_rerun(forecast_date, forecast_date)
            # st.rerun()  # optional: uncomment if you want an immediate refresh

    # --- Upload Tab ---
    with upload_tab:
        uploaded_file = st.file_uploader(
            "Upload Forecast CSV (columns: Date, Forecast Consumption)", type="csv"
        )

        if uploaded_file:
            try:
                uploaded_df = pd.read_csv(uploaded_file)

                if not {"Date", "Forecast Consumption"}.issubset(uploaded_df.columns):
                    st.error("❌ Uploaded file must contain 'Date' and 'Forecast Consumption' columns.")
                else:
                    uploaded_df["Date"] = pd.to_datetime(uploaded_df["Date"], errors="coerce").dt.date
                    uploaded_df = uploaded_df.dropna(subset=["Date"])
                    uploaded_df["Year"] = pd.to_datetime(uploaded_df["Date"]).dt.year
                    uploaded_df["Month"] = pd.to_datetime(uploaded_df["Date"]).dt.month
                    uploaded_df["Day"] = pd.to_datetime(uploaded_df["Date"]).dt.day

                    existing_df = get_forecast()  # session copy
                    merged = pd.concat([existing_df, uploaded_df], ignore_index=True)
                    merged = merged.drop_duplicates(subset=["Date"], keep="last")

                    set_forecast(merged)  # updates session (+ saves locally if ALLOW_WRITE=1)
                    st.success("✅ Forecast file uploaded and merged.")
                    st.dataframe(uploaded_df)
                    include_dates_and_rerun(uploaded_df["Date"].min(), uploaded_df["Date"].max())
                    # st.rerun()  # optional
            except Exception as e:
                st.error(f"❌ Error processing file: {e}")

# ========== SECTION 3: View or Export Forecast Data ==========
with st.expander("2. View or Export Forecast Data"):
    # ---- Inline Help ----
    right_aligned_help(
        "ℹ️ Help",
        """
**Purpose**
- Review your forecast table and **download** a CSV snapshot.

**Tips**
- Toggle between **GJ** and **m³** using the unit selector.
- The table is sorted by `Date`. The download button exports exactly what you see.
        """
    )

    # Use in-memory working copy so session edits are reflected immediately
    forecast_df = get_forecast()

    if not forecast_df.empty:
        # Make a display copy and add m³
        df_view = forecast_df.copy()
        df_view["Forecast (m³)"] = df_view["Forecast Consumption"] * GJ_TO_M3

        # Unit toggle
        display_unit = st.radio("Select Display Unit:", ["GJ", "m³"], horizontal=True)

        if display_unit == "GJ":
            df_to_show = df_view[["Date", "Forecast Consumption"]].sort_values("Date")
        else:
            df_to_show = df_view[["Date", "Forecast (m³)"]].sort_values("Date")

        st.dataframe(df_to_show, use_container_width=True)

        # Download exactly what's shown
        csv_bytes = df_to_show.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download This View (CSV)",
            data=csv_bytes,
            file_name="forecast_view.csv",
            mime="text/csv"
        )
    else:
        st.info("No forecast data available.")

# ========== SECTION 4: Enter Executed Deal ==========
with st.expander("3. Enter Executed Deal"):
    # ---- Inline Help ----
    right_aligned_help(
        "ℹ️ Help",
        """
**Purpose**
- Record **Fixed** or **Index** deals for a date range.

**How it works**
- The **Start/End Date** range expands to **every day** in that range.
- Daily **Volume (GJ/day)** and **Price ($/GJ)** apply uniformly to all days.
- You may enter **negative volumes** to represent sales/offsets.

**Validation**
- End Date must be **on/after** Start Date (you’ll see an error otherwise).

**Where to edit/delete**
- Use **Manage Deals** to update or remove a full deal later.
        """
    )

    deals_df = get_deals()  # <- from session

    with st.form("deal_entry_form"):
        deal_start_date = st.date_input("Start Date")
        deal_end_date = st.date_input("End Date")
        deal_type = st.selectbox("Deal Type", ["Fixed", "Index"])
        # allow negative (sales/offsets) -> no min_value
        deal_volume = st.number_input("Volume (GJ/day)", value=0.0)
        deal_price = st.number_input("Price ($/GJ)", value=0.0)
        deal_supplier = st.selectbox("Supplier", ["Shell", "TD", "Emera", "DirectEnergy", "Other"])
        delivery_point = st.selectbox("Delivery Point", ["DAWN", "Parkway", "AECO", "Other"])
        submit_deal = st.form_submit_button("Add Deal")

    if submit_deal:
        if deal_end_date < deal_start_date:
            st.error("❌ End date cannot be before start date. Please correct the dates.")
        else:
            date_range = pd.date_range(start=deal_start_date, end=deal_end_date)
            deal_entry = pd.DataFrame({
                "Date": date_range.date,
                "Deal Type": deal_type,
                "Volume (GJ/day)": deal_volume,
                "Price ($/GJ)": deal_price,
                "Supplier": deal_supplier,
                "Delivery Point": delivery_point,
                "Start Date": deal_start_date,
                "End Date": deal_end_date
            })

            # update in-memory + (optionally) disk
            new_deals = pd.concat([deals_df, deal_entry], ignore_index=True)
            set_deals(new_deals)

            st.success("✅ Deal added successfully.")
            st.dataframe(deal_entry)

            # --- sanity/coverage checks (using current session data) ---
            forecast_df = get_forecast()
            if not forecast_df.empty:
                forecast_df["Date"] = pd.to_datetime(forecast_df["Date"]).dt.date
                new_deals["Date"]  = pd.to_datetime(new_deals["Date"]).dt.date

                daily_volumes = (
                    new_deals.groupby("Date")["Volume (GJ/day)"]
                    .sum()
                    .reset_index(name="Total Volume")
                )

                forecast_check = pd.merge(daily_volumes, forecast_df, how="left", on="Date")
                forecast_check["Forecast Consumption"] = forecast_check["Forecast Consumption"].fillna(0)
                forecast_check["Remaining"] = forecast_check["Forecast Consumption"] - forecast_check["Total Volume"]

                over = forecast_check[forecast_check["Remaining"] < 0]
                missing = forecast_check[forecast_check["Forecast Consumption"] == 0]

                if not over.empty:
                    st.warning(f"⚠️ Total contracted volume exceeds forecast on {len(over)} day(s).")
                    st.dataframe(over[["Date", "Forecast Consumption", "Total Volume", "Remaining"]])

                if not missing.empty:
                    st.info(f"ℹ️ Forecast data missing for {len(missing)} day(s). These are treated as 0 GJ.")
                    st.dataframe(missing[["Date", "Total Volume"]])
                    include_dates_and_rerun(deal_start_date, deal_end_date)

                if over.empty and missing.empty:
                    st.success("✅ Deal entry saved with no warnings.")
            else:
                st.info("ℹ️ No forecast loaded yet; coverage check skipped.")

# ========== SECTION 5: Manage Deals ==========
with st.expander("4. Manage Deals"):
    # Inline help (right-aligned)
    right_aligned_help(
        "ℹ️ Help",
        """
**Purpose**
- Edit an entire deal group at once (same **Start/End** and **Supplier**).

**How it works**
- Select a deal group, then update **Volume (GJ/day)** and/or **Price ($/GJ)**.
- Changes apply to **every date** in that deal’s range.

**Notes**
- To change Start/End or Supplier, delete and re-add the deal.
        """
    )

    deals_df = get_deals()  # <- from session

    if not deals_df.empty:
        # Create a list of unique deal groups
        deal_groups = (
            deals_df
            .groupby(["Start Date", "End Date", "Supplier"])
            .size()
            .reset_index()
            .rename(columns={0: "Count"})
        )
        deal_groups["Label"] = deal_groups.apply(
            lambda row: f"{row['Supplier']} ({row['Start Date']} to {row['End Date']})", axis=1
        )

        selected_label = st.selectbox("Select a Deal to Edit", ["No Deal"] + deal_groups["Label"].tolist())

        if selected_label != "No Deal":
            selected_row = deal_groups[deal_groups["Label"] == selected_label].iloc[0]
            deal_mask = (
                (deals_df["Start Date"] == selected_row["Start Date"]) &
                (deals_df["End Date"]   == selected_row["End Date"]) &
                (deals_df["Supplier"]   == selected_row["Supplier"])
            )
            selected_deals = deals_df[deal_mask]

            with st.form("bulk_edit_form"):
                st.markdown("### Edit Deal")
                # allow negative updates as well
                new_volume = st.number_input(
                    "Volume (GJ/day)",
                    value=float(selected_deals["Volume (GJ/day)"].iloc[0])
                )
                new_price = st.number_input(
                    "Price ($/GJ)",
                    value=float(selected_deals["Price ($/GJ)"].iloc[0])
                )
                submit_edit = st.form_submit_button("Update Deal")

            if submit_edit:
                updated = deals_df.copy()
                updated.loc[deal_mask, "Volume (GJ/day)"] = new_volume
                updated.loc[deal_mask, "Price ($/GJ)"] = new_price

                # update in-memory + (optionally) disk
                set_deals(updated)

                st.success("✅ Deal updated successfully.")
                st.dataframe(updated[deal_mask])
                st.rerun()
    else:
        st.info("No deals found.")

# ========== SECTION 6: Weekly Action Plan ==========
with st.expander("6. Weekly Action Plan"):
    # ---- Inline Help (right-aligned) ----
    right_aligned_help(
        "ℹ️ Help",
        """
**Purpose**
- Summarize **Forecast vs Executed** by gas week (Sat–Fri) and suggest daily **Buy/Sell**.

**How it works**
- Pick a **Gas Week Start (Saturday)** to see the 7-day window.
- Suggestions = Forecast Consumption − Total Deals (Fixed + Index).
- Positive = **Buy**, Negative = **Sell**, Zero = **Balanced**.
        """
    )

    # Pull the in-memory working copies so edits in this session are reflected immediately
    forecast_df = get_forecast()
    deals_df    = get_deals()

    if forecast_df.empty:
        st.info("Upload or enter forecast data to generate an action plan.")
    else:
        # Ensure datetime
        forecast_df["Date"] = pd.to_datetime(forecast_df["Date"])
        if not deals_df.empty:
            deals_df["Date"] = pd.to_datetime(deals_df["Date"])

        # --- Build list of available gas weeks (Saturday starts) ---
        fc_min = forecast_df["Date"].min().date()
        fc_max = forecast_df["Date"].max().date()

        # Most-recent Saturday relative to *today*
        today = date.today()
        days_since_saturday = (today.weekday() + 2) % 7  # Mon=0,... Sat=5
        most_recent_saturday = today - timedelta(days=days_since_saturday)

        # Saturdays covered by the forecast range
        saturdays = pd.date_range(start=fc_min, end=fc_max, freq="W-SAT").date.tolist()

        # Allow preview of current and next gas week even if not in data yet
        preview = [most_recent_saturday, most_recent_saturday + timedelta(days=7)]
        available_weeks = sorted(set(saturdays + [d for d in preview if d >= fc_min]))

        # Fallback if something odd happens
        default_idx = available_weeks.index(most_recent_saturday) if most_recent_saturday in available_weeks else 0

        week_start = st.selectbox("Select Gas Week Start (Saturday)", available_weeks, index=default_idx)
        week_end   = week_start + timedelta(days=6)
        st.markdown(f"**Week:** {week_start} → {week_end}")

        # --- Filter to week window ---
        mask_fc = (forecast_df["Date"] >= pd.to_datetime(week_start)) & (forecast_df["Date"] <= pd.to_datetime(week_end))
        forecast_week = forecast_df.loc[mask_fc, ["Date", "Forecast Consumption"]].copy()

        if deals_df.empty:
            deals_week = pd.DataFrame(columns=["Date", "Volume (GJ/day)"])
        else:
            mask_dl = (deals_df["Date"] >= pd.to_datetime(week_start)) & (deals_df["Date"] <= pd.to_datetime(week_end))
            deals_week = deals_df.loc[mask_dl, ["Date", "Volume (GJ/day)"]].copy()

        # Aggregate deals and merge
        deals_grouped = (
            deals_week.groupby("Date")["Volume (GJ/day)"].sum().reset_index(name="Total Deals")
            if not deals_week.empty else
            pd.DataFrame({"Date": forecast_week["Date"].unique(), "Total Deals": 0})
        )

        merged = pd.merge(forecast_week, deals_grouped, how="left", on="Date").fillna({"Total Deals": 0})
        merged["Action"] = merged["Forecast Consumption"] - merged["Total Deals"]
        merged["Suggestion"] = merged["Action"].apply(
            lambda x: f"Buy {x:,.1f} GJ" if x > 0 else (f"Sell {abs(x):,.1f} GJ" if x < 0 else "Balanced")
        )

        # Nice little weekly summary up top
        c1, c2, c3 = st.columns(3)
        c1.metric("Weekly Forecast", f"{merged['Forecast Consumption'].sum():,.0f} GJ")
        c2.metric("Weekly Executed", f"{merged['Total Deals'].sum():,.0f} GJ")
        delta = merged["Total Deals"].sum() - merged["Forecast Consumption"].sum()
        c3.metric("Net Position", f"{delta:,.0f} GJ", help="Executed − Forecast over the selected week")

        # Display table
        st.dataframe(
            merged.sort_values("Date")[["Date", "Forecast Consumption", "Total Deals", "Action", "Suggestion"]],
            use_container_width=True
        )
# ========== END OF APP ==========