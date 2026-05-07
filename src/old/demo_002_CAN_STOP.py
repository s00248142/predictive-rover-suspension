import time
from helpers import *
# import tof
import gpiod
from mit_motors import RMDL5015, CubeMarsGL60II



# Initialise I2C for display to indicate program start (blink bottom bar x 2)

# Initialise GPIO for can0 and can1
gpio_request = None # For gpiod as object showing ownership of pin (GPIO line)
gpio_request = gpiod.request_lines(
    "/dev/gpiochip0",
    config={
        43: gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=gpiod.line.Value.INACTIVE
        ),
        106: gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=gpiod.line.Value.INACTIVE
        ),
    },
    consumer="rover_app_can" # visible to Linux GPIO queries.
)

print("GPIO lines 43 & 106 held low. can0 & can1 enabled.")

# Initialise can0 bus for suspension motors
can0 = CanBus(channel=0, bitrate=1000000)
can0.start()
print("ready")
time.sleep(5)


can0.stop()

