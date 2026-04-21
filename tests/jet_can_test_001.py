import time
import gpiod

CHIP = "/dev/gpiochip0"

with gpiod.request_lines(
    CHIP,
    consumer="can-enable",
    config={
        106: gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=gpiod.line.Value.INACTIVE,
        ),
        43: gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=gpiod.line.Value.INACTIVE,
        ),
    },
) as request:
    print("Holding CAN1 and CAN0 enable lines low")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass