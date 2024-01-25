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
        (4, 'Noise mode 4')]

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

@app.route("/malfunction", methods=['GET', 'POST'])
def mal():
    if request.method == 'POST':
        if request.form.get('action1') == 'VALUE1':
            print("test")
            pass # Do something
        elif request.form.get('action2') == 'VALUE2':
            print("test")
            pass # Do something
        else:
            pass # Unknown
    elif request.method == 'GET':
        return render_template('mal.html', data=data, data2=data2)
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
    app_thread = threading.Thread(target=app.run, kwargs={'host': '192.168.2.1', 'port': 5000, 'debug': True})
    app_thread.start()

    # Keep the script running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        client.loop_stop()  # Stop the MQTT loop when you exit
        client.disconnect()
        logger.info("Disconnected from MQTT broker")
