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
        layer = sensor_data["Layer"]
        sensor_id = sensor_data["Sensor"]
        sensor_type = sensor_data["Type"]

        # Check the topic to determine the type of data received
        if msg.topic == topic_pressure:
            expected_voltage = sensor_data["ExpectedVoltage"]
            lowest_voltage = sensor_data["LowestVoltage"]
            calculated_pressure = sensor_data["CalculatedPressure"]

            # Insert data into the pressure table
            cursor.execute("""
            INSERT INTO pressure (sensor_id, mal_code, expected_voltage, 
            lowest_voltage, calculated_pressure, timestamp, level_id) 
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            """, (sensor_id, sensor_type, expected_voltage, lowest_voltage, calculated_pressure, layer))

            logger.info("Pressure sensor data stored in the database")

        elif msg.topic == topic_flow:
            flow_rate = sensor_data["FlowRate"]
            total_liters = sensor_data["TotalLiters"]

            # Insert data into the flow table
            cursor.execute("""
            INSERT INTO flow (sensor_id, mal_code, flow_rate, consump_amount, 
            timestamp, level_id) VALUES (%s, %s, %s, %s, NOW(), %s)
            """, (sensor_id, sensor_type, flow_rate, total_liters, layer))

            logger.info("Flow sensor data stored in the database")

    except (Exception, psycopg2.Error) as e:
        logger.error(f"Error processing the message: {e}")

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
