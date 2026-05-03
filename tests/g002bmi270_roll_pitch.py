import time
import math
from bmi270.BMI270 import *

IMU = BMI270(I2C_PRIM_ADDR)
IMU.load_config_file()

IMU.set_mode(PERFORMANCE_MODE)
IMU.set_acc_range(ACC_RANGE_4G) # Sets the accelerometer for +/- 4g range
IMU.set_gyr_range(GYR_RANGE_1000)
IMU.set_acc_odr(ACC_ODR_200)
IMU.set_gyr_odr(GYR_ODR_200)
IMU.set_acc_bwp(ACC_BWP_OSR4)
IMU.set_gyr_bwp(GYR_BWP_OSR4)
IMU.disable_fifo_header()
IMU.enable_data_streaming()
IMU.enable_acc_filter_perf()
IMU.enable_gyr_noise_perf()
IMU.enable_gyr_filter_perf()

print("BMI270 streaming...")

while True:
    acc = IMU.get_raw_acc_data() # Collect accelerometer data from sensor
    gyr = IMU.get_raw_gyr_data() # Collect gyroscope data from sensor

    ax = acc[0] # Extract individual accelerometer axes
    ay = acc[1]
    az = acc[2]

    ax_g = ax / 8192.0 # Convert from 16-bit raw (+/-4g mode) to g units.
    ay_g = ay / 8192.0
    az_g = az / 8192.0

    # Derived roll formula from XYZ rotation sequence
    roll_deg = math.degrees(math.atan2(ay_g, az_g))

    # Derived roll formula from XYZ rotation sequence
    pitch_deg = math.degrees(math.atan2(-ax_g, math.sqrt(ay_g**2 + az_g**2)))

    print(f"pitch: {pitch_deg:7.2f} deg | roll: {roll_deg:7.2f} deg")

    time.sleep(0.01)
  