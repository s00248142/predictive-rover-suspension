import time
from dataclasses import dataclass

import can # python-can
import pygame

from mit_motors import RMDL5015, CubeMarsGL60II
import joystick_map as joy


@dataclass
class AttitudeCommand:
    pitch: float  # normalised -1.0 to +1.0
    roll: float   # normalised -1.0 to +1.0
    height: float = 0.0  

def mix_body_command(
    cmd: AttitudeCommand,
    max_pitch_deg: float,
    max_roll_deg: float,
    max_height_deg: float = 0.0,
):
    pitch = cmd.pitch * max_pitch_deg
    roll = cmd.roll * max_roll_deg
    height = cmd.height * max_height_deg

    return {
        "front_left": height + pitch + roll,
        "front_right": height + pitch - roll,
        "rear": height - pitch,
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

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0) # Check ls /dev/input/js* for js0 if error
js.init()

can0 = can.Bus(interface='socketcan', channel='can0')

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

    while True:
        pygame.event.pump()

        cmd_obj = AttitudeCommand(
            pitch = -deadzone(js.get_axis(joy.AXIS_R_Y)),
            roll = -deadzone(js.get_axis(joy.AXIS_R_X))
        )

        targets = mix_body_command(
            cmd_obj,
            max_pitch_deg=20.0,
            max_roll_deg=20.0
            )

        left_motor.move(targets["front_left"] - 70, fluidity = 0.2, dt=dt)
        right_motor.move(targets["front_right"] - 70, fluidity = 0.2, dt=dt)
        rear_motor.move(targets["rear"] - 70, dt=dt)

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