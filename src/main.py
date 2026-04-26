import time
from helpers import *
import tof
import gpiod


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

tof1 = tof.TofSensor(xshut=1)
tof2 = tof.TofSensor(xshut=2)
tof3 = tof.TofSensor(xshut=3)
tof4 = tof.TofSensor(xshut=4)


# Initialise can1 for other motors
# can1 = CanBus(channel=1, bitrate=1000000)
# can1.start()


# Initialise TOF sensors I2C


# Show TOF feedback on LED matrix

# Create objects for each motor
# sus_motor_left = SusMotor()

# Calibrate zero

# Rise robot to 60 degrees

# Indicate bluetooth connection to PS3 controller.

# Start program with dance more using right joystick and up/down pad
# Double-up for low power stance
# Double-down for zero sit
# Double-left for flip left

# Triangle to go to drive mode with TOF. Keep flat
# Circle to go to drive mode just wheels
# Square to go to lean mode
# X to go back to dance mode

# Crawling demo
# aiming demo
# flip demo
# upside-down demo

# Safe shutdown
# SSH mode
# Enable desktop
# Disable desktop

# Main section:

# Disable motor
can0.bus.send(can.Message(
        arbitration_id=0x001,
        data=[0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xfd],
        is_extended_id=False
    ))
time.sleep(1)
# Set zero
can0.bus.send(can.Message(
        arbitration_id=0x001,
        data=[0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xfe],
        is_extended_id=False
    ))
time.sleep(1)
# Enable motor
can0.bus.send(can.Message(
        arbitration_id=0x001,
        data=[0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xfc],
        is_extended_id=False
    ))
time.sleep(1)

count = 0x7f

while True:
    msg = can.Message(
        arbitration_id=0x001,
        # data=[count, 0xff, 0x7f, 0xf0, 0x01, 0x00, 0x17, 0xff],
        data=[count, 0xff, 0x7f, 0xf0, 0x10, 0x01, 0x17, 0xff],
        is_extended_id=False
    )

    can0.bus.send(msg)

    count = (count + 0x01) % 256

    

    # rx_msg = can0.bus.recv(timeout=1)
    # if rx_msg is not None:
    #     print(rx_msg)
    #     can0.bus.send(
    #         can.Message(
    #             arbitration_id=0x123,
    #             data=[253,0,0,0,0,0,0,0],
    #             is_extended_id=False)
    #     )
    time.sleep(1)
    cmd = input("q to quit, Enter to continue: ")

    if cmd == "q":
        break

can0.bus.send(can.Message(
        arbitration_id=0x001,
        data=[0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xfd],
        is_extended_id=False
    ))
can0.stop()
if gpio_request is not None:
    gpio_request.release() # Release ownership of line 43.


# Eventually use this with PS3 controller:
# cmd = input("Press q to quit: ")
# if cmd == "q":
#     can0.stop()

