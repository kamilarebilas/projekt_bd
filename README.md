# Projekt: Baza danych i dashboard pogodowy — Open-Meteo

Projekt polega na automatycznym pobieraniu danych pogodowych i jakości powietrza z Open-Meteo API, zapisywaniu ich w bazie danych PostgreSQL oraz wizualizacji na interaktywnym dashboardzie Streamlit.

---



---

## Technologie

- **Python 3.13**
- **PostgreSQL 18**
- **SQLAlchemy** — połączenie z bazą danych
- **psycopg2** — sterownik PostgreSQL dla Pythona
- **pandas** — przetwarzanie danych
- **Streamlit** — dashboard i wizualizacje
- **Open-Meteo API** — darmowe API pogodowe (bez klucza)

---

## Opis API

Projekt korzysta z trzech endpointów Open-Meteo:

| Endpoint | Opis |
|---|---|
| `https://api.open-meteo.com/v1/forecast` | Dane pogodowe godzinowe i dzienne |
| `https://air-quality-api.open-meteo.com/v1/air-quality` | Dane jakości powietrza (AQI, PM2.5, PM10) |
| `https://geocoding-api.open-meteo.com/v1/search` | Geokodowanie nazw miast |

Pobierane dane: temperatura, wilgotność, opady, prędkość wiatru, kod pogody, PM2.5, PM10, AQI.

Lokalizacje: Kraków, Warszawa, Gdańsk, Wrocław, Zakopane, Berlin, Paryż, Londyn, Rzym.

---

## Struktura projektu

```
projekt_bd/
├── config.py               # konfiguracja połączenia z bazą
├── db.py                   # silnik SQLAlchemy
├── create_database.py      # tworzenie bazy i tabel
├── api_import.py           # pobieranie i zapis danych z API
├── main.py                 # punkt wejścia aplikacji
├── queries.py              # zapytania analityczne SQL
├── create_tables.sql       # skrypt SQL tworzący tabele
├── insert_initial_data.sql # skrypt SQL z danymi początkowymi
├── dashboard/
│   └── dashboard.py        # dashboard Streamlit
└── README.md
```

---

## Konfiguracja

Przed uruchomieniem otwórz `config.py` i ustaw dane połączenia z bazą:

```python
DB_USER     = "postgres"
DB_PASSWORD = "twoje_haslo"
DB_HOST     = "localhost"
DB_PORT     = 5432
DB_NAME     = "open_meteo_project"
```

---

## Instalacja zależności

Projekt używa **uv** do zarządzania zależnościami. Aby zainstalować wszystkie biblioteki:

```bash
uv sync
```

---

## Uruchomienie importu danych

**Import jednorazowy:**
```bash
python main.py --once
```

**Import cykliczny (co 60 minut):**
```bash
python main.py
```

**Import cykliczny z własnym interwałem (np. co 30 minut):**
```bash
python main.py --interval 30
```

Przy pierwszym uruchomieniu skrypt automatycznie tworzy bazę danych i wszystkie tabele.

---

## Uruchomienie dashboardu

```bash
streamlit run dashboard/dashboard.py
```

Dashboard otworzy się w przeglądarce pod adresem `http://localhost:8501`.

---

## Funkcje dashboardu

- Filtrowanie danych po lokalizacji, zakresie dat, godzinach, temperaturze, opadach, wietrze, kodzie pogody, AQI, PM2.5, PM10
- Wykres temperatury godzinowej z opcjonalnymi liniami limitów
- Wykresy opadów i prędkości wiatru
- Wykresy jakości powietrza: AQI, PM2.5, PM10
- Kafelki podsumowujące: aktualna temp., maks. temp., suma opadów, maks. wiatr, średni AQI
- Tabele z surowymi danymi
