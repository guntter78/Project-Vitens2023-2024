from machine import ADC, Pin
import time

# Define the ADC pin
adc = ADC(Pin(36))  # Create ADC object on ADC pin 0
adc.atten(ADC.ATTN_0DB)
adc.width(ADC.WIDTH_12BIT)

while True:
    # Read analog value
    analog_value = adc.read()

    # Print the digital value
    print("Digital Value:", analog_value)

    # Wait for one second
    time.sleep(1)
