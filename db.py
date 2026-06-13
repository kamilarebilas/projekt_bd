from sqlalchemy import URL, create_engine

import config


def get_admin_engine():
    base_url = URL.create(
        drivername="postgresql+psycopg2",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database="postgres",
    )

    return create_engine(base_url, isolation_level="AUTOCOMMIT")


def get_engine():
    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
    )

    return create_engine(db_url)