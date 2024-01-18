from machine import Pin, ADC
import utime, time
import config
import network
from umqtt.simple import MQTTClient

# Global variables
is_reading_sensors = False  # True when green button is pressed | False when red button is pressed
interval = 1000  # Interval for measuring sensors
previous_millis = 0  # Variable to measure at certain intervals

# Constants for ADC channels
PRESSURE_CHANNELS = [config.pressure_1, config.pressure_2, config.pressure_3, config.pressure_4, config.pressure_5]

# Constants for Digital channels
FLOW_CHANNELS = [config.flow_1, config.flow_2, config.flow_3, config.flow_4, config.flow_5]

flow_count = [0] * 5  # Counters for flow sensors

# Coefficients for retrieving correct voltage from ADC conversion
PRESSURE_COEFFICIENTS = [
     4.3220814251979441e-002,
     8.4389462175653155e-004,
    -1.5602058901130114e-006,
     2.2509419544953348e-009,
    -1.7566834607660054e-012,
     7.8573137930648812e-016,
    -2.0129813454437095e-019,
     2.7453128579968508e-023,
    -1.5445682269067323e-027
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
    return wlan

# Initialize MQTT client
def connect_mqtt():
    global led
    
    led_blinking = True
    led_blink_interval = 500  # milliseconds

    try:
        client = MQTTClient('esp32', MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        led_blinking = False  # Stop blinking when the connection is established
        return client
    except OSError as e:
        if led_blinking:
            # Blink LED to indicate ongoing connection attempt
            led.value(not led.value())  # Toggle LED state
            utime.sleep_ms(led_blink_interval)
        print(f"MQTT Connection Error: {e}")
        return None
    finally:
        if led_blinking:
            # Turn off LED after the connection attempt
            led.value(0)


# Publish data to MQTT topics
def publish_mqtt(client, topic, data):
    client.publish(topic, data)

# Function to perform multisampling, exclude extreme values, and return the averaged ADC value
def multisample_adc(adc, num_samples=32):
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
    global led, relay, adc_sensors, is_reading_sensors

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
    
    # Blink LED while waiting for WiFi connection
    connect_wifi()
    for _ in range(5):
        led.on()
        utime.sleep_ms(500)
        led.off()
        utime.sleep_ms(500)

    # Set relay pin as output
    relay = Pin(config.relay_pin, Pin.OUT)
    relay.value(1)  # Set relay pin HIGH

# Function to handle polynomial regression calculation
def regress(x, coefficients):
    t = 1
    r = 0
    for c in coefficients:
        r += c * t
        t *= x
    return r

# Interrupt handler for the start button
def button_start_interrupt(pin):
    global is_reading_sensors
    if not is_reading_sensors:
        # Turn on the LED
        led.value(1)

        # Activate the relay
        relay.value(0)

        # Start reading the sensors
        is_reading_sensors = True
        print("Sensors reading started.")

# Interrupt handler for the end button
def button_end_interrupt(pin):
    global is_reading_sensors
    if is_reading_sensors:
        # Turn off the LED
        led.value(0)

        # Deactivate the relay
        relay.value(1)

        # Stop reading the sensors
        is_reading_sensors = False
        print("Sensors reading stopped.")

# Main function
def main():
    global is_reading_sensors, interval, previous_millis, flow_count
    
    wlan = connect_wifi()
    mqtt_client = connect_mqtt()
    
    if mqtt_client is None:
        print("MQTT connection failed. Measurements will be taken, but data won't be sent to MQTT.")

    # Constants for offsets
    OFFSETS = [0.4829402, 0.4843519, 0.4907008, 0.4871744, 0.4762344]

    # Variables to keep the lowest voltage measured from each pressure sensor
    lowest_voltages = [1] * 5

    calibration_factors = [63.3, 63.3, 63.3, 63.3, 63.3]  # Calibration factors for flow sensors
    total_liters = [0.0] * 5  # Amount of water that went by each flow sensor

    print("Main running.")
    while True:
        if is_reading_sensors:
            current_millis = utime.ticks_ms()
            if utime.ticks_diff(current_millis, previous_millis) >= interval:
                previous_millis = current_millis

                # Lists to accumulate data for each sensor
                expected_voltages = []
                lowest_voltages_accumulated = []
                pressures = []

                # Lists to accumulate data for each flow sensor
                flow_rates = []
                total_liters_accumulated = []

                # Calculate flow rates and total liters for each flow sensor
                for i, count in enumerate(flow_count):
                    flow_rate = (count / calibration_factors[i]) * (60000.0 / interval)
                    total_liters[i] += (flow_rate / 60.0)
                    flow_rates.append(flow_rate)
                    total_liters_accumulated.append(total_liters[i])
                    flow_count[i] = 0  # Reset flow counter for the next interval

                # Print accumulated flow data for each flow sensor
                for i, rate in enumerate(flow_rates):
                    print(f"Flow Sensor {i + 1}: Flow Rate: {rate} L/min, Total Liters: {total_liters_accumulated[i]} L")
                    
                    # Publish flow data to MQTT if the client is available
                    if mqtt_client:
                        mqtt_data = f"Flow Sensor {i + 1}: Flow Rate: {rate} L/min, Total Liters: {total_liters_accumulated[i]} L"
                        publish_mqtt(mqtt_client, MQTT_TOPIC_FLOW, mqtt_data)

                    
                print(" ")

                # Loop through each pressure sensor
                for i, adc_sensor in enumerate(adc_sensors):
                    # Perform multisampling and calculate voltage value
                    average_adc_value = multisample_adc(adc_sensor)
#                      print("abg value: ", average_adc_value)
                    voltage_value = regress(average_adc_value, PRESSURE_COEFFICIENTS)

                    # Update lowest voltage
                    lowest_voltages[i] = min(lowest_voltages[i], voltage_value)

                    # Calculate pressure
                    pressure = (voltage_value - OFFSETS[i]) * 400  # 250 for measuring till 1Mpa | 400 for measurements till 1.6Mpa

                    # Accumulate data for pressure sensors
                    expected_voltages.append(voltage_value)
                    lowest_voltages_accumulated.append(lowest_voltages[i])
                    pressures.append(pressure)

                # Print accumulated data for each pressure sensor
                for i in range(len(adc_sensors)):
                    print(f"Pressure Sensor {i + 1}: Expected Voltage: {expected_voltages[i]}, Lowest Voltage: {lowest_voltages_accumulated[i]}, Calculated Pressure: {pressures[i]}")
                    
                    # Publish pressure data to MQTT if the client is available
                    if mqtt_client:
                        mqtt_data = f"Pressure Sensor {i + 1}: Expected Voltage: {expected_voltages[i]}, Lowest Voltage: {lowest_voltages_accumulated[i]}, Calculated Pressure: {pressures[i]}"
                        publish_mqtt(mqtt_client, MQTT_TOPIC_PRESSURE, mqtt_data)
               
                print(" ")

# Run the main function if this script is executed directly
if __name__ == "__main__":
    setup()
    main()

