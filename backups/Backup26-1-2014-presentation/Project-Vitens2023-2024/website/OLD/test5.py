from flask import Flask, render_template
import psycopg2
from decimal import Decimal
from datetime import datetime
import paho.mqtt.client as mqtt
import json
import logging

app = Flask(__name__)

# MQTT broker settings
broker_address = "192.168.2.1"
broker_port = 1883
topic_pressure = "pressure_data"
topic_flow = "flow_data"

# Database configuration
db_config = {
    "dbname": "vitenswatersystem",
    "user": "vitens",
    "password": "project",
    "host": "localhost",
    "port": 5432,
}

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to the PostgreSQL database
try:
    conn = psycopg2.connect(**db_config)
    conn.autocommit = True
    cursor = conn.cursor()
    logger.info("Connected to PostgreSQL database")
except psycopg2.Error as e:
    logger.error(f"Error connecting to the database: {e}")
    exit(1)

# Invoegfunctie voor 'level' en 'malfunction' records
def insert_level_and_malfunction_records():
    # Invoegen van 'level' records
    try:
        print("insert level ID")
        cursor.execute("""
        INSERT INTO level (level_id, description) 
        VALUES (0, 'Layer 0') 
        ON CONFLICT (level_id) DO NOTHING
        """)
        cursor.execute("""
        INSERT INTO level (level_id, description) 
        VALUES (1, 'Layer 1') 
        ON CONFLICT (level_id) DO NOTHING
        """)

    except psycopg2.Error as e:
        logger.error(f"Fout bij het invoegen van 'level' records: {e}")

    # Invoegen van 'malfunction' records
    malfunction_entries = [
        (0, 'no malfunction'),
        (1, 'Noise mode 1'),
        (2, 'Noise mode 2'),
        (3, 'Noise mode 3'),
        (4, 'Noise mode 4')
    ]
    try:
        for mal_code, description in malfunction_entries:
            print("insert malfunction")
            cursor.execute("""
                INSERT INTO malfunction (mal_code, description) 
                VALUES (%s, %s) 
                ON CONFLICT (mal_code) DO NOTHING
            """, (mal_code, description))
    except psycopg2.Error as e:
        logger.error(f"Fout bij het invoegen van 'malfunction' records: {e}")


# input_data: sensor data to add noise to
# noise_lelel: a value corresponding to % noise. For example: 0.2 is +- 20% noise, centered around 1.0 (for noise mode 1. For the others it's just a modifier and does not correspond to anyhting in particular.)
# noise_mode: 0 - no malfunctioning. 1: default noise, centered around 1.
noise_level = 0 
def create_noise(input_data, noise_level, noise_mode):
    import random

    rand = random.random()

    if noise_mode == 0:
        rand = 1

    elif noise_mode == 1:
        rand = rand / (1 / (2 * noise_level)) + (1 - noise_level)

    elif noise_mode == 2:
        rand = rand + (1 / (2 * noise_level)) + (1 - noise_level)

    elif noise_mode == 3:
        rand = rand / (1 / (2 * noise_level)) + (1 - noise_level)

    else:
        rand / (1 % (2 * noise_level)) + (1 - noise_level)


    return input_data * rand

# fetch config data from table config
def fetch_conf_data():
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("SELECT sensor_id, mal_code, value FROM config")
        data = cursor.fetchall()
        
        return data
        
    except psycopg2.Error as e:
        print(f"Fout bij het ophalen van gegevens uit de 'conf' tabel: {e}")
    finally:
        cursor.close()
        conn.close()

# Populate 
# Populate 
def populate_conf_table():
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()

        # Controleer het aantal bestaande records in de config-tabel
        cursor.execute("SELECT COUNT(*) FROM config")
        existing_count = cursor.fetchone()[0]

        # Als er nog geen records zijn, voeg dan 11 records toe met mal_code 0 en value 0
        if existing_count == 0:
            for sensor_id in range(1, 12):
                cursor.execute("""
                    INSERT INTO config (sensor_id, mal_code, value)
                    VALUES (%s, %s, %s)
                """, (sensor_id, 0, 0))
            print("11 records met mal_code 0 en value 0 zijn toegevoegd aan de 'config' tabel.")

    except psycopg2.Error as e:
        print(f"Fout bij het bijwerken van de conf tabel: {e}")
    finally:
        cursor.close()
        conn.close()

# MQTT on_connect event handler
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        # Subscribe to the MQTT topics when connected
        client.subscribe(topic_pressure)
        client.subscribe(topic_flow)
    else:
        logger.error(f"Connection to MQTT broker failed with error code {rc}")

# MQTT on_message event handler
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        sensor_data_array = json.loads(payload)
        print()
        if isinstance(sensor_data_array, list):
            # Iterate through each sensor data in the array
            for sensor_data in sensor_data_array:
                if isinstance(sensor_data, dict):
                    # Extract the sensor data
                    level_id = sensor_data.get("Layer")
                    sensor_id = sensor_data.get("Sensor")
                    sensor_type = sensor_data.get("Type")

                    # Set mal_code to 0
                    mal_code = 0

                    if all(key in sensor_data for key in ("Layer", "Sensor", "Type")):
                        # Print the received data
                        print("Received data:")
                        print(f"Layer: {level_id}")
                        print(f"Sensor ID: {sensor_id}")
                        print(f"Sensor Type: {sensor_type}")

                        # Check the sensor type to determine the type of data received
                        if sensor_type == 0:  # Flow sensor
                            flow_rate = sensor_data.get("FlowRate")
                            cons_amount = sensor_data.get("TotalLiters")

                            # Insert data into the flow table with mal_code set to 0
                            #cursor.execute("""
                            #INSERT INTO sensor (sensor_id, sensor_type, description, level_id) 
                            #VALUES (%s, %s, %s, %s)
                            #""", (sensor_id, sensor_type, 'flowsensor',  level_id))


                            # Fetch the 'value' from the 'conf' table based on 'sensor_id'
                            cursor.execute("SELECT value FROM config WHERE sensor_id = %s", (sensor_id,))
                            conf_value = cursor.fetchone()[0]  # Assuming you expect one result
                            input_data = flow_rate
                            noise_mode = conf_value  # Use the 'value' from 'conf' as noise_mode            
                            flow_rate = create_noise(input_data, noise_level, noise_mode)
                            
                            # Print flow data
                            print(f"Flow Rate: {flow_rate}")
                            print(f"Total Liters: {cons_amount}")

                            # Insert data into the flow table with mal_code set to 0
                            cursor.execute("""
                                INSERT INTO flows (sensor_id, mal_code, flowrate, cons_amount, timestamp) 
                                VALUES (%s, %s, %s, %s, NOW())
                            """, (sensor_id, mal_code, flow_rate, cons_amount))

                            logger.info("Flow sensor data stored in the database")

                        elif sensor_type == 1:  # Pressure sensor
                            pressure = sensor_data.get("CalculatedPressure")

                            # Insert data into the pressure table with mal_code set to 0
                            #cursor.execute("""
                            #INSERT INTO sensor (sensor_id, sensor_type, description, level_id) 
                            #VALUES (%s, %s, %s, %s)
                            #""", (sensor_id, sensor_type, 'pressuresensor', level_id)) 

                            # Fetch the 'value' from the 'conf' table based on 'sensor_id'
                            cursor.execute("SELECT value FROM config WHERE sensor_id = %s", (sensor_id,))
                            conf_value = cursor.fetchone()[0]  # Assuming you expect one result
                            input_data = pressure
                            noise_mode = conf_value  # Use the 'value' from 'conf' as noise_mode            
                            pressure = create_noise(input_data, noise_level, noise_mode)                           
                            # Print pressure data
                            print(f"Calculated Pressure: {pressure}")

                            # Insert data into the pressure table with mal_code set to 0
                            cursor.execute("""
                                INSERT INTO pressure (sensor_id, mal_code, pressure, timestamp) 
                                VALUES (%s, %s, %s, NOW())
                            """, (sensor_id, mal_code, pressure))

                            logger.info("Pressure sensor data stored in the database")

                    else:
                        logger.error("Received data is missing required keys")

                else:
                    logger.error("Invalid sensor data format")

    except (json.JSONDecodeError, Exception, psycopg2.Error) as e:
        logger.error(f"Error processing the message: {e}")

# Flask routes and functions
@app.route('/')
def index():
    def create_connection():
        try:
            # Verbinding maken met de PostgreSQL-database 'vitenswatersystem'
            conn = psycopg2.connect(
                host="localhost",
                database="vitenswatersystem",
                user='vitens',
                password='project')
            return conn
        except Exception as e:
            print(f"Fout bij het verbinden met de database: {str(e)}")
            return None

    def fetch_data():
        conn = create_connection()
        if conn:
            try:
                cur = conn.cursor()
                # Voorbeeldquery om gegevens op te halen uit de 'flowsensor'-tabel
                cur.execute("SELECT * FROM flows")
                data = cur.fetchall()
                return data
            except Exception as e:
                print(f"Fout bij het ophalen van gegevens: {str(e)}")
            finally:
                cur.close()
                conn.close()
        return None

    sensor_data = fetch_data()
    # Convert Decimal and datetime objects to native Python types for better rendering in the template
    formatted_data = [
        {'id': row[0], 'sensor_id': row[1], 'mal_code': row[2], 'flowrate': float(row[3]),
         'cons_amount': float(row[4]), 'timestamp': row[5].strftime('%Y-%m-%d %H:%M:%S')}
        for row in sensor_data
    ]
    return render_template('index.html', sensor_data=formatted_data)

@app.route('/malfunction')
def mal():
    def sensor():
        conn = create_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM sensor")
                data = cur.fetchall()
                print(data)
                return data
            except Exception as e:
                print(f"Fout bij het ophalen van gegevens: {str(e)}")
            finally:
                cur.close()
                conn.close()
        return None

    def mal_func():
        conn = create_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM malfunction")
                data = cur.fetchall()
                print(data)
                return data
            except Exception as e:
                print(f"Fout bij het ophalen van gegevens: {str(e)}")
            finally:
                cur.close()
                conn.close()
        return None

    data = sensor()
    data2 = mal_func()
    return render_template('mal.html', data=data, data2=data2)

if __name__ == '__main__':
    # Voeg 'level' en 'malfunction' records in
    insert_level_and_malfunction_records()
    populate_conf_table()
    # Create an MQTT client and set the event handlers
    client = mqtt.Client()

    # Add a custom on_message handler to print the received data
    def custom_on_message(client, userdata, msg):
        payload = msg.payload.decode()
        print(f"Received MQTT message: {payload}")  # Print the entire received data
        on_message(client, userdata, msg)  # Call the original on_message function

    client.on_connect = on_connect
    client.on_message = custom_on_message  # Use the custom on_message handler

    # Connect to the MQTT broker
    try:
        client.connect(broker_address, broker_port, 60)
        client.loop_start()  # Start the MQTT loop in a separate thread
    except Exception as e:
        logger.error(f"Error connecting to MQTT broker: {e}")
        exit(1)

    # Start the Flask app in a separate thread
    import threading
    app_thread = threading.Thread(target=app.run, kwargs={'host': '192.168.2.1', 'port': 5000, 'debug': False})
    app_thread.start()

    # Keep the script running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        client.loop_stop()  # Stop the MQTT loop when you exit
        client.disconnect()
        logger.info("Disconnected from MQTT broker")
