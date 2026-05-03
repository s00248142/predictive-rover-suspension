import time
import math
from dataclasses import dataclass

import can # python-can
import pygame

from mit_motors import RMDL5015, CubeMarsGL60II
import joystick_map as joy


def mix_body_degrees(pitch_deg, roll_deg, height_deg=0.0):
    return {
        "front_left":  height_deg + pitch_deg + roll_deg,
        "front_right": height_deg + pitch_deg - roll_deg,
        "rear":        height_deg - pitch_deg,
    }


def move_all(left, right, rear, steering,
             left_deg, right_deg, rear_deg, steering_deg,
             dt):
    left.move(left_deg, dt=dt)
    right.move(right_deg, dt=dt)
    rear.move(rear_deg, dt=dt)
    steering.move(steering_deg, dt=dt)
    time.sleep(dt)

def deadzone(value: float, threshold: float = 0.08) -> float:
    if abs(value) < threshold:
        return 0.0
    return value

def map_axis_to_asymmetric_angle(value, negative_limit, positive_limit):
    value = clamp(value, -1.0, 1.0)

    if value >= 0:
        return value * positive_limit
    else:
        return value * abs(negative_limit)

def clamp(value, low, high):
    return max(low, min(high, value))

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0) # Check ls /dev/input/js* for js0 if error
js.init()

can0 = can.Bus(interface='socketcan', channel='can0')

# ******************************************************************************
# Attitude Targets
# ******************************************************************************

BASE_HEIGHT = -70
FLUIDITY = 0.2

PITCH_MIN_DEG = -20.0   # Nose down
PITCH_MAX_DEG = 20.0    # Nose up

ROLL_MIN_DEG  = -20.0
ROLL_MAX_DEG  = 20.0

# ******************************************************************************
# Proportional Controller (P Control)
# ******************************************************************************
# Error:
# pitch_error = target_pitch - pitch_deg
# roll_error  = target_roll  - roll_deg
# KP_PITCH = 0.4
# KP_ROLL  = 0.4

# pitch_cmd = KP_PITCH * pitch_error
# roll_cmd  = KP_ROLL  * roll_error

# pitch_cmd = clamp(pitch_cmd, -3.0, 3.0)
# roll_cmd  = clamp(roll_cmd,  -3.0, 3.0)



print("ready")
time.sleep(3)

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

left_motor.startup()
time.sleep(0.05)

right_motor.startup()
time.sleep(0.05)

rear_motor.startup()
time.sleep(0.05)

steering_motor.startup()
time.sleep(0.05)

try:
    print("waiting for TRIANGLE to stand up...")

    # WAIT FOR PRESS
    while not js.get_button(joy.BTN_TRIANGLE):
        pygame.event.get()
        time.sleep(0.05)

    print("pressed")

    # WAIT FOR RELEASE
    while js.get_button(joy.BTN_TRIANGLE):
        pygame.event.get()
        time.sleep(0.05)
    

    # Stand up the robot
    dt = 0.01

    count = 0
    while count < 100:
        
        left_motor.move(-70)
        right_motor.move(-70)
        rear_motor.move(-70)
        steering_motor.move(0)

        time.sleep(dt)
        count = count + 1

    # Main loop
    while True:
        # pygame.event.pump()
        pygame.event.get()

        # cmd_obj = AttitudeCommand(
        #     pitch = -deadzone(js.get_axis(joy.AXIS_R_Y)),
        #     roll = -deadzone(js.get_axis(joy.AXIS_R_X))
        # )

        pitch_axis = deadzone(-js.get_axis(joy.AXIS_R_Y)) # Invert joystick 
        roll_axis = deadzone(-js.get_axis(joy.AXIS_R_X)) # Invert joystick

        target_pitch_deg = map_axis_to_asymmetric_angle(
            pitch_axis,
            PITCH_MIN_DEG,
            PITCH_MAX_DEG,
        )

        target_roll_deg = map_axis_to_asymmetric_angle(
            roll_axis,
            ROLL_MIN_DEG,
            ROLL_MAX_DEG,
        )

        targets = mix_body_degrees(
            pitch_deg=target_pitch_deg,
            roll_deg=target_roll_deg,
        )

        # targets = mix_body_command(
        #     cmd_obj,
        #     max_pitch_deg=20.0,
        #     max_roll_deg=20.0
        #     )


        # left_motor.move(targets["front_left"] - 70, fluidity = 0.2, dt=dt)
        # right_motor.move(targets["front_right"] - 70, fluidity = 0.2, dt=dt)
        # rear_motor.move(targets["rear"] - 70, dt=dt)

        # Debug before uncommenting below three lines:
        left_motor.move(BASE_HEIGHT + targets["front_left"],
                        fluidity=FLUIDITY, dt=dt)
        right_motor.move(BASE_HEIGHT + targets["front_right"], 
                         fluidity=FLUIDITY, dt=dt)
        rear_motor.move(BASE_HEIGHT + targets["rear"], 
                        fluidity=FLUIDITY, dt=dt)
        steering_motor.move(0, dt=dt)

        # print(
        #     f"Tgt P/R: {target_pitch:6.2f}, {target_roll:6.2f} | "
        #     f"IMU P/R: {pitch_deg:6.2f}, {roll_deg:6.2f} | "
        #     f"Cmd P/R: {pitch_cmd:6.2f}, {roll_cmd:6.2f}"
        # )   

        if js.get_button(joy.BTN_CROSS) == 1:
            break

        time.sleep(dt)

finally:
    # Lie down robot
    dt = 0.01

    count = 0
    while count < 100:
    
        steering_motor.move(0)
        left_motor.move(0)
        right_motor.move(0)
        rear_motor.move(0)

        time.sleep(dt)
        count = count + 1
    
    # Shutdown motors
    steering_motor.shutdown()
    left_motor.shutdown()
    right_motor.shutdown()
    rear_motor.shutdown()