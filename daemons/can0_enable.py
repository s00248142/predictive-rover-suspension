from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.helpers import CanBus
import gpiod
import time

# Initialise GPIO for can0
gpio_request = None # For gpiod as object showing ownership of pin (GPIO line)
gpio_request = gpiod.request_lines(
    "/dev/gpiochip0",
    config={
        43: gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=gpiod.line.Value.INACTIVE
        )
    },
    consumer="rover_app_can" # visible to Linux GPIO queries.
)

print("GPIO lines 43 held low. can0 enabled.")

# Initialise can0 bus for suspension motors
can0 = CanBus(channel=0, bitrate=1000000)
can0.start()

# Keep Python program alive to own GPIO line 43
try:
    print("Holding GPIO line. Press Ctrl+C to exit.")
    while True:
        time.sleep(3600)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    can0.stop()  
    gpio_request.release()