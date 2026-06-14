import json 
import time 
from urllib.parse import urlencode 
from urllib.request import urlopen 
from sqlalchemy import text 
from db import get_engine 
from config import CITY_NAMES

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast" 
AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality" 
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"

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


def fetch_city_coordinates(city_name):
    params = {
        "name": city_name,
        "count": 1,
        "language": "pl",
        "format": "json",
    }

    data = fetch_json(GEOCODING_API_URL, params)
    results = data.get("results", [])

    if not results:
        print(f"Nie znaleziono miasta: {city_name}")
        return None

    city = results[0]

    return {
        "city_name": city.get("name", city_name),
        "latitude": city.get("latitude"),
        "longitude": city.get("longitude"),
    }


def save_location(engine, city_data):
    select_query = text("""
        SELECT id
        FROM locations
        WHERE city_name = :city_name;
    """)

    insert_query = text("""
        INSERT INTO locations (
            city_name,
            latitude,
            longitude
        )
        VALUES (
            :city_name,
            :latitude,
            :longitude
        );
    """)

    update_query = text("""
        UPDATE locations
        SET latitude = :latitude,
            longitude = :longitude
        WHERE id = :id;
    """)

    with engine.begin() as connection:
        existing_location = connection.execute(select_query, {
            "city_name": city_data["city_name"],
        }).mappings().first()

        if existing_location:
            connection.execute(update_query, {
                "id": existing_location["id"],
                "latitude": city_data["latitude"],
                "longitude": city_data["longitude"],
            })
        else:
            connection.execute(insert_query, {
                "city_name": city_data["city_name"],
                "latitude": city_data["latitude"],
                "longitude": city_data["longitude"],
            })


def sync_locations(engine):
    for city_name in CITY_NAMES:
        city_data = fetch_city_coordinates(city_name)

        if city_data is None:
            continue

        save_location(engine, city_data)
        print(f"Zapisano lokalizację: {city_data['city_name']}")


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


def import_air_quality_data(engine, location):
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": TIMEZONE,
        "forecast_days": 3,
        "hourly": ",".join([
            "pm10",
            "pm2_5",
            "european_aqi",
        ]),
    }

    data = fetch_json(AIR_QUALITY_API_URL, params)

    hourly = data.get("hourly", {})
    hourly_times = hourly.get("time", [])

    insert_air_quality = text("""
        INSERT INTO air_quality (
            location_id,
            measurement_time,
            pm10,
            pm2_5,
            aqi
        )
        VALUES (
            :location_id,
            :measurement_time,
            :pm10,
            :pm2_5,
            :aqi
        )
        ON CONFLICT (location_id, measurement_time)
        DO UPDATE SET
            pm10 = EXCLUDED.pm10,
            pm2_5 = EXCLUDED.pm2_5,
            aqi = EXCLUDED.aqi;
    """)

    records_count = 0

    with engine.begin() as connection:
        for i, measurement_time in enumerate(hourly_times):
            connection.execute(insert_air_quality, {
                "location_id": location["id"],
                "measurement_time": measurement_time,
                "pm10": get_value(hourly, "pm10", i),
                "pm2_5": get_value(hourly, "pm2_5", i),
                "aqi": get_value(hourly, "european_aqi", i),
            })

            records_count += 1

    return records_count


def save_import_log(engine, status, records_added, error_message=None):
    query = text("""
        INSERT INTO import_log (
            status,
            records_added,
            error_message
        )
        VALUES (
            :status,
            :records_added,
            :error_message
        );
    """)

    with engine.begin() as connection:
        connection.execute(query, {
            "status": status,
            "records_added": records_added,
            "error_message": error_message,
        })


def run_import():
    engine = get_engine()
    records_added = 0

    try:
        sync_locations(engine)
        locations = get_locations(engine)

        if not locations:
            raise RuntimeError("Brak lokalizacji w tabeli locations.")

        for location in locations:
            print(f"Import danych dla lokalizacji: {location['city_name']}")

            records_added += import_weather_data(engine, location)
            records_added += import_air_quality_data(engine, location)

        save_import_log(
            engine=engine,
            status="SUCCESS",
            records_added=records_added,
        )

        print(f"Import zakończony. Rekordy: {records_added}")

    except Exception as error:
        save_import_log(
            engine=engine,
            status="FAILED",
            records_added=records_added,
            error_message=str(error),
        )

        print(f"Błąd importu: {error}")
        raise