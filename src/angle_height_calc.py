import numpy as np


#*******************************************************************************
# Define Physical Geometry
#*******************************************************************************

# Suspension geometry
origin = np.array([0, 0]) # Centre of suspension from left plane view
sus_angle_deg = 290 # Equivalent to -70 degrees
sus_radius = 87.5 # Centre of suspension motor to centre of wheel
wheel_radius = 45 # 90mm tyres

# Time-of-flight sensor geometry
tof_radius = 40 # Radial offset from centre of suspension
tof_angle_deg = 245 # Sensor is at 245 degrees (-25 forward from vert)

# Calculate ToF cartesian coordinates relative to suspension origin
tof_angle_rad = np.deg2rad(245) 
tof_xy = np.array([tof_radius * np.cos(tof_angle_rad),
                tof_radius * np.sin(tof_angle_rad)])

# Calculate time-of-flight direction unit vector
tof_direction = np.array([
    np.cos(tof_angle_rad),
    np.sin(tof_angle_rad)
])

# Ideal standby ground contact coordinates 
sus_angle_rad = np.deg2rad(sus_angle_deg)
wheel_centre_xy = np.array([sus_radius * np.cos(sus_angle_rad),
                            sus_radius * np.sin(sus_angle_rad)])
ground_contact_y = wheel_centre_xy[1] - wheel_radius # negative y from origin

# Calculate what the ToF sensor should be reading based on Y elements
expected_tof_y = (ground_contact_y - tof_xy[1]) / tof_direction[1]

print(expected_tof_y)

# Function to return calibrated offset to object after settling perion in app
def tof_offset(measured_tof):
    offset = measured_tof - expected_tof_y
    return offset

print(tof_offset(90))

# Function to take the ToF measurement and calculate required suspension angle.
def tof_to_sus_angle(distance):
    measured_ground_y = tof_xy[1] + distance * tof_direction[1]
    wheel_centre_y = measured_ground_y + wheel_radius
    angle_rad = np.arcsin(wheel_centre_y / sus_radius)
    angle_deg = np.rad2deg(angle_rad) # small angle

    return angle_deg




# Example input
# example_tof_distance = 90




# def suspension_ang_deg(tof_distance):








    

#     tof_delta = tof_distance - tof_baseline




#     ground_point = tof_xy + tof_distance * tof_direction


# new_suspension_angle = suspension_ang_deg(example_tof_distance)

# print(new_suspension_angle)