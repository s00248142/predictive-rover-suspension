# from bmi270.BMI270 import *

# imu = BMI270(I2C_PRIM_ADDR)  # common for this library

# print("Loaded config OK")

from bmi270.BMI270 import BMI270
imu = BMI270(0x68)
print([m for m in dir(imu) if not m.startswith("_")])
