import machine
import time

# Define GPIO pin numbers for buttons and relay
button_on_pin = 5  # Replace with the actual GPIO pin for the "turn on" button
button_off_pin = 17  # Replace with the actual GPIO pin for the "turn off" button
relay_pin = 33  # Replace with the actual GPIO pin for the relay

# Setup GPIO pins
button_on = machine.Pin(button_on_pin, machine.Pin.IN, machine.Pin.PULL_UP)
button_off = machine.Pin(button_off_pin, machine.Pin.IN, machine.Pin.PULL_UP)
relay = machine.Pin(relay_pin, machine.Pin.OUT)

# Initialize the relay state
relay.on()

while True:
    # Check the state of the "turn on" button
    if button_on.value() == 0:  # Button is pressed (logic low)
        relay.on()  # Turn on the relay
        print("Relay turned ON")
        while button_on.value() == 0:
            time.sleep(0.1)  # Wait for the button to be released
        time.sleep(0.2)  # Debounce delay

    # Check the state of the "turn off" button
    if button_off.value() == 0:  # Button is pressed (logic low)
        relay.off()  # Turn off the relay
        print("Relay turned OFF")
        while button_off.value() == 0:
            time.sleep(0.1)  # Wait for the button to be released
        time.sleep(0.2)  # Debounce delay

    time.sleep(0.1)  # Adjust this delay as needed based on your requirements
