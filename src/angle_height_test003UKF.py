import numpy as np
import matplotlib.pyplot as plt
from angle_height_calc import *

# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------

object_height = 20       # mm
object_width = 20        # mm
object_start = 100       # mm

sample_spacing = 2       # mm between terrain samples
total_distance = 300     # mm

filter_alpha = 0.3       # larger = faster, smaller = smoother


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def height_to_tof_distance(height):
    ground_y = GROUND_CONTACT_Y + height

    tof_distance = (
        ground_y - TOF_XY[1]
    ) / TOF_DIRECTION[1]

    return tof_distance


def tof_distance_to_hit_xy(tof_distance):
    return TOF_XY + tof_distance * TOF_DIRECTION


def calculate_distance_delay(height):
    tof_distance = height_to_tof_distance(height)
    tof_hit_xy = tof_distance_to_hit_xy(tof_distance)

    wheel_contact_x = WHEEL_CENTRE_XY[0]

    return abs(wheel_contact_x - tof_hit_xy[0])


def delay_signal_by_distance(signal, distance_delay, sample_spacing):
    delay_samples = int(round(distance_delay / sample_spacing))

    delayed = np.zeros_like(signal)

    if delay_samples <= 0:
        return signal.copy(), delay_samples

    delayed[delay_samples:] = signal[:-delay_samples]

    return delayed, delay_samples


def low_pass_filter(signal, alpha):
    filtered = np.zeros_like(signal)

    filtered[0] = signal[0]

    for i in range(1, len(signal)):
        filtered[i] = (
            alpha * signal[i]
            + (1 - alpha) * filtered[i - 1]
        )

    return filtered


def height_to_suspension_angle(height):
    tof_distance = height_to_tof_distance(height)
    return tof_to_sus_angle(tof_distance)


# ---------------------------------------------------------
# Fake terrain: flat ground with one square object
# ---------------------------------------------------------

x = np.arange(0, total_distance, sample_spacing)

height_seen_by_tof = np.zeros_like(x, dtype=float)

object_end = object_start + object_width

height_seen_by_tof[
    (x >= object_start) & (x <= object_end)
] = object_height


# ---------------------------------------------------------
# Calculate geometry-based distance delay
# ---------------------------------------------------------

tof_to_wheel_delay = calculate_distance_delay(object_height)

height_delayed, delay_samples = delay_signal_by_distance(
    height_seen_by_tof,
    tof_to_wheel_delay,
    sample_spacing
)


# ---------------------------------------------------------
# Filter delayed terrain height
# ---------------------------------------------------------

height_filtered = low_pass_filter(
    height_delayed,
    filter_alpha
)


# ---------------------------------------------------------
# Convert filtered height into suspension angle
# ---------------------------------------------------------

target_angles = np.array([
    height_to_suspension_angle(h)
    for h in height_filtered
])


# ---------------------------------------------------------
# Print useful values
# ---------------------------------------------------------

print("Object height:", object_height, "mm")
print("Object width:", object_width, "mm")
print("Calculated ToF-to-wheel distance delay:", round(tof_to_wheel_delay, 2), "mm")
print("Delay samples:", delay_samples)
print("Flat ground angle:", round(height_to_suspension_angle(0), 2), "degrees")
print("20 mm object angle:", round(height_to_suspension_angle(object_height), 2), "degrees")


# ---------------------------------------------------------
# Combined plot: height + suspension angle
# ---------------------------------------------------------

fig, ax1 = plt.subplots(figsize=(11, 6))

# Height plots (left axis)
ax1.plot(x, height_seen_by_tof, label="Height seen by ToF")
ax1.plot(x, height_delayed, "--", label="Height delayed to wheel")
ax1.plot(x, height_filtered, label="Delayed + filtered height")

ax1.set_xlabel("Rover travel distance (mm)")
ax1.set_ylabel("Terrain height (mm)")
ax1.grid(True)

# Second axis for angle
ax2 = ax1.twinx()

ax2.plot(
    x,
    target_angles,
    "r",
    linewidth=2,
    label="Suspension angle"
)

ax2.set_ylabel("Suspension angle (degrees)")

# ---------------------------------------------------------
# Combine legends
# ---------------------------------------------------------

lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()

ax1.legend(lines_1 + lines_2, labels_1 + labels_2)

plt.title("ToF detection, delayed terrain, and resulting suspension angle")
plt.show()