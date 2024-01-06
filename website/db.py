import psycopg2

# Connect to the PostgreSQL server
conn = psycopg2.connect(
    host="localhost",
    database="vitens_data",
    user='vitens',
    password='project')

cur = conn.cursor()

# Drop the existing 'data' table if it exists
cur.execute('DROP TABLE IF EXISTS data')

# Create the new database 'vitenswatersystem' if it doesn't exist
cur.execute('CREATE DATABASE IF NOT EXISTS vitenswatersystem')

# Close the connection to the existing database
cur.close()
conn.close()

# Create a new connection to the 'vitenswatersystem' database
conn = psycopg2.connect(
    host="localhost",
    database="vitenswatersystem",
    user='vitens',
    password='project')

cur = conn.cursor()

# Create the new tables 'level', 'flowsensor', and 'pressuresensor'
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
