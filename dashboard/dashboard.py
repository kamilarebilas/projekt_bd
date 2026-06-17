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
show_temp_limit = st.sidebar.checkbox("Pokaż linię limitu temperatury", value=False, key="show_temp")

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
        (hourly_df["rain"].isna() | (hourly_df["rain"] <= max_rain))
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

# ── Summary tiles ────────────────────────────────────────────────────────────

col1, col2, col3, col4, col5 = st.columns(5)

current_temp = hourly_df["temperature"].dropna().iloc[-1] if not hourly_df.empty and hourly_df["temperature"].notna().any() else None
max_temp     = hourly_df["temperature"].max() if not hourly_df.empty and hourly_df["temperature"].notna().any() else None
total_rain   = hourly_df["rain"].sum() if not hourly_df.empty and hourly_df["rain"].notna().any() else None
max_wind     = hourly_df["wind_speed"].max() if not hourly_df.empty and hourly_df["wind_speed"].notna().any() else None
avg_aqi      = air_df["aqi"].mean() if not air_df.empty and air_df["aqi"].notna().any() else None

col1.metric("🌡️ Aktualna temp.", f"{current_temp:.1f} °C" if current_temp is not None else "—")
col2.metric("🔥 Maks. temp.",     f"{max_temp:.1f} °C"     if max_temp     is not None else "—")
col3.metric("🌧️ Suma opadów",    f"{total_rain:.1f} mm"   if total_rain   is not None else "—")
col4.metric("💨 Maks. wiatr",     f"{max_wind:.1f} km/h"  if max_wind     is not None else "—")
col5.metric("😷 Średni AQI",      f"{avg_aqi:.0f}"         if avg_aqi      is not None else "—")

st.divider()

if data_type == "Godzinowe":
    st.caption(f"Rekordów: {len(hourly_df)}")
    if hourly_df.empty:
        st.info("Brak danych dla wybranych filtrów.")
    else:
        # Temperature chart with reference lines
        st.subheader("🌡️ Temperatura w czasie (°C)")
        temp_chart = hourly_df[["measurement_time", "temperature"]].dropna().set_index("measurement_time")
        temp_chart.columns = ["Temperatura (°C)"]
        if show_temp_limit:
            temp_chart["Limit max (°C)"] = temp_range[1]
            temp_chart["Limit min (°C)"] = temp_range[0]
        st.line_chart(temp_chart, use_container_width=True)

        # Rain and wind charts side by side
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
            wind_df["Limit (km/h)"] = max_wind
            st.line_chart(wind_df, use_container_width=True)

        # Air quality charts
        if not air_df.empty:
            st.subheader("🌫️ AQI w czasie")
            aqi_chart = air_df[["measurement_time", "aqi"]].dropna().set_index("measurement_time")
            aqi_chart.columns = ["AQI"]
            st.line_chart(aqi_chart, use_container_width=True)

            col3, col4 = st.columns(2)
            with col3:
                st.subheader("🔬 PM2.5 (µg/m³)")
                pm25_chart = air_df[["measurement_time", "pm2_5"]].dropna().set_index("measurement_time")
                pm25_chart.columns = ["PM2.5 (µg/m³)"]
                st.line_chart(pm25_chart, use_container_width=True)
            with col4:
                st.subheader("🔬 PM10 (µg/m³)")
                pm10_chart = air_df[["measurement_time", "pm10"]].dropna().set_index("measurement_time")
                pm10_chart.columns = ["PM10 (µg/m³)"]
                st.line_chart(pm10_chart, use_container_width=True)

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
        # AQI chart
        st.subheader("🌫️ AQI w czasie")
        aqi_chart = air_df[["measurement_time", "aqi"]].dropna().set_index("measurement_time")
        aqi_chart.columns = ["AQI"]
        st.line_chart(aqi_chart, use_container_width=True)

        # PM2.5 and PM10 charts side by side
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔬 PM2.5 (µg/m³)")
            pm25_chart = air_df[["measurement_time", "pm2_5"]].dropna().set_index("measurement_time")
            pm25_chart.columns = ["PM2.5 (µg/m³)"]
            st.line_chart(pm25_chart, use_container_width=True)

        with col2:
            st.subheader("🔬 PM10 (µg/m³)")
            pm10_chart = air_df[["measurement_time", "pm10"]].dropna().set_index("measurement_time")
            pm10_chart.columns = ["PM10 (µg/m³)"]
            st.line_chart(pm10_chart, use_container_width=True)

        st.subheader("📋 Dane jakości powietrza")
        st.dataframe(air_df, use_container_width=True)
