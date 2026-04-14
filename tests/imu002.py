import time, math
from bmi270.BMI270 import BMI270

def accel_to_pitch_roll(ax, ay, az):
    # ax/ay/az in g
    roll  = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az))
    return pitch, roll

def rad2deg(x): 
    return x * 180.0 / math.pi

imu = BMI270(0x68)
imu.load_config_file()

# Enable sensors (required before reads on this driver)
imu.enable_acc()
imu.enable_gyr()

# Optional: set ranges/ODR (your class defaults acc=100Hz, gyr=200Hz, ranges set in __init__)
imu.set_acc_odr(200)
imu.set_gyr_odr(200)
# imu.set_acc_range(2)     # if this function expects "g" not m/s^2
# imu.set_gyr_range(1000)  # dps

alpha = 0.95
pitch = 0.0
roll  = 0.0
last = time.time()
i = 0

while True:
    now = time.time()
    dt = now - last
    last = now
    if dt <= 0:
        continue

    # Library-provided reads
    ax, ay, az = imu.get_acc_data()   # typically in g
    gx, gy, gz = imu.get_gyr_data()   # typically in deg/s

    pitch_acc, roll_acc = accel_to_pitch_roll(ax, ay, az)

    # integrate gyro (deg/s -> rad/s)
    gx_r = math.radians(gx)
    gy_r = math.radians(gy)

    pitch = alpha * (pitch + gy_r * dt) + (1 - alpha) * pitch_acc
    roll  = alpha * (roll  + gx_r * dt) + (1 - alpha) * roll_acc

    if i == 40:
        print(f"Pitch: {rad2deg(pitch):7.2f}°, Roll: {rad2deg(roll):7.2f}°")
        i = 0
    else:
        i = i + 1
    # print(f"Pitch: {rad2deg(pitch):7.2f}°, Roll: {rad2deg(roll):7.2f}°")
    
    # time.sleep(0.001)  # ~1000 Hz loop

