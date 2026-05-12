import matplotlib.pyplot as plt

filtered = 0.0
alpha = 0.1

time_values = []
target_values = []
filtered_values = []

for i in range(100):

    # Step input
    if i < 20:
        target = -70
    else:
        target = -50

    # Low-pass filter
    filtered += alpha * (target - filtered)

    time_values.append(i)
    target_values.append(target)
    filtered_values.append(filtered)

plt.plot(time_values, target_values, label="Target")
plt.plot(time_values, filtered_values, label="Filtered")
plt.legend()
plt.grid(True)
plt.show()