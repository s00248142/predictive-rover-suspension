'''
********************************************************************************
* File Name: Lab_5c.py
* Description: Lab 5c. FIR lowpass filter applied using SciPy funtions. 
*              Plot of downsampled signal y(m) from anti-aliased w(n).
*              Plot shows the final signal in the frequency domain after FFT.
* Programmer: Alan Ryan (s00248142)
* Date: 17/04/2025
* Version: 1.0
********************************************************************************
'''
# ******************************************************************************
# Standard modules
# ******************************************************************************

import time

# ******************************************************************************
# Installed modules
# ******************************************************************************

import pygame # For hand controller
import can # python-can

# ******************************************************************************
# Custom modules
# ******************************************************************************

import tof # Custom module for time-of-flight sensors
from mit_motors import RMDL5015, CubeMarsGL60II # Custom module
import joystick_map as joy

# ******************************************************************************
# Initialise hand controller
# ******************************************************************************

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0) # Check ls /dev/input/js* for js0 if error
js.init()

# ******************************************************************************
# Initialise motors
# ******************************************************************************

# Select CAN bus 'can0' for initiating motor objects
can0 = can.Bus(interface='socketcan', channel='can0')

print("ready")
time.sleep(3)

left_motor = CubeMarsGL60II(
    bus=can0,
    motor_id=1,
    lower_deg=-90,
    upper_deg=1,
    max_delta_deg=5,
    direction=-1,
    default_kp=8.0,
    default_kd=0.2,
)

right_motor = CubeMarsGL60II(
    bus=can0,
    motor_id=2,
    lower_deg=-90,
    upper_deg=1,
    max_delta_deg=5,
    direction=1,
    default_kp=8.0,
    default_kd=0.2,
)

rear_motor = CubeMarsGL60II(
    bus=can0,
    motor_id=3,
    lower_deg=-90,
    upper_deg=1,
    max_delta_deg=5,
    direction=1,
    default_kp=4.0,
    default_kd=0.1,
)

steering_motor = RMDL5015(
    bus=can0,
    motor_id=4,
    lower_deg=-80,
    upper_deg=80,
    max_delta_deg=5,
    direction=1,
    default_kp=6,
    default_kd=0.1,
)

left_motor.startup()
time.sleep(0.05)

right_motor.startup()
time.sleep(0.05)

rear_motor.startup()
time.sleep(0.05)

steering_motor.startup()
time.sleep(0.05)


# Initialise I2C for display to indicate program start (blink bottom bar x 2)

# Select CAN bus 'can0' for initiating motor objects (CAN initialised in daemon)
can0 = can.Bus(interface='socketcan', channel='can0')




# tof1 = tof.TofSensor(xshut=1)
# tof2 = tof.TofSensor(xshut=2)
# tof3 = tof.TofSensor(xshut=3)
# tof4 = tof.TofSensor(xshut=4)


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

