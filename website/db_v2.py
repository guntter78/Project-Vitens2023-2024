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

    # Drop the existing tables if they exist
    cur.execute('DROP TABLE IF EXISTS flows CASCADE')
    cur.execute('DROP TABLE IF EXISTS pressure CASCADE')
    cur.execute('DROP TABLE IF EXISTS sensor CASCADE')
    cur.execute('DROP TABLE IF EXISTS level CASCADE')

    # Create tables 'level', 'sensor', 'flows', and 'pressure'
    cur.execute('''
        CREATE TABLE level (
            level_id VARCHAR(20) PRIMARY KEY,
            description VARCHAR(255)
        )
    ''')

    cur.execute('''
        CREATE TABLE sensor (
            sensor_id SERIAL PRIMARY KEY,
            sensor_type VARCHAR(255),
            description VARCHAR(255),
            level_id VARCHAR(255) REFERENCES level(level_id)
        )
    ''')

    cur.execute('''
        CREATE TABLE flows (
            id SERIAL PRIMARY KEY,
            sensor_id INTEGER REFERENCES sensor(sensor_id),
            flowrate NUMERIC,
            cons_amount NUMERIC,
            timestamp TIMESTAMP
        )
    ''')

    cur.execute('''
        CREATE TABLE pressure (
            id SERIAL PRIMARY KEY,
            sensor_id INTEGER REFERENCES sensor(sensor_id),
            pressure NUMERIC,
            timestamp TIMESTAMP
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