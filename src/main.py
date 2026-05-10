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
# import steer_vel_mixer # Uncomment when re-introducing wheel motors.
import angle_height_calc

# ******************************************************************************
# Global flags
# ******************************************************************************

exit_flag = False # Used for setting flag from within nested while loops.
tof_trim_enabled = False # ToF trim can be disabled. False means off.

# ******************************************************************************
# Functions (internal)
# ******************************************************************************

# Attitude Mixer - Pitch and Roll degrees for three-limbs
def mix_body_degrees(pitch_deg, roll_deg, height_deg=0.0):
    return {
        "front_left":  height_deg + pitch_deg + roll_deg,
        "front_right": height_deg + pitch_deg - roll_deg,
        "rear":        height_deg - pitch_deg,
    }

# Use signed multiplier input for asymmetric control of pitch and roll
# Limits based on TARGET_x_y_DEG constants (x is PITCH or ROLL, y is MIN or MAX)
def map_axis_to_asymmetric_angle(value, negative_limit, positive_limit):
    value = clamp(value, -1.0, 1.0)

    if value >= 0:
        return value * positive_limit
    else:
        return value * abs(negative_limit)

# ******************************************************************************
# Deadband for PD control. Using 0.5 as initial threshold.
# ******************************************************************************
def angle_deadband(value, threshold=0.5):
    if abs(value) < threshold:
        return 0.0
    return value

# ******************************************************************************
# Initialise hand controller
# ******************************************************************************

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0) # Check ls /dev/input/js* for js0 if error
js.init()
last_r1_press = 0 # R1 button debounce for TOF_TRIM_ENABLE flag
debounce_time = 0.25   # 250 ms

# ******************************************************************************
# Initialise CAN.
# ******************************************************************************
'''
This relies on the can0_enable.py and daemon_helpers.py runnning at startup as a
Linux service to initialise GPIO and CAN bus. See \daemons\README.md
'''

can0 = can.Bus(interface='socketcan', channel='can0')

# ******************************************************************************
# Initialise ToF sensors as objects from TofSensor class in tof.py
# ******************************************************************************

tof_sensors = [
    tof.TofSensor(tof_idx=1),
    tof.TofSensor(tof_idx=2),
    tof.TofSensor(tof_idx=3),
    tof.TofSensor(tof_idx=4),
]
# The below variables are used to sequentially read each ToF sensor instead of 
# polling altogether. 
# Polling all at the same time was causing performance issues.
tof_index = 0
TOF_PERIOD = 0.005  # 200 Hz. Can be used to indepentently reduce ToF poll freq
last_tof_poll = 0.0

# ******************************************************************************
# Initialise IMU
# Followed example from: https://github.com/CoRoLab-Berlin/bmi270_python
# ******************************************************************************

imu = BMI270(I2C_PRIM_ADDR) # 0x68 on i2c channel 7.
imu.load_config_file() # Required to load from BMI270 module to the IMU itelf

imu.set_mode(PERFORMANCE_MODE)
imu.set_acc_range(ACC_RANGE_4G) # Sets the accelerometer for +/- 4g range
imu.set_gyr_range(GYR_RANGE_1000) # Sets the gyroscope to 1000 DPS
imu.set_acc_odr(ACC_ODR_200) # ODR is output data rate
imu.set_gyr_odr(GYR_ODR_200)
imu.set_acc_bwp(ACC_BWP_OSR4)
imu.set_gyr_bwp(GYR_BWP_OSR4)
imu.disable_fifo_header()
imu.enable_data_streaming()
imu.enable_acc_filter_perf()
imu.enable_gyr_noise_perf()
imu.enable_gyr_filter_perf()

ACC_SCALE_4G = 1.0/8192.0 # Ratio for 16-bit raw (+/-4g mode) to g units.
GYRO_SCALE_1000DPS = 1000.0 / 32768.0 # 16-bit signed degrees per second.

# IMU angle smoothing
ANGLE_ALPHA = 0.15
filtered_pitch_deg = 0.0
filtered_roll_deg = 0.0

# ******************************************************************************
# Attitude Targets and Proportional and Differential Controller Values
# ******************************************************************************

SUS_READY_DEG = angle_height_calc.DEFAULT_SUS_ANGLE_DEG - 360 # Suspension angle
SUS_STANDBY_DEG = -90.0 # Verticle mode to reduce electrical current demand
FLUIDITY = 0.1 # Parameter passed into move() method

# Set Target Limits (joystick or future payload protection ability)
TARGET_PITCH_MIN_DEG = -60
TARGET_PITCH_MAX_DEG = 25

TARGET_ROLL_MIN_DEG = -20.0
TARGET_ROLL_MAX_DEG = 20.0

# Pitch PD Constants
KP_PITCH = 0.9
KD_PITCH = 0.15

# Roll PD Constants
KD_ROLL = 0.15
KP_ROLL  = 0.9

# PD Controller output clamp limits (conservative limits for stability)
CTRL_PITCH_MIN_DEG = -25.0
CTRL_PITCH_MAX_DEG = 25.0

CTRL_ROLL_MIN_DEG = -25.0
CTRL_ROLL_MAX_DEG = 25.0

# Low-pass Filter Constant
CMD_ALPHA = 0.12
filtered_pitch_cmd = 0.0
filtered_roll_cmd = 0.0

# ******************************************************************************
# Steering and Velocity Constants
# ******************************************************************************

STEERING_FLUIDITY = 0.2
RPM_FWD_LIMIT = 200
RPM_REV_LIMIT = -100

# ******************************************************************************
# Trim parameters. 
# ******************************************************************************
'''
Trim overlays on top of PD controlled targets just before 'move()' is applied to
motors.
'''

# Individual leg trim from time-of-flight sensors
# Constants
TOF_TRIM_RATE = 0.8
TOF_TRIM_CLAMP_UPPER = 35
TOF_TRIM_CLAMP_LOWER = 0
# Variables
fl_tof_trim_deg = 0.0       # Front-right
fr_tof_trim_deg = 0.0       # Front-left
rear_tof_trim_deg = 0.0

# Individual leg trim from joystick
# Constants
MANUAL_TRIM_RATE = 1.0 # Default to 0.2 for slow safe response.
# Variables
fl_manual_trim_deg = 0.0 
fr_manual_trim_degree = 0.0
rear_manual_trim_deg = 0.0


# ******************************************************************************
# Initialise Motors
# ******************************************************************************
'''
This creates motors as objects of the MITMotor base class from mit_motors.py
module. The primary reason is they share similar characterists such as using 
the MIT-style CAN frame packing shape. (Postition, Velocity, Kp, Kd, Torque).
The only mode used in this project for the suspension and steering motors is 
position. The STM32 wheel-driving motors needed a custom CAN frame.
'''


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
    default_kp=8,
    default_kd=0.2,
)

# Wheel-driving motors (ST B-G431B-ESC1 controller with iFlight GM3506 motors)

# left_wheel_motor = STM32_ESC(
#     bus=can0,
#     motor_id=5,
#     direction=1,
#     limit_rpm_lower=RPM_REV_LIMIT,
#     limit_rpm_upper=RPM_FWD_LIMIT # 200 observed as optimal.
# )

# right_wheel_motor = STM32_ESC(
#     bus=can0,
#     motor_id=6,
#     direction=1,
#     limit_rpm_lower=RPM_REV_LIMIT,
#     limit_rpm_upper=RPM_FWD_LIMIT
# )

# rear_wheel_motor = STM32_ESC(
#     bus=can0,
#     motor_id=7,
#     direction=1,
#     limit_rpm_lower=RPM_REV_LIMIT,
#     limit_rpm_upper=RPM_FWD_LIMIT
# )


# ******************************************************************************
# Start Motors
# ******************************************************************************
'''
Startup has a slightly different routine per manufacturer. See class methods.
'''

left_sus_motor.startup()
time.sleep(0.05)

right_sus_motor.startup()
time.sleep(0.05)

rear_motor.startup()
time.sleep(0.05)

steering_motor.startup()
time.sleep(0.05)

# left_wheel_motor.startup()
# time.sleep(0.05)

# right_wheel_motor.startup()
# time.sleep(0.05)

# rear_wheel_motor.startup()
# time.sleep(0.1)


# ******************************************************************************
# Waiting Lobby Before Main Loop
# ******************************************************************************

try:
    # Frequency of loops below
    dt = 0.01 # 0.01 is 100 Hz
    last_tof_poll = time.monotonic() # Separate timer for TOF sensors
    
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
    while count < 200: # Needs 200 or ToF sensors won't cal properly.
        
        left_sus_motor.move(SUS_READY_DEG) # SUS_READY_DEG is normally -70
        right_sus_motor.move(SUS_READY_DEG)
        rear_motor.move(SUS_READY_DEG)
        steering_motor.move(0)

        time.sleep(dt)
        count = count + 1

    # Calibrate ToF sensors
    time.sleep(2) # Wait 2 sec to settle movement
    # Warm up sensors first
    count = 0
    while count < 10: # Poll 10 times for average
        for sensor in tof_sensors:
            sensor.poll_once()
        time.sleep(0.1)
        count = count + 1

    # Calibrate from warmed up sensors.
    count = 0
    while count < 10: # Poll 10 times for average
        for sensor in tof_sensors:
            sensor.poll_once()
            print(
                f"raw: {sensor.results.distance_mm:.1f}",
                f"raw avg: {sensor.accumulate:.1f}, "
                f"offset: {sensor.offset:.1f}, "
                f"cal: {sensor.cal_distance:.1f}"
            )
            sensor.accumulate=sensor.accumulate + sensor.results.distance_mm
        time.sleep(0.1)
        count = count + 1

    # Average distance measurement and set the offset for each sensor
    for sensor in tof_sensors:
        sensor.accumulate = sensor.accumulate/10 # Average of 10 readings
        sensor.offset = angle_height_calc.tof_offset(sensor.accumulate)
        # Initiate first height before main loop
        sensor.cal_distance = sensor.accumulate - sensor.offset

        # Uncomment print statement to debug ToF calibration routine.
        # print(
        #     f"raw avg: {sensor.accumulate:.1f}, "
        #     f"offset: {sensor.offset:.1f}, "
        #     f"cal: {sensor.cal_distance:.1f}"
        # )
        sensor.accumulate = 0 # Reset value after offsets are applied.
    
    # Poll all ToF sensors once with calibration before loop start
    for sensor in tof_sensors:
        sensor.poll_once()
        sensor.cal_distance = (
                sensor.results.distance_mm
                - sensor.offset)


# ******************************************************************************
#                         --------------------
#                   Begin Main Application While Loop
#                         --------------------
# ******************************************************************************
    while True:

        # **********************************************************************
        # Collect time-of-flight sensor data
        # Note: Polling all sensors every cycle slows down loop significantly
        # **********************************************************************
        now = time.monotonic()

        if now - last_tof_poll >= TOF_PERIOD:

            # for sensor in tof_sensors: # Uncomment to poll all at once
            #     sensor.poll_once()

            tof_sensors[tof_index].poll_once() # Uncomment to poll sequentially
            tof_sensors[tof_index].cal_distance = (
                tof_sensors[tof_index].results.distance_mm
                - tof_sensors[tof_index].offset)
            # Change index for next sensor on next cycle.
            tof_index = (tof_index + 1) % len(tof_sensors)
            last_tof_poll = now

        # **********************************************************************
        # Use ToF to control trim sensor
        # ToF 0 for left
        # ToF 1 for right
        # Tof 2 for rear
        # Tof 3 for centre but unused
        # **********************************************************************
        if tof_trim_enabled:  # Check TOF_TRIM_ENABLED flag 
            FL_TRIM_TARGET_DEG = (
                angle_height_calc.tof_to_sus_angle(tof_sensors[0].cal_distance)
                - SUS_READY_DEG
            )
            fl_tof_trim_deg += TOF_TRIM_RATE * (
                FL_TRIM_TARGET_DEG - fl_tof_trim_deg
            )
            fl_tof_trim_deg = clamp(fl_tof_trim_deg,
                                    TOF_TRIM_CLAMP_LOWER, TOF_TRIM_CLAMP_UPPER)


            # FR_TRIM_TARGET_DEG = (
            #     angle_height_calc.tof_to_sus_angle(tof_sensors[1].cal_distance)
            #     - SUS_READY_DEG
            # )
            # FR_TOF_TRIM_DEG += TOF_TRIM_RATE * (
            #     FR_TRIM_TARGET_DEG - FR_TOF_TRIM_DEG
            # )

            # REAR_TRIM_TARGET_DEG = (
            #     angle_height_calc.tof_to_sus_angle(tof_sensors[2].cal_distance)
            #     - SUS_READY_DEG
            # )
            # REAR_TOF_TRIM_DEG += TOF_TRIM_RATE * (
            #     REAR_TRIM_TARGET_DEG - REAR_TOF_TRIM_DEG
            # )

        else:
            fl_tof_trim_deg = 0.0
            fr_tof_trim_deg = 0.0
            rear_tof_trim_deg = 0.0

        # **********************************************************************
        # Collect IMU data
        # **********************************************************************
        acc = imu.get_raw_acc_data() # Collect accelerometer data from sensor
        gyr = imu.get_raw_gyr_data() # Collect gyroscope data from sensor

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
        
        # Apply low-pass filter to collected IMU data
        filtered_pitch_deg += ANGLE_ALPHA * (pitch_deg - filtered_pitch_deg)
        filtered_roll_deg += ANGLE_ALPHA * (roll_deg - filtered_roll_deg)

        pitch_deg = filtered_pitch_deg
        roll_deg = filtered_roll_deg
        
        # Organise gyroscope data
        pitch_rate_dps = gy_dps
        roll_rate_dps = -gx_dps # Inverted to match motor model
        
        # **********************************************************************
        # Collect Joystick Events
        # **********************************************************************
        '''
        Use pygame_test_inputs.py in /tools/ to discover live button mapping.
        '''
        
        pygame.event.get() # Collects the current state frame for joystick

        # Extract right joystick data for body attitude control. 
        # (-js. means invert axis)
        pitch_axis_target_input = joy.deadzone(-js.get_axis(joy.AXIS_R_Y))
        roll_axis_target_input = joy.deadzone(-js.get_axis(joy.AXIS_R_X))

        # Extract left joystick data for steering control
        steering_axis = joy.deadzone(js.get_axis(joy.AXIS_L_X))

        # all_height_axis = joy.deadzone(-js.get_axis(joy.AXIS_R_Y))

        # Extract and combine RPM target from right and left triggers
        pos_speed = joy.deadzone(js.get_axis(joy.AXIS_R2))
        neg_speed = joy.deadzone(js.get_axis(joy.AXIS_L2))
        axis = joy.triggers_to_axis(pos_speed , neg_speed) # R2 = fwd, L2 = rev



        # Manual requests for trim control of individual legs
        if js.get_hat(joy.HAT_DPAD) == (-1, 0):
            if js.get_button(joy.BTN_OPTIONS):
                fl_manual_trim_deg -= MANUAL_TRIM_RATE  # extend/lower FL
            else:
                fl_manual_trim_deg += MANUAL_TRIM_RATE # retract/raise FL

        if js.get_hat(joy.HAT_DPAD) == (1, 0):
            if js.get_button(joy.BTN_OPTIONS):
                fr_manual_trim_degree -= MANUAL_TRIM_RATE   # extend/lower FR
            else:
                fr_manual_trim_degree += MANUAL_TRIM_RATE  # retract/raise FR

        if js.get_hat(joy.HAT_DPAD) == (0, -1):
            if js.get_button(joy.BTN_OPTIONS):
                rear_manual_trim_deg -= MANUAL_TRIM_RATE # extend/lower REAR
            else:
                rear_manual_trim_deg += MANUAL_TRIM_RATE # retract/raise REAR

        # Reset trim values
        if js.get_hat(joy.HAT_DPAD) == (0, 1):
            # Press UP + Options to gradually rise
            if js.get_button(joy.BTN_OPTIONS): # Low current vertical stance
                fl_manual_trim_deg = SUS_STANDBY_DEG - SUS_READY_DEG
                fr_manual_trim_degree = SUS_STANDBY_DEG - SUS_READY_DEG
                rear_manual_trim_deg = SUS_STANDBY_DEG - SUS_READY_DEG
            # Just press UP to immediately return to normal (-70 degrees)
            else:
                fl_manual_trim_deg = 0.0
                fr_manual_trim_degree = 0.0
                rear_manual_trim_deg = 0.0


        # Check for lie down requests
        if js.get_button(joy.BTN_CROSS) == 1:
            while True:
                pygame.event.get() # Collect joystick eventss
                
                # Lie down the robot
                steering_motor.move(0)
                left_sus_motor.move(0)
                right_sus_motor.move(0)
                rear_motor.move(0)
                # left_wheel_motor.send_rpm(0)
                # right_wheel_motor.send_rpm(0)
                # rear_wheel_motor.send_rpm(0)

                if js.get_button(joy.BTN_TRIANGLE) == 1:
                    break
                        # Check for EXIT or MODE requests
                if js.get_button(joy.BTN_CREATE) == 1:
                    exit_flag = True #  Set flag due to inner while loop.
                    break

                time.sleep(dt)

        
        # Toggle for TOF_TRIM_ENABLE requests
        if js.get_button(joy.BTN_R1) == 1:
            current_time = time.monotonic()

            if current_time - last_r1_press > debounce_time:

                tof_trim_enabled = not tof_trim_enabled # Toggle flag
                last_r1_press = current_time

        # Check for EXIT or MODE requests
        if js.get_button(joy.BTN_CREATE) == 1:
            break
        if exit_flag is True:
            break


        # **********************************************************************
        # Set Targets
        # **********************************************************************
        '''
        Map the normalised joystick axes (right-stick) as a multiplier input.
        If the joystick input is centred, then the input multiplier is 0 for 
        each axis.
        A target of 0 for pitch and 0 for roll means level rover body.
        Placeholder for future steering and velocity mixer.
        '''

        # If first parameter is neutral position (0), then target is default 0.
        target_pitch_deg = map_axis_to_asymmetric_angle(
            pitch_axis_target_input,
            TARGET_PITCH_MIN_DEG,
            TARGET_PITCH_MAX_DEG,
        )
        # If first parameter is neutral position (0), then target is default 0.
        target_roll_deg = map_axis_to_asymmetric_angle(
            roll_axis_target_input,
            TARGET_ROLL_MIN_DEG,
            TARGET_ROLL_MAX_DEG,
        )

        # left_target_speed= steer_vel_mixer.axis_to_rpm(axis, 
        #                                     left_wheel_motor.limit_rpm_upper)
        # right_target_speed= steer_vel_mixer.axis_to_rpm(axis, 
        #                                     right_wheel_motor.limit_rpm_upper)
        # rear_target_speed= steer_vel_mixer.axis_to_rpm(axis, 
        #                                     rear_wheel_motor.limit_rpm_upper)

        # **********************************************************************
        # Proportional and Differtial Control
        # **********************************************************************

        # Error is target minus body angle deadband (ignores 0.5 degree errors)
        pitch_error = angle_deadband(target_pitch_deg - pitch_deg)
        roll_error  = angle_deadband(target_roll_deg - roll_deg) 

        # Proportional controller (kp pitch * error)
        # Derivative controller (kd pitch * current rate)
        # P term - D term
        pitch_cmd = (KP_PITCH * pitch_error) - (KD_PITCH * pitch_rate_dps)
        roll_cmd  = (KP_ROLL * roll_error) - (KD_ROLL * roll_rate_dps)

        # Apply clamp
        pitch_cmd = clamp(pitch_cmd, CTRL_PITCH_MIN_DEG, CTRL_PITCH_MAX_DEG)
        roll_cmd = clamp(roll_cmd, CTRL_ROLL_MIN_DEG, CTRL_ROLL_MAX_DEG)

        # First order lowpass filter
        filtered_pitch_cmd += CMD_ALPHA * (pitch_cmd - filtered_pitch_cmd)
        filtered_roll_cmd += CMD_ALPHA * (roll_cmd - filtered_roll_cmd)

        pitch_cmd = filtered_pitch_cmd
        roll_cmd = filtered_roll_cmd

        # Send pitch and roll values to mixer function for 3 limbs.
        # Relative suspension angles are returned.
        pd_targets = mix_body_degrees(pitch_cmd, roll_cmd)

        # print(
        #     f"Tgt P/R: {target_pitch_deg:6.2f}, {target_roll_deg:6.2f} | "
        #     f"IMU P/R: {pitch_deg:6.2f}, {roll_deg:6.2f} | "
        #     f"Err P/R: {pitch_error:6.2f}, {roll_error:6.2f} | "
        #     f"Cmd P/R: {pitch_cmd:6.2f}, {roll_cmd:6.2f}"
        #     )
        
        # **********************************************************************
        # Final targets for sending to motors.
        # **********************************************************************
        '''
        The final target commands are summing junctions of the default 
        suspension angle (SUS_READY_DEG = -70 degrees), the mixed pitch/roll
        target outputs from the PD controller, the ToF trim adjustments, and the
        manual trim from the D-PAD buttons (not the joystick axis).
            
        Future intent: 
            - Replace the ToF trim adjustments with the state 
              estimation outputs from an unscented Kalman filter (UKF) as a 
              covariance between velocity and ToF detection.
            - Add centre ToF sensor data to counter the output of the UKF to 
              keep average rover height floating. 
        '''
        front_left_cmd = (SUS_READY_DEG + pd_targets["front_left"] 
                          + fl_tof_trim_deg + fl_manual_trim_deg)
        front_right_cmd = (SUS_READY_DEG + pd_targets["front_right"]
                           + fr_tof_trim_deg + fr_manual_trim_degree)
        rear_cmd = (SUS_READY_DEG + pd_targets["rear"]
                    + rear_tof_trim_deg + rear_manual_trim_deg)


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

        # Uncomment for debugging
        # print(
        #     f"ToF cal: {tof_sensors[0].cal_distance:.1f}, "
        #     f"{tof_sensors[1].cal_distance:.1f}, "
        #     f"{tof_sensors[2].cal_distance:.1f} | "
        #     f"Trim: {fl_tof_trim_deg:.1f}, "
        #     f"{fr_tof_trim_deg:.1f}, "
        #     f"{rear_tof_trim_deg:.1f}"
        # )

        time.sleep(dt)

except KeyboardInterrupt:
    print("Keyboard interrupt received. Shutting down safely...")


# ******************************************************************************
# Safe Shutdown Sequence
# ******************************************************************************
    '''
    The 'finally' clause safely shuts down rover instead on instant motor 
    collapse.
    '''

finally:
    # Lie down robot
    dt = 0.01

    count = 0
    while count < 200: # Longer time to allow reliable shutdown.
    
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
    time.sleep(0.05)
    left_sus_motor.shutdown()
    time.sleep(0.05)
    right_sus_motor.shutdown()
    time.sleep(0.05)
    rear_motor.shutdown()
    time.sleep(0.05)
    # left_wheel_motor.shutdown()
    # time.sleep(0.05)
    # right_wheel_motor.shutdown()
    # time.sleep(0.05)
    # rear_wheel_motor.shutdown()
    # time.sleep(0.05)

    # Turn off all XSHUT signals to ToF sensors to allow re-run
    tof.xshut_reset()


# ******************************* End of file **********************************
