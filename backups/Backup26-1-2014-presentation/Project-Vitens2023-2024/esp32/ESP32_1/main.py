from machine import Pin, ADC
import utime, time
import config
import network
from umqtt.simple import MQTTClient
import json

# Global variables
is_reading_sensors = False  # True when green button is pressed | False when red button is pressed
interval = 5000  # Interval for measuring sensors
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
# WIFI_SSID = 'freek'
# WIFI_PASSWORD = 'freekfreek'

# MQTT broker information
MQTT_BROKER = '192.168.2.1'
MQTT_PORT = 1883
MQTT_TOPIC_FLOW = 'flow_data'
MQTT_TOPIC_PRESSURE = 'pressure_data'
mqtt_client = 'raspberrypi-vitens'
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
        print("ip:", ip_address)
    return wlan


# Initialize MQTT client
def connect_mqtt():
    global led, mqtt_client

    led_blinking = True
    led_blink_interval = 500  # milliseconden

    try:
        mqtt_client = MQTTClient('esp32', MQTT_BROKER, port=MQTT_PORT)
        mqtt_client.connect()
        led_blinking = False  # Stop met knipperen als de verbinding tot stand is gebracht
        led.on()  # Zet de LED aan wanneer zowel WiFi als MQTT zijn verbonden
        return mqtt_client  # Geef het MQTTClient-object terug
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
def multisample_adc(adc, num_samples=20):
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
    global led, adc_sensors, is_reading_sensors

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

# Interrupt handler for the start button
def button_start_interrupt(pin):
    global is_reading_sensors
    if not is_reading_sensors:
        # Turn on the LED
        led.value(1)

        # Wait for 5 seconds
        for _ in range(50):
            utime.sleep_ms(100)  # Sleep for 100 milliseconds

        # Attempt to connect to WiFi and MQTT
        wlan = connect_wifi()
        mqtt_client = connect_mqtt()

        if mqtt_client is None:
            print("MQTT connection failed. Measurements will be taken, but data won't be sent to MQTT.")

        # Start reading the sensors
        is_reading_sensors = True
        print("Sensors reading started.")

# Interrupt handler for the end button
def button_end_interrupt(pin):
    global is_reading_sensors
    if is_reading_sensors:
        # Turn off the LED
        led.value(0)

        while pin.value() == 0:
            time.sleep(0.1)  # Wait for the button to be released
        time.sleep(0.2)  # Debounce delay

        # Stop reading the sensors
        is_reading_sensors = False
        print("Sensors reading stopped.")

# Main function
def main():
    global is_reading_sensors, interval, previous_millis, flow_count

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
                    flow_data = {
                        "Sensor": i + 6,
                        "Type": 0,
                        "Layer": 0,
                        "FlowRate": rate,
                        "TotalLiters": total_liters_accumulated[i]
                    }
                    print(json.dumps(flow_data))
#                     print(f"Sensor: {flow_data['Sensor']}, Type: {flow_data['Type']}, Layer: {flow_data['Layer']}, Flow Rate: {flow_data['FlowRate']} L/min, Total Liters: {flow_data['TotalLiters']} L")

                    # Publish flow data to MQTT if the client is available
                    if mqtt_client:
                        mqtt_data = json.dumps(flow_data)
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
                    sensor_data = {
                        "Sensor": i + 6,
                        "Type": 1,
                        "Layer": 0,
                        "ExpectedVoltage": expected_voltages[i],
                        "LowestVoltage": lowest_voltages_accumulated[i],
                        "CalculatedPressure": pressures[i]
                    }
                    print(json.dumps(sensor_data))
#                     print(f"Sensor: {sensor_data['Sensor']}, Type: {sensor_data['Type']}, Layer: {sensor_data['Layer']}, Expected Voltage: {sensor_data['ExpectedVoltage']}, Lowest Voltage: {sensor_data['LowestVoltage']}, Calculated Pressure: {sensor_data['CalculatedPressure']}")

                    # Publish pressure data to MQTT if the client is available
                    if mqtt_client:
                        mqtt_data = json.dumps(sensor_data)
                        publish_mqtt(mqtt_client, MQTT_TOPIC_PRESSURE, mqtt_data)

                print(" ")

# Run the main function if this script is executed directly
if __name__ == "__main__":
    setup()
    main()

