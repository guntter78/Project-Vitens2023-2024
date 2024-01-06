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

def create_tables():
    conn = psycopg2.connect(
        host="localhost",
        database="vitenswatersystem",
        user="vitens",
        password="project"
    )

    cur = conn.cursor()

    # Drop the existing 'data' table if it exists
    cur.execute('DROP TABLE IF EXISTS data')

    # Create tables 'level', 'flowsensor', and 'pressuresensor'
    cur.execute('''
        CREATE TABLE level (
            level_id SERIAL PRIMARY KEY,
            description VARCHAR(255)
        )
    ''')

    cur.execute('''
        CREATE TABLE flowsensor (
            id SERIAL PRIMARY KEY,
            sensor_type VARCHAR(1),
            flow_rate NUMERIC,
            consumption_amount NUMERIC,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level_id INTEGER REFERENCES level(level_id)
        )
    ''')

    cur.execute('''
        CREATE TABLE pressuresensor (
            id SERIAL PRIMARY KEY,
            sensor_type VARCHAR(1),
            pressure NUMERIC,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level_id INTEGER REFERENCES level(level_id)
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    cur.close()
    conn.close()
    print("Tables created successfully.")


# Start functions
create_database("vitenswatersystem", "vitens", "project")
create_tables()
