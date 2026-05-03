import time
import numpy as np

from bmi270.BMI270 import *


BMI270_1 = BMI270(I2C_PRIM_ADDR)
BMI270_1.load_config_file()

BMI270_1.set_mode(PERFORMANCE_MODE)
BMI270_1.set_acc_range(ACC_RANGE_2G)
BMI270_1.set_gyr_range(GYR_RANGE_1000)
BMI270_1.set_acc_odr(ACC_ODR_200)
BMI270_1.set_gyr_odr(GYR_ODR_200)
BMI270_1.set_acc_bwp(ACC_BWP_OSR4)
BMI270_1.set_gyr_bwp(GYR_BWP_OSR4)
BMI270_1.disable_fifo_header()
BMI270_1.enable_data_streaming()
BMI270_1.enable_acc_filter_perf()
BMI270_1.enable_gyr_noise_perf()
BMI270_1.enable_gyr_filter_perf()

print("BMI270 streaming...")

while True:
    acc = BMI270_1.get_raw_acc_data()
    gyr = BMI270_1.get_raw_gyr_data()

    ax, ay, az = acc
    gx, gy, gz = gyr

    print(
        f"acc raw: {ax:7d} {ay:7d} {az:7d} | "
        f"gyr raw: {gx:7d} {gy:7d} {gz:7d}"
    )

    time.sleep(0.5)
  