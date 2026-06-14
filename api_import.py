import json 
import time 
from urllib.parse import urlencode 
from urllib.request import urlopen 
from sqlalchemy import text 
from db import get_engine 

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast" 
AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality" 
TIMEZONE = "Europe/Warsaw" 

def fetch_json(url, params): 
    query_string = urlencode(params) 
    full_url = f"{url}?{query_string}" 
    
    with urlopen(full_url, timeout=30) as response: 
        data = response.read().decode("utf-8") 
        return json.loads(data) 
    

def get_locations(engine): 
    query = text(""" SELECT id, city_name, latitude, longitude 
                 FROM locations 
                 ORDER BY id; """) 
    
    with engine.connect() as connection: 
        rows = connection.execute(query).mappings().all() 
        
    return [ 
        { 
            "id": row["id"], 
            "city_name": row["city_name"], 
            "latitude": float(row["latitude"]), 
            "longitude": float(row["longitude"]), 
            } 
            for row in rows 
            ] 
    

def get_value(data, key, index): 
    values = data.get(key) or [] 
    if index >= len(values): 
        return None 
    return values[index]


def import_weather_data(engine, location):
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": TIMEZONE,
        "forecast_days": 3,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "rain",
            "wind_speed_10m",
            "weather_code",
        ]),
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "sunrise",
            "sunset",
        ]),
    }

    data = fetch_json(WEATHER_API_URL, params)
    records_count = 0

    hourly = data.get("hourly", {})
    hourly_times = hourly.get("time", [])

    insert_hourly = text("""
        INSERT INTO weather_hourly (
            location_id,
            measurement_time,
            temperature,
            humidity,
            rain,
            wind_speed,
            weather_code
        )
        VALUES (
            :location_id,
            :measurement_time,
            :temperature,
            :humidity,
            :rain,
            :wind_speed,
            :weather_code
        )
        ON CONFLICT (location_id, measurement_time)
        DO UPDATE SET
            temperature = EXCLUDED.temperature,
            humidity = EXCLUDED.humidity,
            rain = EXCLUDED.rain,
            wind_speed = EXCLUDED.wind_speed,
            weather_code = EXCLUDED.weather_code;
    """)

    with engine.begin() as connection:
        for i, measurement_time in enumerate(hourly_times):
            connection.execute(insert_hourly, {
                "location_id": location["id"],
                "measurement_time": measurement_time,
                "temperature": get_value(hourly, "temperature_2m", i),
                "humidity": get_value(hourly, "relative_humidity_2m", i),
                "rain": get_value(hourly, "rain", i),
                "wind_speed": get_value(hourly, "wind_speed_10m", i),
                "weather_code": get_value(hourly, "weather_code", i),
            })

            records_count += 1

    daily = data.get("daily", {})
    daily_dates = daily.get("time", [])

    insert_daily = text("""
        INSERT INTO weather_daily (
            location_id,
            forecast_date,
            temp_max,
            temp_min,
            sunrise,
            sunset
        )
        VALUES (
            :location_id,
            :forecast_date,
            :temp_max,
            :temp_min,
            :sunrise,
            :sunset
        )
        ON CONFLICT (location_id, forecast_date)
        DO UPDATE SET
            temp_max = EXCLUDED.temp_max,
            temp_min = EXCLUDED.temp_min,
            sunrise = EXCLUDED.sunrise,
            sunset = EXCLUDED.sunset;
    """)

    with engine.begin() as connection:
        for i, forecast_date in enumerate(daily_dates):
            connection.execute(insert_daily, {
                "location_id": location["id"],
                "forecast_date": forecast_date,
                "temp_max": get_value(daily, "temperature_2m_max", i),
                "temp_min": get_value(daily, "temperature_2m_min", i),
                "sunrise": get_value(daily, "sunrise", i),
                "sunset": get_value(daily, "sunset", i),
            })

            records_count += 1

    return records_count