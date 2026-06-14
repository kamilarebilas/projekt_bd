import argparse

from api_import import run_import, run_scheduler


def main():
    parser = argparse.ArgumentParser(
        description="Import danych z Open-Meteo API do bazy PostgreSQL."
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Uruchamia import jeden raz."
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Określa interwał w minutach między kolejnymi importami (domyślnie: 60 minut)."
    )

    args = parser.parse_args()

    if args.once:
        run_import()
    else:
        run_scheduler(interval_minutes=args.interval)


if __name__ == "__main__":
    main()