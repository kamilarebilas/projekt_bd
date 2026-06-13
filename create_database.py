import pandas as pd
from sqlalchemy import text
import config
from db import get_admin_engine, get_engine

def create_database():
    
    try:
        sys_engine = get_admin_engine()
        with sys_engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{config.DB_NAME}'"))
            if not result.fetchone():
                conn.execute(text(f"CREATE DATABASE {config.DB_NAME}"))
                print(f"Baza danych '{config.DB_NAME}' została utworzona")
            else:
                print(f"Baza danych '{config.DB_NAME}' już istnieje. Sprawdzanie tabel.")
    except Exception as e:
        print(f"Błąd podczas próby sprawdzenia/tworzenia bazy danych: {e}")
        return
    
    try:
        engine = get_engine()
        
        create_tables_query = text("""
        CREATE TABLE IF NOT EXISTS dict_weather_code (
            weather_code INT PRIMARY KEY,
            description VARCHAR(100) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS locations (
            id SERIAL PRIMARY KEY,
            city_name VARCHAR(100) NOT NULL,
            latitude NUMERIC(5, 2) NOT NULL,
            longitude NUMERIC(5, 2) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS weather_hourly (
            id SERIAL PRIMARY KEY,
            location_id INT NOT NULL,
            measurement_time TIMESTAMP NOT NULL,
            temperature NUMERIC(4, 1),
            humidity INT,
            rain NUMERIC(4, 1),
            wind_speed NUMERIC(4, 1),
            weather_code INT,
            CONSTRAINT fk_location FOREIGN KEY (location_id) REFERENCES locations(id),
            CONSTRAINT fk_weather_code FOREIGN KEY (weather_code) REFERENCES dict_weather_code(weather_code),
            CONSTRAINT unique_location_time UNIQUE (location_id, measurement_time)
        );

        CREATE TABLE IF NOT EXISTS weather_daily (
            id SERIAL PRIMARY KEY,
            location_id INT NOT NULL,
            forecast_date DATE NOT NULL,
            temp_max NUMERIC(4, 1),
            temp_min NUMERIC(4, 1),
            sunrise TIMESTAMP,
            sunset TIMESTAMP,
            CONSTRAINT fk_daily_location FOREIGN KEY (location_id) REFERENCES locations(id),
            CONSTRAINT unique_daily_location_date UNIQUE (location_id, forecast_date)
        );

        CREATE TABLE IF NOT EXISTS air_quality (
            id SERIAL PRIMARY KEY,
            location_id INT NOT NULL,
            measurement_time TIMESTAMP NOT NULL,
            pm10 NUMERIC(4, 1),
            pm2_5 NUMERIC(4, 1),
            aqi INT,
            CONSTRAINT fk_aq_location FOREIGN KEY (location_id) REFERENCES locations(id),
            CONSTRAINT unique_aq_location_time UNIQUE (location_id, measurement_time)
        );

        CREATE TABLE IF NOT EXISTS import_log (
            id SERIAL PRIMARY KEY,
            import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(100) NOT NULL,
            records_added INT, 
            error_message TEXT
        );
        """)

        with engine.connect() as connection:
            print("Pomyślnie nawiązano połączenie z bazą danych.")
            connection.execute(create_tables_query)
            connection.commit()
            print("Wszystkie tabele zostały pomyślnie utworzone")

    except Exception as e:
        print(f"Błąd podczas operacji na bazie danych: {e}")

if __name__ == "__main__":
    create_database()