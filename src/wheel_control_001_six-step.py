import time
import math
from dataclasses import dataclass

import can # python-can
import pygame
from bmi270.BMI270 import *

from mit_motors import RMDL5015, CubeMarsGL60II, STM32_ESC
import joystick as joy


def deadzone(value: float, threshold: float = 0.08) -> float:
    if abs(value) < threshold:
        return 0.0
    return value

def clamp(value, low, high):
    return max(low, min(high, value))

def angle_deadband(value, threshold=0.5):
    if abs(value) < threshold:
        return 0.0
    return value

def norm_trigger(val):
    return (val + 1.0) / 2.0

def triggers_to_axis(fwd_raw, rev_raw):
    fwd = norm_trigger(fwd_raw)
    rev = norm_trigger(rev_raw)
    axis = fwd - rev
    return axis

def axis_to_rpm(axis, max_rpm):
    
    return int(axis * max_rpm)

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0) # Check ls /dev/input/js* for js0 if error
js.init()

can0 = can.Bus(interface='socketcan', channel='can0')

# rear_wheel_motor = STM32_ESC(
#     bus=can0,
#     motor_id=7,
#     direction=1,
#     limit_rpm_lower=-600,
#     limit_rpm_upper=200
# )

left_wheel_motor = STM32_ESC(
    bus=can0,
    motor_id=5,
    direction=1,
    limit_rpm_lower=-600,
    limit_rpm_upper=200
)

right_wheel_motor = STM32_ESC(
    bus=can0,
    motor_id=6,
    direction=1,
    limit_rpm_lower=-600,
    limit_rpm_upper=200
)

# rear_wheel_motor.startup()
# time.sleep(0.1)

left_wheel_motor.startup()
time.sleep(0.5)

right_wheel_motor.startup()
time.sleep(0.5)

try:
    print("Started... Press Triangle")

    # WAIT FOR PRESS
    while not js.get_button(joy.BTN_TRIANGLE):
        pygame.event.get()
        time.sleep(0.05)

    print("pressed")

    # WAIT FOR RELEASE
    while js.get_button(joy.BTN_TRIANGLE):
        pygame.event.get()
        time.sleep(0.05)
    
    dt = 0.1    
    # Main loop
    while True:
   
        # **********************************************************************
        # Collect Joystick Events
        # **********************************************************************
        pygame.event.get()

        pos_speed = deadzone(js.get_axis(joy.AXIS_R2))
        neg_speed = deadzone(js.get_axis(joy.AXIS_L2))
        axis = triggers_to_axis(pos_speed , neg_speed)   # R2 = forward, L2 = reverse
        # rear_target_speed= axis_to_rpm(axis, rear_wheel_motor.limit_rpm_upper)
        left_target_speed= axis_to_rpm(axis, left_wheel_motor.limit_rpm_upper)
        right_target_speed= axis_to_rpm(axis, right_wheel_motor.limit_rpm_upper)
        # read_speed = rear_wheel_motor.read_speed_feedback_rpm()
        # print(f"Target speed: {target_speed} \t Read speed: {read_speed}")
        # rear_wheel_motor.send_rpm(rear_target_speed)
        left_wheel_motor.send_rpm(left_target_speed)
        right_wheel_motor.send_rpm(right_target_speed)

        # fb = rear_wheel_motor.poll_feedback_stm()
        fb = left_wheel_motor.poll_feedback_stm()
        fb = right_wheel_motor.poll_feedback_stm()
        if fb is not None:
            rpm, voltage, duty, direction, state = fb
            print(f"wheel rpm: {rpm} \tvoltage: {voltage} \tduty: {duty/32768}")

        # Check for EXIT or MODE requests
        if js.get_button(joy.BTN_CROSS) == 1:
            break


        # **********************************************************************
        # Set Speed
        # **********************************************************************


        # target_pitch_deg = 0.0
        # target_roll_deg = 0.0



        # print(
        #     f"Tgt P/R: {target_pitch_deg:6.2f}, {target_roll_deg:6.2f} | "
        #     f"IMU P/R: {pitch_deg:6.2f}, {roll_deg:6.2f} | "
        #     f"Err P/R: {pitch_error:6.2f}, {roll_error:6.2f} | "
        #     f"Cmd P/R: {pitch_cmd:6.2f}, {roll_cmd:6.2f}"
        #     )




        # **********************************************************************
        # Request Motor Movement
        # **********************************************************************


        time.sleep(dt)

finally:
    # Lie down robot
    dt = 0.01

    count = 0
    while count < 100:
    
        # rear_wheel_motor.send_rpm(0)
        left_wheel_motor.send_rpm(0)
        right_wheel_motor.send_rpm(0)


        time.sleep(dt)
        count = count + 1
    
    # Shutdown motors
    # rear_wheel_motor.shutdown()
    left_wheel_motor.shutdown()
    right_wheel_motor.shutdown()