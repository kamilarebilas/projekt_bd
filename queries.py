import pandas as pd
from sqlalchemy import text
from db import get_engine

query_current_weather = text("""
    SELECT 
        l.city_name AS miasto,
        w.measurement_time AS data_godzina,
        w.temperature AS temperatura_c,
        w.humidity AS wilgotnosc_procent,
        w.wind_speed AS wiatr_kmh,
        d.description AS stan_pogody
    FROM weather_hourly w
    JOIN locations l ON w.location_id = l.id
    JOIN dict_weather_code d ON w.weather_code = d.weather_code
    ORDER BY w.measurement_time DESC
    LIMIT 24;
""")

query_daily_forecast = text("""
    SELECT
        l.city_name AS miasto,
        wd.forecast_date AS data_prognozy,
        wd.temp_max AS maksymalna_temperatura,
        wd.temp_min AS minimalna_temperatura,
        wd.sunrise AS wschód_słońca,
        wd.sunset AS zachód_słońca
    FROM weather_daily wd
    JOIN locations l ON wd.location_id = l.id
    ORDER BY wd.forecast_date ASC;
""")

query_weather_alerts = text("""
    SELECT 
        l.city_name AS miasto,
        w.measurement_time AS czas_zdarzenia,
        w.temperature AS temperatura,
        w.wind_speed AS predkosc_wiatru,
        d.description AS zjawisko
    FROM weather_hourly w
    JOIN locations l ON w.location_id = l.id
    JOIN dict_weather_code d ON w.weather_code = d.weather_code
    WHERE w.wind_speed > 25.0 
       OR w.temperature < 0.0 
       OR w.weather_code IN (65, 82, 95, 99)
    ORDER BY w.measurement_time DESC;
""")

query_air_quality_stats = text("""
    SELECT 
        l.city_name AS miasto,
        DATE(a.measurement_time) AS dzien,
        ROUND(AVG(a.pm10), 1) AS srednie_pm10,
        ROUND(AVG(a.pm2_5), 1) AS srednie_pm25,
        MAX(a.aqi) AS najwyzsze_aqi
    FROM air_quality a
    JOIN locations l ON a.location_id = l.id
    GROUP BY l.city_name, DATE(a.measurement_time)
    ORDER BY dzien DESC;
""")

query_system_audit = text("""
    SELECT 
        status,
        COUNT(*) AS liczba_uruchomien,
        SUM(records_added) AS lacznie_pobranych_rekordow
    FROM import_log
    GROUP BY status;
""")

def run_analytical_reports(engine):
    reports = {
        "Raport 1: Aktualny przegląd pogody": query_current_weather,
        "Raport 2: Prognoza dzienna": query_daily_forecast,
        "Raport 3: Alerty i anomalie pogodowe": query_weather_alerts,
        "Raport 4: Średnie dobowe zanieczyszczenie": query_air_quality_stats,
        "Raport 5: Statystyki techniczne systemu": query_system_audit,
    }

    for title, query in reports.items():
        print(title)
        try:
            df = pd.read_sql(query, engine)
            if df.empty:
                print("Brak danych w bazie do wygenerowania tego raportu")
            else:
                print(df)
        except Exception as e:
            print(f"Nie udało się wykonać zapytania: {e}")


if __name__ == "__main__":
    engine = get_engine()
    run_analytical_reports(engine)