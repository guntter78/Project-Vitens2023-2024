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

        level_data = [
            ('0', 'Layer 0'),
            ('1','Layer 1'),
        ]
        cur.executemany("INSERT INTO level (level_id, description) VALUES (%s, %s);", level_data)

       
        # Retrieve level_ids to use for foreign key references
        cur.execute("SELECT level_id FROM level;")
        level_ids = cur.fetchall()


        sensor_data = [
            (1, 'flow', 'this is the most right flow sensor','1'),
            (2, 'pressure', 'this is the most left flow sensor','0'),
        ]
        cur.executemany(
            "INSERT INTO sensor (sensor_id, sensor_type, description, level_id) VALUES (%s, %s %s, %s);",
            sensor_data
        )


        mal_data = [
            (2, 'Range Exceeded'),
            (3, 'constant null')
        ]
        cur.executemany(
            "INSERT INTO malfunction(mal_code, description) VALUES (%s, %s);", mal_data
        )


        flow_data = [
            (1, 2, 2, 100.5, 200.5, '2023-07-15 08:32:45' ),
            (2, 1, 3, 75.3, 150.3, '2023-06-6 03:36:46'),
        ]
        
        cur.executemany(
            "INSERT INTO flows(id, sensor_id, mal_code, flowrate, cons_amount, timestamp) VALUES (%s, %s, %s, %s, %s, %s);", flow_data
        )

        pressure_data = [
            (1, 1, 3, 10.5, '2023-11-12 01:45:23' ),
            (2, 2, 2, 77.8, '2024-02-22 06:46:22'),
        ]
        
        cur.executemany(
            "INSERT INTO pressure(id, sensor_id, mal_code, pressure, timestamp) VALUES (%s, %s, %s, %s, %s);", pressure_data
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