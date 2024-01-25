import psycopg2
import paho.mqtt.client as mqtt
import json
import logging

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
        (1, 'Incorrect calibration'),
        (2, 'change ambient conditions'),
        (3, 'Electromagnetic interference (EMI)')
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

# MQTT on_connect event handler
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker with result code " + str(rc))
        client.subscribe([(topic_pressure, 0), (topic_flow, 0)])
    else:
        logger.error("Failed to connect, return code %d\n", rc)

# MQTT on_connect event handler
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker with result code " + str(rc))
        client.subscribe([(topic_pressure, 0), (topic_flow, 0)])
    else:
        logger.error("Failed to connect, return code %d\n", rc)

# MQTT on_message event handler
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        sensor_data = json.loads(payload)

        # Extract the sensor data
        level_id = sensor_data["Layer"]
        sensor_id = sensor_data["Sensor"]
        sensor_type = sensor_data["Type"]

        # Set mal_code to 0
        mal_code = 0

        if "Layer" in sensor_data and "Sensor" in sensor_data and "Type" in sensor_data:
            level_id = sensor_data["Layer"]
            sensor_id = sensor_data["Sensor"]
            sensor_type = sensor_data["Type"]
            mal_code = 0    



            # Print the received data
            print("Received data:")
            print(f"Layer: {level_id}")
            print(f"Sensor ID: {sensor_id}")
            print(f"Sensor Type: {sensor_type}")

            # Check the topic to determine the type of data received
            if msg.topic == topic_pressure:
                pressure = sensor_data["CalculatedPressure"]
        
                # Print pressure data
                print(f"Calculated Pressure: {pressure}")

                # Insert data into the pressure table with mal_code set to 0
                # cursor.execute("""
                # INSERT INTO sensor (sensor_id, sensor_type, description, level_id) 
                # VALUES (%s, %s, %s, %s)
                # """, (sensor_id, sensor_type, 'pressuresensor', level_id))

                cursor.execute("""
                INSERT INTO pressure (sensor_id, mal_code, pressure, timestamp) 
                VALUES (%s, %s, %s, NOW())
                """, (sensor_id, mal_code, pressure))

                logger.info("Pressure sensor data stored in the database")

            elif msg.topic == topic_flow:
                flowrate = sensor_data["FlowRate"]
                cons_amount = sensor_data["TotalLiters"]

                # Print flow data
                print(f"Flow Rate: {flowrate}")
                print(f"Total Liters: {cons_amount}")

                # Insert data into the flow table with mal_code set to 0
                # cursor.execute("""
                # INSERT INTO sensor (sensor_id, sensor_type, description, level_id) 
                # VALUES (%s, %s, %s, %s)
                # """, (sensor_id, sensor_type, 'flowsensor',  level_id))

                cursor.execute("""
                INSERT INTO flows (sensor_id, mal_code, flowrate, cons_amount, timestamp) 
                VALUES (%s, %s, %s, %s, NOW())
                """, (sensor_id, mal_code, flowrate, cons_amount))

                logger.info("Flow sensor data stored in the database")
        else:
            logger.error("Ontvangen gegevens ontbreken vereiste sleutels")

    except (json.JSONDecodeError, KeyError, Exception, psycopg2.Error) as e:
        logger.error(f"Error processing the message: {e}")

# Voeg 'level' en 'malfunction' records in
insert_level_and_malfunction_records()

# Create an MQTT client and set the event handlers
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
try:
    client.connect(broker_address, broker_port, 60)
    client.loop_start()  # Start the loop in a non-blocking way
except Exception as e:
    logger.error(f"Error connecting to MQTT broker: {e}")
    exit(1)

# Keep the script running
try:
    while True:
        pass
except KeyboardInterrupt:
    client.disconnect()
    logger.info("Disconnected from MQTT broker")

