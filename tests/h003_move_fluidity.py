'''
********************************************************************************
* File Name: h003_move_fluidity.py
* Description: Test to demonstrate effects of different fluidity numbers
* Test is to simulate at 200ms intervals.
* Programmer: Alan Ryan (s00248142)
* Date: 06/05/2025
* Version: 1.0
********************************************************************************
'''

import matplotlib.pyplot as plt

filtered = -70.0

fluidity = 0.1
min_tau = 0.02
max_tau = 0.45

tau = min_tau + fluidity * (max_tau - min_tau)

dt = 0.01  # 100 Hz loop
alpha = dt / (tau + dt)

time_values = []
target_values = []
filtered_values = []

t = 0.0

while t < 1.0:

    # Step targets
    if t < 0.2:
        target = -70

    elif t < 0.4:
        target = -40

    elif t < 0.6:
        target = -70

    elif t < 0.8:
        target = -40

    else:
        target = -70

    # Low-pass filter
    filtered += alpha * (target - filtered)

    # Store data
    time_values.append(t)
    target_values.append(target)
    filtered_values.append(filtered)

    # Advance simulated time
    t += dt

print(f"tau = {tau:.3f}")
print(f"alpha = {alpha:.3f}")

plt.plot(time_values, target_values, label="Target")
plt.plot(time_values, filtered_values, label="Filtered")

plt.xlabel("Time (s)")
plt.ylabel("Angle (deg)")
plt.title("Fluidity at 0.1 (Low-pass Filter Response)")

plt.legend()
plt.grid(True)
plt.show()