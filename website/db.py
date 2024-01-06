import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database(dbname, user, password):
    conn = psycopg2.connect(
        dbname='postgres',
        user=user,
        password=password,
        host='localhost'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()

    # Check if database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    exists = cur.fetchone()
    if not exists:
        cur.execute(f"CREATE DATABASE {dbname}")
        print(f"Database '{dbname}' created.")
    else:
        print(f"Database '{dbname}' already exists.")

    cur.close()
    conn.close()

create_database("vitenswatersystem", "vitens", "project")
