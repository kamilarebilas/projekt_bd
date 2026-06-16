"""
KONFIGURACJA POŁĄCZENIA Z BAZĄ DANYCH POSTGRESQL

Przed uruchomieniem projektu należy dostosować poniższe wartości 
do lokalnej konfiguracji serwera PostgreSQL, na którym ma powstać baza danych.
"""

DB_USER = "postgres"
DB_PASSWORD = "haslo"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "open_meteo_project"

CITY_NAMES = [
    "Kraków",
    "Warszawa",
    "Gdańsk",
    "Wrocław",
    "Zakopane",
    "Berlin",
    "Paryż",
    "Londyn",
    "Rzym",
]