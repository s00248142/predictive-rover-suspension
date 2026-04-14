

import time
import board # From CircuitPython library (https://pypi.org/project/Adafruit-Blinka/)
import digitalio # From CircuitPython library
import adafruit_vl53l4cd

PIN = board.D18

print("hello blinky!")

led = digitalio.DigitalInOut(PIN)
led.direction = digitalio.Direction.OUTPUT

while True:
    led.value = True
    time.sleep(0.5)
    led.value = False
    time.sleep(0.5)