from machine import Pin, ADC
import utime, time
import config
import network
from umqtt.simple import MQTTClient
import json

# Global variables

pressure_sensors_connected = 1
flow_sensors_connected = 0

is_reading_sensors = False  # True when green button is pressed | False when red button is pressed
interval = 60000  # Interval for measuring sensors
previous_millis = 0  # Variable to measure at certain intervals
button_start_pressed_time = 0
button_end_pressed_time = 0
BUTTON_PRESS_DURATION = 3000  # Duration in milliseconds for button press to be considered valid


# Constants for ADC channels
PRESSURE_CHANNELS = [config.pressure_1, config.pressure_2, config.pressure_3, config.pressure_4, config.pressure_5]

# Constants for Digital channels
FLOW_CHANNELS = [config.flow_1, config.flow_2, config.flow_3, config.flow_4, config.flow_5]

flow_count = [0] * 5  # Counters for flow sensors

# Constants for offsets
OFFSETS = [0.4563809, 0, 0, 0, 0] 

# Variables to keep the lowest voltage measured from each pressure sensor
lowest_voltages = [1] * 5

calibration_factors = [0, 0, 0, 0, 0]  # Calibration factors for flow sensors
total_liters = [0.0] * 5  # Amount of water that went by each flow sensor

# Mode: reversed (x,y = y,x) analysis
# Polynomial degree 9, 17 x,y data pairs.
# Correlation coefficient = 0.9989626481959121
# Standard error = 0.01633840782839662

# Output form: Python function:
# Coefficients for retrieving correct voltage from ADC conversion
PRESSURE_COEFFICIENTS = [
     4.1430779062682901e-002,
     1.1267234164934186e-003,
    -3.3448588314172105e-006,
     6.4945160901450140e-009,
    -6.8647362384291617e-012,
     4.2762572403803007e-015,
    -1.6136004263220210e-018,
     3.6240521930679960e-022,
    -4.4559540640740166e-026,
     2.3084870973993295e-030
]

# WiFi credentials
WIFI_SSID = 'vitens-rpi-ap'
WIFI_PASSWORD = 'vitensproject'

# MQTT broker information
MQTT_BROKER = '192.168.2.1'
MQTT_PORT = 1883
MQTT_TOPIC_FLOW = 'flow_data'
MQTT_TOPIC_PRESSURE = 'pressure_data'

# Initialize WiFi connection
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        # Blink LED while attempting to connect
        for _ in range(10):
            Pin(config.led_pin, Pin.OUT).on()
            utime.sleep_ms(500)
            Pin(config.led_pin, Pin.OUT).off()
            utime.sleep_ms(500)

        while not wlan.isconnected():
            pass

        print('WiFi connected.')
        ip_address = wlan.ifconfig()[0]
        print("IP:", ip_address)
        return wlan

# Initialize MQTT client
def connect_mqtt():
    global led, mqtt_client

    led_blink_interval = 500  # milliseconds

    try:
        mqtt_client = MQTTClient('esp32_2', MQTT_BROKER, port=MQTT_PORT)
        mqtt_client.connect()
        led_blinking = False  # Stop blinking when the connection is established
        led.off()  # Turn off the LED
        return mqtt_client
    except OSError as e:
        if led_blinking:
            # Knipper de LED om aan te geven dat er een verbindingspoging bezig is
            led.value(not led.value())  # Wissel de LED-status om
            utime.sleep_ms(led_blink_interval)
        print(f"MQTT Connection Error: {e}")
        return None
    finally:
        if led_blinking:
            # Zet de LED uit na de verbindingspoging
            led.value(0)

# Publish data to MQTT topics
def publish_mqtt(client, topic, data):
    print (client,topic,data)
    client.publish(topic, data)

# Function to perform multisampling, exclude extreme values, and return the averaged ADC value
def multisample_adc(adc, num_samples=64):
    values = []

    for _ in range(num_samples):
        value = adc.read()
        values.append(value)
        time.sleep_ms(10)  # Add a small delay between readings to reduce noise

    # Exclude top and bottom 5% of values
    values.sort()
    num_excluded = int(num_samples * 0.05)
    trimmed_values = values[num_excluded:-num_excluded]

    averaged_value = sum(trimmed_values) // len(trimmed_values)
    return averaged_value

# Flow sensor interrupt handlers
def flow_sensor_interrupt(pin, sensor_index):
    global flow_count
    flow_count[sensor_index] += 1

# Function to initialize hardware components
def setup():
    global led, adc_sensors, is_reading_sensors, relay

    # Set button pins as inputs with interrupts
    button_start = Pin(config.button_start_pin, Pin.IN, Pin.PULL_UP)
    button_start.irq(trigger=Pin.IRQ_FALLING, handler=button_start_interrupt)

    button_end = Pin(config.button_end_pin, Pin.IN, Pin.PULL_UP)
    button_end.irq(trigger=Pin.IRQ_FALLING, handler=button_end_interrupt)

    # Set up ADC pins for pressure sensors
    adc_sensors = [ADC(Pin(channel)) for channel in PRESSURE_CHANNELS]
    for adc in adc_sensors:
        adc.atten(ADC.ATTN_0DB)
        adc.width(ADC.WIDTH_12BIT)

    # Set up flow sensor pins and interrupt handlers
    for i, flow_pin in enumerate(FLOW_CHANNELS):
        flow_sensor = Pin(flow_pin, Pin.IN)
        flow_sensor.irq(trigger=Pin.IRQ_FALLING, handler=lambda p, idx=i: flow_sensor_interrupt(p, idx))

    # Set LED pin as output
    led = Pin(config.led_pin, Pin.OUT)
    
# Function to handle polynomial regression calculation
def regress(x, coefficients):
    t = 1
    r = 0
    for c in coefficients:
        r += c * t
        t *= x
    return r

# Function to handle interrupt for the start button
def button_start_interrupt(pin):
    global is_reading_sensors, button_start_pressed_time

    if utime.ticks_diff(utime.ticks_ms(), button_start_pressed_time) >= BUTTON_PRESS_DURATION:
        if not is_reading_sensors:
            # Turn on the LED
            led.on()

            # Start reading the sensors
            is_reading_sensors = True
            print("Sensors reading started.")

# Function to handle interrupt for the end button
def button_end_interrupt(pin):
    global is_reading_sensors, button_end_pressed_time

    if utime.ticks_diff(utime.ticks_ms(), button_end_pressed_time) >= BUTTON_PRESS_DURATION:
        if is_reading_sensors:
            # Turn off the LED
            led.off()

            # Stop reading the sensors
            is_reading_sensors = False
            print("Sensors reading stopped.")

# Main function
def main():
    global is_reading_sensors, interval, previous_millis, flow_count, OFFSETS, lowest_voltages, calibration_factors, total_liters, pressure_sensors_connected, flow_sensors_connected

    try:
        # Initialize WiFi connection at the beginning
        wlan = connect_wifi()

        # Attempt to connect to MQTT
        mqtt_client = connect_mqtt()

        if mqtt_client is None:
            print("MQTT connection failed. Measurements will be taken, but data won't be sent to MQTT.")

        print("Main running.")
        while True:
            if is_reading_sensors:
                current_millis = utime.ticks_ms()
                if utime.ticks_diff(current_millis, previous_millis) >= interval:
                    previous_millis = current_millis

                    # Lists to accumulate data for each sensor type
                    sensor_data_array = []

                    # Calculate flow rates and total liters for each flow sensor
                    for i, count in enumerate(flow_count):
                        if (i < flow_sensors_connected):
                            flow_rate = (count / calibration_factors[i]) * (60000 / interval)
                            total_liters[i] += (flow_rate / (60000 / interval))

                            # Append flow sensor data to the array
                            flow_data = {
                                "Sensor": i + 6,
                                "Type": 0,
                                "Layer": 1 if i <= 1 else 0,
                                "FlowRate": round((flow_rate if flow_rate <= flow_count[0] else flow_count[0]),2),
                                "TotalLiters": round(total_liters[i],2)
                            }
                            sensor_data_array.append(flow_data)
                            flow_count[i] = 0  # Reset flow counter for the next interval

                    # Loop through each pressure sensor
                    for i, adc_sensor in enumerate(adc_sensors):
                        if (i < pressure_sensors_connected):
                            # Perform multisampling and calculate voltage value
                            average_adc_value = multisample_adc(adc_sensor)
                            voltage_value = regress(average_adc_value, PRESSURE_COEFFICIENTS)

                            # Update lowest voltage
                            lowest_voltages[i] = min(lowest_voltages[i], voltage_value)

                            # Calculate pressure
                            pressure = ((voltage_value - OFFSETS[i]) * 400 / 100)  # 250 for measuring till 1Mpa | 400 for measurements till 1.6Mpa

                            # Append pressure sensor data to the array
                            pressure_data = {
                                "Sensor": i + 6,
                                "Type": 1,
                                "Layer": 1 if i <= 1 else 0,
                                "ExpectedVoltage": voltage_value,
                                "LowestVoltage": lowest_voltages[i],
                                "CalculatedPressure": round((pressure if pressure >= 0 else 0),2)
                            }
                            sensor_data_array.append(pressure_data)

                        # Print lowest_voltages
                    print(lowest_voltages)

                    # Print accumulated data for each sensor
                    # for sensor_data in sensor_data_array:
                        # print(json.dumps(sensor_data))

                        # Publish sensor data to MQTT if the client is available
                    if mqtt_client:
                        mqtt_data = json.dumps(sensor_data_array)
                        publish_mqtt(mqtt_client, MQTT_TOPIC_PRESSURE, mqtt_data)
                        print("MQTT Message has been send")

                    print(" ")
                        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Sensor readings will continue, but data won't be sent to MQTT.")


# Run the main function if this script is executed directly
if __name__ == "__main__":
    setup()
    main()






