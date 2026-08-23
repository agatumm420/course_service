"""PostgreSQL connection helpers for the shared Bricks database."""

from __future__ import annotations

import os
from typing import Any, Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
from dotenv import load_dotenv


SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SERVICE_DIR, ".env")

# Always resolve the service's own .env file, regardless of the current
# working directory. Existing process variables keep precedence.
load_dotenv(ENV_FILE, override=False)


def database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    user = os.getenv("POSTGRES_USER", "appuser")
    password = os.getenv("POSTGRES_PASSWORD", "apppass")
    database = os.getenv("POSTGRES_DB", "junkie")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def connect() -> Connection[dict[str, Any]]:
    return psycopg.connect(database_url(), row_factory=dict_row)


def get_db() -> Iterator[Connection[dict[str, Any]]]:
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
