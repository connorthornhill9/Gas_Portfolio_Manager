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

# Load flame logo
logo_path = "C:/Users/thorn/OneDrive/Pictures/Gasflame2.png"

# Encode logo as base64
logo_base64 = base64.b64encode(open(logo_path, "rb").read()).decode()

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

# ========== CONFIG ==========
st.set_page_config(page_title="Gas Portfolio Manager", layout="wide")
#st.title("Natural Gas Portfolio Manager")

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FORECAST_PATH = os.path.join(DATA_DIR, "forecast.csv")
DEALS_PATH = os.path.join(DATA_DIR, "deals.csv")
GJ_TO_M3 = 26.853  # hardcoded conversion factor
os.makedirs(DATA_DIR, exist_ok=True)

# ========== LOAD & SAVE FUNCTIONS ==========

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
    if os.path.exists(FORECAST_PATH):
        df = pd.read_csv(FORECAST_PATH)
        df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed").dt.date
        df = df.dropna(subset=["date"])
        df = df.rename(columns=FORECAST_COL_MAP)
        return df
    else:
        return pd.DataFrame(columns=list(FORECAST_COL_MAP.values()))


def save_forecast(df):
    df = df.rename(columns=FORECAST_REVERSE_COL_MAP)
    df.to_csv(FORECAST_PATH, index=False)


def load_deals():
    if os.path.exists(DEALS_PATH):
        df = pd.read_csv(DEALS_PATH)
        df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce").dt.date
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce").dt.date
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        df = df.rename(columns=DEALS_COL_MAP)
        return df
    else:
        return pd.DataFrame(columns=list(DEALS_COL_MAP.values()))


def save_deals(df):
    df = df.rename(columns=DEALS_REVERSE_COL_MAP)
    df.to_csv(DEALS_PATH, index=False)

# ========== SECTION 1.1: Forecast vs. Executed Visualization (Always Visible) ==========

st.markdown("## Forecast vs. Executed Deals")

# Date range selector
fc = load_forecast()
fc["Date"] = pd.to_datetime(fc["Date"]).dt.date
min_date = fc["Date"].min()
max_date = fc["Date"].max()

default_start = min_date
default_end = max_date

start_date, end_date = st.date_input("Select Date Range", value=(default_start, default_end), min_value=min_date, max_value=max_date)
fc = fc[(fc["Date"] >= start_date) & (fc["Date"] <= end_date)]
fc = fc.set_index("Date").sort_index()

# Load and filter deals
dl = load_deals()
if not dl.empty:
    dl["Date"] = pd.to_datetime(dl["Date"]).dt.date
    dl = dl[(dl["Date"] >= start_date) & (dl["Date"] <= end_date)]

    pivot = dl.pivot_table(index="Date", columns="Deal Type", values="Volume (GJ/day)", aggfunc="sum").fillna(0)
    pivot = pivot.sort_index()
    pivot["Total"] = pivot.sum(axis=1)

    combined_index = fc.index.union(pivot.index)
    fc = fc.reindex(combined_index).fillna(0)
    pivot = pivot.reindex(combined_index).fillna(0)

    pivot["Forecast"] = fc["Forecast Consumption"]
    pivot["Long/Short"] = pivot["Total"] - pivot["Forecast"]

    def status_label(val):
        if val < -1e-2:
            return "Short"
        elif val > 1e-2:
            return "Long"
        else:
            return "Balanced"

    position_status = pivot["Long/Short"].apply(status_label)
    forecast_vals = pivot["Forecast"].to_numpy()
    fixed_vals = pivot.get("Fixed", pd.Series(index=pivot.index, data=0)).to_numpy()
    index_vals = pivot.get("Index", pd.Series(index=pivot.index, data=0)).to_numpy()
    customdata = np.stack([position_status, forecast_vals, fixed_vals, index_vals], axis=-1)

    # Summary metrics
    st.markdown("### Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Forecasted", f"{pivot['Forecast'].sum():,.0f} GJ")
    col2.metric("Total Executed", f"{pivot['Total'].sum():,.0f} GJ")
    col3.metric("% Difference", f"{(pivot['Total'].sum() - pivot['Forecast'].sum()) / pivot['Forecast'].sum() * 100:.1f}%")

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Fixed", x=pivot.index, y=fixed_vals, marker_color="#1f77b4"))
    fig.add_trace(go.Bar(name="Index", x=pivot.index, y=index_vals, marker_color="#ff7f0e"))

    for dt, y, pos in zip(pivot.index, forecast_vals, position_status):
        color = (
            "rgba(0,255,0,0.2)" if pos == "Short"
            else "rgba(255,0,0,0.2)" if pos == "Long"
            else "rgba(255,255,0,0.2)"
        )
        fig.add_trace(go.Scatter(
            x=[dt],
            y=[y],
            mode="markers",
            marker=dict(size=20, color=color, symbol="circle"),
            showlegend=False,
            hoverinfo='skip'
        ))

    fig.add_trace(go.Scatter(
        name="Forecasted Consumption",
        x=pivot.index,
        y=forecast_vals,
        mode="lines+markers",
        line=dict(color="white", width=2),
        marker=dict(size=6),
        customdata=customdata,
        hovertemplate=(
            "<b>Position:</b> %{customdata[0]}<br>"
            "Forecasted Consumption: %{customdata[1]:.0f} GJ<br>"
            "Fixed Deal: %{customdata[2]:.0f} GJ<br>"
            "Index Deal: %{customdata[3]:.0f} GJ<br>"
            "<extra></extra>"
        )
    ))

    fig.update_layout(
        barmode="stack",
        xaxis_title="Date",
        yaxis_title="GJ",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No deals to visualize yet.")

# ========== SECTION 1: Forecast Entry ==========

with st.expander("1. Enter or Upload Daily Forecast"):
    forecast_tab, upload_tab = st.tabs(["Manual Entry", "Upload File"])

    # --- Manual Entry Tab ---
    with forecast_tab:
        with st.form("forecast_form"):
            forecast_date = st.date_input("Forecast Date")
            forecast_consumption = st.number_input("Forecast Consumption (GJ)", min_value=0.0)
            submit_forecast = st.form_submit_button("Add Forecast")

        if submit_forecast:
            forecast_df = load_forecast()

            new_row = pd.DataFrame({
                "Date": [forecast_date],
                "Year": [forecast_date.year],
                "Month": [forecast_date.month],
                "Day": [forecast_date.day],
                "Forecast Consumption": [forecast_consumption]
            })

            forecast_df = forecast_df[forecast_df["Date"] != forecast_date]
            forecast_df = pd.concat([forecast_df, new_row], ignore_index=True)
            save_forecast(forecast_df)
            st.success("✅ Forecast added.")
            st.dataframe(new_row)

    # --- Upload Tab ---
    with upload_tab:
        uploaded_file = st.file_uploader("Upload Forecast CSV (columns: Date, Forecast Consumption)", type="csv")

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

                    existing_df = load_forecast()
                    merged = pd.concat([existing_df, uploaded_df], ignore_index=True)
                    merged = merged.drop_duplicates(subset=["Date"], keep="last")

                    save_forecast(merged)
                    st.success("✅ Forecast file uploaded and merged.")
                    st.dataframe(uploaded_df)

            except Exception as e:
                st.error(f"❌ Error processing file: {e}")

# ========== SECTION 2: View or Export Forecast Data ==========

with st.expander("2. View or Export Forecast Data"):
    forecast_df = load_forecast()

    if not forecast_df.empty:
        forecast_df = forecast_df.copy()
        forecast_df["Forecast (m³)"] = forecast_df["Forecast Consumption"] * GJ_TO_M3

        display_unit = st.radio("Select Display Unit:", ["GJ", "m³"], horizontal=True)

        if display_unit == "GJ":
            st.dataframe(forecast_df[["Date", "Forecast Consumption"]].sort_values("Date"))
        else:
            st.dataframe(forecast_df[["Date", "Forecast (m³)"]].sort_values("Date"))

        with open(FORECAST_PATH, "rb") as f:
            st.download_button("📥 Download Forecast CSV", f, file_name="forecast.csv", mime="text/csv")
    else:
        st.info("No forecast data available.")

# ========== SECTION 3: Enter Executed Deal ==========

with st.expander("3. Enter Executed Deal"):
    deals_df = load_deals()

    with st.form("deal_entry_form"):
        deal_start_date = st.date_input("Start Date")
        deal_end_date = st.date_input("End Date")
        deal_type = st.selectbox("Deal Type", ["Fixed", "Index"])
        deal_volume = st.number_input("Volume (GJ/day)", min_value=0.0)
        deal_price = st.number_input("Price ($/GJ)", min_value=0.0)
        deal_supplier = st.selectbox("Supplier", ["Shell", "TD", "Emera", "DirectEnergy", "Other"])
        delivery_point = st.selectbox("Delivery Point", ["AECO", "DAWN", "Parkway"])
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

            deals_df = pd.concat([deals_df, deal_entry], ignore_index=True)
            save_deals(deals_df)
            st.success("✅ Deal added successfully.")

            forecast_df = load_forecast()
            forecast_df["Date"] = pd.to_datetime(forecast_df["Date"]).dt.date
            deals_df["Date"] = pd.to_datetime(deals_df["Date"]).dt.date

            daily_volumes = deals_df.groupby("Date")["Volume (GJ/day)"].sum().reset_index(name="Total Volume")
            daily_volumes["Date"] = pd.to_datetime(daily_volumes["Date"]).dt.date

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

            if over.empty and missing.empty:
                st.success("✅ Deal entry saved with no warnings.")

            st.dataframe(deal_entry)

# ========== SECTION 4: Manage Deals ==========
with st.expander("4. Manage Deals"):
    deals_df = load_deals()

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
                (deals_df["End Date"] == selected_row["End Date"]) &
                (deals_df["Supplier"] == selected_row["Supplier"])
            )
            selected_deals = deals_df[deal_mask]

            with st.form("bulk_edit_form"):
                st.markdown("### Edit Deal")
                new_volume = st.number_input("Volume (GJ/day)", value=selected_deals["Volume (GJ/day)"].iloc[0])
                new_price = st.number_input("Price ($/GJ)", value=selected_deals["Price ($/GJ)"].iloc[0])
                submit_edit = st.form_submit_button("Update Entire Deal")

            if submit_edit:
                deals_df.loc[deal_mask, "Volume (GJ/day)"] = new_volume
                deals_df.loc[deal_mask, "Price ($/GJ)"] = new_price
                save_deals(deals_df)
                st.success("✅ Deal updated successfully.")
                st.dataframe(deals_df[deal_mask])
    else:
        st.info("No deals found.")

# ========== SECTION 6: Weekly Action Plan ==========
with st.expander("6. Weekly Action Plan"):
    st.subheader("Weekly Forecast Coverage and Action Plan")

    forecast_df = load_forecast()
    deals_df = load_deals()

    if not forecast_df.empty:
        forecast_df["Date"] = pd.to_datetime(forecast_df["Date"])
        deals_df["Date"] = pd.to_datetime(deals_df["Date"])

        today = date.today()
        days_since_saturday = (today.weekday() + 2) % 7  # Monday=0, Saturday=5
        most_recent_saturday = today - timedelta(days=days_since_saturday)

        all_saturdays = pd.date_range(
            start=forecast_df["Date"].min(),
            end=forecast_df["Date"].max(),
            freq="W-SAT"
        ).date

        available_weeks = [d for d in all_saturdays if d >= forecast_df["Date"].min().date()]
        if most_recent_saturday not in available_weeks:
            available_weeks.append(most_recent_saturday)
        available_weeks = sorted(set(available_weeks))

        week_start = st.selectbox("Select Gas Week Start (Saturday)", available_weeks, index=available_weeks.index(most_recent_saturday))
        week_end = week_start + timedelta(days=6)

        st.markdown(f"### Showing Action Plan for **{week_start} to {week_end}**")

        forecast_week = forecast_df[
            (forecast_df["Date"] >= pd.to_datetime(week_start)) &
            (forecast_df["Date"] <= pd.to_datetime(week_end))
        ].copy()

        deals_week = deals_df[
            (deals_df["Date"] >= pd.to_datetime(week_start)) &
            (deals_df["Date"] <= pd.to_datetime(week_end))
        ].copy()

        deals_grouped = deals_week.groupby("Date")["Volume (GJ/day)"].sum().reset_index(name="Total Deals")

        merged = pd.merge(forecast_week, deals_grouped, how="left", on="Date")
        merged["Total Deals"] = merged["Total Deals"].fillna(0)
        merged["Action"] = merged["Forecast Consumption"] - merged["Total Deals"]
        merged["Suggestion"] = merged["Action"].apply(
            lambda x: f"Buy {x:.1f} GJ" if x > 0 else (f"Sell {abs(x):.1f} GJ" if x < 0 else "Balanced")
        )

        st.dataframe(merged[["Date", "Forecast Consumption", "Total Deals", "Action", "Suggestion"]])
    else:
        st.info("Upload forecast data first to generate an action plan.")

# ========== END OF APP ==========