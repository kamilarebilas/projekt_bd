import pandas as pd
from sqlalchemy import URL, create_engine, text
import config

def create_database():

    base_url = URL.create(
        drivername="postgresql+psycopg2",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database="postgres"
    )
    
    try:
        sys_engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
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
    
    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
    )

    try:
        engine = create_engine(db_url)
        
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

        insert_initial_data_query = text("""
        INSERT INTO locations (id, city_name, latitude, longitude) 
        VALUES (1, 'Kraków', 50.06, 19.94)
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO dict_weather_code (weather_code, description) 
        VALUES
            (0, 'Czyste niebo'),
            (1, 'Przeważnie czyste niebo'),
            (2, 'Częściowe zachmurzenie'),
            (3, 'Zachmurzenie całkowite'),
            (45, 'Mgła'),
            (48, 'Osadzająca się mgła szronowa'),
            (51, 'Mżawka: lekka'),
            (53, 'Mżawka: umiarkowana'),
            (55, 'Mżawka: intensywna'),
            (56, 'Marznąca mżawka: lekka'),
            (57, 'Marznąca mżawka: intensywna'),
            (61, 'Deszcz: słaby'),
            (63, 'Deszcz: umiarkowany'),
            (65, 'Deszcz: silny'),
            (66, 'Marznący deszcz: lekki'),
            (67, 'Marznący deszcz: silny'),
            (71, 'Opady śniegu: słabe'),
            (73, 'Opady śniegu: umiarkowane'),
            (75, 'Opady śniegu: silne'),
            (77, 'Ziarna śniegu'),
            (80, 'Przelatujący deszcz: słaby'),
            (81, 'Przelatujący deszcz: umiarkowany'),
            (82, 'Przelatujący deszcz: gwałtowny'),
            (85, 'Przelatujący śnieg: słaby'),
            (86, 'Przelatujący śnieg: silny'),
            (95, 'Burza: lekka lub umiarkowana'),
            (96, 'Burza z gradem: lekka'),
            (99, 'Burza z gradem: ciężka')
        ON CONFLICT (weather_code) DO NOTHING;
        """)

        with engine.connect() as connection:
            print("Pomyślnie nawiązano połączenie z bazą danych.")
            connection.execute(create_tables_query)
            connection.commit()
            print("Wszystkie tabele zostały pomyślnie utworzone")
            connection.execute(insert_initial_data_query)
            connection.commit()
            print("Dane startowe zostały pomyślnie dodane")

    except Exception as e:
        print(f"Błąd podczas operacji na bazie danych: {e}")

if __name__ == "__main__":
    create_database()