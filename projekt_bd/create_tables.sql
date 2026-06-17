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