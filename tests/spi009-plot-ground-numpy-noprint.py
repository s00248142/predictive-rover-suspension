import time
import spidev
import board
import adafruit_vl53l4cd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

ANGLE_REG = 0x3FFF  # angle register (14-bit address space)
READ_BIT  = 1 << 14
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

# ToF sensor radius position
tof_radius = 20
joint_y = 103 

vl53 = adafruit_vl53l4cd.VL53L4CD(i2c)

def even_parity_15bits(x: int) -> int:
    # parity over bits 0..14, parity bit is bit15 so that total #ones is even
    ones = bin(x & 0x7FFF).count("1")
    return 0 if (ones % 2 == 0) else 1

def make_read_cmd(addr: int) -> int:
    cmd = (addr & 0x3FFF) | READ_BIT          # bits 13..0 addr, bit14=R
    cmd |= (even_parity_15bits(cmd) << 15)    # bit15 parity
    return cmd

def xfer16(spi: spidev.SpiDev, word: int) -> int:
    hi = (word >> 8) & 0xFF
    lo = word & 0xFF
    rx = spi.xfer2([hi, lo])
    return (rx[0] << 8) | rx[1]

# OPTIONAL: can set non-default values
vl53.inter_measurement = 0
vl53.timing_budget = 10

vl53.start_ranging()

spi = spidev.SpiDev()
spi.open(0, 0)                 # CE0 (/dev/spidev0.0)
spi.max_speed_hz = 1_000_000
spi.mode = 0b01                # SPI mode 1 per datasheet :contentReference[oaicite:1]{index=1}
spi.bits_per_word = 8

read_angle_cmd = make_read_cmd(ANGLE_REG)

xfer16(spi, read_angle_cmd)          # prime
raw = xfer16(spi, 0x0000)            # read response

err = (raw >> 14) & 0x1              # error flag
angle14 = raw & 0x3FFF               # 14-bit angle
deg_zero = angle14 * 360.0 / 16384.0
# points = []
points = np.empty((0, 2))   # Nx2 array

print("Ready!")

deg = ((angle14 * 360.0 / 16384.0) + 360 - deg_zero) % 360
# while deg > 355 or deg < 10:
#     xfer16(spi, read_angle_cmd)          # prime
#     raw = xfer16(spi, 0x0000)            # read response
#     err = (raw >> 14) & 0x1              # error flag
#     angle14 = raw & 0x3FFF               # 14-bit angle
#     deg = ((angle14 * 360.0 / 16384.0) + 360 - deg_zero) % 360
#     # print(angle14)
#     # print(deg)
#     time.sleep(0.01)

# print("Start!")
try:

    while deg > 355 or deg < 10:
        xfer16(spi, read_angle_cmd)          # prime
        raw = xfer16(spi, 0x0000)            # read response
        err = (raw >> 14) & 0x1              # error flag
        angle14 = raw & 0x3FFF               # 14-bit angle
        deg = ((angle14 * 360.0 / 16384.0) + 360 - deg_zero) % 360
        # print(angle14)
        # print(deg)
        time.sleep(0.01)
    print("Start!")

    while deg > 295:
        # AS5048A returns data for the *previous* command,
        # so do a "command frame" then a "dummy frame" to read the result.
        xfer16(spi, read_angle_cmd)          # prime
        raw = xfer16(spi, 0x0000)            # read response

        err = (raw >> 14) & 0x1              # error flag
        angle14 = raw & 0x3FFF               # 14-bit angle
        deg = ((angle14 * 360.0 / 16384.0) + 360 - deg_zero) % 360

        vl53.clear_interrupt()

        # print(f"raw=0x{raw:04X} err={err} angle={angle14} deg={deg:.2f} Distance: {vl53.distance} cm")

        ########

        measured_rel_range = vl53.distance * 10
        angle_rad = np.deg2rad(360 - deg) # Temorarily gives correct answer for quadrant 4 only
        tof_abs_pos_x = np.cos(angle_rad)*tof_radius # Gives obj_adjacent horizontal from (0, y) (note: radius is hypoteneuse)
        tof_abs_pos_y = joint_y - (np.sin(angle_rad)*tof_radius) # Joint y is the height of the joint (x, 103). # Gives obj_oppositesite (vertical) from (0, y) (note: radius is hypoteneuse)
        # print(f"ToF coordinates: ({tof_abs_pos_x},{tof_abs_pos_y})")

        expected_rel_range = tof_abs_pos_y/np.cos(angle_rad) # Calculate the hypoteneuse (expected range). It's the product of the Tof absolute height * (1/cos(measured angle))
        # print(f"Expected Range: {expected_rel_range}")

        obj_adjacent = np.cos(angle_rad) * measured_rel_range
        obj_opposite = np.sin(angle_rad) * measured_rel_range

        obj_point_y = tof_abs_pos_y - obj_adjacent
        obj_point_x = -1 * (obj_opposite - tof_abs_pos_x)
        sensor_compensation = (-0.16 * obj_point_x) - 8
        obj_point_y = obj_point_y - sensor_compensation
        # print(f"Object coordinates: ({obj_point_x},{obj_point_y})\n")

        # points.append((obj_point_x, obj_point_y))
        points = np.vstack([points, [obj_point_x, obj_point_y]])

        ########

        time.sleep(0.01)

except KeyboardInterrupt:
    print('\nExited by keyboard interrupt.')
    pass

finally:
    spi.close()
    
    # Extract for plotting
    # x, y = zip(*points)
    # plt.scatter(x, y)
    plt.scatter(points[:,0], points[:,1])
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    plt.xlim(-170, 25)
    plt.ylim(-20, 120)

    # plt.show()
    plt.savefig(f"plot_{timestamp}.png")
    print('Finished!')