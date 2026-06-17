# -*- coding: utf-8 -*-
import os
os.environ["PGPASSFILE"] = "NUL"

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import config

st.set_page_config(page_title="Dashboard pogodowy – Open-Meteo", page_icon="🌤️", layout="wide")
st.title("🌤️ Dashboard pogodowy – Open-Meteo")

# ── Database connection ──────────────────────────────────────────────────────

@st.cache_resource
def get_engine():
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
    )
    return create_engine(url)

def load_data(query: str, params: dict = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params)

# ── Connection check ─────────────────────────────────────────────────────────

try:
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))
    st.success("✅ Połączono z bazą: " + config.DB_NAME)
except Exception as e:
    st.error(f"❌ Błąd połączenia: {e}")
    st.stop()

# ── Load locations ───────────────────────────────────────────────────────────

locations_df = load_data("SELECT id, city_name FROM locations ORDER BY city_name")
city_names = locations_df["city_name"].tolist()

# ── SIDEBAR ──────────────────────────────────────────────────────────────────

st.sidebar.header("🔍 Filtry")

# Filter 1 — Location
selected_city = st.sidebar.selectbox("1. Lokalizacja", city_names, key="city")
location_id = int(locations_df.loc[locations_df["city_name"] == selected_city, "id"].values[0])

st.sidebar.divider()

# Filter 2 — Data type
data_type = st.sidebar.radio("2. Typ danych", ["Godzinowe", "Dzienne", "Jakość powietrza"], key="data_type")

st.sidebar.divider()

# Filter 3 — Date range
date_row = load_data("SELECT MIN(measurement_time)::date AS d_min, MAX(measurement_time)::date AS d_max FROM weather_hourly")
from datetime import date, timedelta
if not date_row.empty and date_row["d_min"].iloc[0] is not None:
    min_date = date_row["d_min"].iloc[0]
    max_date = date_row["d_max"].iloc[0]
else:
    min_date = date.today()
    max_date = date.today() + timedelta(days=3)

date_range = st.sidebar.date_input("3. Zakres dat", value=(min_date, max_date),
                                    min_value=min_date, max_value=max_date, key="dates")
date_from = date_range[0] if len(date_range) > 0 else min_date
date_to   = date_range[1] if len(date_range) > 1 else max_date

st.sidebar.divider()

# Filter 4 — Hour range
hour_range = st.sidebar.slider("4. Zakres godzin", 0, 23, (0, 23), key="hours")

st.sidebar.divider()

# Filters 5–6 — Temperature
temp_range = st.sidebar.slider("5–6. Temperatura (°C)", -40.0, 50.0, (-40.0, 50.0), step=0.5, key="temp")

st.sidebar.divider()

# Filter 7 — Rain
max_rain = st.sidebar.slider("7. Maks. opad (mm)", 0.0, 200.0, 200.0, step=0.5, key="rain")

st.sidebar.divider()

# Filter 8 — Wind
max_wind = st.sidebar.slider("8. Maks. wiatr (km/h)", 0.0, 200.0, 200.0, step=0.5, key="wind")

st.sidebar.divider()

# Filter 9 — Weather code
weather_codes_df = load_data("SELECT weather_code, description FROM dict_weather_code ORDER BY weather_code")
code_options = ["Wszystkie"] + [
    f"{row['weather_code']} – {row['description']}"
    for _, row in weather_codes_df.iterrows()
]
selected_code_label = st.sidebar.selectbox("9. Kod pogody", code_options, key="wcode")
selected_code = None if selected_code_label == "Wszystkie" else int(selected_code_label.split("–")[0].strip())

st.sidebar.divider()

# Filter 10 — AQI
max_aqi = st.sidebar.slider("10. Maks. AQI", 0, 500, 500, key="aqi")

st.sidebar.divider()

# Filter 11 — PM2.5
max_pm25 = st.sidebar.slider("11. Maks. PM2.5 (µg/m³)", 0.0, 500.0, 500.0, step=0.5, key="pm25")

st.sidebar.divider()

# Filter 12 — PM10
max_pm10 = st.sidebar.slider("12. Maks. PM10 (µg/m³)", 0.0, 500.0, 500.0, step=0.5, key="pm10")

# ── Load data ────────────────────────────────────────────────────────────────

hourly_df = load_data("""
    SELECT measurement_time, temperature, humidity, rain, wind_speed, weather_code
    FROM weather_hourly WHERE location_id = :lid ORDER BY measurement_time
""", {"lid": location_id})

daily_df = load_data("""
    SELECT forecast_date, temp_max, temp_min, sunrise, sunset
    FROM weather_daily WHERE location_id = :lid ORDER BY forecast_date
""", {"lid": location_id})

air_df = load_data("""
    SELECT measurement_time, pm10, pm2_5, aqi
    FROM air_quality WHERE location_id = :lid ORDER BY measurement_time
""", {"lid": location_id})

# ── Apply filters ────────────────────────────────────────────────────────────

if not hourly_df.empty:
    hourly_df["measurement_time"] = pd.to_datetime(hourly_df["measurement_time"])
    hourly_df = hourly_df[
        (hourly_df["measurement_time"].dt.date >= date_from) &
        (hourly_df["measurement_time"].dt.date <= date_to) &
        (hourly_df["measurement_time"].dt.hour >= hour_range[0]) &
        (hourly_df["measurement_time"].dt.hour <= hour_range[1]) &
        (hourly_df["temperature"].isna() | hourly_df["temperature"].between(temp_range[0], temp_range[1])) &
        (hourly_df["rain"].isna() | (hourly_df["rain"] <= max_rain)) &
        (hourly_df["wind_speed"].isna() | (hourly_df["wind_speed"] <= max_wind))
    ]
    if selected_code is not None:
        hourly_df = hourly_df[hourly_df["weather_code"] == selected_code]

if not daily_df.empty:
    daily_df["forecast_date"] = pd.to_datetime(daily_df["forecast_date"]).dt.date
    daily_df = daily_df[(daily_df["forecast_date"] >= date_from) & (daily_df["forecast_date"] <= date_to)]

if not air_df.empty:
    air_df["measurement_time"] = pd.to_datetime(air_df["measurement_time"])
    air_df = air_df[
        (air_df["measurement_time"].dt.date >= date_from) &
        (air_df["measurement_time"].dt.date <= date_to) &
        (air_df["measurement_time"].dt.hour >= hour_range[0]) &
        (air_df["measurement_time"].dt.hour <= hour_range[1]) &
        (air_df["aqi"].isna() | (air_df["aqi"] <= max_aqi)) &
        (air_df["pm2_5"].isna() | (air_df["pm2_5"] <= max_pm25)) &
        (air_df["pm10"].isna() | (air_df["pm10"] <= max_pm10))
    ]

# ── Main content ─────────────────────────────────────────────────────────────

st.subheader(f"📍 {selected_city}")

if data_type == "Godzinowe":
    st.caption(f"Rekordów: {len(hourly_df)}")
    if hourly_df.empty:
        st.info("Brak danych dla wybranych filtrów.")
    else:
        # Temperature chart
        st.subheader("🌡️ Temperatura w czasie (°C)")
        chart_df = hourly_df[["measurement_time", "temperature"]].dropna().set_index("measurement_time")
        chart_df.columns = ["Temperatura (°C)"]
        st.line_chart(chart_df, use_container_width=True)

        # Rain and wind charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🌧️ Opady (mm)")
            rain_df = hourly_df[["measurement_time", "rain"]].dropna().set_index("measurement_time")
            rain_df.columns = ["Opady (mm)"]
            st.bar_chart(rain_df, use_container_width=True)

        with col2:
            st.subheader("💨 Prędkość wiatru (km/h)")
            wind_df = hourly_df[["measurement_time", "wind_speed"]].dropna().set_index("measurement_time")
            wind_df.columns = ["Wiatr (km/h)"]
            st.line_chart(wind_df, use_container_width=True)

        st.subheader("📋 Dane godzinowe")
        st.dataframe(hourly_df, use_container_width=True)

elif data_type == "Dzienne":
    st.caption(f"Rekordów: {len(daily_df)}")
    if daily_df.empty:
        st.info("Brak danych dla wybranych filtrów.")
    else:
        st.subheader("🌡️ Temperatura dzienna (°C)")
        chart_df = daily_df[["forecast_date", "temp_max", "temp_min"]].dropna().set_index("forecast_date")
        chart_df.columns = ["Temp. max (°C)", "Temp. min (°C)"]
        st.line_chart(chart_df, use_container_width=True)
        st.subheader("📋 Prognoza dzienna")
        st.dataframe(daily_df, use_container_width=True)

else:
    st.caption(f"Rekordów: {len(air_df)}")
    if air_df.empty:
        st.info("Brak danych dla wybranych filtrów.")
    else:
        st.dataframe(air_df, use_container_width=True)
