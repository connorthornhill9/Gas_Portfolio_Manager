# generate_sample_data.py
# Creates synthetic forecast.csv and deals.csv for the Streamlit Gas Portfolio Manager.
# Output matches the app's expected CSV schemas.

from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date

# ----------------------------
# CONFIG — tweak as you like
# ----------------------------
# Where to write files (this matches your app expecting app/data/)
OUTPUT_DIR = Path(__file__).resolve().parent / "app" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FORECAST_PATH = OUTPUT_DIR / "forecast.csv"
DEALS_PATH    = OUTPUT_DIR / "deals.csv"

# Time horizon
START_DATE = pd.to_datetime("2021-08-02")         # ~4 years back
HIST_END   = pd.to_datetime("2025-08-01")         # "actuals" end (still stored as Forecast Consumption)
FORE_END   = pd.to_datetime("2025-12-31")         # forward forecast end

# Demand level parameters (GJ/day)
BASELINE_GJ         = 1400.0   # base level
SEASONAL_AMPLITUDE  = 900.0    # winter lift (proxy for HDD)
WEEKLY_RIPPLE       = 80.0     # Mon-Fri vs weekend ripple
DAILY_NOISE_SD      = 60.0     # random noise

# Deals design
ANNUAL_BASELOAD_GJ  = 1000.0
WINTER_BASELOAD_GJ  = 600.0    # Nov–Mar inclusive
ALLOW_NEGATIVE_INDEX = False   # set True to allow sells (negative Index) if fixed > demand

# Prices (rough demo values)
PRICE_ANNUAL = 3.25
PRICE_WINTER = 4.10
PRICE_INDEX_BASE = 3.50  # we can add a small seasonal wiggle to this

# Suppliers / Delivery
DELIVERY_POINT = "DAWN"
SUP_ANNUAL = "Shell"
SUP_WINTER = "TD"
SUP_INDEX  = "Emera"

RANDOM_SEED = 42  # for reproducibility
np.random.seed(RANDOM_SEED)


# ----------------------------
# Helper functions
# ----------------------------
def build_demand_series(start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Synthetic daily demand with winter seasonality + weekly ripple + noise."""
    idx = pd.date_range(start, end, freq="D")
    df = pd.DataFrame(index=idx)
    df["doy"] = df.index.dayofyear

    # Seasonality: peak in Jan. Use cosine so ~max around day 1 (Jan).
    # Shift by ~15 days so the max is mid-Jan-ish.
    df["seasonal"] = np.cos(2 * np.pi * (df["doy"] - 15) / 365.25)

    # Weekly ripple: higher on weekdays, lower on weekends.
    dow = df.index.dayofweek  # Mon=0
    df["weekly"] = np.where(dow < 5, 1.0, -1.0)

    # Noise
    df["noise"] = np.random.normal(0, DAILY_NOISE_SD, size=len(df))

    # Combine
    demand = (
        BASELINE_GJ
        + SEASONAL_AMPLITUDE * (0.5 + 0.5 * df["seasonal"])  # map from [-1,1] to [0,1]
        + WEEKLY_RIPPLE * df["weekly"]
        + df["noise"]
    )

    # Keep demand positive
    demand = np.clip(demand, 200, None)
    demand.index.name = "date"
    return demand.round(1)


def winter_mask(d: pd.Timestamp) -> bool:
    """True if date is within Nov–Mar (winter)."""
    m = d.month
    return (m == 11) or (m == 12) or (m <= 3)


def expand_fixed_daily(start: pd.Timestamp, end: pd.Timestamp, volume: float,
                       deal_type: str, price: float, supplier: str,
                       delivery_point: str) -> pd.DataFrame:
    """Expand a fixed deal to daily rows with required schema."""
    rng = pd.date_range(start, end, freq="D")
    df = pd.DataFrame({
        "date": rng.date,
        "deal_type": deal_type,
        "volume_gj_per_day": volume,
        "price": price,
        "supplier": supplier,
        "delivery_point": delivery_point,
        "start_date": start.date(),
        "end_date": end.date(),
    })
    return df


# ----------------------------
# Generate Forecast (actuals+future)
# ----------------------------
full_idx = pd.date_range(START_DATE, FORE_END, freq="D")
demand = build_demand_series(START_DATE, FORE_END)  # synthetic “actuals/forecast”

forecast_df = pd.DataFrame({
    "date": full_idx.date,
})
# Split into Y/M/D for app convenience
forecast_df["year"] = pd.to_datetime(forecast_df["date"]).dt.year
forecast_df["month"] = pd.to_datetime(forecast_df["date"]).dt.month
forecast_df["day"] = pd.to_datetime(forecast_df["date"]).dt.day
forecast_df["forecast_consumption"] = demand.reindex(full_idx).values.round(0)

forecast_df.to_csv(FORECAST_PATH, index=False)
print(f"✅ Wrote forecast: {FORECAST_PATH} ({len(forecast_df)} rows)")


# ----------------------------
# Generate Deals (daily-expanded)
# Annual baseload (Fixed 1000 GJ) across the entire horizon
# Winter baseload (Fixed 600 GJ) for each winter window (Nov 1 – Mar 31) per season
# Index residual = demand - fixed_total (>=0 unless ALLOW_NEGATIVE_INDEX=True)
# ----------------------------
deals_parts = []

# Annual baseload for the whole period
annual_start = START_DATE
annual_end   = FORE_END
annual_daily = expand_fixed_daily(
    annual_start, annual_end,
    ANNUAL_BASELOAD_GJ, "Fixed", PRICE_ANNUAL, SUP_ANNUAL, DELIVERY_POINT
)
deals_parts.append(annual_daily)

# Winter baseload for each “winter season” (Nov–Mar) within our range
# We handle each winter crossing the year boundary (e.g., Nov 2021–Mar 2022).
years = range(START_DATE.year, FORE_END.year + 1)

for y in years:
    winter_start = pd.Timestamp(year=y, month=11, day=1)
    winter_end   = pd.Timestamp(year=y + 1, month=3, day=31)
    # Clip to our overall range
    ws = max(winter_start, START_DATE)
    we = min(winter_end, FORE_END)
    if ws <= we:
        winter_daily = expand_fixed_daily(
            ws, we,
            WINTER_BASELOAD_GJ, "Fixed", PRICE_WINTER, SUP_WINTER, DELIVERY_POINT
        )
        deals_parts.append(winter_daily)

# Combine fixed to compute residual Index per day
fixed_df = pd.concat(deals_parts, ignore_index=True)
fixed_df["date"] = pd.to_datetime(fixed_df["date"])

# Sum fixed per day
fixed_per_day = (
    fixed_df.groupby("date")["volume_gj_per_day"].sum().reindex(full_idx, fill_value=0.0)
)

# Residual index volume
residual = demand.reindex(full_idx) - fixed_per_day
if not ALLOW_NEGATIVE_INDEX:
    residual = residual.clip(lower=0.0)

# Add a small seasonal wiggle to Index price (optional)
doy = full_idx.dayofyear
index_price = (PRICE_INDEX_BASE + 0.25 * np.sin(2 * np.pi * (doy / 365.25))).round(2)

index_df = pd.DataFrame({
    "date": full_idx.date,
    "deal_type": "Index",
    "volume_gj_per_day": residual.round(0).values,
    "price": index_price,
    "supplier": SUP_INDEX,
    "delivery_point": DELIVERY_POINT,
    "start_date": full_idx.date,   # daily “deal”
    "end_date": full_idx.date,
})

# If you prefer to drop pure-zero index rows to save space:
index_df = index_df[index_df["volume_gj_per_day"] != 0.0].copy()

# Final deals
deals_df = pd.concat([fixed_df, index_df], ignore_index=True)
deals_df["date"] = pd.to_datetime(deals_df["date"]).dt.date

# IMPORTANT: match your app’s expected file schema: lower_snake_case columns
# (They already are in the correct form above.)

deals_df.to_csv(DEALS_PATH, index=False)
print(f"✅ Wrote deals: {DEALS_PATH} ({len(deals_df)} rows)")
