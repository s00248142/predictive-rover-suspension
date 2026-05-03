

from smbus2 import SMBus
import time
import struct

BMI270_ADDR = 0x68
bus = SMBus(7) # Equivalent to Seeed IIC1 bus

def write(reg, value):
    bus.write_byte_data(BMI270_ADDR, reg, value)
    time.sleep(0.005)

def read_bytes(reg, length):
    return bus.read_i2c_block_data(BMI270_ADDR, reg, length)

def to_int16(lsb, msb):
    return struct.unpack("<h", bytes([lsb, msb]))[0]

print("Chip ID:", hex(bus.read_byte_data(BMI270_ADDR, 0x00)))

# Basic power/config attempt
write(0x7C, 0x00)  # power save off
write(0x7D, 0x0E)  # enable accel + gyro + temp

time.sleep(0.1)

while True:
    data = read_bytes(0x0C, 12)

    ax = to_int16(data[0], data[1])
    ay = to_int16(data[2], data[3])
    az = to_int16(data[4], data[5])

    gx = to_int16(data[6], data[7])
    gy = to_int16(data[8], data[9])
    gz = to_int16(data[10], data[11])

    # print(f"accel raw: {ax:6d} {ay:6d} {az:6d} | gyro raw: {gx:6d} {gy:6d} {gz:6d}")

    for reg in [0x03, 0x21, 0x7C, 0x7D]:
        print(hex(reg), hex(bus.read_byte_data(BMI270_ADDR, reg)))

    time.sleep(0.1)