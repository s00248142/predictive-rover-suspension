'''
********************************************************************************
* File Name: main.py
* Description: Final Year Project
*   Robotic rover with three wheeled legs suspended by field-oriented controlled
*   motors. The motors communicate over CAN with the main system (Nvidia Jetson 
*   running Linux). The steering and driving motors are also FOC-based brusless
*   DC motors. 
*   Time-of-Flight sensors are positioned in front of each wheel for control of
*   each wheel's suspended height using individual trim from an overall body
*   pose control loop primarily controlled by data from an inertial measurement
*   unit mixed with secondary joystick input. 
* Programmer: Alan Ryan (s00248142)
* Date: 06/05/2025
* Version: 5.0
********************************************************************************
'''
# ******************************************************************************
# Standard modules
# ******************************************************************************

import time
import math
from dataclasses import dataclass

# ******************************************************************************
# Installed modules
# ******************************************************************************

import pygame # For hand controller
import can # python-can
from bmi270.BMI270 import * # Accelorometer and gyroscope

# ******************************************************************************
# Custom modules
# ******************************************************************************

import tof # Custom module for time-of-flight sensors
from mit_motors import RMDL5015, CubeMarsGL60II, STM32_ESC # Custom module
import joystick as joy
from helpers import clamp
import steer_vel_mixer

# ******************************************************************************
# Initialise hand controller
# ******************************************************************************

def mix_body_degrees(pitch_deg, roll_deg, height_deg=0.0):
    return {
        "front_left":  height_deg + pitch_deg + roll_deg,
        "front_right": height_deg + pitch_deg - roll_deg,
        "rear":        height_deg - pitch_deg,
    }

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

def angle_deadband(value, threshold=0.5):
    if abs(value) < threshold:
        return 0.0
    return value

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0) # Check ls /dev/input/js* for js0 if error
js.init()

# ******************************************************************************
# Initialise CAN.
# This relies on the can0_enable.py and daemon_helpers.py runnning at startup 
# as a Linux service to initialise GPIO and CAN bus. See \daemons\README.md
# ******************************************************************************

can0 = can.Bus(interface='socketcan', channel='can0')

tof_sensors = [
    tof.TofSensor(tof_idx=1),
    tof.TofSensor(tof_idx=2),
    tof.TofSensor(tof_idx=3),
    tof.TofSensor(tof_idx=4),
]

# ******************************************************************************
# Initialise IMU
# Example from: https://github.com/CoRoLab-Berlin/bmi270_python
# ******************************************************************************

IMU = BMI270(I2C_PRIM_ADDR) # 0x68 on i2c channel 7.
IMU.load_config_file() # Required to load from BMI270 module to the IMU itelf

IMU.set_mode(PERFORMANCE_MODE)
IMU.set_acc_range(ACC_RANGE_4G) # Sets the accelerometer for +/- 4g range
IMU.set_gyr_range(GYR_RANGE_1000) # Sets the gyroscope to 1000 DPS
IMU.set_acc_odr(ACC_ODR_200) # ODR is output data rate
IMU.set_gyr_odr(GYR_ODR_200)
IMU.set_acc_bwp(ACC_BWP_OSR4)
IMU.set_gyr_bwp(GYR_BWP_OSR4)
IMU.disable_fifo_header()
IMU.enable_data_streaming()
IMU.enable_acc_filter_perf()
IMU.enable_gyr_noise_perf()
IMU.enable_gyr_filter_perf()

ACC_SCALE_4G = 1.0/8192.0 # Ratio for 16-bit raw (+/-4g mode) to g units.
GYRO_SCALE_1000DPS = 1000.0 / 32768.0 # 16-bit signed degrees per second.

# IMU angle smoothing
filtered_pitch_deg = 0.0
filtered_roll_deg = 0.0
ANGLE_ALPHA = 0.15

# Individual leg trim
FL_TRIM_DEG = 0.0
FR_TRIM_DEG = 0.0
REAR_TRIM_DEG = 0.0

# leg_trim = {
#     "front_left": 0.0,
#     "front_right": 0.0,
#     "rear": 0.0,
# }

# ******************************************************************************
# Attitude Targets
# ******************************************************************************

SUS_READY_DEG = -70 # Angle from horizontal for the suspension legs
SUS_STANDBY_DEG = -90.0 # Verticle mode to reduce electrical current demand
FLUIDITY = 0.1

# Set Target Limits (joystick or future payload protection ability)
TARGET_PITCH_MIN_DEG = -20.0
TARGET_PITCH_MAX_DEG = 20.0

TARGET_ROLL_MIN_DEG = -20.0
TARGET_ROLL_MAX_DEG = 20.0

# PD Controller output limits
CTRL_PITCH_MIN_DEG = -25.0
CTRL_PITCH_MAX_DEG = 15.0

CTRL_ROLL_MIN_DEG = -25.0
CTRL_ROLL_MAX_DEG = 25.0

# Command smoothing
filtered_pitch_cmd = 0.0
filtered_roll_cmd = 0.0
CMD_ALPHA = 0.12

# ******************************************************************************
# Proportional and Differential Controller Values
# ******************************************************************************
KP_PITCH = 0.9
KP_ROLL  = 0.9

KD_PITCH = 0.15
KD_ROLL = 0.15

# ******************************************************************************
# Initialise Motors

# This creates motors as objects of the MITMotor base class from mit_motors.py
# module. The primary reason is they share similar characterists such as using 
# the MIT-style CAN frame packing shape. (Postition, Velocity, Kp, Kd, Torque).
# The only mode used in this project for the suspension and steering motors is 
# position. The STM32 wheel-driving motors needed a custom CAN frame.
# ******************************************************************************

# Suspension Motors (CubeMars GL60 II)
left_sus_motor = CubeMarsGL60II(
    bus=can0,
    motor_id=1, # This becomes 0x001 for Cube Mars motors within sub class
    lower_deg=-90, # Similar to standby height, but keeping separate.
    upper_deg=1, # Slightly above horizontal (zero)
    max_delta_deg=5, # Limits any one command size. Needs stream for movement.
    direction=-1,   # Test motor to determine. 1 and -1 spin opposite.
    default_kp=8.0, # Used in target following control (tested optimal is 8.0)
    default_kd=0.2, # Used in target followng control (tested optimal is 0.2)
)

right_sus_motor = CubeMarsGL60II(
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

# Suspension Motors (MyActuator RMD-L-5015)

steering_motor = RMDL5015(
    bus=can0,
    motor_id=4,
    lower_deg=-80, # For steering this is the sweep left and rignt. 0 is centre.
    upper_deg=80,
    max_delta_deg=5,
    direction=1,
    default_kp=6,
    default_kd=0.1,
)

# Wheel-driving motors

# left_wheel_motor = STM32_ESC(
#     bus=can0,
#     motor_id=5,
#     direction=1,
#     limit_rpm_lower=-200,
#     limit_rpm_upper=200 # 200 observed as optimal. max_rpm is separate attribute
# )

# right_wheel_motor = STM32_ESC(
#     bus=can0,
#     motor_id=6,
#     direction=1,
#     limit_rpm_lower=-200,
#     limit_rpm_upper=200
# )

# rear_wheel_motor = STM32_ESC(
#     bus=can0,
#     motor_id=7,
#     direction=1,
#     limit_rpm_lower=-200,
#     limit_rpm_upper=200
# )


# ******************************************************************************
# Start Motors

# Startup has a slightly different routine per manufacturer. 
# See class methods.
# ******************************************************************************

left_sus_motor.startup()
time.sleep(0.05)

right_sus_motor.startup()
time.sleep(0.05)

rear_motor.startup()
time.sleep(0.05)

steering_motor.startup()
time.sleep(0.05)

# rear_wheel_motor.startup()
# time.sleep(0.1)

# left_wheel_motor.startup()
# time.sleep(0.05)

# right_wheel_motor.startup()
# time.sleep(0.05)


# ******************************************************************************
# Waiting Lobby Before Main Loop
# ******************************************************************************

try:
    # Frequency of loops below
    dt = 0.5 # 0.01 is 100 Hz
    
    # Triangle button on PS5 controller starts the rover.
    print("Ready!\nPress TRIANGLE to start rover...")


    # WAIT FOR PRESS
    while not js.get_button(joy.BTN_TRIANGLE):
        pygame.event.get()

        # Check for EXIT or MODE requests
        if js.get_button(joy.BTN_CROSS) == 1:
            print("Exiting...")
            raise KeyboardInterrupt

        time.sleep(0.05)

    print("pressed")

    # WAIT FOR RELEASE
    while js.get_button(joy.BTN_TRIANGLE):
        pygame.event.get()
        time.sleep(0.05)
    

    # Stand up the robot
    count = 0
    while count < 100:
        
        left_sus_motor.move(SUS_READY_DEG) # SUS_READY_DEG is normally -70
        right_sus_motor.move(SUS_READY_DEG)
        rear_motor.move(SUS_READY_DEG)
        steering_motor.move(0)

        time.sleep(dt)
        count = count + 1

# ******************************************************************************
#                         --------------------
#                   Begin Main Application While Loop
#                         --------------------
# ******************************************************************************
    while True:

        # **********************************************************************
        # Collect time-of-flight sensor data
        # **********************************************************************
        tof.poll_tof_sensors(tof_sensors)


        # **********************************************************************
        # Collect IMU data
        # **********************************************************************
        acc = IMU.get_raw_acc_data() # Collect accelerometer data from sensor
        gyr = IMU.get_raw_gyr_data() # Collect gyroscope data from sensor

        # Extract and convert to g units before calculations (accelerometer)
        ax_g = acc[0] * ACC_SCALE_4G 
        ay_g = acc[1] * ACC_SCALE_4G
        az_g = acc[2] * ACC_SCALE_4G

        # Extract and convert to DPS before calculations (gyroscope)
        gx_dps = gyr[0] * GYRO_SCALE_1000DPS 
        gy_dps = gyr[1] * GYRO_SCALE_1000DPS
        # gz_dps = gyr[2]* GYRO_SCALE_1000DPS # Unused

        # Derived roll formula from XYZ rotation sequence
        roll_deg = math.degrees(math.atan2(ay_g, az_g))
        roll_deg = -roll_deg # Invert to match model

        # Derived pitch formula from XYZ rotation sequence
        pitch_deg = math.degrees(math.atan2(-ax_g,
                                            math.sqrt(ay_g**2 + az_g**2)))
        
        filtered_pitch_deg += ANGLE_ALPHA * (pitch_deg - filtered_pitch_deg)
        filtered_roll_deg += ANGLE_ALPHA * (roll_deg - filtered_roll_deg)

        pitch_deg = filtered_pitch_deg
        roll_deg = filtered_roll_deg
        
        # Organise gyroscope data
        pitch_rate_dps = gy_dps
        roll_rate_dps = -gx_dps # Inverted to match motor model
        
        # **********************************************************************
        # Collect Joystick Events
        # Use pygame_test_inputs.py in /tools/ to discover live button mapping
        # **********************************************************************
        
        pygame.event.get() # Collects the current state frame for joystick

        # Extract right joystick data for body attitude control
        pitch_axis = deadzone(-js.get_axis(joy.AXIS_R_Y)) # Invert joystick 
        roll_axis = deadzone(-js.get_axis(joy.AXIS_R_X)) # Invert joystick

        # Extract left joystick data for steering control
        steering_axis = deadzone(js.get_axis(joy.AXIS_L_X))

        # all_height_axis = deadzone(-js.get_axis(joy.AXIS_R_Y))

        # Extract and combine RPM target from right and left triggers
        pos_speed = deadzone(js.get_axis(joy.AXIS_R2))
        neg_speed = deadzone(js.get_axis(joy.AXIS_L2))
        axis = joy.triggers_to_axis(pos_speed , neg_speed) # R2 = fwd, L2 = rev



        # Manual requests for trim control of individual legs
        if js.get_hat(joy.HAT_DPAD) == (-1, 0):
            if js.get_button(joy.BTN_OPTIONS):
                FL_TRIM_DEG -= 0.2  # extend/lower FL
            else:
                FL_TRIM_DEG += 0.2  # retract/raise FL

        if js.get_hat(joy.HAT_DPAD) == (1, 0):
            if js.get_button(joy.BTN_OPTIONS):
                FR_TRIM_DEG -= 0.2   # extend/lower FR
            else:
                FR_TRIM_DEG += 0.2   # retract/raise FR

        if js.get_hat(joy.HAT_DPAD) == (0, -1):
            if js.get_button(joy.BTN_OPTIONS):
                REAR_TRIM_DEG -= 0.2 # extend/lower REAR
            else:
                REAR_TRIM_DEG += 0.2 # retract/raise REAR

        # Reset trim values
        if js.get_hat(joy.HAT_DPAD) == (0, 1):
            if js.get_button(joy.BTN_OPTIONS): # Low current vertical stance
                FL_TRIM_DEG = SUS_STANDBY_DEG - SUS_READY_DEG
                FR_TRIM_DEG = SUS_STANDBY_DEG - SUS_READY_DEG
                REAR_TRIM_DEG = SUS_STANDBY_DEG - SUS_READY_DEG
            else:
                FL_TRIM_DEG = 0.0
                FR_TRIM_DEG = 0.0
                REAR_TRIM_DEG = 0.0

        

        # Check for EXIT or MODE requests
        if js.get_button(joy.BTN_CROSS) == 1:
            break


        # **********************************************************************
        # Set Targets
        # **********************************************************************

        target_pitch_deg = map_axis_to_asymmetric_angle(
            pitch_axis,
            TARGET_PITCH_MIN_DEG,
            TARGET_PITCH_MAX_DEG,
        )

        target_roll_deg = map_axis_to_asymmetric_angle(
            roll_axis,
            TARGET_ROLL_MIN_DEG,
            TARGET_ROLL_MAX_DEG,
        )

        # rear_target_speed= steer_vel_mixer.axis_to_rpm(axis, 
        #                                     rear_wheel_motor.limit_rpm_upper)
        # left_target_speed= steer_vel_mixer.axis_to_rpm(axis, 
        #                                     left_wheel_motor.limit_rpm_upper)
        # right_target_speed= steer_vel_mixer.axis_to_rpm(axis, 
        #                                     right_wheel_motor.limit_rpm_upper)

        # **********************************************************************
        # Proportional and Differtial Control
        # **********************************************************************

        # pitch_error = target_pitch_deg - pitch_deg
        # roll_error  = target_roll_deg  - roll_deg

        pitch_error = angle_deadband(target_pitch_deg - pitch_deg)
        roll_error  = angle_deadband(target_roll_deg - roll_deg)

        # pitch_cmd = KP_PITCH * pitch_error
        # roll_cmd = KP_ROLL * roll_error

        pitch_cmd = (KP_PITCH * pitch_error) - (KD_PITCH * pitch_rate_dps)
        roll_cmd  = (KP_ROLL * roll_error) - (KD_ROLL * roll_rate_dps)

        pitch_cmd = clamp(pitch_cmd, CTRL_PITCH_MIN_DEG, CTRL_PITCH_MAX_DEG)
        roll_cmd = clamp(roll_cmd, CTRL_ROLL_MIN_DEG, CTRL_ROLL_MAX_DEG)

        filtered_pitch_cmd += CMD_ALPHA * (pitch_cmd - filtered_pitch_cmd)
        filtered_roll_cmd += CMD_ALPHA * (roll_cmd - filtered_roll_cmd)

        pitch_cmd = filtered_pitch_cmd
        roll_cmd = filtered_roll_cmd

        targets = mix_body_degrees(pitch_cmd, roll_cmd)

        # print(
        #     f"Tgt P/R: {target_pitch_deg:6.2f}, {target_roll_deg:6.2f} | "
        #     f"IMU P/R: {pitch_deg:6.2f}, {roll_deg:6.2f} | "
        #     f"Err P/R: {pitch_error:6.2f}, {roll_error:6.2f} | "
        #     f"Cmd P/R: {pitch_cmd:6.2f}, {roll_cmd:6.2f}"
        #     )



        print(
            f"Trim FL/FR/R: {FL_TRIM_DEG:6.2f}, "
            f"{FR_TRIM_DEG:6.2f}, {REAR_TRIM_DEG:6.2f}"
        )

        front_left_cmd = SUS_READY_DEG + targets["front_left"] + FL_TRIM_DEG
        front_right_cmd = SUS_READY_DEG + targets["front_right"] + FR_TRIM_DEG
        rear_cmd = SUS_READY_DEG + targets["rear"] + REAR_TRIM_DEG


        # **********************************************************************
        # Request Motor Movement
        # **********************************************************************

        left_sus_motor.move(front_left_cmd, fluidity=FLUIDITY, dt=dt)
        right_sus_motor.move(front_right_cmd, fluidity=FLUIDITY, dt=dt)
        rear_motor.move(rear_cmd, fluidity=FLUIDITY, dt=dt)
        steering_motor.move(steering_axis * steering_motor.upper_deg, dt=dt)
        # left_wheel_motor.send_rpm(left_target_speed)
        # right_wheel_motor.send_rpm(right_target_speed)
        # rear_wheel_motor.send_rpm(rear_target_speed)

        time.sleep(dt)

finally:
    # Lie down robot
    dt = 0.01

    count = 0
    while count < 100:
    
        steering_motor.move(0)
        left_sus_motor.move(0)
        right_sus_motor.move(0)
        rear_motor.move(0)
        # left_wheel_motor.send_rpm(0)
        # right_wheel_motor.send_rpm(0)
        # rear_wheel_motor.send_rpm(0)

        time.sleep(dt)
        count = count + 1
    
    # Shutdown motors
    steering_motor.shutdown()
    left_sus_motor.shutdown()
    right_sus_motor.shutdown()
    rear_motor.shutdown()
    # left_wheel_motor.shutdown()
    # right_wheel_motor.shutdown()
    # rear_wheel_motor.shutdown()

    # Turn off all XSHUT signals to ToF sensors to allow re-run
    tof.xshut_reset()


# ******************************* End of file **********************************
