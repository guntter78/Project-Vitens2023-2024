import psycopg2
import paho.mqtt.client as mqtt
import json
import logging

# MQTT broker settings
broker_address = "192.168.2.1"
broker_port = 1883
topic = "UART"

# Database configuration
db_config = {
    "dbname": "vitenswatersystem",
    "user": "username",
    "password": "password",
    "host": "localhost",
    "port": 5432,
}

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to the PostgreSQL database
try:
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    logger.info("Connected to PostgreSQL database")
except psycopg2.Error as e:
    logger.error(f"Error connecting to the database: {e}")
    exit(1)

# MQTT on_connect event handler
def on_connect(client, userdata, flags, rc):
    logger.info("Connected to MQTT broker")
    client.subscribe(topic)

# MQTT on_message event handler
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        sensor_data = json.loads(payload)
        flow_rate_P = sensor_data.get("F1")
        flow_rate_C = sensor_data.get("F2")
        Consumption_P = sensor_data.get("L1")
        Consumption_C = sensor_data.get("L2")
        Pressure_P = sensor_data.get("P1")
        Pressure_C = sensor_data.get("P2")
        
        # Store the sensor data in the database
        cursor.execute("""
        INSERT INTO pressuresensor (sensor_type, pressure, timestamp, level_id) 
        VALUES (%s, %s, NOW(), 1)
        """, ('P', Pressure_P))
        cursor.execute("""
        INSERT INTO flowsensor (sensor_type, flow_rate ,consumption_amount, 
        timestamp, level_id) VALUES (%s, %s, %s, NOW(), 1)
        """, ('P', flow_rate_P, Consumption_P))
        cursor.execute("""
        INSERT INTO pressuresensor (sensor_type, pressure, timestamp, level_id) 
        VALUES (%s, %s, NOW(), 1)
        """, ('C', Pressure_C))
        cursor.execute("""
        INSERT INTO flowsensor (sensor_type, flow_rate ,consumption_amount, 
        timestamp, level_id) VALUES (%s, %s, %s, NOW(), 1)
        """, ('C', flow_rate_C, Consumption_C))
        
        conn.commit()
        logger.info("Sensor data stored in the database")
    except Exception as e:
        logger.error(f"Error processing the message: {e}")

# Create an MQTT client and set the event handlers
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
try:
    client.connect(broker_address, broker_port, 60)
    logger.info("Connected to MQTT broker")
except Exception as e:
    logger.error(f"Error connecting to MQTT broker: {e}")
    exit(1)

# Start the MQTT client loop
client.loop_forever()
