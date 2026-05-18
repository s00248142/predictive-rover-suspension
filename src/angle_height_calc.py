'''
********************************************************************************
* File Name: angle_height_calc.py
* Description: Geometric representation of the suspension, wheel, and senors.
*   All suspension motor, ToF sensor, and wheel groups were designed to have
*   identical geometry, which means this module can be ustilised for all 
*   rover limb reactions.
*   Using the suspension centre as the origin (0,0) NumPy is used to calculate 
*   the cartesian coordinates of the ToF sensor, its unit vector, and the 
*   ideal ground detection distance (103.75 mm)
*   Two functions are provided:
*   1. tof_offset() to calibrate ToF aensors to their ideal geometry
*   2. tof_to_sus_angle() to determine the require motor angle from Tof input
* Programmer: Alan Ryan (s00248142)
* Date: 06/05/2025
* Version: 5.0
********************************************************************************
'''

import numpy as np

#*******************************************************************************
# Define Physical Geometry Constants
#*******************************************************************************

# Suspension geometry
ORIGIN = np.array([0, 0]) # Centre of suspension from left plane view
# SUS_ANGLE_DEG = 290 # Equivalent to -70 degrees
DEFAULT_SUS_ANGLE_DEG = 290 # Equivalent to -70 degrees
SUS_RADIUS = 87.5 # Centre of suspension motor to centre of wheel
WHEEL_RADIUS = 45 # 90mm tyres

# Time-of-flight sensor geometry
TOF_RADIUS = 40 # Radial offset from centre of suspension
TOF_ANGLE_DEG = 245 # Sensor is at 245 degrees (-25 forward from vert)

# Calculate ToF cartesian coordinates relative to suspension origin
TOF_ANGLE_RAD = np.deg2rad(TOF_ANGLE_DEG) 
TOF_XY = np.array([TOF_RADIUS * np.cos(TOF_ANGLE_RAD),
                TOF_RADIUS * np.sin(TOF_ANGLE_RAD)])

# Calculate time-of-flight direction unit vector
TOF_DIRECTION = np.array([
    np.cos(TOF_ANGLE_RAD),
    np.sin(TOF_ANGLE_RAD)
])

# Ideal standby ground contact coordinates 
SUS_ANGLE_RAD = np.deg2rad(DEFAULT_SUS_ANGLE_DEG)
WHEEL_CENTRE_XY = np.array([SUS_RADIUS * np.cos(SUS_ANGLE_RAD),
                            SUS_RADIUS * np.sin(SUS_ANGLE_RAD)])
GROUND_CONTACT_Y = WHEEL_CENTRE_XY[1] - WHEEL_RADIUS # negative y from origin

# Calculate what the ToF sensor should be reading based on Y elements
EXPECTED_TOF_DISTANCE = (GROUND_CONTACT_Y - TOF_XY[1]) / TOF_DIRECTION[1]

print(EXPECTED_TOF_DISTANCE) # Uncomment to show in terminal

#*******************************************************************************
# Functions to return calibrated offset and desired suspension angle.
#*******************************************************************************

# Function to return calibrated offset to object after settling period in app
def tof_offset(measured_distance):
    
    offset = measured_distance - EXPECTED_TOF_DISTANCE
    
    return offset

# print(tof_offset(90)) Uncomment and run for debugging.

# Function to take the ToF measurement and calculate required suspension angle.
def tof_to_sus_angle(cal_measured_distance):
    
    measured_ground_y = TOF_XY[1] + (cal_measured_distance * TOF_DIRECTION[1])
    wheel_centre_y = measured_ground_y + WHEEL_RADIUS
    angle_rad = np.arcsin(wheel_centre_y / SUS_RADIUS) # Sine inverse
    angle_deg = np.rad2deg(angle_rad) # small angle

    return angle_deg

# ******************************* End of file **********************************