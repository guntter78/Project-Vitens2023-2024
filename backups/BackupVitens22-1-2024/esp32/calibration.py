from machine import Pin, ADC
import utime, time
import config

# Global variables
is_reading_sensors = False  # True when green button is pressed | False when red button is pressed
interval = 1000  # Interval for measuring sensors
previous_millis = 0  # Variable to measure at certain intervals

# Constants for Digital channels
FLOW_CHANNELS = [config.flow_1, config.flow_2, config.flow_3, config.flow_4, config.flow_5]

flow_count = [0] * 5  # Counters for flow sensors

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

    # Set up flow sensor pins and interrupt handlers
    for i, flow_pin in enumerate(FLOW_CHANNELS):
        flow_sensor = Pin(flow_pin, Pin.IN)
        flow_sensor.irq(trigger=Pin.IRQ_FALLING, handler=lambda p, idx=i: flow_sensor_interrupt(p, idx))

    # Set LED pin as output
    led = Pin(config.led_pin, Pin.OUT)
    
# Interrupt handler for the start button
def button_start_interrupt(pin):
    global is_reading_sensors
    if not is_reading_sensors:
        # Turn on the LED
        led.value(1)

        # Start reading the sensors
        is_reading_sensors = True
        print("Sensors reading started.")

# Interrupt handler for the end button
def button_end_interrupt(pin):
    global is_reading_sensors
    if is_reading_sensors:
        # Turn off the LED
        led.value(0)

        # Stop reading the sensors
        is_reading_sensors = False
        print("Sensors reading stopped.")

# Main function
def main():
    global is_reading_sensors, interval, previous_millis, flow_count

    calibration_factors = [63.3, 1.0, 1.0, 1.0, 1.0]  # Calibration factors for flow sensors
    total_liters = [0.0] * 5  # Amount of water that went by each flow sensor

    print("Main running.")
    while True:
        if is_reading_sensors:
            current_millis = utime.ticks_ms()
            if utime.ticks_diff(current_millis, previous_millis) >= interval:
                previous_millis = current_millis
                
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
                    
                print(" ")

# Run the main function if this script is executed directly
if __name__ == "__main__":
    setup()
    main()

