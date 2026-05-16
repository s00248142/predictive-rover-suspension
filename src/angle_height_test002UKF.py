import numpy as np
import matplotlib.pyplot as plt
from angle_height_calc import *

# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------

object_height = 20      # mm
object_width = 20       # mm

sample_spacing = 2      # mm between terrain samples
total_distance = 300    # mm

# tof_to_wheel_delay = 80 # mm

def calculate_distance_delay(object_height):
    object_ground_y = GROUND_CONTACT_Y + object_height

    simulated_tof_distance = (
        object_ground_y - TOF_XY[1]
    ) / TOF_DIRECTION[1]

    tof_hit_xy = TOF_XY + simulated_tof_distance * TOF_DIRECTION

    wheel_contact_x = WHEEL_CENTRE_XY[0]

    return abs(wheel_contact_x - tof_hit_xy[0])

tof_to_wheel_delay = calculate_distance_delay(20)
delay_samples = int(tof_to_wheel_delay / sample_spacing)

# ---------------------------------------------------------
# Fake terrain: flat ground with one 20 mm square object
# ---------------------------------------------------------

x = np.arange(0, total_distance, sample_spacing)

height_raw = np.zeros_like(x, dtype=float)

object_start = 100
object_end = object_start + object_width

height_raw[(x >= object_start) & (x <= object_end)] = object_height

# ---------------------------------------------------------
# Delay the height profile so the wheel reacts later
# ---------------------------------------------------------

height_delayed = np.zeros_like(height_raw)

height_delayed[delay_samples:] = height_raw[:-delay_samples]

# ---------------------------------------------------------
# Optional smoothing / filtering
# ---------------------------------------------------------

filter_alpha = 0.3
height_filtered = np.zeros_like(height_delayed)

for i in range(1, len(height_delayed)):
    height_filtered[i] = (
        filter_alpha * height_delayed[i]
        + (1 - filter_alpha) * height_filtered[i - 1]
    )

# ---------------------------------------------------------
# Convert delayed filtered height into ToF distance,
# then into suspension angle using your actual function
# ---------------------------------------------------------

target_angles = []

for h in height_filtered:
    measured_ground_y = GROUND_CONTACT_Y + h

    simulated_tof_distance = (
        measured_ground_y - TOF_XY[1]
    ) / TOF_DIRECTION[1]

    angle = tof_to_sus_angle(simulated_tof_distance)
    target_angles.append(angle)

target_angles = np.array(target_angles)

# ---------------------------------------------------------
# Plot
# ---------------------------------------------------------

plt.figure(figsize=(11, 6))

plt.plot(x, height_raw, label="Height seen by ToF")
plt.plot(x, height_delayed, "--", label="Height after distance delay")
plt.plot(x, height_filtered, label="Delayed + filtered height")

plt.xlabel("Rover travel distance (mm)")
plt.ylabel("Terrain height (mm)")
plt.title("ToF terrain detection vs delayed wheel reaction")
plt.grid(True)
plt.legend()
plt.show()


plt.figure(figsize=(11, 5))

plt.plot(x, target_angles, label="Suspension target angle")

plt.xlabel("Rover travel distance (mm)")
plt.ylabel("Suspension angle (degrees)")
plt.title("Suspension angle generated from delayed filtered terrain height")
plt.grid(True)
plt.legend()
plt.show()