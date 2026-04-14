from datetime import datetime
import matplotlib
# matplotlib.use("TkAgg")  # or Qt5Agg
import matplotlib.pyplot as plt
print(matplotlib.get_backend())
xs = [0, 1, 2, 3, 4, 5, 6, 7]
ys = [1, 0.3, -2.3, 5.1, 7.6, -0.2, -1.8, 4]

plt.plot(xs, ys)
timestamp = datetime.now().strftime("%y%m%d%H%M%S")

# plt.show()
plt.savefig(f"plot_{timestamp}.png")
