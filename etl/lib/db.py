import os
import time
import psycopg2


def get_connection(retries=20, delay=2):
    last_err = None
    for _ in range(retries):
        try:
            conn = psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "db"),
                port=os.environ.get("POSTGRES_PORT", "5432"),
                dbname=os.environ.get("POSTGRES_DB", "anuario_pa"),
                user=os.environ.get("POSTGRES_USER", "anuario"),
                password=os.environ.get("POSTGRES_PASSWORD", "anuario"),
            )
            conn.autocommit = False
            return conn
        except psycopg2.OperationalError as e:
            last_err = e
            time.sleep(delay)
    raise last_err
