import psycopg2

# Function to connect to the database
def connect_to_db():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="vitenswatersystem",
            user="vitens",
            password="project"
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

# Function to insert dummy data with unique IDs
def insert_dummy_data(conn):
    if conn is None:
        return

    try:
        cur = conn.cursor()

        # Original descriptions without replacements
        level_data = [
            ('layer 0',),
            ('layer 1',),
        ]
        cur.executemany("INSERT INTO level (description) VALUES (%s);", level_data)

        # Retrieve level_ids to use for foreign key references
        cur.execute("SELECT level_id FROM level;")
        level_ids = cur.fetchall()

        # Insert dummy data into 'flowsensor' table for layer 0 (2 sensors)
        flowsensor_data_layer0 = [
            ('P', 100.5, 200.5, level_ids[0][0]),
            ('C', 75.3, 150.3, level_ids[0][0]),
        ]
        cur.executemany(
            "INSERT INTO flowsensor (sensor_type, flow_rate, consumption_amount, level_id) VALUES (%s, %s, %s, %s);",
            flowsensor_data_layer0
        )

        # Insert dummy data into 'flowsensor' table for layer 1 (3 sensors)
        flowsensor_data_layer1 = [
            ('P', 110.5, 210.5, level_ids[1][0]),
            ('C', 85.3, 160.3, level_ids[1][0]),
            ('P', 95.5, 180.5, level_ids[1][0]),
        ]
        cur.executemany(
            "INSERT INTO flowsensor (sensor_type, flow_rate, consumption_amount, level_id) VALUES (%s, %s, %s, %s);",
            flowsensor_data_layer1
        )

        # Insert dummy data into 'pressuresensor' table for layer 0 (2 sensors)
        pressuresensor_data_layer0 = [
            ('P', 10.5, level_ids[0][0]),
            ('C', 7.8, level_ids[0][0]),
        ]
        cur.executemany(
            "INSERT INTO pressuresensor (sensor_type, pressure, level_id) VALUES (%s, %s, %s);",
            pressuresensor_data_layer0
        )

        # Insert dummy data into 'pressuresensor' table for layer 1 (2 sensors)
        pressuresensor_data_layer1 = [
            ('P', 8.5, level_ids[1][0]),
            ('C', 6.8, level_ids[1][0]),
        ]
        cur.executemany(
            "INSERT INTO pressuresensor (sensor_type, pressure, level_id) VALUES (%s, %s, %s);",
            pressuresensor_data_layer1
        )

        # Commit changes and close cursor
        conn.commit()
        cur.close()
        print("Dummy data inserted successfully.")
    except psycopg2.Error as e:
        print(f"Error inserting data into the database: {e}")


# Main function to execute the script
def main():
    conn = connect_to_db()
    if conn is not None:
        insert_dummy_data(conn)
        conn.close()

if __name__ == "__main__":
    main()
